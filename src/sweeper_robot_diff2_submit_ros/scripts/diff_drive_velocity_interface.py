#!/usr/bin/env python3
import rospy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import JointState

WHEEL_RADIUS = 0.068
WHEEL_SEPARATION = 0.396
CMD_TOPIC = "/cmd_vel"


class DiffDriveInterface:
    def __init__(self):
        self.left_pos = 0.0
        self.right_pos = 0.0
        self.left_vel = 0.0
        self.right_vel = 0.0
        self.last_time = rospy.Time.now()
        self.pub = rospy.Publisher("/joint_states", JointState, queue_size=10)
        rospy.Subscriber(CMD_TOPIC, Twist, self.on_cmd_vel, queue_size=10)

    def on_cmd_vel(self, msg):
        linear_x = msg.linear.x
        angular_z = msg.angular.z
        self.left_vel = (linear_x - angular_z * WHEEL_SEPARATION * 0.5) / WHEEL_RADIUS
        self.right_vel = (linear_x + angular_z * WHEEL_SEPARATION * 0.5) / WHEEL_RADIUS
        rospy.loginfo_throttle(1.0, "diff2 cmd_vel: left=%.3f rad/s, right=%.3f rad/s", self.left_vel, self.right_vel)

    def spin(self):
        rate = rospy.Rate(30)
        while not rospy.is_shutdown():
            now = rospy.Time.now()
            dt = max((now - self.last_time).to_sec(), 0.0)
            self.last_time = now
            self.left_pos += self.left_vel * dt
            self.right_pos += self.right_vel * dt
            msg = JointState()
            msg.header.stamp = now
            msg.name = ["left_drive_wheel_joint", "right_drive_wheel_joint"]
            msg.position = [self.left_pos, self.right_pos]
            msg.velocity = [self.left_vel, self.right_vel]
            self.pub.publish(msg)
            rate.sleep()


if __name__ == "__main__":
    rospy.init_node("sweeper_diff2_velocity_interface")
    rospy.loginfo("two differential wheel velocity interface started: %s", CMD_TOPIC)
    DiffDriveInterface().spin()
