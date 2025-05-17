import os
import SimpleITK as sitk
import tifffile as tiff
import numpy as np

def load_tiff_stack(file_path):
    return tiff.imread(file_path)

def save_tiff_stack(stack, file_path):
    tiff.imwrite(file_path, stack.astype(np.uint16))

def register_images(fixed_image, moving_image):
    # Convert images to SimpleITK format
    fixed_image_sitk = sitk.GetImageFromArray(fixed_image)
    moving_image_sitk = sitk.GetImageFromArray(moving_image)

    # Initialize the registration
    registration_method = sitk.ImageRegistrationMethod()
    registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=100)
    registration_method.SetOptimizerAsRegularStepGradientDescent(
        learningRate=1.0,
        minStep=1e-5,
        numberOfIterations=500,
        gradientMagnitudeTolerance=1e-8
    )
    
    # Choose a transformation model suitable for your needs
    registration_method.SetInitialTransform(sitk.TranslationTransform(fixed_image_sitk.GetDimension()))
    registration_method.SetInterpolator(sitk.sitkBSpline)  # Consider alternatives like sitk.sitkLinear
    
    # Execute the registration
    final_transform = registration_method.Execute(
        sitk.Cast(fixed_image_sitk, sitk.sitkFloat32),
        sitk.Cast(moving_image_sitk, sitk.sitkFloat32)
    )

    # Resample (apply) the transformation to the moving image
    moving_resampled = sitk.Resample(
        moving_image_sitk,
        fixed_image_sitk,
        final_transform,
        sitk.sitkLinear,
        0.0,
        moving_image_sitk.GetPixelID()
    )
    
    return sitk.GetArrayFromImage(moving_resampled)

def align_stack(frames):
    ref_frame = frames[0]
    aligned_frames = [ref_frame]

    for i in range(1, len(frames)):
        frame = frames[i]
        aligned_frame = register_images(ref_frame, frame)
        aligned_frames.append(aligned_frame)

    return aligned_frames

def process_time_series_images(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in sorted(os.listdir(input_folder)):
        if filename.endswith(".tif"):
            print(f"Processing time series: {filename}")
            file_path = os.path.join(input_folder, filename)
            frames = load_tiff_stack(file_path)

            # Align the frames in the stack
            aligned_frames = align_stack(frames)

            # Save the aligned stack
            output_path = os.path.join(output_folder, filename)
            save_tiff_stack(np.array(aligned_frames), output_path)




# User defined paths
input_folder = '/Users/laurabreimann/Documents/Postdoc/Colabs/Elisabeth/multi_channel'
output_folder = '/Users/laurabreimann/Documents/Postdoc/Colabs/Elisabeth/resistered_images'

# Process each time series
process_time_series_images(input_folder, output_folder)