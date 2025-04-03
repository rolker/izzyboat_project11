cmake_minimum_required(VERSION 3.18.2)
project(izzyboat_project11)

find_package(ament_cmake REQUIRED)
find_package(xacro REQUIRED)

install(DIRECTORY config DESTINATION share/${PROJECT_NAME})
install(DIRECTORY launch DESTINATION share/${PROJECT_NAME})
install(DIRECTORY urdf DESTINATION share/${PROJECT_NAME})

ament_export_dependencies(
  xacro
)

ament_package()
