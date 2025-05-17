import os
import numpy as np
import tifffile
import pandas as pd
from typing import List, Tuple


class SplitChannelInputHandler:
    """
    Loads FOVs from a channel_map CSV file for split_channels mode.
    Expects a CSV with the columns: fov, timepoint, channel, filepath.
    Groups images by (fov, timepoint), loads each channel, and returns stacks
    with uniform shape per timepoint.
    """

    def __init__(self, channel_map_file: str):
        if not os.path.exists(channel_map_file):
            raise FileNotFoundError(f"Cannot find channel_map file: {channel_map_file}")
        
        self.map_df = pd.read_csv(channel_map_file)

        required_cols = {"fov", "timepoint", "channel", "filepath"}
        if not required_cols.issubset(set(self.map_df.columns)):
            raise ValueError(f"CSV must have columns: {required_cols}")

    def load_stacks(self) -> List[Tuple[str, np.ndarray, List[str]]]:
        """
        Load grouped stacks for each (fov, timepoint).

        Returns:
            List of tuples:
                - output_name (e.g., 'field01_t000')
                - np.ndarray with shape [C, Z, X, Y]
                - list of channel names
        """
        grouped = self.map_df.groupby(['fov', 'timepoint'])
        results = []

        for (fov_name, tp), group in grouped:
            group_sorted = group.sort_values(by='channel')  # consistent channel order
            channel_names = list(group_sorted['channel'])
            channel_stacks = []

            for _, row in group_sorted.iterrows():
                filepath = row['filepath']
                if not os.path.exists(filepath):
                    raise FileNotFoundError(f"Missing image file: {filepath}")

                stack = tifffile.imread(filepath)

                # Accept [Z, X, Y] or [X, Y]
                if stack.ndim == 2:
                    stack = np.expand_dims(stack, axis=0)

                if stack.ndim != 3:
                    raise ValueError(
                        f"Image at {filepath} must be 2D or 3D (Z, Y, X), got shape: {stack.shape}"
                    )

                channel_stacks.append(stack)

            # Validate uniform shape
            shapes = [s.shape for s in channel_stacks]
            if not all(s == shapes[0] for s in shapes):
                raise ValueError(
                    f"Inconsistent shapes for {fov_name} t{tp}: {[list(s.shape) for s in channel_stacks]}"
                )

            # Stack into a single array with shape (C, Z, X, Y)
            stack_array = np.stack(channel_stacks, axis=0)

            time_str = f"{int(tp):03d}" if str(tp).isdigit() else str(tp)
            output_name = f"{fov_name}_t{time_str}"
            results.append((output_name, stack_array, channel_names))

        return results