import copy
import numpy as np
import nibabel as ni
import SimpleITK as sitk
import os

"""Author: Thomas Sanchez"""

def squeeze_dim(arr, dim):
    if arr.shape[dim] == 1 and len(arr.shape) > 3:
        return np.squeeze(arr, axis=dim)
    return arr

def get_cropped_stack_based_on_mask(
    image_ni, seg_ni, mask_ni, boundary_i=0, boundary_j=0, boundary_k=0, unit="mm"
):
    """
    Crops the input image to the field of view given by the bounding box
    around its mask.
    Code inspired from Michael Ebner: https://github.com/gift-surg/NiftyMIC/blob/master/niftymic/base/stack.py

    Input
    -----
    image_ni: Nifti image
        Nifti image
    mask_ni: Nifti image
        Corresponding nifti mask
    boundary_i: int
        Boundary to add to the bounding box in the i direction
    boundary_j: int
        Boundary to add to the bounding box in the j direction
    boundary_k: int
        Boundary to add to the bounding box in the k direction
    unit: str
        The unit defining the dimension size in nifti

    Output
    ------
    image_cropped:
        Image cropped to the bounding box of mask_ni, including boundary
    mask_cropped
        Mask cropped to its bounding box
    """

    image_ni = copy.deepcopy(image_ni)

    image = squeeze_dim(image_ni.get_fdata(), -1)
    seg = squeeze_dim(seg_ni.get_fdata(), -1)
    mask = squeeze_dim(mask_ni.get_fdata(), -1)

    assert all(
        [i >= m] for i, m in zip(image.shape, mask.shape)
    ), "For a correct cropping, the image should be larger or equal to the mask."
    assert all(
        [i >= m] for i, m in zip(seg.shape, mask.shape)
    ), "For a correct cropping, the image should be larger or equal to the mask."

    assert(image.shape == seg.shape)

    # Get rectangular region surrounding the masked voxels
    [x_range, y_range, z_range] = get_rectangular_masked_region(mask)

    if np.array([x_range, y_range, z_range]).all() is None:
        print("Cropping to bounding box of mask led to an empty image.")
        return None

    if unit == "mm":
        spacing = image_ni.header.get_zooms()
        boundary_i = np.round(boundary_i / float(spacing[0]))
        boundary_j = np.round(boundary_j / float(spacing[1]))
        boundary_k = np.round(boundary_k / float(spacing[2]))

    shape = [min(im, m) for im, m in zip(image.shape, mask.shape)]
    x_range[0] = np.max([0, x_range[0] - boundary_i])
    x_range[1] = np.min([shape[0], x_range[1] + boundary_i])

    y_range[0] = np.max([0, y_range[0] - boundary_j])
    y_range[1] = np.min([shape[1], y_range[1] + boundary_j])

    z_range[0] = np.max([0, z_range[0] - boundary_k])
    z_range[1] = np.min([shape[2], z_range[1] + boundary_k])

    new_origin = list(
        ni.affines.apply_affine(mask_ni.affine, [x_range[0], y_range[0], z_range[0]])
    ) + [1]

    new_affine = image_ni.affine
    new_affine[:, -1] = new_origin

    image_cropped = image[
        x_range[0] : x_range[1],
        y_range[0] : y_range[1],
        z_range[0] : z_range[1],
    ]

    seg_cropped = seg[
        x_range[0] : x_range[1],
        y_range[0] : y_range[1],
        z_range[0] : z_range[1],
    ]

    image_cropped = ni.Nifti1Image(image_cropped, new_affine)
    seg_cropped = ni.Nifti1Image(seg_cropped, new_affine)
    return image_cropped, seg_cropped


def get_rectangular_masked_region(
    mask: np.ndarray,
) -> tuple:
    """
    Computes the bounding box around the given mask
    Code inspired from Michael Ebner: https://github.com/gift-surg/NiftyMIC/blob/master/niftymic/base/stack.py

    Input
    -----
    mask: np.ndarray
        Input mask
    range_x:
        pair defining x interval of mask in voxel space
    range_y:
        pair defining y interval of mask in voxel space
    range_z:
        pair defining z interval of mask in voxel space
    """
    if np.sum(abs(mask)) == 0:
        return None, None, None
    shape = mask.shape
    # Define the dimensions along which to sum the data
    sum_axis = [(1, 2), (0, 2), (0, 1)]
    range_list = []

    # Non-zero elements of numpy array along the the 3 dimensions
    for i in range(3):
        sum_mask = np.sum(mask, axis=sum_axis[i])
        ran = np.nonzero(sum_mask)[0]

        low = np.max([0, ran[0]])
        high = np.min([shape[0], ran[-1] + 1])
        range_list.append(np.array([low, high]).astype(int))

    return range_list

def get_mask_from_seg(seg_ni):

    # Build mask and Save as nii.gz file
    return sitk.BinaryThreshold(seg_ni, 
                                   lowerThreshold=1, 
                                   upperThreshold=float(sitk.GetArrayFromImage(seg_ni).max()), 
                                   insideValue=1, 
                                   outsideValue=0)

def gen_mask_from_seg(root_directory):

    # Walk through the directory
    for dirpath, dirnames, filenames in sorted(os.walk(root_directory)):
        for filename in filenames:
            # Check if the filename contains 'dseg'
            if 'tissue' in filename:
                # Get mask and Save as ni.gz
                print(dirpath)
                seg_ni = sitk.ReadImage(os.path.join(dirpath,filename))
                mask_ni = get_mask_from_seg(seg_ni)
                sitk.WriteImage(mask_ni, os.path.join(dirpath, filename.replace('tissue','mask')))


def gen_crop(root_directory):
    # Walk through the directory
    for dirpath, dirnames, filenames in sorted(os.walk(root_directory)):
        for filename in filenames:
            # Check if the filename contains 'dseg'
            if ('tissue' in filename) and ('remapped' not in filename):
                print(dirpath)
                # Get mask and Save as ni.gz
                seg_ni = ni.load(os.path.join(dirpath,filename))
                image_ni = ni.load(os.path.join(dirpath,filename.replace('tissue', 'T2w')))
                mask_ni = ni.load(os.path.join(dirpath,filename.replace('tissue', 'mask')))
                image_crop_ni, seg_crop_ni = get_cropped_stack_based_on_mask(image_ni, seg_ni, mask_ni)
                # overwrite original images with new centered ones
                ni.save(image_crop_ni,os.path.join(dirpath, filename.replace('tissue', 'T2w')))
                ni.save(seg_crop_ni,os.path.join(dirpath, filename))
# **********************************************************************************
# Path to the root directory
root_directory = '/home/mroulet/Documents/PYTHON/fabian_utils/atlas/FETAnew/'
gen_mask_from_seg(root_directory)
gen_crop(root_directory)
