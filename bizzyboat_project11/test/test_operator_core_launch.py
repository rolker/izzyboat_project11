"""Station-agnostic wiring in operator_core_launch.py.

The two behaviours guarded here fail *silently* in the field if they break —
a wrong return_host means the bridge comes up clean at both ends while the
boat transmits to a different station, and a stale connections_list means
uplink packets stream into a WiFi path that isn't there. Neither surfaces as
an error, so they get a test instead.
"""

import importlib.util
import socket
from pathlib import Path

import pytest

from launch import LaunchContext
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.utilities import perform_substitutions
from launch_ros.actions import SetParameter
from launch_ros.actions import SetParametersFromFile

LAUNCH_FILE = Path(__file__).resolve().parent.parent / 'launch' / 'operator_core_launch.py'


def _load_launch_module():
    spec = importlib.util.spec_from_file_location('operator_core_launch', LAUNCH_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _resolve(**overrides):
    """Return (param-file basenames loaded, {param name: value}) for these args."""
    module = _load_launch_module()
    context = LaunchContext()
    context.launch_configurations.update(overrides)
    description = module.generate_launch_description()
    for entity in description.entities:
        if isinstance(entity, DeclareLaunchArgument):
            entity.visit(context)

    files = []
    params = {}

    def walk(entities):
        for entity in entities:
            if isinstance(entity, GroupAction):
                walk(entity._GroupAction__actions)
            elif isinstance(entity, SetParametersFromFile):
                if entity.condition is None or entity.condition.evaluate(context):
                    resolved = perform_substitutions(context, entity._input_file)
                    files.append(Path(resolved).name)
            elif isinstance(entity, SetParameter):
                for name, value in entity._SetParameter__param_dict.items():
                    params[perform_substitutions(context, name)] = \
                        perform_substitutions(context, value)

    walk(description.entities)
    return files, params


def test_return_hosts_default_to_this_stations_hostname():
    station = socket.gethostname().split('.')[0].lower()
    _, params = _resolve()
    assert params['remotes.bizzy.connections.vpn.return_host'] == \
        f'{station}.vpn.bizzy.p11.lan'
    assert params['remotes.bizzy.connections.cell.return_host'] == \
        f'{station}.cell.bizzy.p11.lan'
    assert params['remotes.bizzy.connections.wifi.return_host'] == \
        f'{station}.op.p11.lan'


def test_return_host_prefix_reproduces_salmons_historical_literals():
    """Derivation is behaviour-preserving: these are the exact strings
    operator.yaml carried before they moved into the launch file."""
    _, params = _resolve(return_host_prefix='salmon')
    assert params == {
        'remotes.bizzy.connections.wifi.return_host': 'salmon.op.p11.lan',
        'remotes.bizzy.connections.vpn.return_host': 'salmon.vpn.bizzy.p11.lan',
        'remotes.bizzy.connections.cell.return_host': 'salmon.cell.bizzy.p11.lan',
    }


@pytest.mark.parametrize('wifi,expected', [
    ('true', ['operator.yaml']),
    ('false', ['operator.yaml', 'operator_no_wifi.yaml']),
])
def test_no_wifi_overlay_loads_only_when_wifi_is_disabled(wifi, expected):
    files, _ = _resolve(wifi=wifi)
    assert files == expected, \
        'the delta must load after the base file so its shorter list wins'


def test_return_host_is_never_left_empty():
    """udp_bridge only re-points an *existing* boat-side connection when
    return_host is non-empty (remote_node.cpp:74-80); an empty value lets a
    boat that has been up since the previous station's session keep
    transmitting there, with no error at either end.
    """
    for overrides in ({}, {'wifi': 'false'}):
        _, params = _resolve(**overrides)
        for connection in ('vpn', 'cell'):
            value = params[f'remotes.bizzy.connections.{connection}.return_host']
            assert value and not value.startswith('.'), \
                f'{connection} return_host resolved to {value!r}'
