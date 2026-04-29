cmake_minimum_required(VERSION 3.18.2)
project(bizzyboat_project11)

find_package(ament_cmake REQUIRED)
find_package(xacro REQUIRED)

install(DIRECTORY config DESTINATION share/${PROJECT_NAME})
install(DIRECTORY docs DESTINATION share/${PROJECT_NAME})
install(DIRECTORY launch DESTINATION share/${PROJECT_NAME})
install(DIRECTORY meshes DESTINATION share/${PROJECT_NAME})
install(DIRECTORY urdf DESTINATION share/${PROJECT_NAME})
install(PROGRAMS
  scripts/start_tmux_project11.bash
  scripts/start_tmux_operator_project11.bash
  scripts/stop_tmux_project11.bash
  scripts/gps_rtk_diagnostics_node.py
  scripts/ntrip_diagnostics_node.py
  scripts/rtcm_relay_node.py
  DESTINATION lib/${PROJECT_NAME})

ament_export_dependencies(
  xacro
)

ament_package()
