from ament_index_python.packages import get_package_share_path
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command
from launch.substitutions import LaunchConfiguration
from launch.substitutions import TextSubstitution
from launch_ros.actions import SetParameter
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    namespace = LaunchConfiguration('namespace')
    parameter_name = LaunchConfiguration('parameter_name')

    namespace_arg = DeclareLaunchArgument(
      "namespace", default_value=TextSubstitution(text="izzy")
    )

    parameter_name_arg = DeclareLaunchArgument(
        'parameter_name', default_value=[namespace, '.robot_description']
    )

    path_to_urdf = get_package_share_path('izzyboat_project11') / 'urdf' / 'izzyboat.urdf'
    set_robot_description = SetParameter(
        name=parameter_name,
        value=ParameterValue(
            Command(['xacro ', str(path_to_urdf)])
        )
    )

    return LaunchDescription([
       namespace_arg,
       parameter_name_arg,
       set_robot_description
    ])


