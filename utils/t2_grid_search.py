## Use Parallel Pooling to do the curve fit (16 CPU) ##
#from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
#from concurrent.futures import wait
from multiprocessing import Pool
import numpy as np
from scipy.optimize import curve_fit
import time
import SimpleITK as sitk
from functools import partial
import os
import pandas as pd
import json

def get_nifti_files(directory: str):
    nifti_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.nii.gz')):
                nifti_files.append(os.path.join(root, file))

    if len(nifti_files) > 1:
        return sorted(nifti_files,key=lambda x: os.path.basename(x))
    else:
        return nifti_files[0]

# **********************************************************************************************************************

# Define the exponential decay function
def exponential_decay(t, A, T2, C):
    return A * np.exp(-t / T2) + C

def linearized_exp_decay(t, A, T2, C):
    return np.log(A) - t / T2 + np.log(C)

def linear_fit(TEeffs, voxel_values):
    fit_params = np.polyfit(TEeffs, np.log(voxel_values), 1)
    return -1 / fit_params[0]

def fit_voxel(voxel, fit_linear, TEeffs, reshaped_t2w, initial_guess, param_bounds):
    if fit_linear:
        # Linear fit
        # Fit the exponential decay model (method: non-linear least square)
        params, _ = curve_fit(linearized_exp_decay, TEeffs, reshaped_t2w[voxel, :], p0=initial_guess, bounds=param_bounds)
    else:
        # Mono-exponential fit
        # Fit the exponential decay model (method: non-linear least square)
        params, _ = curve_fit(exponential_decay, TEeffs, reshaped_t2w[voxel, :], p0=initial_guess, bounds=param_bounds)

    return np.array(params)

# ************************************************************************************************************************

# T2 mapping - mono-exponential fit / linear - version with for loop
fit_linear = 0  # 0 = mono-exponential, 1 = linear

# Initial guess and boundaries for the parameters
initial_guess = [200, 70, 0.05]
param_bounds = ([0, 0, 0], [1000, 2000, 0.2])

# Path
recon_dir = '/home/mroulet/Documents/Data/FaBIAN/sim-006/data/'
labels_dir = '/home/mroulet/Documents/Data/FaBIAN/sim-006/data/derivatives/labels/sub-030/ses-06/anat/'
masks_dir = '/home/mroulet/Documents/Data/FaBIAN/sim-006/data/derivatives/masks/'
root_path = '/home/mroulet/Documents/Data/FaBIAN/sim-006/'

sub_value = 'sub-030'
ses_value = 'ses-06'

tissues = ['wm', 'gm', 'csf']

# ************************************************************************************************************************

def t2mapping(sub_lst, TEeffs):
    
    # initialization
    t2w = []
    mask = []

    for img_flnm in sub_lst:

        # set input and output directories
        mask_flnm = os.path.join(masks_dir,sub_value,ses_value,'anat',os.path.basename(img_flnm).replace("T2w", "mask"))
        recon_img = sitk.ReadImage(img_flnm)
        mask_img = sitk.ReadImage(mask_flnm)
        t2w.append(sitk.GetArrayFromImage(recon_img))
        mask.append(sitk.GetArrayFromImage(mask_img)) 

    t2w = np.stack(t2w, axis=-1)
    mask = np.stack(mask, axis=-1)
    mask = np.sum(mask,axis=3) > 0
    TEeffs = np.array(TEeffs)

    print(f"Dimensions of the simulated t2w images: {t2w.shape} (x,y,slice,necho)")
    print(f"Mask Dimension: {mask.shape} -  Number of voxels inside mask: {int(np.sum(mask))}")
    print(f"TEeffs: {TEeffs}")
    #*********************************************************************************

    # reshape for computation time
    reshaped_t2w = np.reshape(t2w, (-1, TEeffs.size)).astype(np.float32)
    reshaped_mask = np.reshape(mask, (-1, 1))

    # Initialize an array to store the fitting parameters for each voxel
    t2map = np.zeros_like(reshaped_t2w[..., 0])
    Amap = np.zeros_like(reshaped_t2w[..., 0])
    Cmap = np.zeros_like(reshaped_t2w[..., 0])
    params = np.zeros((reshaped_t2w.shape[0], 3), dtype=np.float32)
    
    # get indices inside mask
    mask_indices, _ = np.where(reshaped_mask)
    starttime = time.time()
    
    #********** Partial Function Definition **************
    partial_fit_voxel = partial(fit_voxel, 
                                fit_linear=fit_linear, 
                                TEeffs=TEeffs, 
                                reshaped_t2w=reshaped_t2w,
                                initial_guess=initial_guess, 
                                param_bounds=param_bounds)
    #******************************************************
    
    # Fit on multiple workers
    print("Fitting using mono-exponential decay ...")
    with Pool(processes=20) as pool:
        params[mask_indices]  = np.array(pool.map(partial_fit_voxel, mask_indices))
    print(f"... done. Time to fit: {round(time.time()-starttime, 4)} sec")

    t2map = np.reshape(params[:,1].astype(np.float32), (t2w.shape[0], t2w.shape[1], t2w.shape[2]))
    Amap = np.reshape(params[:,0].astype(np.float32), (t2w.shape[0], t2w.shape[1], t2w.shape[2]))
    Cmap = np.reshape(params[:,2].astype(np.float32), (t2w.shape[0], t2w.shape[1], t2w.shape[2]))

    return t2map, Amap, Cmap

def get_grid(t2map, Amap, Cmap,indices,flipangle,tissue):

    grid = pd.DataFrame({   "flipangle": [flipangle], 
                            "tissue": [tissue],
                            "T2_mean": [ np.mean(t2map[indices])],
                            "T2_sd": [np.std(t2map[indices]) ],
                            "A_mean": [ np.mean(Amap[indices])], 
                            "A_sd": [np.std(Amap[indices])], 
                            "C_mean": [ np.mean(Cmap[indices])],
                            "C_sd": [ np.std(Cmap[indices])]})
    
    return grid


img_path = '/home/mroulet/Documents/Data/FaBIAN/sim-006/data/sub-030/ses-06/anat/'
nifti_lst = get_nifti_files(os.path.join(img_path))
# Get a sub DataFrame for a given subject

TEeffs = [90, 120, 150, 180, 210]
flipangles = [140,150,160,170,180,190]

# Segmentation wrt to label map *********************************
label_img = sitk.ReadImage(os.path.join(labels_dir,'sub-030_ses-06_run-01_labels.nii.gz'))
label_vol = sitk.GetArrayFromImage(label_img)

indices_wm = np.where((label_vol == 3)) # WM labels
indices_gm = np.where((label_vol == 2) | (label_vol == 6)) # GM labels
indices_csf = np.where(label_vol == 1)

idx_dict = {"wm": indices_wm, "gm": indices_gm, "csf": indices_csf}

# Initialize an empty DataFrame with column names
grid = pd.DataFrame()
for flipangle in flipangles:

    sub_lst= [s for s in nifti_lst if f"flip-{str(flipangle)}" in s]
    t2map, Amap, Cmap = t2mapping(sub_lst, TEeffs)

    for tissue in tissues:
        entry = get_grid(t2map, Amap, Cmap,idx_dict[tissue], flipangle, tissue)
        grid = pd.concat([grid, entry], ignore_index=True)
        print(grid)

print(grid)
# Save to a file
json_filename = '/home/mroulet/Documents/PYTHON/fabian_utils/code/grid_search.json'
grid.to_json(json_filename, orient='records', lines=True)
