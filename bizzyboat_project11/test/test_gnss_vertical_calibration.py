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


# --- honesty gates on the corpus -------------------------------------------

def test_the_run_this_tool_was_written_for_passes_its_own_gates():
    """4.91 h, 91 samples, ten populated buckets -- the 2026-08-21 corpus."""
    assert gvc.uncertainty_gates(91, 4.91, 10) == []


def test_a_single_bucket_is_reported_as_not_measured_not_as_stable():
    """The failure this gate exists for: under 30 minutes everything lands in
    one bucket, max(drift) - min(drift) is 0, and the tool printed '0.0 mm --
    this, not the sem, is the honest uncertainty'."""
    failures = gvc.uncertainty_gates(200, 0.4, 1)
    assert failures
    assert any('bucket' in f for f in failures)
    assert any('not measured' in f.lower() or 'stable' in f for f in failures)


def test_one_sample_fails_the_sample_count_gate():
    """pstdev and sem of a single sample are both exactly 0, which prints as
    millimetre-perfect agreement from one reading."""
    failures = gvc.uncertainty_gates(1, 4.0, 8)
    assert any('samples' in f for f in failures)


def test_a_short_corpus_fails_the_timespan_gate():
    failures = gvc.uncertainty_gates(500, 0.6, 2)
    assert any('h of data' in f for f in failures)


def test_every_failure_names_which_gate_failed():
    """'no samples survived' told an operator nothing; a bare refusal would
    repeat that."""
    for failure in gvc.uncertainty_gates(1, 0.1, 1):
        assert len(failure) > 20


def test_a_failing_corpus_marks_the_report_provisional():
    text = '\n'.join(gvc.correction_report(
        MEASURED, gate_failures=gvc.uncertainty_gates(1, 0.1, 1)))
    assert 'PROVISIONAL' in text
    assert 'do not write these values' in text
    # The numbers are still shown -- the operator needs to see what was
    # measured -- but they are not presented as quotable.
    assert '+0.890 -> +0.835' in text


def test_a_passing_corpus_is_not_marked_provisional():
    text = '\n'.join(gvc.correction_report(MEASURED, gate_failures=[]))
    assert 'PROVISIONAL' not in text


def test_summarise_does_not_claim_zero_scatter_from_one_sample(capsys):
    gvc.summarise('one sample', [0.055])
    out = capsys.readouterr().out
    assert 'n/a' in out
    assert 'sd    0.0' not in out
