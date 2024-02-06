# -----------------------------------------------------------
# Python script to crop the white matter volume from the 
# high resolution reference model and apply on it a 3 classes 
# unsupervised segmentation through FAST-FSL tool.
# 
# REQUIRES FSL (https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FAST)
# Note: Since FSL tools work only in linux based OS, this script 
#       has been launch from WSL2
#
# 2022-03-23 Andrés le Boeuf
# andres.le.boeuf@estudiantat.upc.edu
# -----------------------------------------------------------

import sys
from os import listdir
import numpy as np
import nibabel as nib
import subprocess

def extract_WM(folder_path):
    """
    Main function which first cropps the WM volume from the reference model
    and then applies a 3 class FAST segmentation on it.

            inputs: - folder_path: Path were reference 
                                   volumes' folders are
    """
    # Andres for STA -> included WM, cerebellum, brainstem, and some depp grey matter labels too
    # wm = np.array([91, 94, 100, 101, 110, 111, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 125]) # WM labels derived from the atlas annotations.
    # segmentation_name = "tissue"
    # Margaux for FeTA -> included, WM, cerebellum and brainstem
    wm = np.array([3,5,7])
    segmentation_name = "tissue.nii.gz"

    for folders in sorted(listdir(folder_path)):
        path= folder_path + "/" + folders 
        for files in listdir(path):
            if segmentation_name in files:
                
                tissue_path = path + "/" + files
                print(tissue_path)
                #replacement = "_" + segmentation_name
                #brain_path = tissue_path.replace(replacement, "") # for
                brain_path = tissue_path.replace(segmentation_name, "T2w.nii.gz") # for CHUV and FETA
                print("Extracting WM from " + brain_path.split("/")[-1] )

                brain = nib.load(brain_path).get_fdata()
                tissues_nii = nib.load(tissue_path)
                tissues = tissues_nii.get_fdata()

                # Create WM mask
                tissues[~(np.isin(tissues,wm))] = 0
                tissues[tissues!=0] = 1
                # Apply WM mask to the high resolution reference volume
                wm_tissue = brain*tissues
                wm_image = nib.Nifti1Image(dataobj=wm_tissue, affine=tissues_nii.affine)
                wm_image._header = tissues_nii.header
                save_path = path + "/" + path.split("/")[-1] + "_WM.nii.gz"
                
                nib.save(img=wm_image,filename=save_path)  
                print("Applying FAST to: ",save_path)

                _fsl(save_path) 

def _fsl(output_basename):
    """
    Function which calls bash script to launch FSL

                inputs: - output_basename: output nifti 
                                            image(s) path
    """    
    subprocess.run(["/home/mroulet/fsl/bin/fast", "-t", "2", "-n", "3", "-H", "0.1", "-I", "4", "-l", "20.0", "-o", output_basename])
    

if __name__ == "__main__":

    folder_path = r'/home/mroulet/Documents/PYTHON/fabian_utils/atlas/FETA'
    extract_WM(folder_path)
