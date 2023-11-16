import numpy as np
import os
import re
import nibabel as nib
import matplotlib.pyplot as plt
from scipy.ndimage import zoom
from sklearn.preprocessing import MinMaxScaler

# Define the desired dimensions for the MRI images
desired_depth, desired_width, desired_height = 64, 64, 64

# Create a scaler for image normalization
scaler = MinMaxScaler()

slice_indices = [10, 20, 30, 40, 50, 60]
save_directory = 'uploads/'


def resize_volume(img, desired_depth, desired_width, desired_height):

    current_depth = img.shape[0]
    current_width = img.shape[1]
    current_height = img.shape[2]

    depth = current_depth / desired_depth
    width = current_width / desired_width
    height = current_height / desired_height

    depth_factor = 1 / depth
    width_factor = 1 / width
    height_factor = 1 / height

    img = zoom(img, (depth_factor, width_factor, height_factor), order=1)
    return img


def convert_image_to_numpy(test_image):
    # Load and process the test image
    temp_img = nib.load(test_image).get_fdata()
    temp_img = scaler.fit_transform(
        temp_img.reshape(-1, temp_img.shape[-1])).reshape(temp_img.shape)

    # Resize and stack the image
    temp_img = resize_volume(temp_img, desired_depth,
                             desired_width, desired_height)
    temp_img = np.stack((temp_img,) * 3, axis=-1)

    return temp_img


def save_mask(test_prediction_argmax):
    # Create a single figure with six subplots
    fig, axes = plt.subplots(nrows=1, ncols=6, figsize=(15, 15))

    for i, a in enumerate(axes.flatten()):
        if i < len(slice_indices):
            mri_slice = test_prediction_argmax[:, slice_indices[i], :, 1]
            # Create a subplot with no axes
            fig, ax = plt.subplots(figsize=(5, 5))
            # You can specify a colormap if needed
            ax.imshow(mri_slice, cmap='gray')
            ax.axis("off")
            # Define the filename for the saved image
            filename = f"output_mask.png"

            # Save the image to the specified directory
            file_path = os.path.join(save_directory, filename)
            plt.savefig(file_path, bbox_inches='tight', pad_inches=0)

            # Close the plot to release resources
            plt.close()
    print("All Masks are saved")


def save_image(test_img):
    # Create a single figure with six subplots
    fig, axes = plt.subplots(nrows=1, ncols=6, figsize=(15, 15))

    for i, a in enumerate(axes.flatten()):
        if i < len(slice_indices):
            mri_slice = test_img[:, slice_indices[i], :, 1]
            # Create a subplot with no axes
            fig, ax = plt.subplots(figsize=(5, 5))
            # You can specify a colormap if needed
            ax.imshow(mri_slice, cmap='gray')
            ax.axis("off")
            # Define the filename for the saved image
            filename = f"output_image.png"

            # Save the image to the specified directory
            file_path = os.path.join(save_directory, filename)
            plt.savefig(file_path, bbox_inches='tight', pad_inches=0)

            # Close the plot to release resources
            plt.close()
    print("All Images are saved")


def get_pred(filename):
    # Match one or more digits (\d+) before ".nii.gz"
    match = re.search(r'(\d+)', filename)

    if match:
        # Extract the matched digits
        number = int(match.group())
        return number
    else:
        # Return None if no digits are found
        return None
