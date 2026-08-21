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
  scripts/start_tmux_camera_test.bash
  scripts/start_tmux_operator_bridge.bash
  scripts/stop_tmux_project11.bash
  scripts/gps_rtk_diagnostics_node.py
  scripts/rtcm_diagnostics_node.py
  scripts/rtcm_relay_node.py
  DESTINATION lib/${PROJECT_NAME})

ament_export_dependencies(
  xacro
)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  # Unit tests for the one-off bag-retrofit utility (#342). The script itself is
  # not installed (manual offline tool, like retrofit_sidescan_bag.py).
  ament_add_pytest_test(test_retrofit_m3_bag test/test_retrofit_m3_bag.py)
  # Station-agnostic wiring in operator_core_launch.py (return_host derivation
  # + the wifi:=false overlay). Both fail silently in the field if broken.
  ament_add_pytest_test(test_operator_core_launch test/test_operator_core_launch.py)
  # RTCM framing/CRC, 1005-1006 decode, baseline and thresholds.
  ament_add_pytest_test(test_rtcm_diagnostics test/test_rtcm_diagnostics.py)
endif()

ament_package()
