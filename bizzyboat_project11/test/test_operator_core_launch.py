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
import yaml

from launch import LaunchContext
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.utilities import perform_substitutions
from launch_ros.actions import Node
from launch_ros.actions import SetParameter
from launch_ros.actions import SetParametersFromFile

PACKAGE_DIR = Path(__file__).resolve().parent.parent
LAUNCH_FILE = PACKAGE_DIR / 'launch' / 'operator_core_launch.py'
MONITOR_LAUNCH_FILE = PACKAGE_DIR / 'launch' / 'network_monitor_operator_launch.py'
CONFIG_DIR = PACKAGE_DIR / 'config'


def _load_launch_module(path=LAUNCH_FILE):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _text(context, value):
    """Resolve a launch value that may be a plain string or substitutions."""
    if isinstance(value, str):
        return value
    return perform_substitutions(context, value)


def _monitor_nodes(**overrides):
    """Return {node name: config basename or None} for the monitor launch."""
    module = _load_launch_module(MONITOR_LAUNCH_FILE)
    context = LaunchContext()
    context.launch_configurations.update(overrides)
    description = module.generate_launch_description()
    for entity in description.entities:
        if isinstance(entity, DeclareLaunchArgument):
            entity.visit(context)

    running = {}
    for entity in description.entities:
        if not isinstance(entity, Node):
            continue
        if entity.condition is not None and not entity.condition.evaluate(context):
            continue
        name = _text(context, entity._Node__node_name)
        config = None
        for parameter in entity._Node__parameters or []:
            # Inline dicts (the Starlink node) have no config file; file
            # parameters are normalised into ParameterFile by Node.
            param_file = getattr(parameter, 'param_file', None)
            if param_file is not None:
                config = Path(_text(context, param_file)).name
        running[name] = config
    return running


def _targets(basename):
    data = yaml.safe_load((CONFIG_DIR / basename).read_text())
    return data['ping_monitor']['ros__parameters']['targets']


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


# --- network_monitor_operator_launch.py ------------------------------------
#
# Every node here polls a specific piece of hardware. At a station that does
# not have that hardware the node cannot succeed, and a permanently failed
# diagnostic is worse than an absent one — it trains the operator to ignore
# the annunciator.

def test_all_monitors_run_at_a_fully_equipped_station():
    running = _monitor_nodes()
    assert set(running) == {
        'mikrotik_monitor', 'teltonika_monitor', 'starlink_diagnostics', 'ping_monitor'}
    assert running['ping_monitor'] == 'ping_targets_operator.yaml'


def test_no_wifi_drops_the_bridge_radio_monitor_and_swaps_ping_targets():
    running = _monitor_nodes(wifi='false')
    assert 'mikrotik_monitor' not in running, \
        'bizzy.wifi.op is absent at such a station, not merely unreachable'
    assert running['ping_monitor'] == 'ping_targets_operator_no_wifi.yaml'
    assert 'teltonika_monitor' in running, 'router.op is reachable without the bridge'


def test_exactly_one_ping_monitor_runs_in_either_mode():
    """Both ping_monitor Nodes carry the same node name; if the conditions ever
    stopped being mutually exclusive, two would race on it."""
    for overrides in ({}, {'wifi': 'false'}):
        module = _load_launch_module(MONITOR_LAUNCH_FILE)
        context = LaunchContext()
        context.launch_configurations.update(overrides)
        description = module.generate_launch_description()
        for entity in description.entities:
            if isinstance(entity, DeclareLaunchArgument):
                entity.visit(context)
        running = [
            entity for entity in description.entities
            if isinstance(entity, Node)
            and _text(context, entity._Node__node_name) == 'ping_monitor'
            and (entity.condition is None or entity.condition.evaluate(context))
        ]
        assert len(running) == 1, f'{len(running)} ping monitors with {overrides or "defaults"}'


def test_starlink_is_gated_independently_of_wifi():
    """A station's dish and its bridge radio are separate facts; the ROC lacks
    both, but the arguments must not be entangled."""
    assert 'starlink_diagnostics' in _monitor_nodes(wifi='false')
    assert 'starlink_diagnostics' not in _monitor_nodes(op_starlink='false')
    assert 'mikrotik_monitor' in _monitor_nodes(op_starlink='false')


def test_ping_target_lists_differ_only_by_the_wifi_path_targets():
    """The two lists are duplicated (ping_monitor takes a flat string array, so
    a second file replaces rather than shortens it). This is what stops them
    drifting: a target added to one and not the other fails here."""
    wifi_targets = _targets('ping_targets_operator.yaml')
    no_wifi_targets = _targets('ping_targets_operator_no_wifi.yaml')
    dropped = [t for t in wifi_targets if t not in no_wifi_targets]
    assert dropped == [
        'gabby_direct:gabby.bizzy.p11.lan',
        'router_bizzy_direct:router.bizzy.p11.lan',
    ]
    assert [t for t in no_wifi_targets if t not in wifi_targets] == []


def test_both_ping_lists_cover_the_cell_path():
    """Cell is one of two redundant links to the boat; it had no health signal
    at all before this."""
    for basename in ('ping_targets_operator.yaml', 'ping_targets_operator_no_wifi.yaml'):
        names = [t.split(':', 1)[0] for t in _targets(basename)]
        assert 'gabby_cell' in names, basename
        assert 'router_bizzy_cell' in names, basename
