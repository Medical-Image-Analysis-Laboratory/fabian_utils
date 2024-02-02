 # Readme
This repository contains a wrapper to run FaBIAN simulation tool via python. It will be use to do synthetic data augmentation on deformed segmentation maps.

It contains some command-line commands that are listed below, as well as utility functions for preprocessing fetal brain model inputs prior running fabian (ex: fsl_clustering.py, Authors: Andrés le Boeuf, Hélène Lajoux).


## Commands:
`python run_fabian.py`
```
usage: run_fabian.py [-h] --config CONFIG --out OUT --model MODEL [--FetalModel FETALMODEL] [--WMheterogeneity {0,1}] [--GA GA]
                     [--Orientation {1,2,3}] [--B0 {1.5,3.0}] [--FlipAngle FLIPANGLE] [--TEeff TEEFF] [--SDnoise SDNOISE]
                     [--Shift_mm SHIFT_MM] [--SliceThickness SLICETHICKNESS] [--MotionLevel {0,1,2,3,4,5}] [--MotionBounds [MOTIONBOUNDS]]



optional arguments:
  -h, --help                                  show this help message and exit
  --config CONFIG                             Path to the configuration file
  --out OUT                                   Path to the output directory
  --model MODEL                               Path to the atlas fetal brain model directory ../STA/
  --FetalModel FETALMODEL                     Fetal Model: [STA] (default = STA)
  --WMheterogeneity {0,1}                     WM Heterogeneity: 1 - ON, 0 - OFF (default=1)
  --GA GA                                     Gestational age range: [21,35] weeks (default=random)
  --Orientation {1,2,3}                       Orientation: 1 - sagittal, 2 - coronal, 3 - axial (default=random)
  --B0 {1.5,3.0}                              B0: field strength (T)
  --FlipAngle FLIPANGLE                       Flip Angle range: [150,180]° (default=random)
  --TEeff TEEFF                               TEeff should range between [90,300] ms (default=random)
  --SDnoise SDNOISE                           SD Noise should range in between [0.002, 0.2] (default=0.002)
  --Shift_mm SHIFT_MM                         Shift_mm choice: [-1.6,0,1.6] (default = 0)
  --SliceThickness SLICETHICKNESS             Slice Thickness range: [0.8,5] mm, (default=1.2mm)
  --MotionLevel {0,1,2,3,4,5}                 Motion level: 0 - none , 1 - little, 2 - moderate, 3 - strong, 4 - hyper, 5 - custom (default=0)
  --MotionBounds [MOTIONBOUNDS]               Used if motionlevel=5, Motion Bounds for Translation and Rotation and the ratio of corrupted slice: [5,5,5,20,0.05]

```

Notes: When optional arguments are not parse by user, parameters values are assigned from a .json configuration file (ex: haste_default_config.json). Given the .json template, either a default value is assigned or a random value is computed from a specified range.

*Current Status*: `python run_fabian.py` runs any fetal model. Prior running the script you should run fsl_clustering to generate the partial volumes.

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
    "T1_WM": {"range": [2324,3098], "default": null, "target": 0, "n_subrange": 4, "flat_factor": 0.2},
    "T1_GM": {"range": [1955,2434], "default": null, "target": 0, "n_subrange": 4, "flat_factor": 0.2},
    "T1_CSF": {"range": [3000,4000], "default": null, "target": 4000, "n_subrange": 4, "flat_factor": 0.6},
    "T2_WM": {"range": [0,2000], "default": null, "target": 285, "n_subrange": 4, "flat_factor": 0.2},
    "T2_GM": {"range": [0,2000], "default": null, "target": 181, "n_subrange": 4, "flat_factor": 0.2},
    "T2_CSF": {"range": [0,2000], "default": null, "target": 2000, "n_subrange": 4, "flat_factor": 0.6},
    "ClipValue": {"range": [0,1], "default": null}
}

```

Required libraries: 
`pip install matlabengine`

## Available configuration files:
- haste_default_config.json: the template to the haste sequence. 
- haste_isotropic_config.json: the template to generate isotropic images of 1.
- haste_range_config.json: tge tenoakte to the haste sequence without any default values. This configuration can be use to simulate image using random parameters within defined range.

*IMPORTANT NOTES*: default simulation deviates from typical haste sequence as FOV is set to 300x300 instead of 360x360. Base resolution and Reconstruction matrix ar set to 250 so that fabian can generate high isotropic 1.2x1.2x1.2mm images without getting out of memory.

## Atlas Directory Structure
The atlas directory should be structured as in `./STA/` directory (with subdirectories for each GA)


## ToDos:
- [ x ] Change input fetal brain model handling: input a directory that contains all required file to run the sim (segmentation and pve_X)
- [ x ] Enable simulation on all kinds of datasets -> use Andrès fsl_clustering script. 
- [ x ] Prior work on label maps required though (Vlad on it).
- [ x ] input random brain properties using set_brainproperties.m 
- [ x ] Generate json file for each simulation listing parameters
- [   ] dive into K-Space Sampling function to optimize memory handling

*************************************************************************************

## FaBIAN Simulation Parameters for HASTE Sequence using STA

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


## Modifications to FaBIAN
- `set_brainproperties`: new function that inputs brain property given field strength B0. This function can be further modify to enable setting random T1/T2 values given tissues, without any physical meaning for data augmentation (test required thoug, especially of epgm formalism).
- `set_motion`, `motion_transform_mr`: new functions that enables inistialisation of custom motion bounds. `set_motion` takes a motion level in and outputs a matlab struct with motion bounds. This parameter is then input to FaBIAN main function and as argsin of `motion_transform_mr`.
- `clipvalue`: is now a parameter to FaBIAN_main function.
- `T1, T2 and clip values` can all be set randomly. 