import copy
import numpy as np
import nibabel as ni
import SimpleITK as sitk
import os
import monai
from monai.transforms import (LoadImage,
                              SaveImage,
                              CropForegroundd,
                              Spacing,)

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

def get_img_size(root_directory):
    maxpx = 0
    maxpxs = []
    dirxs = []
    sizexs = []
    for dirpath, dirnames, filenames in sorted(os.walk(root_directory)):
        for filename in filenames:
            # Check if the filename contains 'dseg'
            if ('T2w' in filename):
                # Get mask and Save as ni.gz
                # Read the NIfTI image using SimpleITK
                image = sitk.ReadImage(os.path.join(dirpath,filename))
                # Get the size of the image
                size = image.GetSize()
                # Print the size of the image
                # Compute the number of voxels
                #print(f"{dirpath}: {image.GetNumberOfPixels()}")
                sizexs.append(size)
                maxpxs.append(image.GetNumberOfPixels())
                dirxs.append(dirpath)
                if maxpx < image.GetNumberOfPixels():
                    maxpx = image.GetNumberOfPixels()

    # Get the sorted indices
    sorted_indices = sorted(range(len(maxpxs)), key=lambda k: maxpxs[k])
    sorted_info_list = [dirxs[i] for i in sorted_indices]
    sorted_sizexs= [sizexs[i] for i in sorted_indices]
    sorted_maxpxs= [maxpxs[i] for i in sorted_indices]
    
    for i,size,px in zip(sorted_info_list, sorted_sizexs, sorted_maxpxs):
        print(f'{i}: {size} - {px}')

def gen_crop_monai(root_directory):

    # Walk through the directory
    for dirpath, dirnames, filenames in sorted(os.walk(root_directory)):
        for filename in filenames:
            # Check if the filename contains 'dseg'
            if ('tissue' in filename) and ('remapped' not in filename):
                
                tissue = LoadImage()(os.path.join(dirpath,filename))
                image = LoadImage()(os.path.join(dirpath,filename.replace('tissue', 'T2w')))
                pve0 = LoadImage()(os.path.join(dirpath,filename.replace('tissue', 'WM_pve_0')))
                pve1 = LoadImage()(os.path.join(dirpath,filename.replace('tissue', 'WM_pve_1')))
                pve2 = LoadImage()(os.path.join(dirpath,filename.replace('tissue', 'WM_pve_2')))
                #mask = LoadImage()(os.path.join(dirpath,filename.replace('tissue', 'mask')))

                image = image.unsqueeze(0)
                tissue = tissue.unsqueeze(0)
                pve0 = pve0.unsqueeze(0)
                pve1 = pve1.unsqueeze(0)
                pve2 = pve2.unsqueeze(0)

                #mask = mask.unsqueeze(0)

                data = {'image': image, 'label': tissue, 'pve0': pve0, 'pve1': pve1, 'pve2': pve2}
                data_cropped = CropForegroundd(keys=['image', 'label', 'pve0', 'pve1', 'pve2'],
                                            source_key='label')(data)

                image = data_cropped['image']
                tissue = data_cropped['label']
                pve0 = data_cropped['pve0']
                pve1 = data_cropped['pve1']
                pve2 = data_cropped['pve2']
                #mask = data_cropped['mask']
                
                # resample to 0.8mm isotropic
                #image = Spacing((0.8, 0.8, 0.8),mode='bilinear')(image)
                #tissue = Spacing((0.8, 0.8, 0.8),mode='nearest')(tissue)

                os.remove(os.path.join(dirpath,filename))
                os.remove(os.path.join(dirpath,filename.replace('tissue', 'T2w')))
                os.remove(os.path.join(dirpath,filename.replace('tissue', 'WM_pve_0')))
                os.remove(os.path.join(dirpath,filename.replace('tissue', 'WM_pve_1')))
                os.remove(os.path.join(dirpath,filename.replace('tissue', 'WM_pve_2')))

                SaveImage(dirpath, separate_folder=False, output_postfix='')(tissue,)
                SaveImage(dirpath, separate_folder=False, output_postfix='')(image,)
                SaveImage(dirpath, separate_folder=False, output_postfix='')(pve0,)
                SaveImage(dirpath, separate_folder=False, output_postfix='')(pve1,)
                SaveImage(dirpath, separate_folder=False, output_postfix='')(pve2,)

# **********************************************************************************
# Path to the root directory
root_directory = '/home/mroulet/Documents/Data/miccai_submission/FIDON_CHUV/subs_prior/'
#gen_crop_monai(root_directory)
#gen_mask_from_seg(root_directory)
#gen_crop(root_directory)
#get_img_size(root_directory)



