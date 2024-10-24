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
import json
import math
import os
import argparse

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

def extract_BG(folder_path):
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
                print("Extracting BG from " + brain_path.split("/")[-1] )

                brain = nib.load(brain_path).get_fdata()
                tissues_nii = nib.load(tissue_path)
                tissues = tissues_nii.get_fdata()

                # Create BG mask
                bg = np.zeros_like(tissues)
                bg[tissues == 0] = 1
                #bg[tissues != 0] = 0
                # Apply BG mask to the high resolution reference volume
                bg = brain*bg
                bg_image = nib.Nifti1Image(dataobj=bg, affine=tissues_nii.affine)
                bg_image._header = tissues_nii.header
                save_path = path + "/" + path.split("/")[-1] + "_BG.nii.gz"
                
                nib.save(img=bg_image,filename=save_path)  
                print("Applying FAST to: ",save_path)

                _fsl(save_path) 

                bgseg_path = tissue_path.replace(segmentation_name, "BG_pveseg.nii.gz") # for CHUV and FETA
                if os.path.exists(bgseg_path):
                    bgseg = nib.load(bgseg_path).get_fdata()
                    for bg_label in np.unique(bgseg):
                        if bg_label > 0:
                            bgseg[bgseg == bg_label] = bg_label + 7
                    tissue_bg = tissues + bgseg
                    tissue_bg_image = nib.Nifti1Image(dataobj=tissue_bg, affine=tissues_nii.affine)
                    tissue_bg_image._header = tissues_nii.header
                    save_path = path + "/" + path.split("/")[-1] + "_tissue_BG.nii.gz"
                    nib.save(img=tissue_bg_image,filename=save_path) 
                else:
                    print(f'=========> FAIL <=========')

def write_med_background(folder_path):

    t2_wm = [270,300]
    t1_wm = [2324,3098]
    gm_range = [172,191]

    acq_param = {"kispi": {"TR": 3000, "TE": 120},"chuv": {"TR": 1200, "TE": 90}}

    pd_wm = 0.70
    pd_bg = {"8": 0.10, "9": 0.80, "10": 0.50}

    segmentation_name = "tissue_BG.nii.gz"
    subs = sorted(listdir(folder_path))[:-1]
    for folders in subs:
        path= folder_path + "/" + folders 
        i=0
        for files in listdir(path):
            #print(files)
            if segmentation_name in files:

                relax_dict = {}
                tissue_path = path + "/" + files
                brain_path = tissue_path.replace(segmentation_name, "T2w.nii.gz") # for CHUV and FETA
                print(brain_path)
                brain = nib.load(brain_path).get_fdata()
                bgseg = nib.load(tissue_path).get_fdata()

                # normalized SRR image
                #brain = brain / np.max(brain)

                # get intensity signal of WM (normalized) (SRR)
                Swm = np.round(np.mean( brain [ bgseg == 3 ] ))
                Swm_max = np.round(np.max( brain [ bgseg == 3 ] ))

                for bg_label in range(8,11): #np.unique(bgseg).astype(int):
                    if np.size(brain [ bgseg == bg_label ]) > 0:
                        relax_dict[str(bg_label)] = {}
                        relax_dict[str(bg_label)]["mean"] = np.round(np.mean( brain [ bgseg == bg_label ] ))
                        relax_dict[str(bg_label)]["median"] = np.round(np.median( brain [ bgseg == bg_label ] ))
                        relax_dict[str(bg_label)]["std"] = np.round(np.std( brain [ bgseg == bg_label ] ))
                        relax_dict[str(bg_label)]["min"] = np.round(np.min( brain [ bgseg == bg_label ] ))
                        relax_dict[str(bg_label)]["max"] = np.round(np.max( brain [ bgseg == bg_label ] ))
                
                # define bg_label 
                        # 8 -> bone
                        # 9 -> fat
                        # 10 -> other

                for bg_label in range(8,11): #np.unique(bgseg).astype(int):
                    if np.size(brain [ bgseg == bg_label ]) > 0:
                        Sbg_pv = relax_dict[str(bg_label)]["mean"] 
                        Sbg_pv_max = relax_dict[str(bg_label)]["max"] 
                        pd_bg_pv = pd_bg[str(bg_label)]

                        # T2 background partial volume range estimation
                        if Swm > pd_wm and Sbg_pv > pd_bg_pv :
                            relax_dict[str(bg_label)]["t2min"] = t2_wm[0] * math.log( Swm / pd_wm ) / math.log( Sbg_pv / pd_bg_pv )
                            relax_dict[str(bg_label)]["t2max"] = t2_wm[1] * math.log( Swm / pd_wm ) / math.log( Sbg_pv / pd_bg_pv )
                        else:
                            relax_dict[str(bg_label)]["t2min"] = 0
                            relax_dict[str(bg_label)]["t2max"] = 0

                        t2_bg_pv_min = relax_dict[str(bg_label)]["t2min"]
                        t2_bg_pv_max = relax_dict[str(bg_label)]["t2max"]

                        print(f'Smean: {Swm} {Sbg_pv}')
                        print(f'T2 range: {t2_bg_pv_min} {t2_bg_pv_max}')

                        # T1 background partial volume range estimation -> normalized signal
                        #Swm = relax_dict["3"]["mean"] #/ relax_dict["3"]["max"] # normalized
                        #/ relax_dict[str(bg_label)]["max"] # normalized

                        # set TE according to subject (sub-7XX = chuv subject)
                        if i > 79:
                            TE = acq_param["chuv"]["TE"]
                        else:
                            TE = acq_param["kispi"]["TE"]

                        #print(f'Swm x exp: {Swm * math.exp(TE/t2_wm[0])} - Sbg x exp {Sbg_pv * math.exp(TE/t2_bg_pv_min)}')

                        if t2_bg_pv_min > 0:
                            print(f'SforT1: wm {Swm * math.exp(TE/t2_wm[0]) / Swm_max} bg {Sbg_pv * math.exp( TE/t2_bg_pv_min) / Sbg_pv_max }')

                        if  (   ( t2_bg_pv_min > 0 )                                          and
                                ( Swm * math.exp( TE/t2_wm[0]) / Swm_max < 1 )                and 
                                ( 0 < Sbg_pv * math.exp( TE/t2_bg_pv_min) / Sbg_pv_max < 1 )  ):

                            #relax_dict[str(bg_label)]["t1min"] = t1_wm[0] * math.log( 1 - Swm * math.exp( TE/t2_wm[0]) / Swm_max / pd_wm ) / math.log( 1 - Sbg_pv * math.exp( TE/t2_bg_pv_min) / Sbg_pv_max / pd_bg_pv ) 
                            relax_dict[str(bg_label)]["t1min"] = t1_wm[0] * math.log( 1 - Swm * math.exp( TE/t2_wm[0]) / Swm_max ) / math.log( 1 - Sbg_pv * math.exp( TE/t2_bg_pv_min) / Sbg_pv_max ) 
                        else:
                            relax_dict[str(bg_label)]["t1min"] = 0

                        if  (   ( relax_dict[str(bg_label)]["t1min"] != 0 )          and
                                ( t2_bg_pv_max > 0 )                                 and
                                ( Swm * math.exp( TE/t2_wm[1]) / Swm_max < 1 )       and 
                                ( 0 < Sbg_pv * math.exp( TE/t2_bg_pv_max) / Sbg_pv_max < 1 ) ):

                            #relax_dict[str(bg_label)]["t1max"] = t1_wm[1] * math.log( 1 - Swm * math.exp( TE/t2_wm[1]) / Swm_max / pd_wm ) / math.log( 1 - Sbg_pv * math.exp( TE/t2_bg_pv_max) / Sbg_pv_max / pd_bg_pv ) 
                            relax_dict[str(bg_label)]["t1max"] = t1_wm[1] * math.log( 1 - Swm * math.exp( TE/t2_wm[1]) / Swm_max ) / math.log( 1 - Sbg_pv * math.exp( TE/t2_bg_pv_max) / Sbg_pv_max ) 
                        else:
                            relax_dict[str(bg_label)]["t1max"] = 0
                        
                        print(f'T1 range: {relax_dict[str(bg_label)]["t1min"]} {relax_dict[str(bg_label)]["t1max"]}')

                json_filename = path + "/" + path.split("/")[-1] + "_t2w_mean.json"
                # Writing dictionary to JSON file
                with open(json_filename, "w") as json_file:
                    json.dump(relax_dict, json_file, indent=4)
            i+=1

def _fsl(output_basename):
    """
    Function which calls bash script to launch FSL

                inputs: - output_basename: output nifti 
                                            image(s) path
    """    
    subprocess.run(["/home/mroulet/fsl/bin/fast", "-t", "2", "-n", "3", "-H", "0.1", "-I", "4", "-l", "20.0", "-o", output_basename])

def parse_arguments():
    parser = argparse.ArgumentParser(description='Configuration Parser')
    parser.add_argument('--atlas', help='Path to the atlas directory', required=True)
    parser.add_argument('--wm', action='store_true', help='Extract White Matter Partial Volumes', required=False)
    parser.add_argument('--background', action='store_true', help='Extract Background Partial Volumes', required=False)

    return parser.parse_args()

if __name__ == "__main__":

    args = parse_arguments()
    
    if args.wm:
        # Extract White Matter and Partial Volume (n_pve = 3)
        extract_WM(args.atlas)

    if args.background:
        # Background Simulation and Partial Volume (n_pve = 3)
        extract_BG(args.atlas)
        write_med_background(args.atlas)

    if not (args.wm and args.background):
        print("Provide --wm or --background arguments for script to do something ^^.")