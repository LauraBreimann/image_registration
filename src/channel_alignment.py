import os
import json
import argparse
from typing import List, Dict
import numpy as np
from skimage.transform import warp, AffineTransform
import tifffile
import pandas as pd

from input_handler import SplitChannelInputHandler  # Ensure this module is available in your path


def load_transformations(json_path: str, microscope_name: str) -> Dict[str, AffineTransform]:
    """Load a dictionary of AffineTransform objects for each channel for a given microscope."""
    with open(json_path, 'r') as f:
        all_tf = json.load(f)
    if microscope_name not in all_tf:
        raise ValueError(f"Microscope '{microscope_name}' not found in {json_path}")

    tf_dict = {}
    for ch_name, mat in all_tf[microscope_name].items():
        tf_dict[ch_name] = AffineTransform(np.array(mat))
    return tf_dict


def apply_transform_to_stack(stack: np.ndarray, transform: AffineTransform) -> np.ndarray:
    """Apply an affine transformation slice-by-slice to a 3D stack."""
    transformed = np.zeros_like(stack)
    for z in range(stack.shape[0]):
        transformed[z] = warp(
            stack[z],
            transform.inverse,
            preserve_range=True,
            mode='constant',
            cval=0
        ).astype(stack.dtype)
    return transformed


def align_tiff_channels(
    image_path: str,
    output_path: str,
    transformation_dict: Dict[str, AffineTransform],
    channel_labels: List[str]
) -> None:
    """Align a multichannel TIFF and save the result."""
    stack = tifffile.imread(image_path)

    if stack.ndim != 4:
        raise ValueError(f"{image_path}: Expected shape (C, Z, Y, X). Got shape: {stack.shape}")

    aligned_stack = np.zeros_like(stack)

    for i, ch_name in enumerate(channel_labels):
        if ch_name not in transformation_dict:
            raise ValueError(f"Channel '{ch_name}' not found in transformation dictionary")
        aligned_stack[i] = apply_transform_to_stack(stack[i], transformation_dict[ch_name])

    tifffile.imwrite(output_path, aligned_stack)
    print(f"[✓] Saved aligned multichannel stack: {output_path}")


def process_folder(
    input_folder: str,
    output_folder: str,
    transformation_file: str,
    microscope_name: str,
    channel_labels: List[str]
) -> None:
    """Process all multichannel TIFFs in a folder."""
    os.makedirs(output_folder, exist_ok=True)
    transformations = load_transformations(transformation_file, microscope_name)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith((".tif", ".tiff")):
            input_path = os.path.join(input_folder, filename)
            aligned_name = (
                filename.replace(".tif", "_aligned.tif").replace(".tiff", "_aligned.tiff")
            )
            output_path = os.path.join(output_folder, aligned_name)
            print(f"[→] Processing {filename}")
            align_tiff_channels(input_path, output_path, transformations, channel_labels)


def process_individual_files_from_csv(
    channel_map_file: str,
    output_root: str,
    transformation_file: str,
    microscope: str,
    suffix: str = "_aligned"
) -> None:
    """Apply alignment to individual image files using a channel map CSV and keep folder structure."""
    handler = SplitChannelInputHandler(channel_map_file)
    df = handler.map_df
    tf_dict = load_transformations(transformation_file, microscope)

    os.makedirs(output_root, exist_ok=True)

    for _, row in df.iterrows():
        filepath = row['filepath']
        channel = row['channel']

        if not os.path.exists(filepath):
            print(f"[!] Skipping missing file: {filepath}")
            continue

        if channel not in tf_dict:
            print(f"[!] Skipping file for channel '{channel}' (no transformation)")
            continue

        transform = tf_dict[channel]
        image = tifffile.imread(filepath)

        is_2d = image.ndim == 2
        if is_2d:
            image = np.expand_dims(image, axis=0)

        aligned = apply_transform_to_stack(image, transform)
        if is_2d:
            aligned = np.squeeze(aligned, axis=0)


        base_name = os.path.basename(filepath)         
        root, ext = os.path.splitext(base_name)        
        new_name = root + suffix + ext                 

        output_path = os.path.join(output_root, new_name)  
        os.makedirs(output_root, exist_ok=True)

        tifffile.imwrite(output_path, aligned.astype(image.dtype))
        print(f"[✓] Saved aligned: {output_path}")


# -------------------- Entry Point --------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Apply chromatic alignment to images using affine transformations."
    )

    parser.add_argument(
        "--input_mode",
        choices=["multichannel", "split_channels_preserve_structure"],
        default="multichannel",
        help="Which mode to use: 'multichannel' TIFFs or separate files per channel."
    )
    parser.add_argument("--input_folder", type=str, help="Folder containing multichannel TIFFs.")
    parser.add_argument("--channel_map_file", type=str, help="CSV file for split_channels mode.")
    parser.add_argument("--output_folder", required=True, help="Where to save aligned images.")
    parser.add_argument("--transformation_file", required=True, help="Path to transformation_dicts.json.")
    parser.add_argument("--microscope", required=True, help="Microscope name used inside the transformation file.")
    parser.add_argument("--channel_order", nargs='+', help="List of channel names in order.")
    parser.add_argument("--suffix", default="_aligned", help="Suffix to append to aligned output filenames.")

    args = parser.parse_args()

    if args.input_mode == "multichannel":
        if not args.input_folder or not args.channel_order:
            raise ValueError("--input_folder and --channel_order are required for multichannel mode")

        process_folder(
            input_folder=args.input_folder,
            output_folder=args.output_folder,
            transformation_file=args.transformation_file,
            microscope_name=args.microscope,
            channel_labels=args.channel_order
        )

    elif args.input_mode == "split_channels_preserve_structure":
        if not args.channel_map_file:
            raise ValueError("--channel_map_file is required for split_channels_preserve_structure mode")

        process_individual_files_from_csv(
            channel_map_file=args.channel_map_file,
            output_root=args.output_folder,
            transformation_file=args.transformation_file,
            microscope=args.microscope,
            suffix=args.suffix
        )