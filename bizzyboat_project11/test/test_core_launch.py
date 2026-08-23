#!/usr/bin/env python3
"""Unit tests for core_launch.py's cross-repo preflight check.

core_launch.py launches echo_helm's ellipsoidal_fix_node, which exists only on
seafloor_echoboat_project11 PR #56. On an older echo_helm the launch aborts --
deliberately, because the alternative is a boat that floats with no publisher
on mavros/global_position/global_ellipsoidal and a missing annunciator tile.
These cases pin the failure to a message that names the repo to rebuild rather
than a SubstitutionFailure on an executable name.
"""
import importlib.util
import pathlib

import pytest

from launch import LaunchContext

HERE = pathlib.Path(__file__).resolve().parent
LAUNCH_FILE = HERE.parent / 'launch' / 'core_launch.py'
_spec = importlib.util.spec_from_file_location('core_launch', LAUNCH_FILE)
cl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cl)


def test_the_message_names_the_repo_and_branch_to_rebuild():
    """A stack trace saying 'executable not found' does not tell an operator on
    a boat which of eight repos is stale."""
    text = cl.missing_ellipsoidal_fix_message()
    assert 'echo_helm' in text
    assert '#56' in text
    assert 'colcon build --packages-select echo_helm' in text


def test_the_message_says_why_refusing_to_start_is_the_choice():
    """The failure is loud on purpose; the reasoning has to travel with it, or
    the next person to see it will 'fix' it by deleting the node."""
    text = cl.missing_ellipsoidal_fix_message()
    assert 'global_ellipsoidal' in text
    assert 'absent' in text


def test_an_installed_package_without_the_executable_raises_the_guided_error(
        monkeypatch):
    """The case that actually happens: echo_helm is installed, just too old.

    The check must fail on the same lookup the Node uses, so it cannot pass
    while the Node it guards fails -- hence a real executable lookup against a
    real installed package rather than a stub.
    """
    monkeypatch.setattr(cl, 'ELLIPSOIDAL_FIX_EXECUTABLE', 'no_such_exec_452')
    with pytest.raises(RuntimeError) as caught:
        cl.check_ellipsoidal_fix_available(LaunchContext())
    assert 'colcon build --packages-select echo_helm' in str(caught.value)
    assert '#56' in str(caught.value)


def test_a_missing_package_also_raises_the_guided_error(monkeypatch):
    """Deterministic half of the test above: whatever echo_helm is installed
    here, an absent one must produce the guided message and not a bare
    SubstitutionFailure."""
    monkeypatch.setattr(cl, 'ELLIPSOIDAL_FIX_PACKAGE', 'no_such_package_452')
    with pytest.raises(RuntimeError) as caught:
        cl.check_ellipsoidal_fix_available(LaunchContext())
    assert 'no_such_package_452' in str(caught.value)
    assert '#56' in str(caught.value)


def test_the_check_runs_before_anything_else_is_launched():
    """Aborting part-way through bringing 130 nodes up leaves a half-started
    stack; aborting first does not."""
    description = cl.generate_launch_description()
    first = description.entities[0]
    assert getattr(first, '_OpaqueFunction__function', None) is \
        cl.check_ellipsoidal_fix_available
