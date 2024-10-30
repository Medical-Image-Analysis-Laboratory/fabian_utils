 # ReadMe
This repository contains a wrapper to run FaBIAN simulation tool via python. It will be use to do synthetic data augmentation on deformed segmentation maps.

It contains some command-line that are listed below, as well as utility functions for preprocessing fetal brain model inputs prior running fabian (ex: fsl_clustering.py, Authors: Andrés le Boeuf, Hélène Lajoux).

Instructions to run fsl_clustering can be found in section 5.


## 1. Commands:
`python run_fabian.py`
```
usage: run_fabian.py [-h] --config CONFIG --out OUT --model MODEL --sim SIM [--nruns NRUNS] [--WMheterogeneity {0,1}] [--GA GA] [--Orientation {1,2,3}] [--B0 {1.5,3.0}]
                     [--FlipAngle FLIPANGLE] [--TEeff TEEFF] [--SDnoise SDNOISE] [--Shift_mm SHIFT_MM] [--SliceThickness SLICETHICKNESS] [--MotionLevel {0,1,2,3,4,5}]
                     [--MotionBounds [MOTIONBOUNDS]] [--FabianBrainProperties] [--T1_WM T1_WM] [--T1_GM T1_GM] [--T1_CSF T1_CSF] [--T1_FAT T1_FAT] [--T1_SKULL T1_SKULL]
                     [--T1_BG T1_BG] [--T2_WM T2_WM] [--T2_GM T2_GM] [--T2_CSF T2_CSF] [--T2_FAT T2_FAT] [--T2_SKULL T2_SKULL] [--T2_BG T2_BG] [--ClipValue CLIPVALUE]
                     [--Background]

mandatory arguments:
  --config                                    Path to the .json configuration file
  --out OUT                                   Path to the output directory
  --model MODEL                               Path to the atlas fetal brain model directory ../STA/
  --sim SIM                                   ID of the simulation
  --nruns NRUNS                               Number of run per subject within atlas

optional arguments:
  -h, --help                                  show this help message and exit
  --WMheterogeneity {0,1}                     WM Heterogeneity: 1 - ON, 0 - OFF (default=1)
  --GA GA                                     Gestational age range: [21,35] weeks (default=random)
  --Orientation {1,2,3}                       Orientation: 1 - sagittal, 2 - coronal, 3 - axial (default=random)
  --B0 {1.5,3.0}                              B0: field strength (T) (default=1.5)
  --FlipAngle FLIPANGLE                       Flip Angle range: [150,180]° (default=random)
  --TEeff TEEFF                               TEeff should range between [90,300] ms (default=random)
  --SDnoise SDNOISE                           SD Noise should range in between [0.002, 0.2] (default=0.002)
  --Shift_mm SHIFT_MM                         Shift_mm choice: [-1.6,0,1.6] (default = 0)
  --SliceThickness SLICETHICKNESS             Slice Thickness range: [0.8,5] mm, (default=1.2mm)
  --MotionLevel {0,1,2,3,4,5}                 Motion level: 0 - none , 1 - little, 2 - moderate, 3 - strong, 4 - hyper, 5 - custom (default=0)
  --MotionBounds [MOTIONBOUNDS]               Used if motionlevel=5, Motion Bounds for Translation and Rotation and the ratio of corrupted slice: [5,5,5,20,0.05]
  --FabianBrainProperties                     Enable FabianBrainProperties and set T1 and T2 values of tissues based on FaBIAN software
  --T1_WM T1_WM                               T1 WM Tissue Property
  --T1_GM T1_GM                               T1 GM Tissue Property
  --T1_CSF T1_CSF                             T1 CSF Tissue Property
  --T1_FAT T1_FAT                             T1 Fat Property
  --T1_SKULL T1_SKULL                         T1 Skull Property
  --T1_BG T1_BG                               T1 Background Property
  --T2_WM T2_WM                               T2 WM Tissue Property
  --T2_GM T2_GM                               T2 GM Tissue Property
  --T2_CSF T2_CSF                             T2 CSF Tissue Property
  --T2_FAT T2_FAT                             T2 Fat Property (when Background=True)
  --T2_SKULL T2_SKULL                         T2 Skull Property (when Background=True)
  --T2_BG T2_BG                               T2 Background Property (when Background=True)
  --ClipValue CLIPVALUE                       Control value set not to deviate T1 and T2 values more than a specific percentage (see FaBIAN software)
  --Background                                Enable background simulation (default=False)

```

Important Note: When optional arguments are not parse by user, parameters values are assigned from a .json configuration file (ex: haste_default_config.json). Given the .json template, either a default value is assigned or a random value is computed from a specified range. I encourage working with the json file rather than parsing optional arguments.

Required libraries: `fabian_utils` run in `gomar` conda environment on the mialtron. All libraries requirements are available in the `requirements_frozen.txt`. Also make sure to install
`pip install matlabengine` and matlab to run FaBIAN.

## 2. Available configuration files:
- haste_default_config.json: the template to the haste sequence. 
- haste_isotropic_config.json: the template to generate isotropic images of 1.
- haste_range_config.json: tge tenoakte to the haste sequence without any default values. This configuration can be use to simulate image using random parameters within defined range.


Example of Configuration file:
Below you'll find the content of the haste_range_config.json file.
```
{
    "AcquisitionType": "Haste",
    "FetalModel": "CHUV",
    "INU": "./code/rf20_B.rawb",
    "SimResampling": "false",
    "SimCrop": "true",
    "SamplingFactor": 2,
    "FOVRead": 120,
    "FOVPhase": 120,
    "TR": 4.08,
    "ESP": 4.08,
    "ETL": 224,
    "PhaseOversampling": 0.80357100000,
    "PhaseResolution": 0.7,
    "ACF": 2,
    "RefLines": 42,
    "ZIP": 1,
    "BaseResolution": 150,
    "ReconMatrix": 150,
    "SliceGap": 0,
    "SliceThickness": {"range": [0.8, 5],  "default": 3.0},
    "WMheterogeneity": {"range": [0, 1],  "default": 1},
    "B0": {"range": [1.5, 3],  "default": 1.5},
    "SDnoise": {"range": [0.002, 0.02],  "default": null},
    "Shift_mm": {"range": [-1.6, 0, 1.6], "default": 0},
    "Orientation": {"range": [1, 3], "default": null},
    "MotionLevel": {"range": [0, 4], "default": 0},
    "FlipAngle": {"range": [150, 180],"default": null},
    "TEeff": {"range": [90, 300],"default": null},
    "GA": {"range": [21, 35],  "default": null},
    "T1_WM": {"range": [2324,3098], "default": null, "target": 2711, "n_subrange": 4, "flat_factor": 0.2},
    "T1_GM": {"range": [1955,2434], "default": null, "target": 2195, "n_subrange": 4, "flat_factor": 0.2},
    "T1_CSF": {"range": [3000,4000], "default": null, "target": 4000, "n_subrange": 4, "flat_factor": 0.6},
    "T1_SKULL": {"range": [1000,1500], "default": null, "target": 1250, "n_subrange": 4, "flat_factor": 0.2},
    "T1_FAT": {"range": [2500,3000], "default": null, "target": 3500, "n_subrange": 4, "flat_factor": 0.2},
    "T1_BG": {"range": [3000,4000], "default": null, "target": 1250, "n_subrange": 4, "flat_factor": 0.2},
    "T2_WM": {"range": [0,2000], "default": null, "target": 285, "n_subrange": 4, "flat_factor": 0.2},
    "T2_GM": {"range": [0,2000], "default": null, "target": 181, "n_subrange": 4, "flat_factor": 0.2},
    "T2_CSF": {"range": [0,2000], "default": null, "target": 2000, "n_subrange": 4, "flat_factor": 0.6},
    "T2_SKULL": {"range": [50,100], "default": null, "target": 75, "n_subrange": 4, "flat_factor": 0.2},
    "T2_FAT": {"range": [250,350], "default": null, "target": 300, "n_subrange": 4, "flat_factor": 0.2},
    "T2_BG": {"range": [50,100], "default": null, "target": 75, "n_subrange": 4, "flat_factor": 0.2},
    "ClipValue": {"range": [0.1,0.9], "default": null}
}

```

*IMPORTANT NOTES*: default simulation deviates from typical haste sequence as FOV is set to 300x300 instead of 360x360. Base resolution and Reconstruction matrix ar set to 250 so that fabian can generate high isotropic 1.2x1.2x1.2mm images without getting out of memory.

## 3. Atlas Directory Structure
The atlas directory should be structured as in `./STA/` directory (with subdirectories for each GA or for each sub). In a given GA/sub directory, the following file should be present:
```
- sub-001_T2w.nii.gz          Input atlas T2w image
- sub-001_tissue.nii.gz       Segmentation image
```
After running fsl clustering, the following files should be in:
```
- sub-001_WM.nii.gz           WM segmented T2w image
- sub-001_WM_pve0.nii.gz      WM partial volume 0
- sub-001_WM_pve1.nii.gz      WM partial volume 1
- sub-001_WM_pve2.nii.gz      WM partial volume 2
- sub-001_BG.nii.gz           Background segmented T2w image (If simulation of the background is required for the FaBIAN simulation)
- sub-001_BG_pve0.nii.gz      BG partial volume 0
- sub-001_BG_pve1.nii.gz      BG partial volume 1
- sub-001_BG_pve2.nii.gz      BG partial volume 2
- others                      Not used in FaBIAN but generated by fsl
```
## 4. Out Directory Structure
Once a simulation has been run, all data generated by FaBIAN will be found in the data/data_crop/data_reo folders. 
In addition, the FaBIAN wrapper will output several additional files in the subfolder `code`:
```
- `code/config/`              Configurations file for each run (filename : sub-XXX_ses-XX_run-XX_config.json)
- `code/log`                  Log file of each session run within same simulaion ID. Log python/matlab possible error or warning of each run.
```

## 5. `run_fsl_clustering` instructions

Prior running FaBIAN make sure you have run `run_fsl_clustering` to output partial volume estimate of the White Matter (anf Background if you simulate background).

`python utils/run_fsl_clustering.py -h`
```
usage: run_fsl_clustering.py [-h] --atlas ATLAS [--wm] [--background]

--atlas ATLAS                 Path to the atlas directory
--wm                          Extract White Matter Partial Volumes
--background                  Extract Background Partial Volumes (required if you want to simulate the background with FaBIAN)
```

## 6. Modifications to FaBIAN
- `set_brainproperties`: new function that inputs brain property given field strength B0. This function can be further modify to enable setting random T1/T2 values given tissues, without any physical meaning for data augmentation (test required thoug, especially of epgm formalism).
- `set_motion`, `motion_transform_mr`: new functions that enables inistialisation of custom motion bounds. `set_motion` takes a motion level in and outputs a matlab struct with motion bounds. This parameter is then input to FaBIAN main function and as argsin of `motion_transform_mr`.
- `clipvalue`: is now a parameter to FaBIAN_main function.
- `T1, T2 and clip values` can all be set randomly. 
- `set_orientation`: new function that checks fetal model affine is compatible with FaBIAN simuulation as the function `reorient_volume`is not robust to all types of affine. If user input orientation is not compatible with fetal model affine, new compatible orientation is set, else, continue. (NOT ROBUST ENOUGH, some bug renains)
- `set_backgroundproperties`: new function that inputs background properties. It adds labels for the skull, fat and pure background segmented from the original atlas T2w image.


## 7. References
[1] SynthSeg: Segmentation of brain MRI scans of any contrast and resolution without retraining
B. Billot, D.N. Greve, O. Puonti, A. Thielscher, K. Van Leemput, B. Fischl, A.V. Dalca, J.E. Iglesias
Medical Image Analysis, accepted for publication.


## Supp1. FaBIAN Simulation Parameters for HASTE Sequence (details)

- GA (weeks): Gestational Age in weeks. Possible values with STA : [21 - 33] (default:random)
- B0: Magnetic field strength (T). [1.5, 3] (default: 1.5)

Acquisition Parameters - Contrast:
- Effective echo time (ms): [90 - 300] (default: random)
- Echo Spacing (ESP) (ms): time interval between successive echoes in a multi-echo imaging sequence. (const: 4.08)
- Repetition Time (TR) (ms): time interval between successive radiofrequency (RF) pulses in a pulse sequence (ms). (const: 4.08)
- Echo Train Length (-): refers to the number of echo in the sequence (const: 224)
- Refocusing pulse flip angle (°): [150 - 180] (default: random)

Acquisition Parameters - Geometry:
- Slice Orientation: sagittal (1), coronal (2), axial (3) (default: random)
- Slice Thickness (mm):  (default: 1.2)
- Slice Gap (mm): (const: 0.3)
- Phase Oversampling (%): phase oversampling refers to the percentage of additional data points acquired in the phase-encoding direction (const: 80)
- Shift of FOV (mm): variable that induce a shift in the FOV. Typically used for simulation of two acquisition done in the same orientation [1.6, 0, 1.6] (default: 0)

Acquisition Parameters - Resolution:
- Field of view (mm2): 360 (FOVRead) x 360 (FOVPhase) (default= 300x300, see note above)
- Base Resolution (voxels): [320 - 327] (default: 250, see note above)
- Phase Resolution (%): phase resolution is input as a percentage of base resolution (const= 70)
- Reconstruction matrix. Reconstruction matrix is function of base and phase resoltuion and is generally ranging from 320x404 to 327x414 (default=250, see note above)
- Zero-interpolation filling (ZIP) (-): Refers to k-space data edge filling during the acquisition to reach the desired reconstruction matrix size : [0, 1] (default: 1)

Acquisition Parameters - Acceleration Technique:
- Reference Lines: number of lines that are consecutively sampled around the center of K-space  (const: 42)
- Acceleration factor: (const: 2)

Amplitude of 3D rigid motion:
- Motion Level (-): none (0), little (1), moderate (2), strong(3), custom (4). (default = 0) 
Amplitude of motion is set randomly within input motion bounds specified by motion level.
  - little: translation bounds 1 mm, 3D rotation bounds 2°
  - moderate: translation bounds 3 mm, 3D rotation bounds 5°
  - strong: translation bounds 4 mm, 3D rotation bounds 8°
  - hyper : translation bounds 10mm, rotation bounds 45°
  - custom: custom bounds parse by user

White Matter Heterogeneity:
- WMHeterogeneity: White matter maturation processes implementation in FaBiAN simulator. ON - 1, OFF - 0. (default = 1)
- ClipValue: clip value takes value between 0-1 and define the level of WM heterogeneity that can happen given the GA (optimization done by Andrès)


*************************************************************************************

## Supp2. ToDos:
- [ x ] Change input fetal brain model handling: input a directory that contains all required file to run the sim (segmentation and pve_X)
- [ x ] Enable simulation on all kinds of datasets -> use Andrès fsl_clustering script. 
- [ x ] Prior work on label maps required though (Vlad on it).
- [ x ] input random brain properties using set_brainproperties.m 
- [ x ] Generate json file for each simulation listing parameters
- [ x ] Log the simulation status
- [ x ] Build a dictionary for MR fingerprinting
- [   ] dive into K-Space Sampling function to optimize memory handling
- [   ] Solve orientation handling bugs in matlab
- [   ] simulation with different motion level

*Current Status*: `python run_fabian.py` runs any fetal model (STA, FETA_CHUV, FIDON_CHUV). Prior running the script you should run fsl_clustering to generate the partial volumes. There remain some issues in Matlab given the orientation code of the volume, which FaBIAN cannot robustely manage.

