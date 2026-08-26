"""Recorder wiring in logging_launch.py.

Every assertion here guards something that fails *silently* on the boat —
the failure mode is a bag that looks like it is recording and isn't, or one
that is truncated at shutdown. None of it raises an error in the field.

Split out of perception_launch.py in #458, so this also pins the two
cross-file invariants that split created: the M3's raw `.all` archive stays a
sibling of the sonar bag directory (it lives in perception_launch.py now), and
the tmux stop script waits longer than the grace the recorders are given.
"""

import importlib.util
import re
from pathlib import Path

import pytest

from launch import LaunchContext
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.utilities import perform_substitutions
from launch_ros.actions import Node
from launch_ros.actions import PushRosNamespace

PACKAGE_DIR = Path(__file__).resolve().parent.parent
LAUNCH_FILE = PACKAGE_DIR / 'launch' / 'logging_launch.py'
PERCEPTION_LAUNCH_FILE = PACKAGE_DIR / 'launch' / 'perception_launch.py'
STOP_SCRIPT = PACKAGE_DIR / 'scripts' / 'stop_tmux_project11.bash'


# Variables that would otherwise reach these tests from whatever shell ran
# them: the two P11_* defaults feed the bag directories, and launch honours
# OVERRIDE_LAUNCH_PROCESS_OUTPUT ahead of a node's own `output=`. A developer
# with any of them exported would see different results from CI, in both
# directions -- a real regression passing, or a green branch failing.
AMBIENT_VARIABLES = (
    'P11_LOG_DIR',
    'P11_SONAR_LOG_DIR',
    'OVERRIDE_LAUNCH_PROCESS_OUTPUT',
)


@pytest.fixture(autouse=True)
def _clean_environment(monkeypatch):
    """Resolve every launch default from the launch files, not the shell."""
    for name in AMBIENT_VARIABLES:
        monkeypatch.delenv(name, raising=False)


def _load_launch_module(path=LAUNCH_FILE):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _resolve(context, value):
    """Resolve a launch value that may be plain, a substitution, or a tuple."""
    if isinstance(value, (str, bool, int, float)) or value is None:
        return value
    if not isinstance(value, (list, tuple)):
        value = [value]
    return perform_substitutions(context, list(value))


def _recorders(path=LAUNCH_FILE, **overrides):
    """Return {node name: Node} for the recorders this launch would start."""
    module = _load_launch_module(path)
    context = LaunchContext()
    context.launch_configurations.update(overrides)
    description = module.generate_launch_description()
    for entity in description.entities:
        if isinstance(entity, DeclareLaunchArgument):
            entity.visit(context)

    running = {}

    def walk(entities):
        for entity in entities:
            if isinstance(entity, GroupAction):
                walk(entity._GroupAction__actions)
            elif isinstance(entity, Node):
                if entity.condition is not None and \
                        not entity.condition.evaluate(context):
                    continue
                # Node.node_name (the public property) raises until the node
                # has actually been executed, so the name before launch is
                # only reachable through the mangled attribute. Everything
                # else this file inspects has a usable public property.
                name = _resolve(context, entity._Node__node_name)
                running[name] = (entity, context)

    walk(description.entities)
    return running


def _pushed_namespaces(path=LAUNCH_FILE, **overrides):
    """Return the namespaces pushed around the recorders, resolved."""
    module = _load_launch_module(path)
    context = LaunchContext()
    context.launch_configurations.update(overrides)
    description = module.generate_launch_description()
    for entity in description.entities:
        if isinstance(entity, DeclareLaunchArgument):
            entity.visit(context)

    pushed = []

    def walk(entities):
        for entity in entities:
            if isinstance(entity, GroupAction):
                actions = entity._GroupAction__actions
                if any(isinstance(action, Node) for action in actions):
                    pushed.extend(
                        _resolve(context, action.namespace)
                        for action in actions
                        if isinstance(action, PushRosNamespace))
                walk(actions)

    walk(description.entities)
    return pushed


def _params(entry):
    """Return {param name: resolved value} for the node's inline dicts."""
    entity, context = entry
    params = {}
    for parameter in entity._Node__parameters or []:
        if not isinstance(parameter, dict):
            continue  # ParameterFile (bizzyboat.yaml) — topic lists live there
        for name, value in parameter.items():
            params[_resolve(context, name)] = _resolve(context, value)
    return params


def _param_files(entry):
    """Return the config paths this node loads, relative to the package share.

    Only the tail of each `PathJoinSubstitution` is resolved: the head is a
    `FindPackageShare`, which needs the package installed, and these tests run
    against the source tree.
    """
    entity, context = entry
    files = []
    for parameter in entity._Node__parameters or []:
        param_file = getattr(parameter, 'param_file', None)
        if param_file is None:
            continue
        join = param_file[0]
        files.append('/'.join(
            _resolve(context, part) for part in join.substitutions[1:]))
    return files


def test_both_recorders_run_by_default():
    """A bring-up that passes nothing must record both bags."""
    assert sorted(_recorders()) == ['logger', 'sonar_logger']


@pytest.mark.parametrize('argument,expected', [
    ('logger', ['sonar_logger']),
    ('sonar_logger', ['logger']),
])
def test_each_recorder_can_be_disabled_alone(argument, expected):
    """Dropping one bag must not silently drop the other."""
    assert sorted(_recorders(**{argument: 'false'})) == expected


@pytest.mark.parametrize('name', ['logger', 'sonar_logger'])
def test_keyboard_controls_are_disabled(name):
    """emulate_tty arms rosbag2's SPACE-to-pause handler, and these recorders
    now sit in an operator-facing tmux window: a stray keypress there would
    pause the boat's data of record with no error anywhere."""
    entry = _recorders()[name]
    assert _params(entry)['record.disable_keyboard_controls'] is True
    assert entry[0].emulate_tty is True, \
        'if emulate_tty ever goes away, revisit why this test exists'


@pytest.mark.parametrize('name', ['logger', 'sonar_logger'])
def test_recorder_output_reaches_the_logging_window(name):
    """The dedicated window is the operator's only view of whether recording
    started; the launch_ros default ('log') would leave it blank."""
    entity, context = _recorders()[name]
    assert _resolve(context, entity.output) == 'both'


@pytest.mark.parametrize('name,base,subdir', [
    ('logger', 'log_directory', 'log_subdirectory'),
    ('sonar_logger', 'sonar_log_directory', 'sonar_log_subdirectory'),
])
def test_each_recorder_writes_under_its_own_base_directory(name, base, subdir):
    entry = _recorders(**{base: '/tmp/base', subdir: 'stamp'})[name]
    assert _params(entry)['storage.uri'] == '/tmp/base/stamp'


def test_the_two_bags_never_share_a_directory():
    """rosbag2 errors out if its target directory already exists, so a shared
    path would take one of the two recorders down at start."""
    recorders = _recorders()
    uris = {name: _params(entry)['storage.uri']
            for name, entry in recorders.items()}
    assert len(set(uris.values())) == len(uris), uris


def test_the_recorders_run_under_the_boat_namespace():
    """The manual's own check is `ros2 node list | grep /bizzy/...logger`, and
    the operator has no other way to see the bags are running. Without the
    namespace push the recorders come up as `/logger` / `/sonar_logger` and
    that grep silently finds nothing."""
    assert _pushed_namespaces() == ['bizzy']


def test_the_namespace_argument_moves_the_recorders():
    """`namespace:=` has to reach the push, not just be declared."""
    assert _pushed_namespaces(namespace='otherboat') == ['otherboat']


def test_pointing_both_recorders_at_one_directory_is_an_error():
    """Both subdirectory defaults are the same UTC stamp, so one shared base
    directory (P11_LOG_DIR == P11_SONAR_LOG_DIR, which relocating to an
    external disk invites) gives both recorders one `storage.uri` and kills
    whichever starts second."""
    logging_launch = _load_launch_module()
    context = LaunchContext()
    context.launch_configurations.update({
        'log_directory': '/mnt/disk',
        'sonar_log_directory': '/mnt/disk',
        'log_subdirectory': 'stamp',
        'sonar_log_subdirectory': 'stamp',
    })
    with pytest.raises(RuntimeError) as excinfo:
        logging_launch.reject_colliding_bag_directories(context)
    assert 'sonar_log_subdirectory' in str(excinfo.value), \
        'the error must name a way out'


def test_one_shared_base_directory_is_fine_with_distinct_subdirectories():
    """Separate subdirectories under one disk is a legitimate layout."""
    logging_launch = _load_launch_module()
    context = LaunchContext()
    context.launch_configurations.update({
        'log_directory': '/mnt/disk',
        'sonar_log_directory': '/mnt/disk',
        'log_subdirectory': 'stamp',
        'sonar_log_subdirectory': 'stamp_sonar',
    })
    assert logging_launch.reject_colliding_bag_directories(context) == []


def test_each_recorder_loads_the_shared_config():
    """The recorded topic lists live in bizzyboat.yaml, not here."""
    for name, entry in _recorders().items():
        assert _param_files(entry) == ['config/bizzyboat.yaml'], name


def test_the_m3_all_archive_stays_a_sibling_of_the_sonar_bag():
    """perception_launch.py keeps the raw `.all` archive; it must not default
    into the sonar bag's directory or that directory's parent, or the bridge's
    makedirs races the recorder (#458)."""
    perception = _load_launch_module(PERCEPTION_LAUNCH_FILE)
    context = LaunchContext()
    description = perception.generate_launch_description()
    for entity in description.entities:
        if isinstance(entity, DeclareLaunchArgument):
            entity.visit(context)
    all_dir = Path(context.launch_configurations['m3_all_directory'])

    sonar_uri = Path(_params(
        _recorders()['sonar_logger'])['storage.uri'])
    assert all_dir != sonar_uri
    assert all_dir != sonar_uri.parent
    assert all_dir.parent == sonar_uri.parent, \
        'the archive is meant to be a collision-free sibling of the bag dir'


@pytest.mark.parametrize('argument', [
    'log_directory',
    'log_subdirectory',
    'sonar_log_directory',
    'sonar_log_subdirectory',
])
def test_perception_rejects_the_recorder_arguments_that_moved(argument):
    """`ros2 launch` ignores undeclared top-level args, so passing one of these
    to perception_launch.py would bring the boat up clean with the bags at the
    default location and nothing saying so. It has to be a hard error."""
    perception = _load_launch_module(PERCEPTION_LAUNCH_FILE)
    context = LaunchContext(argv=[f'{argument}:=/tmp/somewhere-else'])
    with pytest.raises(RuntimeError) as excinfo:
        perception.reject_moved_recorder_arguments(context)
    message = str(excinfo.value)
    assert argument in message
    assert 'logging_launch.py' in message, 'the error must say where it went'


def test_logging_rejects_the_perception_argument():
    """The relocation table lists all three destinations together, so
    `m3_all_directory:=` aimed at this launch file is the natural mistake;
    `ros2 launch` would take it silently and leave the .all archive behind."""
    logging_launch = _load_launch_module()
    context = LaunchContext(argv=['m3_all_directory:=/tmp/somewhere-else'])
    with pytest.raises(RuntimeError) as excinfo:
        logging_launch.reject_perception_arguments(context)
    message = str(excinfo.value)
    assert 'm3_all_directory' in message
    assert 'perception_launch.py' in message, \
        'the error must say where it goes'


def test_logging_accepts_a_bare_bring_up():
    """The guard must not fire on the normal case."""
    logging_launch = _load_launch_module()
    assert logging_launch.reject_perception_arguments(LaunchContext()) == []


def test_perception_accepts_a_bare_bring_up():
    """The guard must not fire on the normal case."""
    perception = _load_launch_module(PERCEPTION_LAUNCH_FILE)
    assert perception.reject_moved_recorder_arguments(LaunchContext()) == []


@pytest.mark.parametrize('module_path,guard,argument', [
    (PERCEPTION_LAUNCH_FILE, 'reject_moved_recorder_arguments',
     'log_directory'),
    (LAUNCH_FILE, 'reject_perception_arguments', 'm3_all_directory'),
])
def test_the_guards_ignore_an_inherited_configuration(
        module_path, guard, argument):
    """The guards are for a command-line mistake. A larger bring-up that
    includes one of these files and declares the same name for its own
    purposes leaks it in through `launch_configurations` — aborting the whole
    boat over that would be a worse failure than the one being prevented."""
    module = _load_launch_module(module_path)
    context = LaunchContext()
    context.launch_configurations[argument] = '/tmp/inherited'
    assert getattr(module, guard)(context) == []


@pytest.mark.parametrize('name', ['logger', 'sonar_logger'])
def test_the_stop_script_outwaits_the_recorder_shutdown_grace(name):
    """stop_tmux_project11.bash kill-sessions after its timeout; if that is
    shorter than sigterm+sigkill, it SIGHUPs a finalizing mcap.

    Checked per recorder: either one can be the last to finish writing, so
    the budget has to cover whichever grace is longest, not just `logger`'s.
    """
    entity, context = _recorders()[name]
    grace = int(_resolve(context, entity.sigterm_timeout)) + \
        int(_resolve(context, entity.sigkill_timeout))
    match = re.search(r'^SHUTDOWN_TIMEOUT=(\d+)', STOP_SCRIPT.read_text(),
                      re.MULTILINE)
    assert match, 'stop_tmux_project11.bash no longer sets SHUTDOWN_TIMEOUT'
    assert int(match.group(1)) >= grace, \
        f'stop script waits {match.group(1)}s but {name} may take {grace}s'
