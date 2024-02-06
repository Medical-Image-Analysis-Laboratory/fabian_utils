import numpy as np
import json
import argparse
import random
import matlab.engine
import os
import time 
import logging
from datetime import datetime
import re

"""Minimal Command to run the script:   
python run_fabian.py --config /home/mroulet/Documents/PYTHON/fabian_utils/code/haste_range_config.json --out /home/mroulet/Documents/Data/STA_FaBIAN/sim-006/ --model /home/mroulet/Documents/PYTHON/fabian_utils/STA/
"""

class Logging:
    def __init__(self, flnm):
        # Configure the logger
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)  # Set the default level to INFO

        # Create a file handler to save logs to a file
        file_handler = logging.FileHandler(flnm)
        file_handler.setLevel(logging.INFO)  # Only save ERROR level logs to the file

        # Create a console handler to display logs in the console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create a formatter and set it for both handlers
        formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add both handlers to the logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

class Simulation:
    def __init__(self,args,ids):

        self.ConfigFilePath = args.config
        self.OutputFolder = args.out

        with open(self.ConfigFilePath, 'r') as file:
            config_dict = json.load(file)

        # Simulation Parameters
        self.FetalModel = args.FetalModel if args.FetalModel else config_dict.get('FetalModel')
        self.INU = config_dict.get('INU')
        self.SimResampling = config_dict.get('SimResampling')
        self.SimCrop = config_dict.get('SimCrop')
        self.SamplingFactor = float(config_dict.get('SamplingFactor'))
        self.FOVRead = float(config_dict.get('FOVRead'))
        self.FOVPhase = float(config_dict.get('FOVPhase'))
        self.TR = float(config_dict.get('TR'))
        self.ESP = float(config_dict.get('ESP'))
        self.ETL = config_dict.get('ETL')
        self.PhaseOversampling = float(config_dict.get('PhaseOversampling'))
        self.SliceGap = float(config_dict.get('SliceGap'))
        self.BaseResolution = float(config_dict.get('BaseResolution'))
        self.PhaseResolution = float(config_dict.get('PhaseResolution'))
        self.ReconMatrix = float(config_dict.get('ReconMatrix'))
        self.ACF = config_dict.get('ACF')
        self.RefLines = config_dict.get('RefLines')
        self.ZIP = config_dict.get('ZIP')
        self.WMheterogeneity = self.set_param_value(args.WMheterogeneity, config_dict.get('WMheterogeneity'))
        self.Orientation = round(self.set_param_value(args.Orientation, config_dict.get('Orientation')))
        self.B0 = self.set_param_value(args.B0, config_dict.get('B0'))
        self.SDnoise = float(self.set_param_value(args.SDnoise, config_dict.get('SDnoise')))
        self.SliceThickness = float(self.set_param_value(args.SliceThickness, config_dict.get('SliceThickness')))
        self.Shift_mm = float(self.set_param_value(args.Shift_mm, config_dict.get('Shift_mm')))
        self.FlipAngle = round(float(self.set_param_value(args.FlipAngle, config_dict.get('FlipAngle'))),2)
        self.TEeff = round(float(self.set_param_value(args.TEeff, config_dict.get('TEeff'))),2)
        self.GA = round(self.set_param_value(args.GA, config_dict.get('GA')))
        #self.GA = self.get_ga(self.FetalBrainModelPath)

        # Motion
        self.MotionLevel = self.set_param_value(args.MotionLevel, config_dict.get('MotionLevel'))
        self.MotionBounds = args.MotionBounds
        self.set_fabian_motion()

        # Tissue Properties
        self.FabianBrainProperties = args.FabianBrainProperties
        if self.FabianBrainProperties:
            self.set_fabian_brainproperties()
            self.ClipValue = 'adapt' # so the matlab function run as expected
        else:
            self.T1_WM = round(float(self.set_Tvalue(args.T1_WM, config_dict.get('T1_WM'))))
            self.T1_GM = round(float(self.set_Tvalue(args.T1_GM, config_dict.get('T1_GM'))))
            self.T1_CSF = round(float(self.set_Tvalue(args.T1_CSF, config_dict.get('T1_CSF'))))
            self.T2_WM = round(float(self.set_Tvalue(args.T2_WM, config_dict.get('T2_WM'))))
            self.T2_GM = round(float(self.set_Tvalue(args.T2_GM, config_dict.get('T2_GM'))))
            self.T2_CSF = round(float(self.set_Tvalue(args.T2_CSF, config_dict.get('T2_CSF'))))
            self.ClipValue = round(float(self.set_param_value(args.ClipValue, config_dict.get('ClipValue'))),2)

        # Simulation SUB SES RUN IDs
        self.SubID = ids['SubID']
        self.SesID = ids['SesID']
        self.RunID = ids['RunID']

        # Paths
        if self.FetalModel == 'STA':
            self.SubID = self.GA
            self.FetalBrainModelPath = args.model + self.FetalModel + str(self.SubID) + '/'
        else:
            self.FetalBrainModelPath = args.model + 'sub-' + str(self.SubID).zfill(3) + '/'

        self.set_json_filepath()

    def set_json_filepath(self):
        json_dir = self.OutputFolder + 'code/config/'
        if not os.path.exists(json_dir):
            os.makedirs(json_dir)
        self.JsonOutFilePath = json_dir + 'sub-' + str(self.SubID) + '_ses-' +  f"{self.SesID:02}" + '_run-' +  f"{self.RunID:02}" + '_config.json'
    
    def set_param_value(self, user_value, param):
        if user_value is not None:
            return user_value
        elif param["default"] is not None:
            return param["default"]
        elif param["range"] is not None:
            return random.uniform(*param['range'])
        else:
            raise ValueError("No value is parsed by the user nor default value or range are available in the config.json file you provided.")

    def set_Tvalue(self, user_value, param):
        if user_value is not None:
            return user_value
        elif param["default"] is not None:
            return param["default"]
        elif param["range"] is not None:
            subranges = generate_subranges(param["range"], param["n_subrange"])
            selected_subrange, _= select_subrange(subranges, param["target"], param["flat_factor"])

            return np.random.uniform(subranges[selected_subrange][0], subranges[selected_subrange][1])
        else:
            raise ValueError("No value is parsed by the user nor default value or range are available in the config.json file you provided.")

    def set_fabian_motion(self):
        try:
            eng = matlab.engine.start_matlab()
            eng.rng("shuffle")
            eng.addpath('matlab/Utilities')   
            eng.addpath('matlab/')

            # Set motion translation and rotation amplitude, and ratio of corrupted slice number
            if self.MotionLevel == 5:
                self.Motion = eng.set_motion(self.MotionLevel,self.MotionBounds,nargout=1)
            else:
                self.Motion = eng.set_motion(self.MotionLevel,nargout=1)

        except Exception as e:
            print("Error: simulation parameters generated FaBIAN crash:", e)
    
        finally:
            eng.quit()
        
    def set_fabian_brainproperties(self):
        try:
            eng = matlab.engine.start_matlab()
            eng.rng("shuffle")
            eng.addpath('matlab/Utilities')   
            eng.addpath('matlab/')
            [self.T1_WM,self.T2_WM,self.T1_GM,self.T2_GM,self.T1_CSF,self.T2_CSF]  = eng.set_brainproperties(self.B0,nargout=6)
        
        except Exception as e:
            print("Error: simulation parameters generated FaBIAN crash:", e)
        
        finally:
            eng.quit()

    def get_log_flnm(self):
        log_dir = self.OutputFolder + 'code/log/'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        return 'sub-' + str(self.SubID) + '_ses-' +  f"{self.SesID:02}" + '_run-' +  f"{self.RunID:02}" + '_log.json'
        
    def to_json(self):
        json_data = {}
        for attribute, value in vars(self).items():
            json_data[attribute] = value
        with open(self.JsonOutFilePath, "w") as json_file:
            json.dump(json_data, json_file, indent=4)
        print(f"Simulation parameters written to : {self.JsonOutFilePath}")

    def run_simulation(self,log=Logging):

            for attribute, value in vars(self).items():
                print(f"{attribute}: {value}")

            
            if is_model_in(self.FetalBrainModelPath):
                start_time = time.time()
                self.call_fabian(log)
                self.to_json()  
                log.logger.info(f"sub-{self.SubID}_ses-{self.SesID}_run-{self.RunID} Computational Time: {time.time()-start_time}")
            else:
                log.logger.info(f"sub-{self.SubID}_ses-{self.SesID}_run-{self.RunID} Missing files in directory: simulation is skipped")
            
    def call_fabian(self,log=Logging):
        try:
            eng = matlab.engine.start_matlab()
            eng.rng("shuffle")
            eng.addpath('matlab/Utilities')   
            eng.addpath('matlab/')
            
            # call fabian
            imgs = eng.FaBiAN_main_CHUV_DA( self.FetalBrainModelPath,
                                            self.FetalModel,
                                            self.SubID,
                                            self.SesID,
                                            self.RunID,
                                            self.Shift_mm,
                                            self.Orientation,
                                            self.INU,
                                            self.SamplingFactor,
                                            self.B0,
                                            self.ESP,
                                            self.ETL,
                                            self.PhaseOversampling,
                                            self.SliceThickness,
                                            self.SliceGap,
                                            self.FOVRead,
                                            self.FOVPhase,
                                            self.BaseResolution,
                                            self.PhaseResolution,
                                            self.TR,
                                            self.TEeff,
                                            self.FlipAngle,
                                            self.ACF,
                                            self.RefLines,
                                            self.Motion,
                                            self.ZIP,
                                            self.ReconMatrix,
                                            self.SDnoise,
                                            self.SimResampling,
                                            self.SimCrop,
                                            self.OutputFolder,
                                            self.WMheterogeneity,
                                            self.T1_WM,
                                            self.T2_WM,
                                            self.T1_GM,
                                            self.T2_GM,
                                            self.T1_CSF,
                                            self.T2_CSF,
                                            self.ClipValue,
                                            self.GA)

        except matlab.engine.MatlabExecutionError as matlab_error:
            log.logger.error(f"sub-{self.SubID}_ses-{self.SesID}_run-{self.RunID} MATLAB Execution Error: {matlab_error}")

        finally:
            # Stop matlab engine
            eng.quit()
            
#**********************************************************

def generate_subranges(T2range, num_subranges):
    
    start = T2range[0]
    end = T2range[1]
    # Generate logarithmically spaced points between 0 and 1
    points = np.logspace(0,1, num_subranges, base=10,endpoint=False)-1
    
    # Scale points to fit the desired range
    scaled_points = start + (end - start) * points /10
    scaled_points = np.append(scaled_points,end)

    # Round the scaled points to integers
    rounded_points = np.round(scaled_points).astype(int)
    # Create subranges
    subranges = [(rounded_points[i-1], rounded_points[i]) for i in range(1, len(rounded_points))]

    return subranges

def select_subrange(subranges,target_mean,flat_factor=0.2):

    # Calculate means of the subranges
    subrange_means = [(start + end) / 2 for start, end in subranges]

    # Calculate distances between the means and the target mean
    distances = np.abs(np.array(subrange_means) - target_mean)

    # Calculate probabilities based on distances
    probabilities = 1 / distances
    probabilities = probabilities**flat_factor
    probabilities /= probabilities.sum()

    # Select one subrange randomly with uniform weighting
    return np.random.choice(len(subranges), p=probabilities), np.round(probabilities,2)

def parse_arguments():
    parser = argparse.ArgumentParser(description='Configuration Parser')
    parser.add_argument('--config', help='Path to the configuration file', required=True)
    parser.add_argument('--out', help='Path to the output directory', required=True)
    parser.add_argument('--model', help='Path to the atlas fetal brain model directory ../STA/', required= True)
    # Fetal Model
    parser.add_argument('--FetalModel', help='Fetal Model: [STA, CHUV, STA] (default = random)',required=False)
    # Integers
    parser.add_argument('--WMheterogeneity', type=int, choices=[0,1], help='WM Heterogeneity: 1 - ON, 0 - OFF (default=1)',required=False)
    parser.add_argument('--GA', type=int, help='Gestational age range: [21,35] weeks (default=random)',required=False) 
    # --> GA eventually removed and read from json given path to specific sub in atlas
    parser.add_argument('--Orientation', type=int, choices=[1,2,3], help='Orientation: 1 - sagittal, 2 - coronal, 3 - axial (default=random)',required=False)
    # Float
    parser.add_argument('--B0', type=float, choices=[1.5, 3.], help='B0',required=False)
    parser.add_argument('--FlipAngle', type=float, help='Flip Angle range: [150,180]° (default=random)',required=False)
    parser.add_argument('--TEeff', type=float, help='TEeff should range between [90,300] ms (default=random)',required=False)
    parser.add_argument('--SDnoise', type=float, help='SD Noise: should range in between [0.002, 0.2] (default=0.002)',required=False)
    parser.add_argument('--Shift_mm', type=float, help='Shift_mm choice: [-1.6,0,1.6] (default = 0)',required=False)
    parser.add_argument('--SliceThickness', type=float, help='Slice Thickness range: [0.8,5] mm, (default=1.2mm)',required=False)
    # Motion
    parser.add_argument('--MotionLevel', type=int, choices=[0, 1, 2, 3, 4, 5], help='Motion level: 0 - none , 1 - little, 2 - moderate, 3 - strong, 4 - hyper, 5 - custom (default=0)')
    parser.add_argument('--MotionBounds', type=float, nargs='?', default=None, help='Used if motionlevel=5, Motion Bounds for Translation and Rotation and the ratio of corrupted slice: [5,5,5,20,0.05]')
    # Tissue Properties
    parser.add_argument('--FabianBrainProperties', action='store_true', help='Enable FabianBrainProperties', required=False)
    parser.add_argument('--T1_WM', type=float, help='T1 WM Tissue Property', required=False)
    parser.add_argument('--T1_GM', type=float, help='T1 GM Tissue Property', required=False)
    parser.add_argument('--T1_CSF', type=float, help='T1 CSF Tissue Property', required=False)
    parser.add_argument('--T2_WM', type=float, help='T2 WM Tissue Property', required=False)
    parser.add_argument('--T2_GM', type=float, help='T2 GM Tissue Property', required=False)
    parser.add_argument('--T2_CSF', type=float, help='T2 cSF Tissue Property', required=False)
    parser.add_argument('--ClipValue', type=float, help='control value set not to deviate T1 and T2 values more than a specific percentage', required=False)

    args = parser.parse_args()

    return args

def motion_arguments(MotionBounds, MotionLevel=1):
    if MotionLevel == 5 and MotionBounds is None:
        raise argparse.ArgumentTypeError("MotionBounds is obligatory when MotionLevel is set to 5 (custom motion bounds).")

def is_model_in(model_path):
    model_dir = model_path.split("/")[-2]
    print(model_path)
    print(model_dir)
    if not os.path.isdir(model_path):
        return False # ValueError(f'Missing directory: {model_path}')
    
    elif (not os.path.isfile(model_path + model_dir + '_tissue.nii.gz') or
          not os.path.isfile(model_path + model_dir + '_WM_pve_0.nii.gz') or 
          not os.path.isfile(model_path + model_dir + '_WM_pve_1.nii.gz') or
          not os.path.isfile(model_path + model_dir + '_WM_pve_2.nii.gz')):
        
        return False #ValueError(f'Missing segmentation file(s): {model_dir}_tissue.nii.gz or {model_dir}_WM_pve_X.nii.gz')

    else:
        return True

def study_bias_FOV(args,log):

    run_ids = [1,2,3,4,5,6]
    FOVs = [324, 300, 248, 200, 152, 120]
    base_resolutions = [405, 375, 310, 250, 190, 150]

    for fov, base_resolution, run_id in zip(FOVs, base_resolutions, run_ids):
        ids = {'SubID': None, 'SesID': 1, 'RunID': run_id}
        sim = Simulation(args,ids)
        sim.FOVPhase = float(fov)
        sim.FOVRead = float(fov)
        sim.BaseResolution = float(base_resolution)
        sim.ReconMatrix = float(base_resolution)
        sim.RunID = run_id
        sim.run_simulation(log)

def study_noise(args):

    # Log initialization
    log = Logging(args.out + 'code/log/' + datetime.now().strftime("%Y%m%d%H%M") + '_sim-006_ses-01.log')

    slice_thicknesses = [3., 2.5, 2., 1.5, 1.2, 1., 0.8]

    log.logger.info("Noise Study: 6 runs with fixed parameters except thicknesses: [3., 2.5, 2., 1.5, 1.2, 1., 0.8]")
    for slice_thickness, run_id in zip(slice_thicknesses, range(1,len(slice_thicknesses))):
        ids = {'SubID': None, 'SesID': 1, 'RunID': run_id}
        sim = Simulation(args,ids)
        sim.SliceThickness = slice_thickness
        sim.run_simulation(log)

def study_noise_fov(args):

    # Log initialization
    log = Logging(args.out + 'code/log/' + datetime.now().strftime("%Y%m%d%H%M") + '_sim-006_ses-05.log')

    run_ids = [1,2,3,4,5,6]
    FOVs = [324, 300, 248, 200, 152, 120]
    base_resolutions = [405, 375, 310, 250, 190, 150]

    log.logger.info("Noise Study: 6 runs with fixed parameters except fov and base_resolution, res =3.0, FOV: [324, 300, 248, 200, 152, 120]")
    for FOV, base_resolution, run_id in zip(FOVs, base_resolutions, run_ids):
        ids = {'SubID': None, 'SesID': 5, 'RunID': run_id}
        sim = Simulation(args,ids)
        sim.FOVPhase = float(FOV)
        sim.FOVRead = float(FOV)
        sim.BaseResolution = float(base_resolution)
        sim.ReconMatrix = float(base_resolution)
        sim.run_simulation(log)

def study_noise_ga(args):
    # Log initialization
    log = Logging(args.out + 'code/log/' + datetime.now().strftime("%Y%m%d%H%M") + '_sim-006_ses-04.log')

    GAs = [26, 30, 34, 38]

    log.logger.info("Noise Study: 6 runs with fixed parameters except fov and base_resolution, res =0.8, GA: [26, 30, 34, 38]")
    for ga, run_id in zip(GAs, range(1,5)):
        ids = {'SubID': ga, 'SesID': 4, 'RunID': run_id}
        args.GA = ga
        sim = Simulation(args,ids)
        sim.run_simulation(log)

def study_TE_flipangle(args):

    # Log initialization
    log = Logging(args.out + 'code/log/' + datetime.now().strftime("%Y%m%d%H%M") + '_sim-006_ses-07.log')
    log.logger.info("Random study: 40 runs with fixed parameters except flip angle ACF=1, RefLines=0: [140,150,160,180,190] and TEs: [90, 120, 150, 180, 210, 240, 270, 300,330]")

    flipangles = [140,150,160,170,180,190]
    TEs = [90, 120, 150, 180, 210, 240, 270, 300, 330]
    i=0
    for flipangle in flipangles:
        for TEeff in TEs:
            i+=1
            ids = {'SubID': None, 'SesID': 7, 'RunID': i}
            sim = Simulation(args,ids)
            sim.FlipAngle = float(flipangle)
            sim.TEeff = float(TEeff)
            log.logger.info(f"Starting simulation: Flip Angle: {str(flipangle)} TE: {str(TEeff)}")
            sim.run_simulation(log)

def test_simulation(args):

    # Log initialization
    log = Logging(args.out + 'code/log/' + datetime.now().strftime("%Y%m%d%H%M") + '_sim-006_ses-08.log')
    log.logger.info("Test for debugging FaBIAN: check if at 0.8 isotropic TE >= 240 works")

    for run_id in range(1,3):
        ids = {'SubID': 'STA', 'SesID': 8, 'RunID': run_id}
        sim = Simulation(args,ids)
        sim.run_simulation(log) 

def pick_random_sub(directory_path,fetal_model):
    # Check if the input is a valid directory
    if not os.path.isdir(directory_path):
        raise ValueError('Input is not a valid directory.')

    # Get the directory contents
    dir_contents = os.listdir(directory_path)
    if fetal_model == "STA":
         # Extract numbers from folder names using regular expression
        folder_numbers = [int(re.search(r'STA(\d+)', folder).group(1)) for folder in dir_contents if re.search(r'STA(\d+)', folder)]
    else:
        # Extract numbers from folder names using regular expression
        folder_numbers = [int(re.search(r'sub-(\d+)', folder).group(1)) for folder in dir_contents if re.search(r'sub-(\d+)', folder)]

    folder_numbers = sorted(folder_numbers)

    return random.choice(folder_numbers)

def random_simulation_physical(args):

    ses_id = 1
    log_filename = args.out + 'log/' +f'sim-007_ses-{str(ses_id).zfill(2)}.log'
    while os.path.exists(log_filename):
        ses_id += 1
        log_filename = args.out + 'log/' + f'sim-007_ses-{str(ses_id).zfill(2)}.log'

    # Log initialization
    log = Logging(log_filename)
    log.logger.info("Random Simulation using FabianBrainProperties and using 3 sets of data: CHUV, FETA (centered), STA")

    root_data = '/home/mroulet/Documents/Data/FaBIAN/sim-007/'
    root_atlas = '/home/mroulet/Documents/PYTHON/fabian_utils/atlas/'

    for run_id in range(1,5001):
        args.FetalModel = random.choice(["STA","CHUV", "FETA"])
        args.out = os.path.join(root_data,args.FetalModel) + "/"
        args.model = os.path.join(root_atlas,args.FetalModel) + "/"

        sub_id = pick_random_sub(args.model,args.FetalModel)

        ids = {'SubID': sub_id, 'SesID': ses_id, 'RunID': run_id}
        sim = Simulation(args,ids)
        sim.run_simulation(log) 

#**********************************************************
def main():
    
    # Parse optional arguments
    args = parse_arguments()

    # SMALL STUDIES
    #study_noise_ga(args)
    #study_noise_fov(args)
    #study_bias_FOV(args)
    #study_TE_flipangle(args)   

    # DEBUG TEST
    #test_simulation(args)    

    # RANDOM SIMULATION
    random_simulation_physical(args)

if __name__ == "__main__":
    main()