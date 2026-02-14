"""Tests for SleeperStateMachine — transition table, timer expiry, thread safety."""

from __future__ import annotations

import threading

import pytest

from sleep_manager.state_machine import SleeperState, SleeperStateMachine

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_sm(
    wake_timeout: float = 120.0,
    heartbeat_interval: float = 60.0,
    heartbeat_miss_threshold: int = 3,
    now: float = 1_000_000.0,
) -> tuple[SleeperStateMachine, list[float]]:
    """Return (sm, clock) where clock[0] is the mutable current time."""
    clock = [now]
    sm = SleeperStateMachine(
        wake_timeout=wake_timeout,
        heartbeat_interval=heartbeat_interval,
        heartbeat_miss_threshold=heartbeat_miss_threshold,
        _time_fn=lambda: clock[0],
    )
    return sm, clock


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

class TestInitialState:
    def test_starts_off(self):
        sm, _ = make_sm()
        assert sm.get_state() == SleeperState.OFF

    def test_to_dict(self):
        sm, _ = make_sm()
        d = sm.to_dict()
        assert d["state"] == "OFF"
        assert d["last_heartbeat_at"] is None
        assert d["wake_requested_at"] is None


# ---------------------------------------------------------------------------
# Transition table — wake_requested
# ---------------------------------------------------------------------------

class TestWakeRequested:
    def test_off_to_waking(self):
        sm, _ = make_sm()
        assert sm.wake_requested() == SleeperState.WAKING

    def test_off_to_waking_records_timestamp(self):
        sm, clock = make_sm(now=500.0)
        sm.wake_requested()
        assert sm.wake_requested_at == 500.0

    def test_failed_to_waking(self):
        sm, clock = make_sm(now=0.0)
        sm.wake_requested()
        clock[0] = 200.0  # exceed wake_timeout=120
        sm.check_timeouts()
        assert sm.get_state() == SleeperState.FAILED
        sm.wake_requested()
        assert sm.get_state() == SleeperState.WAKING

    def test_waking_resets_timer(self):
        sm, clock = make_sm(now=0.0)
        sm.wake_requested()
        clock[0] = 50.0
        sm.wake_requested()
        assert sm.wake_requested_at == 50.0
        assert sm.get_state() == SleeperState.WAKING

    def test_on_is_noop(self):
        sm, _ = make_sm()
        sm.heartbeat_received()  # OFF -> ON
        assert sm.get_state() == SleeperState.ON
        sm.wake_requested()
        assert sm.get_state() == SleeperState.ON


# ---------------------------------------------------------------------------
# Transition table — heartbeat_received
# ---------------------------------------------------------------------------

class TestHeartbeatReceived:
    def test_off_to_on(self):
        sm, _ = make_sm()
        assert sm.heartbeat_received() == SleeperState.ON

    def test_waking_to_on(self):
        sm, _ = make_sm()
        sm.wake_requested()
        assert sm.heartbeat_received() == SleeperState.ON

    def test_on_stays_on(self):
        sm, _ = make_sm()
        sm.heartbeat_received()
        assert sm.heartbeat_received() == SleeperState.ON

    def test_failed_to_on(self):
        sm, clock = make_sm(now=0.0)
        sm.wake_requested()
        clock[0] = 200.0
        sm.check_timeouts()
        assert sm.get_state() == SleeperState.FAILED
        assert sm.heartbeat_received() == SleeperState.ON

    def test_records_timestamp(self):
        sm, clock = make_sm(now=999.0)
        sm.heartbeat_received()
        assert sm.last_heartbeat_at == 999.0

    def test_clears_wake_requested_at(self):
        sm, _ = make_sm()
        sm.wake_requested()
        sm.heartbeat_received()
        assert sm.wake_requested_at is None


# ---------------------------------------------------------------------------
# Transition table — check_timeouts / timer-driven
# ---------------------------------------------------------------------------

class TestCheckTimeouts:
    def test_waking_to_failed_after_timeout(self):
        sm, clock = make_sm(wake_timeout=120.0, now=0.0)
        sm.wake_requested()
        clock[0] = 120.0
        assert sm.check_timeouts() == SleeperState.FAILED

    def test_waking_not_failed_before_timeout(self):
        sm, clock = make_sm(wake_timeout=120.0, now=0.0)
        sm.wake_requested()
        clock[0] = 119.9
        assert sm.check_timeouts() == SleeperState.WAKING

    def test_on_to_off_after_missed_heartbeats(self):
        # interval=60, threshold=3 => off after 180s without heartbeat
        sm, clock = make_sm(heartbeat_interval=60.0, heartbeat_miss_threshold=3, now=0.0)
        sm.heartbeat_received()  # ON, last_heartbeat_at=0.0
        clock[0] = 181.0
        assert sm.check_timeouts() == SleeperState.OFF

    def test_on_not_off_before_miss_threshold(self):
        sm, clock = make_sm(heartbeat_interval=60.0, heartbeat_miss_threshold=3, now=0.0)
        sm.heartbeat_received()
        clock[0] = 179.9
        assert sm.check_timeouts() == SleeperState.ON

    def test_off_unchanged_by_check_timeouts(self):
        sm, clock = make_sm(now=0.0)
        clock[0] = 9999.0
        assert sm.check_timeouts() == SleeperState.OFF

    def test_failed_unchanged_by_check_timeouts(self):
        sm, clock = make_sm(wake_timeout=120.0, now=0.0)
        sm.wake_requested()
        clock[0] = 200.0
        sm.check_timeouts()  # -> FAILED
        clock[0] = 9999.0
        assert sm.check_timeouts() == SleeperState.FAILED

    def test_waking_clears_wake_requested_at_on_failure(self):
        sm, clock = make_sm(wake_timeout=120.0, now=0.0)
        sm.wake_requested()
        clock[0] = 200.0
        sm.check_timeouts()
        assert sm.wake_requested_at is None

    def test_on_clears_last_heartbeat_on_miss(self):
        sm, clock = make_sm(heartbeat_interval=60.0, heartbeat_miss_threshold=3, now=0.0)
        sm.heartbeat_received()
        clock[0] = 300.0
        sm.check_timeouts()
        assert sm.last_heartbeat_at is None


# ---------------------------------------------------------------------------
# suspend_requested — no state change
# ---------------------------------------------------------------------------

class TestSuspendRequested:
    def test_off_stays_off(self):
        sm, _ = make_sm()
        assert sm.suspend_requested() == SleeperState.OFF

    def test_on_stays_on(self):
        sm, _ = make_sm()
        sm.heartbeat_received()
        assert sm.suspend_requested() == SleeperState.ON


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------

class TestThreadSafety:
    def test_concurrent_heartbeat_and_wake_requested(self):
        sm, clock = make_sm(now=0.0)
        errors: list[Exception] = []

        def sender():
            for _ in range(200):
                try:
                    sm.heartbeat_received()
                except Exception as exc:
                    errors.append(exc)

        def waker():
            for _ in range(200):
                try:
                    sm.wake_requested()
                except Exception as exc:
                    errors.append(exc)

        threads = [threading.Thread(target=sender), threading.Thread(target=waker)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Thread errors: {errors}"
        # State must be valid
        assert sm.get_state() in list(SleeperState)

    def test_concurrent_check_timeouts(self):
        sm, clock = make_sm(now=0.0)
        sm.wake_requested()
        errors: list[Exception] = []

        def checker():
            for _ in range(100):
                try:
                    clock[0] += 1
                    sm.check_timeouts()
                except Exception as exc:
                    errors.append(exc)

        threads = [threading.Thread(target=checker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
