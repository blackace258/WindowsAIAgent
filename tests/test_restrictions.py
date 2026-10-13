"""Tests for the restriction / filter engine."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.restrictions import Restrictions, LEVEL_PRESETS, available_levels


def test_default_level():
    r = Restrictions()
    assert r.level == "balanced"
    assert r.safe_mode is True
    assert len(r.blocked_patterns) > 0


def test_apply_levels():
    r = Restrictions()
    for level in LEVEL_PRESETS:
        msg = r.apply_level(level)
        assert level in msg or "set to" in msg.lower()
        assert r.level == level


def test_block_unblock_pattern():
    r = Restrictions(level="balanced")
    r.block_pattern("mycustomcmd")
    assert "mycustomcmd" in r.blocked_patterns
    allowed, reason = r.is_command_allowed("mycustomcmd /force")
    assert allowed is False
    r.unblock_pattern("mycustomcmd")
    allowed, _ = r.is_command_allowed("mycustomcmd /force")
    assert allowed is True


def test_block_tool():
    r = Restrictions()
    r.block_tool("write_file")
    allowed, reason = r.is_tool_allowed("write_file")
    assert allowed is False
    r.unblock_tool("write_file")
    allowed, _ = r.is_tool_allowed("write_file")
    assert allowed is True


def test_unrestricted():
    r = Restrictions()
    r.apply_level("unrestricted")
    assert r.safe_mode is False
    allowed, _ = r.is_command_allowed("format c:")
    assert allowed is True


def test_summary_and_levels():
    r = Restrictions()
    s = r.summary()
    assert "balanced" in s
    al = available_levels()
    assert "strict" in al and "unrestricted" in al


if __name__ == "__main__":
    test_default_level()
    test_apply_levels()
    test_block_unblock_pattern()
    test_block_tool()
    test_unrestricted()
    test_summary_and_levels()
    print("All restriction tests passed.")
