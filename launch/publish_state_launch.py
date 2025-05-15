from ament_index_python.packages import get_package_share_path
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command
from launch.substitutions import LaunchConfiguration
from launch.substitutions import TextSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    namespace = LaunchConfiguration('namespace')

    namespace_arg = DeclareLaunchArgument(
      "namespace", default_value=TextSubstitution(text="izzy")
    )

    remappings = []#('/tf', 'tf'), ('/tf_static', 'tf_static')]
    
    path_to_urdf = get_package_share_path('izzyboat_project11') / 'urdf' / 'izzyboat.urdf'
    robot_state_publisher_node = Node(
       package='robot_state_publisher',
       executable='robot_state_publisher',
       name='robot_state_publisher',
       namespace=namespace,
       parameters=[{
           'robot_description': ParameterValue(
            Command(['xacro ', str(path_to_urdf)]), value_type=str
           )
       }],
       remappings=remappings
    )



    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        namespace=namespace,
        remappings=remappings
    )

    return LaunchDescription([
        namespace_arg,
        robot_state_publisher_node,
        joint_state_publisher_node
    ])


