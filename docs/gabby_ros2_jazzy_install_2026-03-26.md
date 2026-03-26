# Install ROS 2 Jazzy on gabby

**Date**: 2026-03-26
**Issue**: rolker/unh_echoboats_project11#16
**Host**: gabby (Neousys Nuvo 9160GC, Ubuntu 24.04 Server)
**Operator**: Roland + Claude Code Agent

## Prerequisites

- Ubuntu 24.04 Server installed
- Network connectivity confirmed (BizzyBoat LAN, operator network, ZeroTier)
- SSH access working

## Step 1: Install ROS 2 Jazzy

Followed official install instructions:
- https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html
- Installed `ros-jazzy-ros-base` (base install, no GUI)
- Installed optional dev tools
- Verified working:
  ```
  source /opt/ros/jazzy/setup.bash
  ros2 topic list
  # /parameter_events
  # /rosout
  ```

## Summary

ROS 2 Jazzy base install complete on gabby. Ready for workspace bootstrap (#17).
