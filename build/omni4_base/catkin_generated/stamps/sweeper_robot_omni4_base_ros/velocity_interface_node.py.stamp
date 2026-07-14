#!/usr/bin/env python3
import math
import threading

import rospy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import JointState

WHEEL_RADIUS = 0.05
PUBLISH_RATE = 50.0

# name, x, y, drive_x, drive_y.  The drive vectors match the 45-degree omni layout.
WHEELS = [
    ("front_left_omni_wheel_joint", 0.145, 0.145, -math.sqrt(0.5), math.sqrt(0.5)),
    ("front_right_omni_wheel_joint", 0.145, -0.145, math.sqrt(0.5), math.sqrt(0.5)),
    ("rear_left_omni_wheel_joint", -0.145, 0.145, -math.sqrt(0.5), -math.sqrt(0.5)),
    ("rear_right_omni_wheel_joint", -0.145, -0.145, math.sqrt(0.5), -math.sqrt(0.5)),
]

lock = threading.Lock()
wheel_velocity = {name: 0.0 for name, *_ in WHEELS}
wheel_position = {name: 0.0 for name, *_ in WHEELS}


def calc_wheel_speeds(msg):
    result = {}
    for name, x, y, drive_x, drive_y in WHEELS:
        contact_vx = msg.linear.x - msg.angular.z * y
        contact_vy = msg.linear.y + msg.angular.z * x
        result[name] = (contact_vx * drive_x + contact_vy * drive_y) / WHEEL_RADIUS
    return result


def on_cmd_vel(msg):
    speeds = calc_wheel_speeds(msg)
    with lock:
        wheel_velocity.update(speeds)
    rospy.loginfo_throttle(
        1.0,
        "cmd_vel vx=%.3f vy=%.3f wz=%.3f | wheel rad/s FL=%.2f FR=%.2f RL=%.2f RR=%.2f",
        msg.linear.x,
        msg.linear.y,
        msg.angular.z,
        speeds["front_left_omni_wheel_joint"],
        speeds["front_right_omni_wheel_joint"],
        speeds["rear_left_omni_wheel_joint"],
        speeds["rear_right_omni_wheel_joint"],
    )


def main():
    rospy.init_node("sweeper_omni4_velocity_interface")
    rospy.Subscriber("/cmd_vel", Twist, on_cmd_vel, queue_size=10)
    joint_pub = rospy.Publisher("/joint_states", JointState, queue_size=10)
    rate = rospy.Rate(PUBLISH_RATE)
    last_time = rospy.Time.now()
    rospy.loginfo("velocity interface ready: subscribe /cmd_vel, publish /joint_states")

    while not rospy.is_shutdown():
        now = rospy.Time.now()
        dt = max((now - last_time).to_sec(), 0.0)
        last_time = now
        with lock:
            names = [name for name, *_ in WHEELS]
            velocities = [wheel_velocity[name] for name in names]
            for name, vel in zip(names, velocities):
                wheel_position[name] += vel * dt
            positions = [wheel_position[name] for name in names]

        msg = JointState()
        msg.header.stamp = now
        msg.name = names
        msg.position = positions
        msg.velocity = velocities
        joint_pub.publish(msg)
        rate.sleep()


if __name__ == "__main__":
    main()
