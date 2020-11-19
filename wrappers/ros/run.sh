catkin_make --source src
catkin_make install --source src
source devel/setup.bash
roslaunch mynteye_wrapper_d display.launch