from grasper import AutograsperBase, RobotActivity
from library.rgb_object_tracker import (
    get_object_pos,
    all_objects_are_visible,
)
from library.utils import OrderType, pick_random_positions, get_undistorted_bottom_image, clear_center, manual_control
import numpy as np
from typing import List, Tuple
import time
import random


class RandomGrasper(AutograsperBase):
    def __init__(
        self,
        args,
        output_dir: str = "",
        colors=None,
        block_heights=None,
        position_bank=None,
        stack_position=None,
        object_size=2,
        camera_matrix=None,
        distortion_coefficients=None,
    ):
        super().__init__(args, output_dir, camera_matrix, distortion_coefficients)
        # Task-specific initialization
        self.colors = colors
        self.block_heights = block_heights
        self.position_bank = position_bank
        self.stack_position = stack_position
        self.object_size = object_size

        # Prepare experiment
        self.position_bank, self.stack_position = self.prepare_experiment(
            self.position_bank, self.stack_position
        )
        self.bottom_image = get_undistorted_bottom_image(
            self.robot, self.camera_matrix, self.distortion_coefficients
        )

        self.time_between_orders = 1

    def prepare_experiment(self, position_bank, stack_position):
        if position_bank is None:
            position_bank = [[0.2, 0.2], [0.8, 0.2], [0.8, 0.8]]
        position_bank = np.array(position_bank)

        if stack_position is None:
            stack_position = [0.5, 0.5]

        return position_bank, stack_position
    
    def move_red_to_center(self):
 
        target_color = "red"
        object_position = get_object_pos(
            self.bottom_image, self.robot_idx, target_color)
        self.pickup_and_place_object(
            object_position,
            0,
            0,
            target_position=[0.5,0.5]
        )


    def perform_task(self):

        margin = 0.2
        random_position = self.generate_new_block_position()
        x = random_position[0]
        y = random_position[1]


        self.queue_robot_orders([
            (OrderType.MOVE_XY, random_position),
            (OrderType.GRIPPER_OPEN, []),
            (OrderType.MOVE_Z, [0]),
            (OrderType.GRIPPER_CLOSE, [])], delay=3.0
        )


        object_position = get_object_pos(
            self.bottom_image, self.robot_idx, "green")
        if (
            abs(x - 0.5) > margin
            and abs(y - 0.5) > margin
            and np.linalg.norm(np.array(random_position) - np.array(object_position)) < 0.12
        ):
            self.failed = False
            print("succesful grasp")
        else:
            print("failed grasp")
            self.failed = True

        print("task complete")

    def generate_new_block_position(self):
        import random

        margin = 0.2
        while True:
            x = random.uniform(0.1, 0.9)
            y = random.uniform(0.1, 0.9)
            if abs(x - 0.5) > margin and abs(y - 0.5) > margin:
                break

        return [x, y]

    def recover_after_fail(self):

        block_pos = self.generate_new_block_position()

        target_color = "green"
        object_position = get_object_pos(
            self.bottom_image, self.robot_idx, target_color)
        self.pickup_and_place_object(
            object_position,
            0,
            0,
            target_position=block_pos,
        )
        self.go_to_start()

    def reset_task(self):
        self.recover_after_fail()

    def pickup_and_place_object(
        self,
        object_position: Tuple[float, float],
        object_height: float,
        target_height: float,
        target_position: List[float] = [0.5, 0.5],
        time_between_orders: float = 2.0,
    ):
        orders = [
            (OrderType.GRIPPER_OPEN, []),
            (OrderType.MOVE_Z, [1]),
            (OrderType.MOVE_XY, object_position),
            #(OrderType.GRIPPER_OPEN, []),
            (OrderType.MOVE_Z, [object_height]),
            (OrderType.GRIPPER_CLOSE, []),
            (OrderType.MOVE_Z, [1]),
            (OrderType.MOVE_XY, target_position),
            (OrderType.MOVE_Z, [target_height]),
            (OrderType.GRIPPER_OPEN, []),
        ]
        self.queue_robot_orders(orders, time_between_orders)