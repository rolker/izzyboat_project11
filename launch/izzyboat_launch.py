from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch.substitutions import TextSubstitution
from launch_ros.actions import Node
from launch_ros.actions import PushRosNamespace
from launch_ros.actions import SetParameter
from launch_ros.actions import SetParametersFromFile
from launch_ros.actions import SetRemap
from launch_ros.substitutions import FindPackageShare

import datetime

def generate_launch_description():
    namespace = LaunchConfiguration('namespace')

    namespace_arg = DeclareLaunchArgument(
      "namespace", default_value=TextSubstitution(text="izzy")
    )

    frame_prefix = LaunchConfiguration('frame_prefix')

    frame_prefix_arg = DeclareLaunchArgument(
        "frame_prefix", default_value="izzy/"
    )


    fcu_url = LaunchConfiguration('fcu_url')
    gcs_url = LaunchConfiguration('gcs_url')

    fcu_url_arg = DeclareLaunchArgument(
      #"fcu_url", default_value=TextSubstitution(text="/dev/ttyACM0:57600")
      "fcu_url", default_value=TextSubstitution(text="/dev/ttyUSB0:57600")
    )

    gcs_url_arg = DeclareLaunchArgument(
      "gcs_url", default_value=TextSubstitution(text="udp://@192.168.12.8")
    )

    log_directory = LaunchConfiguration('log_directory')

    log_directory_arg = DeclareLaunchArgument('log_directory')

    sonar_log_directory = LaunchConfiguration('sonar_log_directory')
    sonar_log_directory_arg = DeclareLaunchArgument(
        'sonar_log_directory',
        default_value=TextSubstitution(text='/home/field/project11/logs/izzyboat_sonar')
    )

    datetime_str = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds').replace(':', '-')
    sonar_log_subdirectory = LaunchConfiguration('sonar_log_subdirectory')

    sonar_log_subdirectory_arg = DeclareLaunchArgument( 'sonar_log_subdirectory', 
    default_value=TextSubstitution(text=datetime_str))

    return LaunchDescription([
      namespace_arg,
      frame_prefix_arg,
      fcu_url_arg,
      gcs_url_arg,
      log_directory_arg,
      sonar_log_directory_arg,
      sonar_log_subdirectory_arg,
      GroupAction(
          actions=[
            IncludeLaunchDescription(
              PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                  FindPackageShare('echoboat_project11'),
                  'launch',
                  'echo_launch.py'
                ])
              ),
              launch_arguments={
                'namespace': namespace,
                'frame_prefix': frame_prefix,
                'fcu_url': fcu_url,
                'gcs_url': gcs_url,
              }.items()
            ),
            IncludeLaunchDescription(
              PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                  FindPackageShare('izzyboat_project11'),
                  'launch',
                  'publish_state_launch.py'
                ])
              ),
              launch_arguments={
                'namespace': namespace
              }.items()
            )
          ]
      ),
      GroupAction(
          actions=[
            PushRosNamespace(namespace),
            SetParametersFromFile(
              filename=PathJoinSubstitution([
                  FindPackageShare('izzyboat_project11'),
                  'config',
                  'izzyboat.yaml'
              ])                
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution([
                        FindPackageShare('udp_bridge'),
                        'launch',
                        'udp_bridge_launch.py'
                    ])
                )
            ),
            GroupAction(
                actions=[
                  PushRosNamespace('sensors/deltat'),
                  IncludeLaunchDescription(
                      PythonLaunchDescriptionSource(
                          PathJoinSubstitution([
                              FindPackageShare('imagenex_deltat'),
                              'launch',
                              'deltat_launch.py'
                          ])
                      )
                  ),
                  IncludeLaunchDescription(
                      PythonLaunchDescriptionSource(
                          PathJoinSubstitution([
                              FindPackageShare('cube_bathymetry'),
                              'launch',
                              'cube_bathymetry_launch.py'
                          ])
                      )
                  ),

                ]
            ),
            # GroupAction(
            #     actions=[
            #       PushRosNamespace('sensors/norbit'),
            #       # IncludeLaunchDescription(
            #       #     PythonLaunchDescriptionSource(
            #       #         PathJoinSubstitution([
            #       #             FindPackageShare('norbit_driver'),
            #       #             'launch',
            #       #             'norbit_launch.py'
            #       #         ])
            #       #     )
            #       # ),
            #       GroupAction(
            #           actions=[
            #             SetRemap(
            #               src='position',
            #               dst=PathJoinSubstitution([
            #                   namespace,
            #                   'sensors/posmv/position'
            #               ])
            #             ),
            #             SetRemap(
            #                 src='orientation',
            #                 dst=PathJoinSubstitution([
            #                     namespace,
            #                     'sensors/posmv/orientation'
            #                 ])
            #             ),
            #             SetRemap(
            #                 src='velocity',
            #                 dst=PathJoinSubstitution([
            #                     namespace,
            #                     'sensors/posmv/velocity'
            #                 ])
            #             ),
            #             IncludeLaunchDescription(
            #                 PythonLaunchDescriptionSource(
            #                     PathJoinSubstitution([
            #                         FindPackageShare('cube_bathymetry'),
            #                         'launch',
            #                         'detections_to_pointcloud_launch.py'
            #                     ])
            #                 )
            #             ),
            #           ]
            #       ),
            #       IncludeLaunchDescription(
            #           PythonLaunchDescriptionSource(
            #               PathJoinSubstitution([
            #                   FindPackageShare('cube_bathymetry'),
            #                   'launch',
            #                   'cube_bathymetry_launch.py'
            #               ])
            #           )
            #       ),
            #     ]
            # ),
            GroupAction(
              actions=[
                  PushRosNamespace('sensors/posmv'),
                  IncludeLaunchDescription(
                      PythonLaunchDescriptionSource(
                          PathJoinSubstitution([
                              FindPackageShare('posmv'),
                              'launch',
                              'posmv_launch.py'
                          ])
                      )
                  )
              ]      
            ),
            GroupAction(
              actions=[
                PushRosNamespace('sensors/cameras/front'),
                GroupAction(
                  actions=[
                      PushRosNamespace('usb/'),
                      Node(
                          package="usb_cam",
                          executable="usb_cam_node_exe",
                          name="usb_camera_forward",
                          parameters=[{
                              'camera_name': 'usb_camera_forward',
                              'framerate': 30.0,
                              'image_width': 1920,
                              'image_height': 1080,
                              'frame_id': 'izzy/usb_camera_forward_optical',
                              'camera_info_url': 'package://izzyboat_project11/config/camera_forward.yaml',
                              'pixel_format': 'yuyv2rgb',
                        
                          }]
                      ),
                      # Node(
                      #   package="topic_tools",
                      #   executable="throttle",
                      #   name="throttle_usb",
                      #   arguments=['message',],
                      #   parameters=[{
                      #       'input_topic':'image_raw/compressed',
                      #       'output_topic': 'image_raw/throttled/compressed',
                      #       'throttle_type': 'messages',
                      #       'msgs_per_sec': 0.2
                      #   }]
                        
                      # ),
                  ]
                ),
                IncludeLaunchDescription(
                  PythonLaunchDescriptionSource(
                    PathJoinSubstitution([
                      FindPackageShare('izzyboat_project11'),
                      'launch',
                      'oak1_launch.py'
                    ])
                  ),
                ),
              ]
            ),
            Node(
              package='rosbag2_transport',
              executable='recorder',
              name='logger',
              parameters=[
                PathJoinSubstitution([
                  FindPackageShare('izzyboat_project11'),
                  'config',
                  'izzyboat.yaml'
                ]),
                {'storage.uri': log_directory}                     
              ]
            ),
            Node(
              package='rosbag2_transport',
              executable='recorder',
              name='sonar_logger',
              parameters=[
                PathJoinSubstitution([
                  FindPackageShare('izzyboat_project11'),
                  'config',
                  'izzyboat.yaml'
                ]),
                {'storage.uri': PathJoinSubstitution([
                  sonar_log_directory,
                  sonar_log_subdirectory
                ])},
              ]
            ),

          ]
      ),

      IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
          PathJoinSubstitution([
            FindPackageShare('izzyboat_project11'),
            'launch',
            'ntrip_launch.py'
          ])
        ),
      ),
          

    ])




# <launch>
#   <arg name="namespace" default="izzy"/>
#   <arg name="platform_name" default="$(arg namespace)"/>
#   <arg name="platform_package" default="izzyboat_project11"/>
#   <arg name="operator_host" default="salmonib"/>
#   <arg name="logDirectory" default="/dev/null"/>
#   <arg name="urdf_model" default="$(find izzyboat_project11)/urdf/izzyboat.urdf"/>
#   <arg name="fcu_url" default="/dev/ttyUSB0:57600"/> 
#   <arg name="gcs_url" default="udp://@192.168.12.8"/> 
#   <!-- <arg name="gcs_url" default="udp://@192.168.13.142"/> -->


#   <remap from="/$(arg namespace)/sensors/mbes/soundings" to="/$(arg namespace)/sensors/deltat/soundings"/>
#   <remap from="/$(arg namespace)/sensors/ntrip/rtcm" to="/$(arg namespace)/mavros/gps_rtk/send_rtcm"/>

#   <!-- <include file="$(find izzyboat_project11)/launch/ntrip.launch">
#     <arg name="namespace" value="$(arg namespace)"/>
#   </include> -->

#   <include file="$(find echoboat_project11)/launch/echo.launch">
#     <arg name="namespace" value="$(arg namespace)"/>
#     <arg name="platform_name" value="$(arg platform_name)"/>
#     <arg name="platform_package" value="$(arg platform_package)"/>
#     <arg name="operator_host" value="$(arg operator_host)"/>
#     <arg name="fcu_url" value="$(arg fcu_url)"/>
#     <arg name="gcs_url" value="$(arg gcs_url)"/>
#   </include> 

#   <group ns="$(arg namespace)">

#     <node name="robot_state_publisher" pkg="robot_state_publisher" type="robot_state_publisher">
#       <param name="use_tf_static" value="false"/>
#     </node>

#     <group ns="sensors/cameras/">

#       <node pkg="usb_cam" type="usb_cam_node" name="camera_forward"> 
#         <param name="camera_name" value="camera_forward" />
#         <param name="framerate" value="30" />
#         <param name="image_width" value="1920"/>
#         <param name="image_height" value="1080"/>
#         <param name="camera_frame_id" type="string" value="$(arg namespace)/camera_forward_optical" />
#         <param name="camera_info_url" value="file://$(find izzyboat_project11)/config/camera_forward.yaml"/>
#       </node>

#       <!-- <node pkg="opencv_dnn" type="opencv_dnn_node" name="yolov8">
#         <param name="model" value="$(find opencv_dnn)/config/jenna.onnx"/>
#         <param name="detections_parser" value="opencv_dnn::YOLOv5Parser"/>
#         <remap from="image" to="camera_forward/image_raw"/>
#       </node> -->

#       <node pkg="topic_tools" type="throttle" name="throttle_forward" args="messages camera_forward/image_raw/compressed .5"/>


#       <include file="$(find depthai_ros_driver)/launch/camera.launch">
#       </include>

#       <node pkg="topic_tools" type="throttle" name="throttle_oak" args="messages oak/rgb/image_raw/compressed .5"/>

#       <!-- <node pkg="octomap_server" type="octomap_server_node" name="octomap_server" ns="oak">
#         <remap from="cloud_in" to="points"/>
#         <param name="resolution" value="0.1"/>
#         <param name="frame_id" value="$(arg namespace)/map"/>
#       </node> -->

#     </group>

#     <node pkg="imu_to_tss" type="imu_to_tss.py" name="imu_to_tss">
#       <remap from="input" to="mavros/imu/data"/>
#       <param name="address" value="blaze"/>
#       <param name="port" value="4321"/>
#     </node> 

#     <group ns="mavros/global_position">
#       <node pkg="marine_tools" type="navsatfix_to_nmea" name="navsatfix_to_nmea">
#         <remap from="input" to="raw/fix"/>
#         <remap from="satellites" to="raw/satellites"/>
#       </node>
#       <node pkg="marine_tools" type="nmea_to_udp.py" name="gga_to_udp">
#         <param name="address" value="blaze"/>
#       </node>
#       <node pkg="marine_tools" type="nmea_to_udp.py" name="gga_to_udp_4041">
#         <param name="address" value="blaze"/>
#         <param name="port" value="4041"/>
#       </node>
#     </group>

#     <group ns="mavros/imu">
#       <node pkg="marine_tools" type="imu_to_hdt" name="imu_to_hdt">
#         <remap from="input" to="data"/>
#       </node>
#       <node pkg="marine_tools" type="imu_to_pashr" name="imu_to_pashr">
#         <remap from="input" to="data"/>
#       </node>
#       <node pkg="marine_tools" type="nmea_to_udp.py" name="hdt_to_udp">
#         <param name="address" value="blaze"/>
#       </node>
#       <node pkg="marine_tools" type="nmea_to_udp.py" name="hdt_to_udp_4041">
#         <param name="address" value="blaze"/>
#         <param name="port" value="4041"/>
#       </node>
#       <node pkg="marine_tools" type="nmea_to_udp.py" name="hdt_to_udp_4042">
#         <param name="address" value="blaze"/>
#         <param name="port" value="4042"/>
#       </node>
#     </group>

#     <group ns="sensors/deltat">
#       <node pkg="imagenex_deltat" type="deltat.py" name="deltat">
#         <param name="frame_id" value="$(arg platform_name)/deltat"/>
#       </node>

#       <node pkg="octomap_server" type="octomap_server_node" name="octomap_server">
#         <remap from="cloud_in" to="soundings"/>
#         <param name="resolution" value="0.25"/>
#         <param name="frame_id" value="$(arg namespace)/map"/>
#       </node>
#     </group>



#     <node pkg="rosbag" type="record" name="logger"  ns="$(arg namespace)" args="-o $(arg logDirectory)/izzyboat --split --duration=15m --repeat-latched --lz4 -a -x  &quot;(.*)image(.*)|(.*)lidar(.*)|(.*)points(.*)|(.*)s57_grids(.*)|(.*)octomap(.*)|(.*)projected_map(.*)|(.*)occupied_cells_vis_array(.*)&quot;
# "   />

#     <node pkg="rosbag" type="record" name="video_logger"  ns="$(arg namespace)" args="-o $(arg logDirectory)/izzyboat_video --split --duration=15m --repeat-latched --lz4 /izzy/sensors/cameras/camera_forward/camera_info /izzy/sensors/cameras/camera_forward/image_raw/compressed_throttle /izzy/sensors/cameras/oak/rgb/camera_info /izzy/sensors/cameras/oak/rgb/image_raw/compressed_throttle"   />

#     <node pkg="rosbag" type="record" name="sonar_logger"  ns="$(arg namespace)" args="-o $(arg logDirectory)/izzyboat_sonar --split --duration=15m --repeat-latched --lz4 /izzy/sensors/deltat/soundings"   />


#     <rosparam command="load" file="$(find izzyboat_project11)/config/izzyboat.yaml"/>

  
#     <param name="robot_description" command="$(find xacro)/xacro $(arg urdf_model) namespace:=$(arg namespace)"/>

#   </group>


# </launch>
