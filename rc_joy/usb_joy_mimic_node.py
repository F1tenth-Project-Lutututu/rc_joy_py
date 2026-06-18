#!/usr/bin/env python3

# Copyright 2024
#
# Licensed under the Apache License, Version 2.0 (the "License");
# ...

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy

class UsbJoyMimicNode(Node):

    def __init__(self):
        # We use the exact same node name as the original so that the relative 
        # topic '~/output/joy' evaluates to the exact same absolute topic path.
        super().__init__('rc_joy_node')

        # --- Parameters to map standard gamepads to your custom logic ---
        # Default axes/buttons are configured for a standard Xbox One/360 controller on Linux.
        self.declare_parameter('axis_throttle', 1)       # Left stick Up/Down
        self.declare_parameter('axis_steering', 3)       # Right stick Left/Right
        self.declare_parameter('axis_left_gain', 2)      # LT (Left Trigger)
        
        self.declare_parameter('button_main', 0)         # 'A' button
        self.declare_parameter('button_trig_left', 4)    # LB (Left Bumper)
        self.declare_parameter('button_trig_center', 2)  # 'X' button
        self.declare_parameter('button_trig_right', 5)   # RB (Right Bumper)

        self.axis_throttle = self.get_parameter('axis_throttle').value
        self.axis_steering = self.get_parameter('axis_steering').value
        self.axis_left_gain = self.get_parameter('axis_left_gain').value
        
        self.btn_main = self.get_parameter('button_main').value
        self.btn_trig_l = self.get_parameter('button_trig_left').value
        self.btn_trig_c = self.get_parameter('button_trig_center').value
        self.btn_trig_r = self.get_parameter('button_trig_right').value

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
        throttle = msg.axes[self.axis_throttle] if len(msg.axes) > self.axis_throttle else 0.0
        steering = msg.axes[self.axis_steering] if len(msg.axes) > self.axis_steering else 0.0

        # Standard analog triggers range from 1.0 (unpressed) to -1.0 (fully pressed).
        # The original code mapped left_gain to [0.0 to 1.0]. We remap this mathematically:
        raw_gain = msg.axes[self.axis_left_gain] if len(msg.axes) > self.axis_left_gain else 1.0
        left_gain = (1.0 - raw_gain) / 2.0 

        out_msg.axes = [throttle, steering, left_gain]

        # --- Safely Extract and Remap Buttons ---
        # Original expects: buttons = [main_button, trig_left, trig_center, trig_right]
        b_main = msg.buttons[self.btn_main] if len(msg.buttons) > self.btn_main else 0
        b_tl = msg.buttons[self.btn_trig_l] if len(msg.buttons) > self.btn_trig_l else 0
        b_tc = msg.buttons[self.btn_trig_c] if len(msg.buttons) > self.btn_trig_c else 0
        b_tr = msg.buttons[self.btn_trig_r] if len(msg.buttons) > self.btn_trig_r else 0

        out_msg.buttons = [b_main, b_tl, b_tc, b_tr]

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