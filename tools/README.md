# Tools for MYNT® EYE cameras

## Prerequisites

[OpenCV](https://opencv.org/),

```bash
# Linux, macOS
export OpenCV_DIR=~/opencv

# Windows
set OpenCV_DIR=C:\opencv
```

Python packages,

```bash
cd <sdk>/tools/
sudo pip install -r requirements.txt
```

[ROS](http://www.ros.org/) if using rosbag.

## Build

```bash
cd <sdk>
make tools
```

---

## Record data (mynteye dataset)

```bash
./tools/_output/bin/dataset/record


## Analytics data (mynteye dataset)

### imu_analytics.py

```bash
python tools/analytics/imu_analytics.py -i dataset -c tools/config/mynteye/mynteye_config.yaml \
-al=-1.2,1.2 -gl= -gdu=d -gsu=d -kl=
```

### stamp_analytics.py

```bash
python tools/analytics/stamp_analytics.py -i dataset -c tools/config/mynteye/mynteye_config.yaml
```

---

## Record data (rosbag)

```bash
cd <sdk>
make ros
```

```bash
source wrappers/ros/devel/setup.bash
roslaunch mynteye_wrapper_d mynteye.launch
```

```bash
rosbag record -O mynteye.bag /mynteye/left/image_color /mynteye/imu/data_raw /mynteye/temp/data_raw
```

## Analytics data (rosbag)

### imu_analytics.py

```bash
python tools/analytics/imu_analytics.py -i mynteye.bag
```

### stamp_analytics.py

```bash
python tools/analytics/stamp_analytics.py -i mynteye.bag
```
