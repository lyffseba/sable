# SABLE tracking v1
Geometry is inverted vs Sinden: camera at display, marker on mouse.
1-blob homography = laser pointer (JS proto). Gun heading needs 2-3 dots or ArUco+PnP.
HID click never waits on camera. Lift = HID idle AND camera. No LOD in Win32 mouse API.
2021 G14 often has no built-in webcam — clip cam top-center, AE off, 720p YUY2.
AimSample { uv, valid, lifted, confidence, t_hw }
