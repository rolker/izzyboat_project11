#!/usr/bin/env python3
"""Unit tests for gps_rtk_diagnostics_node.py.

Pure classification logic: fix_type to level, the reported-accuracy override,
and the formatting of the GPSRAW fields that carry sentinel values. No ROS
graph is required.

The case these exist for is 2026-08-20, when this boat published 'RTK Fixed',
OK, green, with a vertical accuracy of 1.750 m alongside it.
"""
import importlib.util
import pathlib

import pytest

from diagnostic_msgs.msg import DiagnosticStatus

HERE = pathlib.Path(__file__).resolve().parent
SCRIPT = HERE.parent / 'scripts' / 'gps_rtk_diagnostics_node.py'
_spec = importlib.util.spec_from_file_location('gps_rtk_diagnostics_node', SCRIPT)
gd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gd)

OK = DiagnosticStatus.OK
WARN = DiagnosticStatus.WARN
ERROR = DiagnosticStatus.ERROR
STALE = DiagnosticStatus.STALE

WARN_V = 0.10
ERROR_V = 0.50


# --- fix_type classification -----------------------------------------------

@pytest.mark.parametrize('fix_type,level', [
    (6, OK), (7, OK), (8, OK),
    (5, WARN), (4, WARN), (3, WARN),
    (2, ERROR), (1, ERROR), (0, ERROR),
])
def test_fix_type_maps_to_its_level(fix_type, level):
    assert gd.classify_fix(fix_type, 6, 3)[0] == level


def test_an_unknown_fix_type_is_named_not_swallowed():
    level, message = gd.classify_fix(42, 6, 3)
    assert level == OK          # >= ok_min, whatever it is
    assert '42' in message


# --- the 2026-08-20 case ---------------------------------------------------

def test_rtk_fixed_with_a_metre_of_vertical_error_is_not_ok():
    """The whole reason this override exists.

    fix_type 6 with v_acc 1.750 m published OK and the tile stayed green while
    tide and every sounding carried that metre and a half.
    """
    level, message = gd.classify_fix(6, 6, 3)
    assert level == OK
    level, message = gd.apply_vertical_accuracy(
        level, message, gd.accuracy_m(1750), WARN_V, ERROR_V)
    assert level == ERROR
    assert '1.75' in message


def test_a_degraded_but_not_hopeless_vertical_warns():
    level, message = gd.apply_vertical_accuracy(
        OK, 'RTK Fixed', gd.accuracy_m(250), WARN_V, ERROR_V)
    assert level == WARN
    assert '0.25' in message


def test_a_good_vertical_leaves_the_fix_type_verdict_alone():
    assert gd.apply_vertical_accuracy(
        OK, 'RTK Fixed', gd.accuracy_m(25), WARN_V, ERROR_V) == (OK, 'RTK Fixed')


def test_a_good_vertical_cannot_turn_a_bad_fix_green():
    """Raises the level, never lowers it. A receiver claiming 5 mm while
    holding a 3D fix is still not an RTK fix."""
    assert gd.apply_vertical_accuracy(
        WARN, '3D Fix', gd.accuracy_m(5), WARN_V, ERROR_V) == (WARN, '3D Fix')


def test_a_warning_vertical_does_not_downgrade_an_error_fix():
    level, _ = gd.apply_vertical_accuracy(
        ERROR, 'No Fix', gd.accuracy_m(250), WARN_V, ERROR_V)
    assert level == ERROR


def test_an_unreported_vertical_accuracy_changes_nothing():
    """v_acc is a MAVLink extension field: a receiver that does not populate it
    leaves it zero. Absent is not the same as good, and it is not the same as
    bad either -- it must not manufacture a level in either direction."""
    for raw in (0, -1):
        assert gd.apply_vertical_accuracy(
            OK, 'RTK Fixed', gd.accuracy_m(raw), WARN_V, ERROR_V) \
            == (OK, 'RTK Fixed')


def test_stale_data_is_not_re_judged_on_its_last_accuracy():
    """A stale status already says the feed is dead; the accuracy it carries
    describes whenever it died, not now."""
    level, message = gd.apply_vertical_accuracy(
        STALE, 'stale: no update for 30s (last RTK Fixed)',
        gd.accuracy_m(1750), WARN_V, ERROR_V)
    assert level == STALE
    assert 'vertical' not in message


# --- accuracy formatting ---------------------------------------------------

def test_an_unreported_accuracy_is_not_published_as_perfect():
    assert gd.accuracy_text(0) == 'not reported'
    assert gd.accuracy_m(0) is None


def test_a_reported_accuracy_is_metres():
    assert gd.accuracy_text(1750) == '1.750'
    assert gd.accuracy_m(1750) == pytest.approx(1.75)


def test_the_text_and_the_number_agree_about_what_is_reported():
    """They gate the same condition; if they ever disagree the key and the
    level would describe different receivers."""
    for raw in (-1, 0, 1, 25, 1750, 65535):
        assert (gd.accuracy_text(raw) == 'not reported') == (gd.accuracy_m(raw) is None)
