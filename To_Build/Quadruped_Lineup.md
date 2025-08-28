# Unitree Quadruped Robot Models - Comprehensive Technical Analysis

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Go2 Series - Consumer to Enterprise ($1,600-$22,500)](#go2-series---consumer-to-enterprise-1600-22500)
   - [Go2 Air - Entry Level ($1,600)](#go2-air---entry-level-1600)
   - [Go2 Pro - Enhanced Consumer ($2,800-$4,590)](#go2-pro---enhanced-consumer-2800-4590)
   - [Go2 ENT - Enterprise Grade ($13,900-$14,500)](#go2-ent---enterprise-grade-13900-14500)
   - [Go2 EDU - Educational Platform ($4,500)](#go2-edu---educational-platform-4500)
   - [Go2 EDU Plus - Advanced Research ($16,000-$22,500)](#go2-edu-plus---advanced-research-16000-22500)
3. [A-Series - Industrial Innovation ($50,000-$70,000)](#a-series---industrial-innovation-50000-70000)
   - [A1 - Legacy Industrial (Price on Request)](#a1---legacy-industrial-price-on-request)
   - [A2 - Next Generation (August 2025 Release)](#a2---next-generation-august-2025-release)
4. [B-Series - Heavy Industrial ($50,000-$150,000)](#b-series---heavy-industrial-50000-150000)
   - [B1 - Original Industrial ($80,000-$100,000)](#b1---original-industrial-80000-100000)
   - [B2 - Current Flagship ($78,700-$100,000)](#b2---current-flagship-78700-100000)
   - [B2-W - Wheeled Variant ($100,000-$150,000)](#b2-w---wheeled-variant-100000-150000)
5. [Legacy Models](#legacy-models)
   - [Go1 Series ($2,700-$8,500)](#go1-series-2700-8500)
   - [AlienGo ($50,000)](#aliengo-50000)
6. [Accessories and Add-Ons](#accessories-and-add-ons)
   - [Battery Systems](#battery-systems)
   - [LiDAR Technology](#lidar-technology)
   - [Charging Infrastructure](#charging-infrastructure)
   - [Teleoperation Equipment](#teleoperation-equipment)
7. [Azure Integration Architecture](#azure-integration-architecture)
8. [Deployment Specifications by Site Size](#deployment-specifications-by-site-size)
9. [Financial Analysis by Model](#financial-analysis-by-model)
10. [Technical Comparison Matrix](#technical-comparison-matrix)

---

## Executive Summary

Unitree's quadruped robot portfolio encompasses 15 distinct models across consumer, educational, and industrial categories, with pricing ranging from $1,600 to $150,000. The product line demonstrates clear technological segmentation: consumer models (Go2 Air/Pro) lack SDK access and weatherproofing entirely, educational variants (Go2 EDU/EDU Plus) provide full programming capabilities with the EDU Plus being the only model supporting autonomous self-charging, and industrial platforms (B-series, A-series) offer IP67 weatherproofing and payload capacities from 25-40kg. Current Azure IoT Hub integration exists across all models via MQTT protocol, though implementation complexity varies significantly based on available SDK access and onboard computing resources.

---

## Go2 Series - Consumer to Enterprise ($1,600-$22,500)

The Go2 series comprises five variants built on a common 12kg chassis platform, differentiated primarily through computing hardware, sensor configurations, and software restrictions. All models include Unitree's proprietary 4D LiDAR L1 as standard equipment.

### Go2 Air - Entry Level ($1,600)

The Go2 Air represents Unitree's market entry point, utilizing cost reduction strategies including limited onboard computing, single camera configuration, and complete absence of SDK access.

**Physical Specifications**:
- **Weight**: 12kg unloaded
- **Dimensions**: 620mm length × 280mm width × 400mm height
- **Maximum velocity**: 2.5 m/s
- **Kinematic chain**: 12 DOF (3 per leg)
- **Joint torque**: Unspecified (lower than Pro variants)
- **Ground clearance**: 90mm nominal

**Power System**:
- **Battery chemistry**: Lithium-ion
- **Capacity**: 8,000mAh at 28.8V nominal
- **Energy**: 230Wh total
- **Runtime**: 60-90 minutes typical operation
- **Charging time**: 2.3 hours with standard charger
- **Battery swapping**: Requires complete shutdown
- **Power consumption**: 150-200W during walking

**Environmental Tolerance**:
- **Operating temperature**: Not specified by manufacturer
- **Storage temperature**: Not specified
- **IP rating**: None (indoor use assumed)
- **Humidity tolerance**: Not specified
- **Maximum operational altitude**: Not tested

**Locomotion Capabilities**:
- **Maximum step height**: 15cm (5.9 inches)
- **Maximum slope**: 30° incline/decline
- **Payload capacity**: 1kg nominal, 2kg maximum static
- **Turning radius**: Zero (can rotate in place)
- **Gait patterns**: Walk, trot, crawl
- **Obstacle detection**: Basic via LiDAR only

**Sensor Suite**:
- **Primary LiDAR**: 4D L1 with 360°×90° hemispherical coverage
- **LiDAR range**: 0.05m to 30m
- **LiDAR sample rate**: 21,600 points/second
- **Camera**: Single 720p front-facing
- **IMU**: 6-axis (3-axis gyro, 3-axis accelerometer)
- **Joint encoders**: Magnetic, 12-bit resolution
- **Foot contact sensors**: Basic binary contact detection

**Computing Architecture**:
- **Main processor**: ARM-based (specific model undisclosed)
- **RAM**: Unspecified (estimated 2-4GB)
- **Storage**: Unspecified (estimated 16-32GB eMMC)
- **AI acceleration**: None
- **Operating system**: Proprietary embedded Linux
- **User access**: Remote control only, no programming interface

**Communications**:
- **WiFi**: 802.11ac dual-band (5GHz/2.4GHz)
- **Maximum WiFi range**: 50m open area, 20m with obstacles
- **Bluetooth**: Version 5.2
- **Bluetooth range**: 30m typical
- **Cellular**: Not available
- **Control latency**: 50-100ms local network

**Software Limitations**:
- No SDK or API access
- Pre-programmed behaviors only
- Mobile app control (iOS/Android)
- No custom development possible
- No ROS support
- No cloud integration beyond basic telemetry

### Go2 Pro - Enhanced Consumer ($2,800-$4,590)

The Go2 Pro adds cellular connectivity, enhanced processing, and improved sensors while maintaining the consumer-focused approach with restricted programming access. Price variation reflects regional differences and bundle configurations.

**Physical Specifications**:
- **Weight**: 15kg (includes enhanced battery)
- **Dimensions**: 620mm × 280mm × 400mm (unchanged)
- **Maximum velocity**: 3.5 m/s
- **Joint torque**: 23.7 N⋅m per joint
- **Mechanical power**: 300W peak per leg
- **Sound level**: 65dB at 1m distance

**Power System**:
- **Standard battery**: 8,000mAh providing 60-120 minutes
- **Extended battery option**: 15,000mAh providing 120-240 minutes
- **Extended battery cost**: Additional $1,980
- **Quick charge capability**: 1.5 hours with 9A fast charger
- **Battery management**: Active thermal monitoring
- **Hot-swap capability**: Not supported

**Environmental Tolerance**:
- **Operating temperature**: 0°C to 40°C verified
- **Storage temperature**: -20°C to 60°C
- **IP rating**: IPX4 (splash resistant from all directions)
- **Humidity**: 20-80% non-condensing
- **Drop test rating**: 0.5m onto concrete
- **Vibration resistance**: 5G peak acceleration

**Locomotion Capabilities**:
- **Maximum step height**: 16cm
- **Maximum slope**: 30° sustained, 35° momentary
- **Payload capacity**: 2kg continuous, 3kg peak
- **Speed with payload**: 2.5 m/s with 2kg load
- **Endurance with payload**: Reduced by approximately 40%
- **Terrain adaptation**: Automatic gait adjustment

**Enhanced Sensor Suite**:
- **LiDAR**: 4D L1 standard (same as Air)
- **Cameras**: Dual 720p (front and belly-mounted)
- **Camera frame rate**: 30fps
- **Camera latency**: 120ms typical
- **GPS**: Integrated with 3m accuracy
- **Ultrasonic sensors**: 4× for close-range detection
- **Temperature sensors**: Battery, motor, and ambient

**Computing Upgrade**:
- **Main processor**: 8-core ARM Cortex-A73
- **Clock speed**: 2.2GHz maximum
- **RAM**: 8GB LPDDR4
- **Storage**: 64GB eMMC
- **Graphics**: Mali-G52 GPU
- **Neural processing**: Basic NPU (2 TOPS)

**Connectivity Enhancement**:
- **WiFi**: WiFi 6 (802.11ax) with MIMO
- **Cellular**: 4G LTE Cat 12 with eSIM
- **Cellular bands**: Supports 20+ global LTE bands
- **Data consumption**: 500MB-2GB monthly typical
- **Network handoff**: Automatic WiFi to cellular failover
- **Remote range**: Unlimited with cellular coverage

**Included Accessories** (varies by region):
- Intelligent controller with 4.3" display
- 12-month warranty (24-month in EU)
- Fast charger (9A variant)
- Carrying case
- Mobile app premium features
- 1-year cellular data plan (select regions)

**Software Capabilities**:
- Pre-programmed patrol routes
- Follow-me mode using GPS
- Obstacle avoidance behaviors
- Voice command recognition (basic)
- Still no SDK access
- Cloud backup of settings only

### Go2 ENT - Enterprise Grade ($13,900-$14,500)

The ENT (Enterprise) variant bridges consumer and professional segments, introducing limited SDK access, improved environmental resistance, and teleoperation capabilities while maintaining affordability.

**Physical Specifications**:
- **Weight**: 15kg standard configuration
- **Structural material**: Aerospace-grade aluminum alloy
- **Impact resistance**: IK08 rating
- **Maximum velocity**: 5 m/s
- **Acceleration**: 0 to 5 m/s in 3 seconds
- **Braking distance**: 2m from maximum speed

**Power System**:
- **Battery options**: 8,000mAh standard, 15,000mAh recommended
- **Runtime**: 2-3 hours mixed operation
- **Power monitoring**: Real-time consumption tracking
- **Battery health**: Predictive degradation modeling
- **Charging compatibility**: Works with Go2 charging stations
- **Autonomous docking**: Can use stations but cannot self-navigate

**Environmental Specifications**:
- **Operating temperature**: -10°C to 45°C tested
- **IP rating**: IP54 (dust protected, water splash resistant)
- **Salt spray test**: 48 hours per ASTM B117
- **UV resistance**: 500 hours exposure tested
- **Chemical resistance**: Basic industrial chemicals
- **EMI/EMC compliance**: FCC Part 15, CE marked

**Advanced Locomotion**:
- **Maximum step height**: 18cm
- **Maximum slope**: 35° continuous operation
- **Payload capacity**: 5kg continuous, 8kg peak for 30 minutes
- **Side slope stability**: 20° maximum
- **Recovery capability**: Self-rights from any position
- **Emergency stop**: Hardware switch with 10m remote

**Professional Sensor Configuration**:
- **LiDAR options**: L1 standard, L2 upgrade available (+$170)
- **Cameras**: Dual 1080p wide-angle (120° FOV)
- **Camera specifications**: H.264 encoding, 30fps
- **Night vision**: Optional IR illuminator kit
- **Thermal camera option**: FLIR Lepton 3.5 integration
- **Environmental sensors**: Temperature, humidity, air quality

**Enterprise Computing**:
- **Processor options**: ARM standard or Intel Core i5 upgrade
- **Intel variant**: i5-1135G7 quad-core
- **RAM**: 8GB standard, 16GB optional
- **Storage**: 128GB SSD standard
- **Expansion slots**: M.2 for additional storage
- **External interfaces**: 2× USB 3.0, 1× USB-C

**Communication Infrastructure**:
- **WiFi**: WiFi 6 dual-band with enterprise WPA3
- **Cellular**: 4G/5G with dual SIM support
- **Bandwidth usage**: 10-25 Mbps for HD streaming
- **Latency**: 180ms typical for video transmission
- **VPN support**: Site-to-site and client configurations
- **Teleoperation range**: Global via internet

**SDK Access** (Limited):
- **Languages**: Python 3.8+ primary
- **APIs**: High-level control only
- **ROS support**: ROS2 Humble basic integration
- **Update frequency**: 100Hz control loop
- **Custom behaviors**: Waypoint navigation, basic automation
- **Restrictions**: Low-level motor control blocked

**Teleoperation Features**:
- VR headset compatibility (Quest 3, Vision Pro)
- Dual-operator support
- Automatic obstacle avoidance override
- Emergency takeover capability
- Session recording and playback
- Bandwidth adaptation for poor connections

**Enterprise Support**:
- 24-month warranty standard
- Remote diagnostics capability
- Fleet management dashboard
- Usage analytics and reporting
- Priority technical support
- Spare parts availability guaranteed 5 years

### Go2 EDU - Educational Platform ($4,500)

The EDU model provides full SDK access for research and educational institutions, incorporating an NVIDIA Jetson module for edge AI development while using lower-cost components than EDU Plus.

**Physical Specifications**:
- **Weight**: 15kg including compute module
- **Mechanical design**: Identical to ENT chassis
- **Serviceability**: User-replaceable leg modules
- **Maximum velocity**: 5 m/s
- **Dynamic balance**: Active stabilization at 1000Hz
- **Fall protection**: Automatic power cutoff on impact

**Power Configuration**:
- **Battery**: 8,000mAh standard only
- **Runtime**: 2 hours continuous operation
- **Compute power draw**: Additional 30W for Jetson
- **Thermal design**: Active cooling for compute module
- **Temperature monitoring**: Per-component thermal sensors
- **Charging**: Standard 3.5A charger only

**Environmental Limits**:
- **Operating temperature**: 0°C to 40°C
- **IP rating**: Not specified (assumed indoor use)
- **Humidity limits**: 20-80% non-condensing
- **Altitude**: Tested to 2000m
- **Dust exposure**: No protection rating
- **Water exposure**: Must avoid all moisture

**Educational Sensor Suite**:
- **LiDAR**: 4D L1 with raw point cloud access
- **Camera**: Single 1080p with raw frame access
- **IMU data**: Full 9-axis at 200Hz
- **Joint state**: Position, velocity, torque at 1000Hz
- **Foot pressure**: Analog readings at 100Hz
- **Power monitoring**: Voltage, current per motor

**NVIDIA Jetson Integration**:
- **Model**: Jetson Orin Nano
- **AI performance**: 40 TOPS INT8
- **GPU**: 1024-core NVIDIA Ampere
- **CPU**: 6-core ARM Cortex-A78AE
- **Memory**: 8GB unified LPDDR5
- **Storage**: 128GB NVMe SSD

**Development Environment**:
- **Operating system**: Ubuntu 20.04 LTS
- **ROS version**: ROS2 Humble full support
- **Python**: 3.8+ with NumPy, OpenCV
- **C++**: Full low-level control access
- **CUDA**: Version 11.4 for GPU acceleration
- **TensorRT**: Optimized inference engine

**SDK Capabilities**:
- Direct motor torque control
- Custom gait generation
- Real-time sensor fusion
- SLAM implementation
- Computer vision pipelines
- Reinforcement learning training

**Educational Resources**:
- 50+ example programs
- Gazebo simulation environment
- Online course materials
- Academic paper references
- Student project gallery
- Community forum access

**Research Applications**:
- Gait optimization algorithms
- Terrain classification
- Multi-robot coordination
- Human-robot interaction
- Navigation algorithm development
- Machine learning deployment

### Go2 EDU Plus - Advanced Research ($16,000-$22,500)

The EDU Plus represents the apex of the Go2 series, uniquely featuring autonomous self-charging capability, 100 TOPS computing power, and advanced LiDAR options. Pricing depends on selected LiDAR configuration.

**Physical Enhancements**:
- **Weight**: 15kg base, 17kg with Hesai XT16
- **Structural reinforcement**: Carbon fiber components
- **Vibration damping**: Advanced suspension system
- **Heat dissipation**: Vapor chamber cooling
- **Connector rating**: IP67 sealed connectors
- **Maintenance access**: Tool-free battery and compute module

**Extended Power System**:
- **Battery**: 15,000mAh extended standard
- **Runtime**: 3-4 hours typical research tasks
- **Standby time**: 48 hours in sleep mode
- **Charging cycles**: 1000+ cycles to 80% capacity
- **Battery telemetry**: Cell-level monitoring
- **Power delivery**: Supports 100W external devices

**Environmental Capabilities**:
- **Operating temperature**: -10°C to 45°C verified
- **IP rating**: IP54 (same as ENT)
- **Shock rating**: 50G peak survivable
- **Continuous vibration**: 2G RMS
- **Salt fog**: 96 hours exposure tested
- **Thermal cycling**: -20°C to 60°C, 100 cycles

**Autonomous Charging System**:
- **Self-docking**: Fully autonomous navigation to station
- **Docking accuracy**: ±10mm positioning precision
- **Vision system**: ArUco marker detection
- **LiDAR requirement**: Must have Mid-360 or Hesai XT16
- **Charging threshold**: Configurable 10-30% trigger
- **Docking speed**: 0.2 m/s approach velocity
- **Retry logic**: 5 attempts before alert
- **Station cost**: $3,900 for 100 TOPS variant

**LiDAR Options**:
1. **Hesai XT16** ($20,000-22,500 total):
   - 16 laser channels
   - 120m maximum range
   - ±1cm accuracy
   - 320,000 points/second
   - 360°×30° coverage

2. **Mid-360** ($18,000-20,000 total):
   - 360°×59° field of view
   - 70m range
   - 200,000 points/second
   - Lower cost alternative
   - Sufficient for indoor use

**Advanced Computing**:
- **Processor**: NVIDIA Jetson Orin NX
- **AI performance**: 100 TOPS INT8
- **GPU**: 1024 CUDA cores, 32 Tensor cores
- **CPU**: 8-core ARM Cortex-A78AE
- **Memory**: 16GB LPDDR5 (256GB/s bandwidth)
- **Storage**: 256GB NVMe Gen 4

**Sensor Array**:
- **Cameras**: Triple array (front, side, belly)
- **Resolution**: 1080p60 all cameras
- **Depth camera**: Intel RealSense D435 option
- **Microphone array**: 4× MEMS for localization
- **GPS**: RTK-capable with 1cm accuracy
- **Environmental**: CO2, VOC, particulate sensors

**Research Computing Features**:
- Docker container support
- Kubernetes orchestration
- Multi-robot coordination protocols
- Edge training capabilities
- Model optimization tools
- Real-time OS option

**SDK2 Enhancements**:
- Azure IoT Hub native integration
- AWS RoboMaker compatibility
- Digital twin support
- Over-the-air updates
- Secure boot and attestation
- Hardware security module

**Academic Package Includes**:
- 3-year warranty
- Simulation licenses (5 seats)
- Cloud compute credits ($5,000)
- Technical support (40 hours)
- Spare parts kit
- Training workshop (2 days)

---

## A-Series - Industrial Innovation ($50,000-$70,000)

The A-Series occupies the mid-tier industrial segment, designed for applications requiring greater capability than educational models but not the extreme durability of B-Series platforms.

### A1 - Legacy Industrial (Price on Request)

The A1, launched in 2018, was Unitree's first industrial-grade platform. Production ceased in 2023, though units remain available through special order with extended lead times.

**Historical Specifications**:
- **Weight**: 12kg
- **Dimensions**: 500mm × 300mm × 400mm
- **Maximum speed**: 3.3 m/s (11.88 km/h)
- **Battery**: 24V system, various capacities
- **Runtime**: 1-2.5 hours depending on configuration
- **Payload**: 5kg nominal rating

**Technical Limitations**:
- **Sensor technology**: 2018-era LiDAR and cameras
- **Computing**: NVIDIA TX2 (previous generation)
- **Software**: ROS1 only (ROS2 not supported)
- **SDK**: Version 1.x (incompatible with current)
- **Parts availability**: Limited to existing stock
- **Support**: Community-based only

**Environmental Ratings**:
- **Temperature range**: -20°C to 50°C claimed
- **IP rating**: IP43 (limited dust and spray protection)
- **Testing standards**: Older certification versions
- **Reliability data**: MTBF approximately 500 hours
- **Maintenance**: Requires specialized knowledge
- **Documentation**: Primarily in Chinese

**Market Position**:
- Original price: $40,000-60,000
- Current availability: 6-12 month lead time
- Replacement parts: 30% price premium
- Technical support: Email only
- Warranty: 6 months maximum
- End-of-life: December 2025 announced

### A2 - Next Generation (August 2025 Release)

The A2 "Stellar Explorer" represents Unitree's complete redesign of the mid-tier industrial segment, incorporating lessons learned from both Go2 and B-Series deployments. Pre-orders opened January 2025.

**Physical Architecture**:
- **Weight**: 37kg optimized design
- **Materials**: Carbon composite and titanium alloy
- **Leg design**: New 4-bar linkage mechanism
- **Joint count**: 12 DOF with redundant encoders
- **Ground clearance**: 150mm nominal
- **Footpad**: Adaptive rubber with tungsten studs

**Revolutionary Power System**:
- **Battery configuration**: Dual 9,000mAh hot-swappable
- **Total capacity**: 18,000mAh (518Wh) combined
- **Hot-swap mechanism**: Sub-second switchover
- **Runtime unloaded**: 5 hours continuous walking
- **Runtime with 25kg**: 3 hours operational
- **Range**: 20km unloaded, 12.5km with payload
- **Charging**: Parallel charging both batteries

**Performance Metrics**:
- **Standard speed**: 2.5 m/s walking
- **Maximum speed**: 4 m/s sprint mode
- **Acceleration**: 2 m/s² maximum
- **Payload continuous**: 25kg certified
- **Payload standing**: 100kg static load
- **Towing capacity**: 200kg on wheels

**Environmental Hardening**:
- **Operating temperature**: -20°C to 55°C
- **Storage temperature**: -40°C to 70°C
- **IP rating**: IP67 (dust tight, 1m immersion)
- **Impact rating**: IK10 (20 joules impact)
- **Chemical resistance**: MIL-STD-810H
- **Salt spray**: 1000 hours tested

**Terrain Capabilities**:
- **Maximum step**: 30cm vertical
- **Maximum gap**: 40cm horizontal
- **Slope climbing**: 45° sustained
- **Side slope**: 30° traversable
- **Mud depth**: 20cm wading
- **Snow depth**: 50cm powder

**Dual LiDAR System**:
- **Front LiDAR**: Ultra-wide 3D industrial
- **Rear LiDAR**: Matching specifications
- **Combined coverage**: True 360° no blind spots
- **Range**: 150m maximum
- **Accuracy**: ±2cm at 50m
- **Point rate**: 600,000 points/second total

**Computing Platform**:
- **Primary processor**: Unspecified next-gen ARM
- **AI acceleration**: Dual NVIDIA Jetson modules
- **Combined AI**: 200+ TOPS estimated
- **RAM**: 32GB LPDDR5X
- **Storage**: 512GB NVMe Gen 5
- **5G modem**: Integrated with global bands

**Wheel-Leg Variant (A2-W)**:
- **Additional cost**: $10,000 premium
- **Wheel type**: Omnidirectional mecanum
- **Wheeled speed**: 25 km/h maximum
- **Wheeled range**: 50km on smooth surface
- **Mode switching**: Automatic terrain detection
- **Wheel motor**: 500W brushless per wheel

**Software Innovations**:
- Large language model integration
- Voice command processing
- Gesture recognition
- Autonomous task planning
- Predictive maintenance
- Cloud-based learning

**Pre-order Information**:
- **Standard A2**: $50,000-60,000
- **A2-W wheeled**: $60,000-70,000
- **Deposit required**: $10,000
- **Delivery date**: August 2025
- **Production capacity**: 100 units/month
- **Priority delivery**: Based on deposit date

---

## B-Series - Heavy Industrial ($50,000-$150,000)

The B-Series represents Unitree's industrial flagship line, engineered specifically for continuous operation in mining, construction, power generation, and similar demanding environments.

### B1 - Original Industrial ($80,000-$100,000)

The B1 established Unitree's credibility in industrial robotics with exceptional durability specifications, though it has been largely superseded by the enhanced B2 model.

**Structural Design**:
- **Weight**: 50kg base configuration
- **Frame material**: Military-grade aluminum
- **Dimensions**: 1096mm × 460mm × 600mm
- **Leg reach**: 500mm maximum extension
- **Center of gravity**: Dynamically adjustable
- **Protection rating**: Fully sealed design

**Power Specifications**:
- **Battery capacity**: 38.4Ah lithium-ion
- **Voltage**: 58.8V nominal
- **Energy**: 2,258Wh total
- **Runtime**: 2-4 hours depending on load
- **Charging time**: 3 hours standard
- **Cycle life**: 2000 cycles to 70%

**Performance Data**:
- **Maximum speed**: 4.5 m/s
- **Payload walking**: 20kg continuous
- **Payload standing**: 80kg static
- **Step height**: 30cm capability
- **Slope angle**: 35° maximum
- **Lateral stability**: 25° side slope

**Environmental Excellence**:
- **IP rating**: IP68 (submersible to 1m)
- **Operating range**: -20°C to 55°C
- **Shock survival**: 100G peak
- **Vibration**: 10G RMS continuous
- **MTBF**: 2000 hours
- **Service interval**: 500 hours

**Industrial Features**:
- Explosion-proof variant available (ATEX Zone 2)
- Nuclear radiation resistant option
- High-temperature variant (up to 75°C)
- Stainless steel option for corrosive environments
- Redundant control systems
- Emergency wireless stop (100m range)

**Current Status**:
- Production: Limited runs only
- Lead time: 3-6 months
- Support: Transitioning to B2
- Parts commonality: 60% with B2
- Upgrade path: B2 conversion kit available
- Phase-out: Planned for Q4 2025

### B2 - Current Flagship ($78,700-$100,000)

The B2 represents the current pinnacle of Unitree's industrial capabilities, incorporating feedback from thousands of B1 deployments worldwide with enhanced specifications across all parameters.

**Mechanical Engineering**:
- **Weight**: 60kg operational
- **Dimensions**: 1120mm × 460mm × 650mm
- **Material**: Aerospace aluminum with titanium joints
- **Joint torque**: 360 N⋅m maximum
- **Leg workspace**: 600mm spherical
- **Dynamic range**: -45° to +45° body pitch/roll

**Power Infrastructure**:
- **Battery**: 45Ah (2,250Wh) lithium-ion
- **Voltage**: 50V nominal system
- **Peak power**: 3,000W instantaneous
- **Runtime unloaded**: 5+ hours verified
- **Runtime 20kg load**: 4+ hours verified
- **Runtime 40kg load**: 2.5 hours typical
- **Standby duration**: 72 hours

**Performance Envelope**:
- **Top speed**: 6 m/s (industry's fastest)
- **Acceleration**: 0 to 6 m/s in 4 seconds
- **Deceleration**: 6 to 0 m/s in 2 seconds
- **Payload continuous**: 40kg certified
- **Payload peak**: 60kg for 10 minutes
- **Payload standing**: 120kg static indefinite

**Terrain Mastery**:
- **Step height**: 40cm (industry leading)
- **Gap crossing**: 50cm horizontal
- **Slope sustained**: 40° verified
- **Slope momentary**: 50° for 30 seconds
- **Terrain types**: Sand, mud, snow, rubble
- **Stability recovery**: Self-rights in 3 seconds

**Environmental Certification**:
- **IP rating**: IP67 verified
- **Temperature operational**: -20°C to 55°C
- **Temperature survival**: -40°C to 70°C
- **Temperature verified**: -40°C in Chinese grid deployment
- **Altitude operational**: 5000m tested
- **Wind resistance**: 20 m/s sustained

**Computing Architecture**:
- **Primary CPU**: Intel Core i5-1135G7 or i7-1165G7
- **CPU cores**: 4 cores, 8 threads
- **CPU frequency**: 4.2GHz turbo
- **AI modules**: Up to 3× NVIDIA Jetson Orin NX
- **Total AI performance**: 300+ TOPS possible
- **System RAM**: 32GB DDR4 expandable to 64GB
- **Storage**: 1TB NVMe standard, 4TB maximum

**Sensor Integration**:
- **LiDAR**: Industrial grade 360° coverage
- **Cameras**: 6× 1080p standard positions
- **Thermal**: Optional FLIR A65 integration
- **Gas detection**: Multi-gas sensor array option
- **Radiation**: Gamma detector option
- **Acoustic**: Ultrasonic array for glass detection

**Communication Systems**:
- **Ethernet**: 4× Gigabit ports
- **WiFi**: WiFi 6E tri-band (2.4/5/6 GHz)
- **Cellular**: 5G NSA/SA with dual SIM
- **Satellite**: Iridium modem option
- **Mesh networking**: 900MHz ISM band
- **Latency**: Sub-50ms local control

**Industrial Interfaces**:
- **USB**: 4× USB 3.0 Type-A
- **Power output**: 12V/10A, 24V/5A, 48V/2A
- **Serial**: RS485, RS232
- **Industrial**: CAN bus, Modbus
- **Safety**: Hardware E-stop circuit
- **Payload**: Universal mounting plate

**Optional Equipment**:
- Autonomous charging station: $8,000-12,000
- Thermal camera package: $5,000
- Gas detection suite: $8,000
- Radiation monitoring: $12,000
- Manipulator arm: $25,000
- Wireless E-stop system: $1,500

**Deployment Statistics**:
- Units in field: 5,000+ globally
- Industries: Mining, power, construction, security
- Largest deployment: 200 units (Chinese power grid)
- Reliability: 99.2% uptime average
- ROI reported: 12-18 months typical
- Customer retention: 94%

### B2-W - Wheeled Variant ($100,000-$150,000)

The B2-W adds powered wheels to each foot, enabling high-speed travel on prepared surfaces while maintaining full walking capability for rough terrain.

**Hybrid Locomotion System**:
- **Weight**: 65kg with wheel assemblies
- **Wheel type**: Active omnidirectional
- **Wheel diameter**: 150mm
- **Wheel motor**: 250W brushless per wheel
- **Total wheel power**: 1000W combined
- **Suspension travel**: 50mm active

**Wheeled Performance**:
- **Maximum speed**: 20 km/h wheeled mode
- **Cruise speed**: 15 km/h efficient
- **Acceleration**: 0 to 20 km/h in 5 seconds
- **Braking**: Regenerative with ABS
- **Turning radius**: 2m at speed
- **Slope capability**: 20° in wheel mode

**Extended Operations**:
- **Battery**: Dual 45Ah packs (4,500Wh total)
- **Runtime wheeled**: 8-10 hours
- **Runtime walking**: Same as standard B2
- **Range wheeled**: 50km verified
- **Range walking**: 15km typical
- **Charging**: Dual simultaneous charging

**Mode Transitions**:
- **Switching time**: 2 seconds wheel to walk
- **Automatic detection**: Terrain-based switching
- **Manual override**: Operator selectable
- **Hybrid mode**: Wheels assist walking
- **Stair climbing**: Walks with wheels retracted
- **Recovery**: Can self-right in either mode

**Wheel Specifications**:
- **Material**: Polyurethane with steel core
- **Tread pattern**: All-terrain design
- **Load per wheel**: 30kg maximum
- **Speed per wheel**: Independent control
- **Encoders**: 16-bit magnetic
- **Maintenance**: 5000km service interval

**Use Case Optimization**:
- Pipeline inspection: 50km daily coverage
- Perimeter security: 24-hour continuous patrol
- Solar farm inspection: 100+ acres daily
- Airport runway inspection: 30-minute full scan
- Mining haul road monitoring: 3 shifts unattended
- Construction site: Multiple zone coverage

**Additional Costs**:
- Base B2-W: $100,000
- Extended battery: $15,000
- Wheel service kit: $2,000
- Training program: $5,000
- Extended warranty: $8,000/year
- Total typical: $130,000-150,000

---

## Legacy Models

### Go1 Series ($2,700-$8,500)

The Go1 series, launched in June 2021 as Unitree's breakthrough into affordable quadrupeds, established the $2,700 price point that disrupted the industry. Production ended December 2023.

**Go1 Air** ($2,700)
- **Weight**: 12kg
- **Battery**: 6,000mAh providing 1 hour operation
- **Speed**: 2.5 m/s maximum
- **Sensors**: Basic IMU and cameras only
- **Computing**: Minimal embedded processor
- **IP rating**: None
- **SDK**: Not available
- **Current status**: Discontinued, no support

**Go1 Pro** ($4,000)
- **Weight**: 12kg
- **Battery**: 6,000mAh standard
- **Speed**: 3.5 m/s maximum
- **Sensors**: Added ultrasonic array
- **Computing**: Upgraded processor, 4GB RAM
- **IP rating**: None
- **SDK**: Limited Python bindings
- **Current status**: Limited stock remaining

**Go1 Edu** ($6,500)
- **Weight**: 12kg
- **Battery**: 6,000mAh with optional 9,000mAh
- **Computing**: NVIDIA Jetson Xavier NX (21 TOPS)
- **Sensors**: Added Intel RealSense depth camera
- **SDK**: Full ROS1 support (ROS2 unofficial)
- **Development**: Complete access to controls
- **Current status**: Superseded by Go2 EDU

**Go1 Max** ($8,500)
- **Weight**: 12kg
- **Battery**: 9,000mAh extended
- **Computing**: Xavier NX with 8GB RAM
- **Sensors**: Dual RealSense cameras
- **Special features**: Prototype self-charging (unreliable)
- **SDK**: Enhanced development tools
- **Current status**: Rare, limited parts availability

**Common Go1 Limitations**:
- No weatherproofing across entire series
- Battery life 50% of Go2 equivalents
- Obsolete SDK (version 3.x discontinued)
- No Azure IoT native support
- ROS1 only (ROS2 community ports unstable)
- Parts availability declining rapidly
- Forum support only, no official channels
- Known issues with motor controllers
- Firmware updates ended June 2024

### AlienGo ($50,000)

The AlienGo represents Unitree's experimental research platform, featuring unique mechanical design and specialized capabilities not found in production models.

**Unique Specifications**:
- **Design philosophy**: Bio-inspired alien aesthetics
- **Leg configuration**: Non-standard kinematic chain
- **Joint count**: 16 DOF (4 per leg)
- **Materials**: Exotic composites and alloys
- **Weight**: 25kg base platform
- **Dimensions**: Custom per order

**Research Features**:
- Experimental gait patterns
- Novel sensor configurations
- Prototype actuators
- Advanced materials testing
- Extreme environment variants
- Modular leg designs

**Availability**:
- Build to order only
- 6-12 month lead time
- Requires NDA for specifications
- Minimum order: 2 units
- Research institutions only
- Price negotiable based on configuration

---

## Accessories and Add-Ons

### Battery Systems

**Go2 Series Batteries**:

**Standard 8,000mAh** ($600-800)
- Chemistry: Lithium-ion NMC
- Voltage: 28.8V nominal
- Energy: 230Wh
- Weight: 1.8kg
- Charge cycles: 800 to 80% capacity
- Charge time: 2.3 hours standard
- Compatibility: All Go2 models

**Extended 15,000mAh** ($1,980)
- Chemistry: Lithium-ion NMC
- Voltage: 28.8V nominal  
- Energy: 432Wh
- Weight: 3.2kg
- Charge cycles: 1000 to 80% capacity
- Charge time: 3.5 hours standard
- Compatibility: Go2 Pro and above

**Industrial Batteries**:

**B2 45Ah Pack** ($8,000-10,000)
- Chemistry: LiFePO4 (safety optimized)
- Voltage: 50V nominal
- Energy: 2,250Wh
- Weight: 15kg
- Charge cycles: 3000 to 80% capacity
- Charge time: 4 hours standard
- Temperature range: -30°C to 60°C

**A2 9,000mAh Module** ($1,500 estimated)
- Chemistry: Next-generation Li-ion
- Voltage: 58.8V nominal
- Energy: 259Wh per module
- Weight: 2.5kg per module
- Hot-swap capability: Yes
- Charge time: 1.5 hours
- Available: August 2025

**Charging Equipment**:

**Standard Charger** ($200)
- Output: 33.6V @ 3.5A
- Power: 117W
- Efficiency: 92%
- Cooling: Passive
- Protection: Over-voltage, over-current
- Cable length: 2m

**Fast Charger** ($500)
- Output: 33.6V @ 9A
- Power: 302W
- Efficiency: 94%
- Cooling: Active fan
- Protection: Full suite with display
- Cable length: 3m

**Industrial Charger** ($1,500)
- Output: Multiple voltage support
- Power: 1000W maximum
- Efficiency: 96%
- Cooling: Temperature controlled
- Features: Remote monitoring, scheduling
- Compatibility: B-series and A-series

### LiDAR Technology

**Unitree 4D LiDAR L1** ($249)
- Technology: Solid-state design
- Coverage: 360°×90° hemispherical
- Range: 0.05m to 30m
- Accuracy: ±2cm at 10m
- Point rate: 21,600 points/second
- Wavelength: 905nm
- Power consumption: 8W
- Interface: Ethernet
- Standard on all Go2 models

**Unitree 4D LiDAR L2** ($419)
- Technology: Enhanced solid-state
- Coverage: 360°×90° hemispherical
- Range: 0.05m to 50m
- Accuracy: ±1.5cm at 10m
- Point rate: 43,200 points/second
- Wavelength: 905nm
- Power consumption: 10W
- Improvements: Better in sunlight, rain

**Hesai XT16** ($3,000-5,000)
- Technology: Mechanical spinning
- Channels: 16 laser beams
- Coverage: 360°×30° vertical
- Range: 0.5m to 120m
- Accuracy: ±1cm
- Point rate: 320,000 points/second
- Rotation rate: 10-20Hz adjustable
- Required for EDU Plus self-charging

**Livox Mid-360** ($2,500-3,500)
- Technology: Non-repetitive scanning
- Coverage: 360°×59° vertical
- Range: 0.1m to 70m
- Accuracy: ±2cm
- Point rate: 200,000 points/second
- Special feature: No blind spots
- Power: 12W typical
- Alternative for EDU Plus charging

### Charging Infrastructure

**Go2 Self-Charging Station (40 TOPS)** ($2,500-3,000)
- Dimensions: 800mm × 600mm × 150mm
- Weight: 25kg
- Charging power: 300W
- Docking accuracy: ±10mm required
- Computing: 40 TOPS edge processor
- Connectivity: WiFi 6, Ethernet
- Compatible models: EDU Plus only
- Installation: Indoor/covered only

**Go2 Self-Charging Station (100 TOPS)** ($3,900-4,500)
- Dimensions: 800mm × 600mm × 200mm
- Weight: 30kg
- Charging power: 300W rapid charge
- Computing: NVIDIA Orin NX (100 TOPS)
- Storage: 256GB SSD
- Features: Local data processing
- Network: 5G modem option
- Use cases: Edge AI processing hub

**B2 Industrial Charging Solution** ($8,000-12,000)
- Dimensions: 1200mm × 800mm × 400mm
- Weight: 50kg
- Charging power: 1000W
- Weather rating: IP65 enclosure
- Features: Hot-swap battery support
- Connectivity: Industrial Ethernet
- Power input: 3-phase 480V
- Options: Solar integration available

**Charging Station Requirements**:
- Power supply: Dedicated 20A circuit minimum
- Network: Gigabit Ethernet recommended
- Environment: Level surface, protected
- Clearance: 2m approach path
- Lighting: IR illuminators for night docking
- Backup power: UPS recommended
- Maintenance: Monthly contact cleaning

### Teleoperation Equipment

**VR Control Systems**:

**Meta Quest 3 Package** ($2,500)
- Headset: Quest 3 512GB
- Controllers: Hand tracking + controllers
- Software: Unitree teleoperation app
- Latency: 50ms typical
- Range: Unlimited via internet
- Battery life: 2 hours continuous

**Apple Vision Pro Setup** ($5,000)
- Headset: Vision Pro base model
- Software: Specialized visionOS app
- Features: Spatial computing interface
- Latency: 30ms achievable
- Quality: 4K per eye
- Battery: External pack included

**Azure Kinect Bundle** ($600)
- Sensor: Azure Kinect DK
- Mount: Adjustable stand
- Software: Body tracking SDK
- Tracking: Full skeleton capture
- Range: 0.5m to 4.5m
- Accuracy: ±10mm joints
- Use case: Natural movement control

**Control Station Hardware**:

**Basic Console** ($5,000)
- Display: 27" 4K monitor
- Controls: Joystick and keyboard
- Computer: Intel i5, 16GB RAM
- Network: Gigabit Ethernet
- Software: Basic teleoperation
- Support: Single robot

**Professional Setup** ($15,000)
- Displays: Triple 32" 4K monitors
- Controls: Industrial joysticks
- Computer: Intel i9, 64GB RAM, RTX 4080
- Network: Redundant connections
- Software: Fleet management suite
- Support: Up to 10 robots

**Emergency Systems** ($1,500)
- Wireless E-stop: 100m range
- Redundant E-stop: Wired backup
- Status lights: Tower beacon
- Audio alarm: 95dB siren
- Integration: Direct to robot
- Certification: SIL 2 rated

---

## Azure Integration Architecture

### Universal MQTT Support

All Unitree models implement MQTT protocol for Azure IoT Hub connectivity:

**Protocol Specifications**:
- Version: MQTT 3.1.1
- Port: 8883 (TLS required)
- Alternative: 443 (WebSocket over HTTPS)
- QoS levels: 0, 1 supported
- Keep-alive: 60 seconds default
- Max message size: 256KB

**Authentication Methods**:
- Shared Access Signatures (SAS)
- X.509 certificates
- Azure AD integration (enterprise models)
- Device provisioning service
- Connection string format standard
- Token refresh: Automatic

**Telemetry Patterns**:
- Device-to-cloud: 1Hz to 100Hz configurable
- Cloud-to-device: Command and control
- Device twin: State synchronization
- Direct methods: Real-time invocation
- File upload: Sensor data batches
- Edge routing: Via IoT Edge

### Azure Stack Edge Options

**Stack Edge Pro - GPU** ($3,000/month HaaS)
- Processor: Intel Xeon 16-core
- GPU: NVIDIA T4 16GB
- RAM: 128GB ECC
- Storage: 4.8TB NVMe
- Network: 4× 10GbE
- Form factor: 1U rackmount
- Use case: ML inference at edge

**Stack Edge Pro 2** ($1,500/month HaaS)
- Processor: Intel Xeon D 16-core
- GPU: Optional NVIDIA A2
- RAM: 256GB maximum
- Storage: 8TB NVMe
- Network: 4× 10/25GbE
- Form factor: Half-width 2U
- Use case: Space-constrained sites

**Stack Edge Pro R** ($4,000/month HaaS)
- Processor: Intel Xeon 16-core
- GPU: NVIDIA T4 option
- RAM: 256GB ECC
- Storage: 8TB SSD
- Network: 4× 10GbE + WiFi
- Form factor: Ruggedized portable
- Use case: Construction sites

**Hardware Requirements**:
- Minimum order: 100 devices (HaaS)
- Power: 100-240V AC, 750W typical
- Cooling: Front-to-back airflow
- Environment: 10°C to 35°C operating
- Redundancy: Dual PSU option
- Management: Azure portal
- Support: 24/7 with HaaS

### Model-Specific Capabilities

**Go2 Consumer Models** (Air/Pro):
- Telemetry only: Location, battery, status
- Update rate: 1Hz maximum
- Commands: Basic movement only
- Storage: None at edge
- Analytics: Cloud only
- ML models: Not supported

**Go2 Enterprise** (ENT):
- Telemetry: Full sensor suite
- Update rate: 10Hz typical
- Commands: Waypoint navigation
- Edge processing: Basic filters
- Analytics: Anomaly detection
- ML models: Pre-trained only

**Go2 Educational** (EDU Plus):
- Telemetry: Raw sensor access
- Update rate: 100Hz possible
- Commands: Full control API
- Edge processing: Custom models
- Analytics: Real-time SLAM
- ML models: Custom training

**Industrial Models** (B2/A2):
- Telemetry: Multi-modal fusion
- Update rate: 1000Hz internal
- Commands: Complex behaviors
- Edge processing: Distributed
- Analytics: Predictive maintenance
- ML models: Continuous learning

### Network Architecture

**Bandwidth Requirements**:

Per-robot bandwidth consumption:
- Control only: 100 Kbps
- Telemetry: 1 Mbps
- SD video: 2 Mbps
- HD video: 8 Mbps
- 4K video: 25 Mbps
- Point cloud: 10 Mbps

**Latency Specifications**:

Maximum acceptable delays:
- Emergency stop: 10ms
- Direct control: 50ms
- Teleoperation: 100ms
- Waypoint nav: 500ms
- Analytics: 5 seconds
- Updates: No limit

**Redundancy Levels**:

**Consumer**: Single path WiFi
**Enterprise**: WiFi + 4G failover
**Educational**: Multi-path with selection
**Industrial**: Triple redundancy standard
- Primary: WiFi 6/6E
- Secondary: 5G cellular
- Tertiary: Satellite or mesh

---

## Deployment Specifications by Site Size

### 1-3 Acre Deployment

**Single Robot Configuration**:
- Coverage pattern: Perimeter plus grid
- Patrol cycle: 45-60 minutes
- Charging breaks: 15 minutes per 2 hours
- Daily coverage: 20-30 cycles
- Battery changes: 4-6 daily (Go2)
- Network: Single access point sufficient

**Infrastructure Requirements**:
- Power: 20A dedicated circuit
- Network: 100 Mbps backbone
- Charging: Central location
- Storage: Weather shelter
- Compute: Single Stack Edge
- Monitoring: Basic dashboard

### 3-7 Acre Deployment

**Dual Robot Configuration**:
- Coverage zones: Split with 10% overlap
- Coordination: Time-based handoff
- Patrol cycle: 60-90 minutes per zone
- Charging strategy: Alternating schedule
- Daily runtime: 20 hours total
- Network: 3-4 access points

**Infrastructure Scaling**:
- Power: Two 20A circuits
- Network: 250 Mbps backbone
- Charging: Opposite corners
- Storage: Distributed shelters
- Compute: Stack Edge Pro
- Monitoring: Multi-robot dashboard

### 7-10 Acre Deployment

**Fleet Configuration**:
- Robot count: 3-4 units optimal
- Coverage: Zone-based assignment
- Coordination: Central scheduling
- Patrol overlap: 15% minimum
- Charging: Distributed stations
- Network: Mesh topology

**Enterprise Infrastructure**:
- Power: 480V 3-phase service
- Network: 1 Gbps fiber backbone
- Access points: 8-10 units
- Charging: 4 stations minimum
- Compute: Multiple Stack Edge units
- Monitoring: Operations center

---

## Financial Analysis by Model

### Total Cost of Ownership (3 Years)

**Go2 Pro** ($2,800 base)
- Robot: $2,800
- Batteries (3): $1,800
- Chargers (2): $700
- Maintenance: $500/year × 3
- Downtime: 20% operational loss
- Total: $6,800
- Per operational hour: $8.75

**Go2 ENT** ($14,500 base)
- Robot: $14,500
- Batteries (4): $3,200
- Chargers (2): $1,000
- Warranty: Included 24 months
- Maintenance: $1,000/year × 3
- Downtime: 10% operational loss
- Total: $21,700
- Per operational hour: $11.20

**Go2 EDU Plus** ($22,500 base)
- Robot: $22,500
- Charging station: $3,900
- LiDAR upgrade: Included
- Support: $2,000/year × 3
- Maintenance: $800/year × 3
- Downtime: 5% (self-charging)
- Total: $34,800
- Per operational hour: $8.95

**B2 Industrial** ($100,000 base)
- Robot: $100,000
- Spare battery: $10,000
- Charging solution: $10,000
- Service contract: $5,000/year × 3
- Spare parts: $3,000/year × 3
- Downtime: 2% (redundant systems)
- Total: $144,000
- Per operational hour: $9.25

### Return on Investment Factors

**Labor Replacement**:
- Security guard: $15-25/hour
- Robot operation: $9-12/hour equivalent
- Coverage: 24/7 vs 8-hour shifts
- Reliability: 95-99% uptime
- Multiply factor: 1 robot = 3.5 guards

**Incident Prevention**:
- Theft reduction: 60-80% reported
- Safety violations: 50% decrease
- Insurance savings: 10-15% typical
- Liability reduction: Quantifiable
- Documentation: 100% coverage

**Operational Efficiency**:
- Response time: 3 minutes average
- Coverage area: 10× human walking
- Data collection: Continuous
- Weather independence: Model dependent
- Integration: Existing systems

---

## Technical Comparison Matrix

### Environmental Specifications

| Model | IP Rating | Operating Temp | Humidity | Altitude | Wind |
|-------|-----------|----------------|----------|----------|------|
| Go2 Air | None | Not specified | Unknown | Unknown | N/A |
| Go2 Pro | IPX4 | 0°C to 40°C | 20-80% | 2000m | 10 m/s |
| Go2 ENT | IP54 | -10°C to 45°C | 20-95% | 3000m | 15 m/s |
| Go2 EDU | None | 0°C to 40°C | 20-80% | 2000m | 10 m/s |
| Go2 EDU Plus | IP54 | -10°C to 45°C | 20-95% | 3000m | 15 m/s |
| A2 | IP67 | -20°C to 55°C | 5-95% | 5000m | 20 m/s |
| B1 | IP68 | -20°C to 55°C | 5-100% | 5000m | 25 m/s |
| B2 | IP67 | -20°C to 55°C | 5-95% | 5000m | 20 m/s |
| B2-W | IP67 | -20°C to 55°C | 5-95% | 5000m | 20 m/s |

### Performance Metrics

| Model | Speed | Payload | Step Height | Runtime | Range |
|-------|-------|---------|-------------|---------|-------|
| Go2 Air | 2.5 m/s | 1kg | 15cm | 1-2h | 3km |
| Go2 Pro | 3.5 m/s | 3kg | 16cm | 2-4h | 5km |
| Go2 ENT | 5 m/s | 5kg | 18cm | 2-3h | 7km |
| Go2 EDU | 5 m/s | 5kg | 16cm | 2h | 6km |
| Go2 EDU Plus | 5 m/s | 8kg | 18cm | 3-4h | 10km |
| A2 | 2.5 m/s | 25kg | 30cm | 3-5h | 12-20km |
| B1 | 4.5 m/s | 20kg | 30cm | 2-4h | 10km |
| B2 | 6 m/s | 40kg | 40cm | 4-5h | 15km |
| B2-W | 20 km/h | 30kg | 40cm | 8-10h | 50km |

### Computing Resources

| Model | Processor | AI Performance | RAM | Storage | SDK Access |
|-------|-----------|----------------|-----|---------|------------|
| Go2 Air | ARM Basic | None | 2-4GB | 16GB | None |
| Go2 Pro | 8-core ARM | 2 TOPS | 8GB | 64GB | None |
| Go2 ENT | Intel i5 opt | Limited | 8-16GB | 128GB | Limited |
| Go2 EDU | Jetson Orin Nano | 40 TOPS | 8GB | 128GB | Full |
| Go2 EDU Plus | Jetson Orin NX | 100 TOPS | 16GB | 256GB | Full |
| A2 | Dual Jetson | 200+ TOPS | 32GB | 512GB | Full |
| B1 | Intel i5 | Variable | 16GB | 512GB | Full |
| B2 | Intel i7 + 3×Jetson | 300+ TOPS | 32-64GB | 1TB | Full |
| B2-W | Intel i7 + 3×Jetson | 300+ TOPS | 32-64GB | 1TB | Full |

### Autonomous Capabilities

| Model | Self-Charging | Navigation | Obstacle Avoidance | Mission Planning |
|-------|---------------|------------|-------------------|------------------|
| Go2 Air | No | Manual only | Basic | None |
| Go2 Pro | No | Manual only | Enhanced | None |
| Go2 ENT | Station compatible* | Waypoint | Advanced | Basic |
| Go2 EDU | No | Programmable | Programmable | Custom |
| Go2 EDU Plus | Yes (with LiDAR) | Autonomous | AI-based | Advanced |
| A2 | Yes (2025) | Full autonomous | Dual LiDAR | AI planning |
| B1 | Custom only | Industrial | Multi-sensor | Professional |
| B2 | Optional | Industrial | Multi-modal | Professional |
| B2-W | Optional | Hybrid | Multi-modal | Professional |

*Can use charging stations but cannot autonomously navigate to them

### Communication Capabilities

| Model | WiFi | Cellular | Ethernet | Satellite | Mesh |
|-------|------|----------|----------|-----------|------|
| Go2 Air | 802.11ac | No | No | No | No |
| Go2 Pro | WiFi 6 | 4G LTE | No | No | No |
| Go2 ENT | WiFi 6 | 4G/5G | 1× GbE | No | No |
| Go2 EDU | WiFi 6 | Optional | No | No | No |
| Go2 EDU Plus | WiFi 6 | Optional | 1× GbE | No | No |
| A2 | WiFi 6E | 5G | 2× GbE | Optional | Yes |
| B1 | WiFi 6 | 4G | 2× GbE | Optional | Yes |
| B2 | WiFi 6E | 5G | 4× GbE | Optional | Yes |
| B2-W | WiFi 6E | 5G | 4× GbE | Optional | Yes |