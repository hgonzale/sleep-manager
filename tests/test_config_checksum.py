import pytest

from sleep_manager.config_checksum import compute_config_checksum

pytestmark = pytest.mark.unit


class TestComputeConfigChecksum:
    def _base(self):
        common = {"api_key": "secret", "domain": "test.local", "port": 51339}
        waker = {"name": "waker", "wol_exec": "/usr/sbin/etherwake"}
        sleeper = {"name": "sleeper", "mac_address": "00:11:22:33:44:55"}
        return common, waker, sleeper

    def test_identical_configs_same_checksum(self):
        c, w, s = self._base()
        assert compute_config_checksum(c, w, s) == compute_config_checksum(c, w, s)

    def test_different_common_key_different_checksum(self):
        c, w, s = self._base()
        c2 = dict(c, port=9999)
        assert compute_config_checksum(c, w, s) != compute_config_checksum(c2, w, s)

    def test_different_waker_key_different_checksum(self):
        c, w, s = self._base()
        w2 = dict(w, name="other-waker")
        assert compute_config_checksum(c, w, s) != compute_config_checksum(c, w2, s)

    def test_different_sleeper_key_different_checksum(self):
        c, w, s = self._base()
        s2 = dict(s, mac_address="ff:ff:ff:ff:ff:ff")
        assert compute_config_checksum(c, w, s) != compute_config_checksum(c, w, s2)

    def test_key_ordering_does_not_affect_checksum(self):
        c, w, s = self._base()
        c_reordered = {"port": c["port"], "api_key": c["api_key"], "domain": c["domain"]}
        assert compute_config_checksum(c, w, s) == compute_config_checksum(c_reordered, w, s)

    def test_output_is_16_hex_chars(self):
        c, w, s = self._base()
        result = compute_config_checksum(c, w, s)
        assert isinstance(result, str)
        assert len(result) == 16
        assert all(ch in "0123456789abcdef" for ch in result)
