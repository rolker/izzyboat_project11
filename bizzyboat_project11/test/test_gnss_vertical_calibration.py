#!/usr/bin/env python3
"""Unit tests for gnss_vertical_calibration.py.

The tool's printed correction is the line an operator copies into an autopilot
parameter and a URDF, so the sign of that line is the thing worth testing. The
URDF is z-up and ArduPilot's GPS_POS* are z-down (FRD): this repo's records
carry the same forward antenna as +0.890 in one and -0.890 in the other. An
earlier version printed a single signed delta for both, which applied to
GPS_POS1_Z would have added about 110 mm to the FCU vertical path instead of
removing 55 mm.

The bag-reading half needs bags and is exercised in the field; these cases are
the pure arithmetic underneath the report.
"""
import importlib.util
import math
import pathlib

import pytest

HERE = pathlib.Path(__file__).resolve().parent
SCRIPT = HERE.parent / 'scripts' / 'gnss_vertical_calibration.py'
_spec = importlib.util.spec_from_file_location('gnss_vertical_calibration', SCRIPT)
gvc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gvc)


# The values this hull actually carries, from
# docs/logs/2026/2026-05-21_gabby_logs.md and bizzyboat_hardware.md.
URDF_Z = 0.890
GPS_POS1_Z = -0.890
# The 2026-08-21 result: the FCU path put base_link low, so the antenna is
# really lower than the URDF places it.
MEASURED = -0.055


def test_the_urdf_and_the_autopilot_disagree_by_a_sign_to_begin_with():
    """The premise the whole report rests on. If this ever stops being true,
    every sign below is wrong."""
    assert gvc.FCU_ANT[1] == pytest.approx(URDF_Z)
    assert GPS_POS1_Z == pytest.approx(-gvc.FCU_ANT[1])


def test_a_negative_measurement_lowers_the_urdf_antenna():
    new_urdf_z, _ = gvc.corrected_antenna_height(MEASURED)
    assert new_urdf_z == pytest.approx(0.835)
    assert new_urdf_z < URDF_Z


def test_the_same_measurement_raises_gps_pos1_z_because_that_frame_is_down():
    """The bug this test exists for: the two edits are opposite in sign.

    Applying the z-up delta to GPS_POS1_Z gives -0.945, which is 110 mm from
    the truth in the wrong direction -- worse than not correcting at all.
    """
    _, new_gps_pos_z = gvc.corrected_antenna_height(MEASURED)
    assert new_gps_pos_z == pytest.approx(-0.835)
    assert new_gps_pos_z > GPS_POS1_Z
    naive = GPS_POS1_Z + MEASURED
    assert naive == pytest.approx(-0.945)
    assert abs(naive - new_gps_pos_z) == pytest.approx(2 * abs(MEASURED))


@pytest.mark.parametrize('correction', [-0.055, -0.09, 0.03, 0.0])
def test_the_two_outputs_always_describe_the_same_antenna(correction):
    new_urdf_z, new_gps_pos_z = gvc.corrected_antenna_height(correction)
    assert new_urdf_z == pytest.approx(-new_gps_pos_z)


def test_the_printed_report_carries_both_targets_with_their_own_signs():
    text = '\n'.join(gvc.correction_report(MEASURED))
    assert '+0.890 -> +0.835' in text
    assert '-0.890 -> -0.835' in text
    # Both frames named beside their number, so the reader is not asked to
    # remember which convention each target uses.
    assert 'z UP' in text and 'z DOWN' in text
    # And the aft antenna is explicitly out of scope: it was never measured.
    assert 'GPS_POS2_Z' in text and 'NOT covered' in text


def test_the_report_refuses_an_implausible_correction():
    """A datum mismatch is not an antenna height, and must not be printed in
    the same confident millimetres as one. 0.626 m is the geoid round trip
    that started this investigation."""
    text = '\n'.join(gvc.correction_report(0.626))
    assert 'REFUSING' in text
    assert '0.835' not in text
    assert 'datum' in text


def test_a_correction_just_inside_the_bound_is_still_quoted():
    text = '\n'.join(gvc.correction_report(-0.4))
    assert 'REFUSING' not in text
    assert 'GPS_POS1_Z' in text


# --- the lever-arm reduction the correction is derived from ----------------

def test_lever_arm_is_the_mounting_height_when_level():
    assert gvc.lever_z(0.835, 0.890, 0.0) == pytest.approx(0.890)


def test_nose_down_pitch_lowers_a_forward_antenna():
    """REP-103 positive pitch is nose down, so an antenna ahead of base_link
    drops. Getting this backwards would flip the sign of the whole result."""
    assert gvc.lever_z(0.835, 0.890, math.radians(5.0)) < 0.890
    assert gvc.lever_z(-1.073, 0.882, math.radians(5.0)) > 0.882
