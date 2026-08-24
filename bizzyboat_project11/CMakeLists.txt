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
  # NOT installed, deliberately: scripts/gnss_vertical_calibration.py is an
  # offline bag-analysis tool run by hand from the source tree, like the
  # retrofit_*_bag.py scripts. It reads bags and prints numbers; nothing on the
  # boat launches it.
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
  # The cross-repo preflight check in core_launch.py: echo_helm's
  # ellipsoidal_fix_node exists only on seafloor_echoboat_project11 #56, and a
  # stale build must fail with a message naming the repo to rebuild.
  ament_add_pytest_test(test_core_launch test/test_core_launch.py)
  # fix_type -> level, and the vertical-accuracy override that catches the
  # 2026-08-20 case: 'RTK Fixed', OK, green, with v_acc 1.750 m beside it.
  ament_add_pytest_test(test_gps_rtk_diagnostics test/test_gps_rtk_diagnostics.py)
  # The sign of the correction gnss_vertical_calibration.py prints: the URDF is
  # z-up and ArduPilot's GPS_POS* are z-down, so the two edits it recommends
  # are opposite in sign, and it is the line an operator copies.
  ament_add_pytest_test(test_gnss_vertical_calibration
    test/test_gnss_vertical_calibration.py)
endif()

ament_package()
