import logging
import threading
import time
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SleeperState(Enum):
    OFF = "OFF"
    WAKING = "WAKING"
    ON = "ON"
    FAILED = "FAILED"


class SleeperStateMachine:
    """State machine tracking whether the sleeper machine is on, off, waking, or failed.

    States:
        OFF     - No heartbeats. Sleeper is asleep.
        WAKING  - WoL sent. Waiting for first heartbeat.
        ON      - Heartbeats flowing. Sleeper confirmed alive.
        FAILED  - WoL sent, wake_timeout elapsed with no heartbeat.

    Thread-safe: all public methods acquire a lock before mutating state.
    """

    def __init__(
        self,
        wake_timeout: float = 120.0,
        heartbeat_interval: float = 60.0,
        heartbeat_miss_threshold: int = 3,
        _time_fn: Any = None,
    ) -> None:
        self.wake_timeout = wake_timeout
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_miss_threshold = heartbeat_miss_threshold
        self._time = _time_fn or time.time

        self.state: SleeperState = SleeperState.OFF
        self.last_heartbeat_at: float | None = None
        self.wake_requested_at: float | None = None
        self._lock = threading.Lock()

    def wake_requested(self) -> SleeperState:
        """Transition: wake command issued (WoL packet sent)."""
        with self._lock:
            if self.state in (SleeperState.OFF, SleeperState.FAILED):
                logger.info("State: %s -> WAKING (wake requested)", self.state.value)
                self.state = SleeperState.WAKING
                self.wake_requested_at = self._time()
            elif self.state == SleeperState.WAKING:
                logger.info("State: WAKING -> WAKING (retry, resetting timer)")
                self.wake_requested_at = self._time()
            elif self.state == SleeperState.ON:
                logger.info("State: ON (wake requested, already on — no-op)")
            return self.state

    def suspend_requested(self) -> SleeperState:
        """Log suspend intent; no state change (state transitions via heartbeat_missed)."""
        with self._lock:
            logger.info(
                "Suspend requested in state %s — waiting for heartbeats to stop", self.state.value
            )
            return self.state

    def heartbeat_received(self) -> SleeperState:
        """Process an incoming heartbeat from the sleeper."""
        with self._lock:
            now = self._time()
            prev = self.state
            self.last_heartbeat_at = now
            if self.state in (SleeperState.WAKING, SleeperState.OFF, SleeperState.FAILED):
                logger.info("State: %s -> ON (heartbeat received)", self.state.value)
                self.state = SleeperState.ON
                self.wake_requested_at = None
            elif self.state == SleeperState.ON:
                logger.debug("State: ON (heartbeat refreshed)")
            return self.state

    def check_timeouts(self) -> SleeperState:
        """Check timer-based transitions. Call from a background thread every ~10s."""
        with self._lock:
            now = self._time()

            if self.state == SleeperState.WAKING:
                if (
                    self.wake_requested_at is not None
                    and (now - self.wake_requested_at) >= self.wake_timeout
                ):
                    logger.warning(
                        "State: WAKING -> FAILED (wake_timeout=%.0fs exceeded)", self.wake_timeout
                    )
                    self.state = SleeperState.FAILED
                    self.wake_requested_at = None

            elif self.state == SleeperState.ON:
                if self.last_heartbeat_at is not None:
                    missed_window = self.heartbeat_interval * self.heartbeat_miss_threshold
                    if (now - self.last_heartbeat_at) > missed_window:
                        logger.info(
                            "State: ON -> OFF (heartbeat_missed: no heartbeat for %.0fs)",
                            now - self.last_heartbeat_at,
                        )
                        self.state = SleeperState.OFF
                        self.last_heartbeat_at = None

            return self.state

    def get_state(self) -> SleeperState:
        with self._lock:
            return self.state

    def to_dict(self) -> dict[str, Any]:
        with self._lock:
            return {
                "state": self.state.value,
                "last_heartbeat_at": self.last_heartbeat_at,
                "wake_requested_at": self.wake_requested_at,
            }
