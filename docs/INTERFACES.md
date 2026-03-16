# AgentSlam Interface Draft

## Design Principles

- Prefer standard ROS 2 messages first.
- Keep data contracts explicit and versioned through docs before code complexity grows.
- Assume GT pose is available in the initial runtime.
- Avoid custom messages until they are clearly justified by an integration gap.

## Planned Runtime Interfaces

### Isaac Sim Bridge Inputs

- office scene assets from `/home/peng/isaacsim_assets`
- Nova wheeled robot asset selection
- camera configuration
- IMU configuration

### Isaac Sim Bridge Outputs

- `/clock` using ROS simulation time
- `/tf` and `/tf_static`
- camera image topic using `sensor_msgs/msg/Image`
- camera intrinsics using `sensor_msgs/msg/CameraInfo`
- IMU topic using `sensor_msgs/msg/Imu`
- GT pose or odometry using a standard message such as `geometry_msgs/msg/PoseStamped` or `nav_msgs/msg/Odometry`

### Mapping Inputs

- synchronized camera image plus camera info
- IMU stream
- GT pose for early-stage alignment and evaluation

### Mapping Outputs

- semantic map representation stored under `maps/semantic/`
- room graph representation stored under `maps/rooms/`
- route-supporting artifacts stored under `maps/routes/`

### Navigation Inputs

- GT pose
- room graph or semantic map queries
- standard Nav2 goal interfaces

### Navigation Outputs

- route or waypoint decisions
- Nav2-compatible goal execution signals
- evaluation artifacts for smoke and replay validation

## Interface Rules

- Any interface change must update this file and `docs/DATAFLOW.md`.
- Topic names, frame names, and message selections should be frozen only after Prompt 2 environment audit and Prompt 3 upstream analysis.
- LiDAR topics are out of scope by default unless the project direction changes explicitly.

## Open Items

- final GT pose topic name and message type
- exact TF tree between world, map, odom, base, camera, and imu frames
- whether semantic outputs should first be filesystem artifacts, ROS topics, or both
