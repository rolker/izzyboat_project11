# UNH CCOM EchoBoat 160 measurements

The GPS reports distance realtive to the mounting point of the aft antenna, which is about 2 centimeters below the bottom of the antenna.

Initial URDF config will set that as base_link.

The top mounting bar is 177 cm long by 7 cm wide. Aft gps is about 2.5 cm from aft end of bar. Fwd gps is about 9 cm from front of bar.

Forward camera imaging reference point is approximately 5.5 cm forward of bar and 5.5 cm below bar.

Aft trimble gps to aft cuav gps ~10" or ~.25m

cuav gps aft to ref point (center of well cover) 0.203m



# Dynamics estimate from looking at foxglove graphs

1 m/s in about 1.5 s


tops out at 1 m/s

Acc about .6 m/s

Drif decel -.15 m/s

Powered decel about -1 m/s2

rotation speed 1 rad/s max

 rot accel 1.2 rad/s2 or 1.1 rad/s2
 
Above p11, below rc

 1.7 in 2 seconds
 
 Top about 2 m/s
 
 .5 to about 1.8 in 2 seconds
 
 Decel not powered, 10 seconds to loose 1.5 m/s
 
 1.85 to .75 in 3 sec
 
 Powered decel 2.0 m/s to 0 in about 2.2 secs
 
 
 rotation speed max 1.5 rad/sec
 
 unpowere rotational decel 1.5 to .5 in 3 sec
 
 powered rotation change 1.45 to -.95 in 3 secs
 
  Turn radius about 4m at 2 m/s, 3m at 1 m/s