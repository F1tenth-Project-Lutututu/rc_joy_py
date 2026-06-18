#!/usr/bin/env python3

# Copyright 2024
#
# Licensed under the Apache License, Version 2.0 (the "License");
# ...

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy

from enum import Enum

class Mode(Enum):
    STOP = 0
    MANUAL = 1
    AUTONOMOUS = 2

class UsbJoyMimicNode(Node):

    def __init__(self):
        # We use the exact same node name as the original so that the relative 
        # topic '~/output/joy' evaluates to the exact same absolute topic path.
        super().__init__('rc_joy_node')

        # --- Parameters to map standard gamepads to your custom logic ---
        # Default axes/buttons are configured for a standard Xbox One/360 controller on Linux.
        self.declare_parameter('left_stick', 1)       # Left stick Up/Down
        self.declare_parameter('right_stick', 3)       # Right stick Left/Right
        self.declare_parameter('left_trigger', 2)      # LT (Left Trigger)
        self.declare_parameter('right_trigger', 5)      # RT (Right Trigger)
        
        self.declare_parameter('button_A', 0)         # 'A' button
        self.declare_parameter('button_B', 1)         # 'B' button
        self.declare_parameter('button_X', 2)  # 'X' button
        self.declare_parameter('button_Y', 3)  # 'Y' button
        self.declare_parameter('left_bumper', 4)    # LB (Left Bumper)
        self.declare_parameter('right_bumper', 5)   # RB (Right Bumper)

        self.left_stick = self.get_parameter('left_stick').value
        self.right_stick = self.get_parameter('right_stick').value
        self.left_trigger = self.get_parameter('left_trigger').value
        self.right_trigger = self.get_parameter('right_trigger').value
        
        self.btn_A = self.get_parameter('button_A').value
        self.btn_B = self.get_parameter('button_B').value
        self.btn_X = self.get_parameter('button_X').value
        self.btn_Y = self.get_parameter('button_Y').value
        self.btn_LB = self.get_parameter('left_bumper').value
        self.btn_RB = self.get_parameter('right_bumper').value
        
        self.emergency_stop = False
        self.mode_switch = Mode.MANUAL

        self.latest_joy = None

        # Subscribe to standard ROS 2 joy node output
        self.subscription = self.create_subscription(
            Joy,
            '/joy',
            self.joy_callback,
            10)

        # Publisher mimicking the original custom topic and message structure
        self.publisher = self.create_publisher(Joy, '~/output/joy', 1)

        # Timer mimicking the original 50Hz (0.02s) hardware polling loop
        self.timer = self.create_timer(0.02, self.timer_callback)
        
        self.get_logger().info('USB Joy Mimic Node initialized. Waiting for /joy messages...')

    def joy_callback(self, msg: Joy):
        self.latest_joy = msg

    def timer_callback(self):
        # Emulate original behavior: do nothing if no joystick data has been received yet
        if self.latest_joy is None:
            return

        out_msg = Joy()
        out_msg.header.stamp = self.get_clock().now().to_msg()
        msg = self.latest_joy

        # --- Safely Extract and Remap Axes ---
        # Original expects: axes = [throttle (-1 to 1), steering (-1 to 1), left_gain (0 to 1)]
        # throttle pedal
        throttle_pedal = -msg.axes[self.left_trigger] / 2. + 0.5
        # add break pedal
        break_pedal = -msg.axes[self.right_trigger] / 2. + 0.5
        throttle = throttle_pedal - break_pedal

        steering = msg.axes[self.right_stick]

        out_msg.axes = [throttle, steering, 1.]

        if msg.buttons[self.btn_A]:
            self.emergency_stop = not self.emergency_stop
        
        if msg.buttons[self.btn_B]:
            self.mode_switch = Mode.MANUAL

        if msg.buttons[self.btn_X]:
            self.mode_switch = Mode.STOP

        if msg.buttons[self.btn_Y]:
            self.mode_switch = Mode.AUTONOMOUS

        out_msg.buttons = [self.emergency_stop,
                           self.mode_switch == Mode.STOP,
                           self.mode_switch == Mode.MANUAL,
                           self.mode_switch == Mode.AUTONOMOUS]

        self.publisher.publish(out_msg)

def main(args=None):
    rclpy.init(args=args)
    node = UsbJoyMimicNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()