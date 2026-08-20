# unh_echoboats_project11

ROS 2 configuration and launch files for UNH CCOM's EchoBoats. The current,
deployed platform is **BizzyBoat** (EchoBoat 240); **IzzyBoat** (EchoBoat 160) is
the older testing platform.

## Packages

- **bizzyboat_project11** — URDF, launch files, and configuration for **BizzyBoat
  (EchoBoat 240)**, the current deployed boat. Includes the autonomy bring-up
  (core/perception/navigation launches), sensor drivers (OAK cameras, sonar), and
  UDP bridge configuration for operator communication.
- **izzyboat_project11** — URDF, launch files, and configuration for IzzyBoat
  (EchoBoat 160), the older testing platform.

## Network

BizzyBoat communicates with the operator station over a dedicated WiFi backhaul
link with a Starlink/VPN fallback path. See
[docs/bizzyboat_network.md](docs/bizzyboat_network.md) for full network
documentation.

## Documentation

- **[BizzyBoat operator manual](docs/bizzyboat_operator_manual.md)** — student
  operator guide: bring the boat up, drive it, run a survey, shut it down.
- [BizzyBoat network setup](docs/bizzyboat_network.md) — subnets, devices, VPN,
  router details.
- [BizzyBoat hardware](bizzyboat_project11/docs/bizzyboat_hardware.md) — sensors,
  computers, payload.
- [BizzyBoat power](bizzyboat_project11/docs/bizzyboat_power.md) — power system and
  power-on notes.
- [BizzyBoat reference geometry](bizzyboat_project11/docs/bizzyboat_reference_geometry.md)
  — offsets and mounting geometry.
- [Datum polygon deploy](docs/datum_polygon_deploy.md) — materializing the
  git-reviewed datum override polygons into `~/data/world/datum/user/` on the
  boat host (the ADR-0010 D1 git-authored exception; CAMP provisioning
  deferred).
- [IzzyBoat network setup](docs/izzyboat_network.md) — legacy 160 platform.
