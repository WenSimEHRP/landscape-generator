import numpy as np

mask_list = {
    1: {"cliff_right": "cliff_r_left.png", "flat_land": "flat_right.png"},
    4: {"flat_land": "flat_left.png", "cliff_left": "cliff_l_right.png"},
    5: {"cliff_right": "cliff_r_left.png", "cliff_left": "cliff_l_right.png"},
    11: {"flat_land": "flat_left.png", "cliff_right": "cliff_r_right.png"},
    14: {"cliff_left": "cliff_l_left.png", "flat_land": "flat_right.png"},
    2: {"cliff_back": "cliff_b_lower.png", "flat_land": "flat_upper.png"},
    7: {"flat_land": "flat_lower.png", "cliff_back": "cliff_b_upper.png"},
    8: {"flat_land": "flat_lower.png", "cliff_front": "cliff_f_upper.png"},
    10: {"cliff_back": "cliff_b_lower.png", "cliff_front": "cliff_f_upper.png"},
    13: {"cliff_front": "cliff_f_lower.png", "flat_land": "flat_upper.png"},
}

order_translation = {
    "flat_land": 0,
    "slope_back_right": 3,
    "slope_back_left": 6,
    "slope_front_right": 9,
    "slope_front_left": 12,
    "cliff_front": 15,
    "cliff_back": 16,
    "cliff_right": 17,
    "cliff_left": 18,
}

TRANSFORM_MATRIX = {
    "flat_land": np.array(
        [
            [-2, 2],
            [1, 1],
        ]
    ),
    "slope_front_right": np.array(
        [
            [-2, 2],
            [1.5, 1],
        ]
    ),
    "slope_front_left": np.array(
        [
            [-2, 2],
            [1, 1.5],
        ]
    ),
    "cliff_front": np.array(
        [
            [-2, 2],
            [1.5, 1.5],
        ]
    ),
    "cliff_right": np.array(
        [
            [-2, 2],
            [1.5, 0.5],
        ]
    ),
    "slope_back_right": np.array(
        [
            [-2, 2],
            [1, 0.5],
        ]
    ),
    "slope_back_left": np.array(
        [
            [-2, 2],
            [0.5, 1],
        ]
    ),
    "cliff_back": np.array(
        [
            [-2, 2],
            [0.5, 0.5],
        ]
    ),
    "cliff_left": np.array(
        [
            [-2, 2],
            [0.5, 1.5],
        ]
    ),
}

MIRROR = np.array(
    [
        [0, 1],
        [1, 0],
    ]
)
