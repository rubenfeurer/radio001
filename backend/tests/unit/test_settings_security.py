"""
Unit tests for settings input hardening and atomic radio.conf writes.

Regression: a value like "x\nWIFI_INTERFACE=eth0" written verbatim into
radio.conf would inject arbitrary config keys that main._load_radio_conf()
loads into os.environ at next boot.
"""

import pytest
from unittest.mock import patch
from pydantic import ValidationError

from api.routes.settings import SettingsPayload, _write_conf

CONF_TEMPLATE = """# Radio Pi configuration
HOTSPOT_SSID=Radio-Setup
HOTSPOT_PASSWORD=Configure123!
DEFAULT_VOLUME=50
"""


@pytest.fixture
def conf(tmp_path):
    path = tmp_path / "radio.conf"
    path.write_text(CONF_TEMPLATE)
    return path


@pytest.mark.unit
class TestSettingsValidation:
    def test_newline_injection_rejected(self):
        for field in ("HOTSPOT_SSID", "HOTSPOT_PASSWORD"):
            with pytest.raises(ValidationError):
                SettingsPayload(**{field: "x\nWIFI_INTERFACE=eth0"})

    def test_carriage_return_rejected(self):
        with pytest.raises(ValidationError):
            SettingsPayload(HOTSPOT_SSID="x\rDEFAULT_STATION_1_URL=http://evil")

    def test_control_characters_rejected(self):
        with pytest.raises(ValidationError):
            SettingsPayload(HOTSPOT_SSID="bad\x00ssid")
        with pytest.raises(ValidationError):
            SettingsPayload(HOTSPOT_PASSWORD="password\x1b[31m")

    def test_non_ascii_rejected(self):
        with pytest.raises(ValidationError):
            SettingsPayload(HOTSPOT_SSID="Radiö-Setup")

    def test_length_caps(self):
        with pytest.raises(ValidationError):
            SettingsPayload(HOTSPOT_SSID="s" * 33)
        with pytest.raises(ValidationError):
            SettingsPayload(HOTSPOT_PASSWORD="p" * 64)
        with pytest.raises(ValidationError):
            SettingsPayload(HOTSPOT_PASSWORD="short")
        with pytest.raises(ValidationError):
            SettingsPayload(HOTSPOT_SSID="")

    def test_boundary_values_accepted(self):
        p = SettingsPayload(HOTSPOT_SSID="s" * 32, HOTSPOT_PASSWORD="p" * 63)
        assert p.HOTSPOT_SSID == "s" * 32
        assert p.HOTSPOT_PASSWORD == "p" * 63

    def test_normal_values_accepted(self):
        p = SettingsPayload(HOTSPOT_SSID="Radio-Setup", HOTSPOT_PASSWORD="Configure123!")
        assert p.HOTSPOT_SSID == "Radio-Setup"


@pytest.mark.unit
class TestAtomicConfWrite:
    def test_write_updates_value_atomically(self, conf):
        changed = _write_conf(conf, {"HOTSPOT_SSID": "NewName"})
        assert changed == ["HOTSPOT_SSID"]
        content = conf.read_text()
        assert "HOTSPOT_SSID=NewName" in content
        assert "DEFAULT_VOLUME=50" in content  # untouched lines preserved
        assert not list(conf.parent.glob("*.tmp"))

    def test_unchanged_value_reports_nothing(self, conf):
        assert _write_conf(conf, {"HOTSPOT_SSID": "Radio-Setup"}) == []

    def test_newline_value_raises_without_writing(self, conf):
        original = conf.read_text()
        with pytest.raises(ValueError):
            _write_conf(conf, {"HOTSPOT_SSID": "x\nWIFI_INTERFACE=eth0"})
        assert conf.read_text() == original

    def test_failure_before_rename_leaves_original_intact(self, conf):
        original = conf.read_text()
        with patch("api.routes.settings.os.fsync", side_effect=OSError("disk full")):
            with pytest.raises(OSError):
                _write_conf(conf, {"HOTSPOT_SSID": "NewName"})
        assert conf.read_text() == original
        assert not list(conf.parent.glob("*.tmp"))


@pytest.mark.unit
class TestSharedConfParser:
    """One parser defines the radio.conf format for both consumers."""

    def test_parses_key_values_skipping_comments_and_blanks(self):
        from core.config import parse_conf_lines
        lines = [
            "# comment\n", "\n", "KEY=value\n", "  SPACED = padded  \n",
            "NOEQUALS\n", "=novalue\n",
        ]
        assert parse_conf_lines(lines) == {"KEY": "value", "SPACED": "padded"}

    def test_inline_comment_stripping_is_opt_in(self):
        from core.config import parse_conf_lines
        lines = ["PASSWORD=abc#def\n"]
        # Settings path preserves the value verbatim ('#' is legal in values)
        assert parse_conf_lines(lines) == {"PASSWORD": "abc#def"}
        # Env-seeding path strips inline comments (historical behavior)
        assert parse_conf_lines(lines, strip_inline_comments=True) == {"PASSWORD": "abc"}

    def test_parse_conf_file(self, tmp_path):
        from core.config import parse_conf_file
        p = tmp_path / "radio.conf"
        p.write_text("A=1\n# c\nB=2 # note\n")
        assert parse_conf_file(p) == {"A": "1", "B": "2 # note"}
        assert parse_conf_file(p, strip_inline_comments=True) == {"A": "1", "B": "2"}
