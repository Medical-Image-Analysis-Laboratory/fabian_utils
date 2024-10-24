import numpy as np
import json
import argparse
import random
import pandas as pd
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
        self.OutputFolder = args.out + f'sim-{args.sim:03}/'

        with open(self.ConfigFilePath, 'r') as file:
            config_dict = json.load(file)

        # Simulation Parameters
        self.FetalModel = get_top_dir(args.model)
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
        self.SDnoise = float(self.set_noise_value(args.SDnoise, config_dict.get('SDnoise')))
        self.SliceThickness = float(self.set_param_value(args.SliceThickness, config_dict.get('SliceThickness')))
        self.Shift_mm = float(self.set_param_value(args.Shift_mm, config_dict.get('Shift_mm')))
        self.FlipAngle = round(float(self.set_param_value(args.FlipAngle, config_dict.get('FlipAngle'))),2)
        self.TEeff = round(float(self.set_param_value(args.TEeff, config_dict.get('TEeff'))),2)

        # Motion
        self.MotionLevel = self.set_param_value(args.MotionLevel, config_dict.get('MotionLevel'))
        self.MotionBounds = args.MotionBounds
        self.set_fabian_motion()

        # Simulation SUB SES RUN IDs
        self.SubID = ids['SubID']
        self.SesID = ids['SesID']
        self.RunID = ids['RunID']
        self.SimID = ids['SimID']

        # Paths
        if self.FetalModel == 'STA':
            self.set_GA(args)
            self.FetalBrainModelPath = args.model + self.FetalModel + str(self.SubID) + '/'
        else:
            self.set_GA(args)
            self.FetalBrainModelPath = args.model + 'sub-' + str(self.SubID).zfill(3) + '/'

        self.set_json_filepath()

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

        # Background Simulation
        self.T1_FAT = round(float(self.set_Tvalue(args.T1_FAT, config_dict.get('T1_FAT'))))
        self.T1_SKULL = round(float(self.set_Tvalue(args.T1_SKULL, config_dict.get('T1_SKULL'))))
        self.T1_BG = round(float(self.set_Tvalue(args.T1_BG, config_dict.get('T1_BG'))))
        self.T2_FAT = round(float(self.set_Tvalue(args.T2_FAT, config_dict.get('T2_FAT'))))
        self.T2_SKULL = round(float(self.set_Tvalue(args.T2_SKULL, config_dict.get('T2_SKULL'))))
        self.T2_BG = round(float(self.set_Tvalue(args.T2_BG, config_dict.get('T2_BG'))))
        self.set_fabian_backgroundproperties(args.Background)

        # Orientation fix for FETA-CHUV
        self.set_fabian_orientation()

    def set_GA(self,args):
        if self.FetalModel == 'STA':
            self.GA = self.SubID
        else:
            # Load the CSV file into a DataFrame
            df = pd.read_csv(args.model + 'sub_meta.csv')

            # Function to get gestational age based on subject ID
            try:
                self.GA = round(float(df.loc[df['participant_id'] == f'sub-{self.SubID:03}', 'gestational_age'].values[0]))
            except IndexError:
                self.GA = 0

    def set_json_filepath(self):
        #json_dir = self.OutputFolder + 'code/config/'
        json_dir = self.OutputFolder + 'code/config/' # clean this !!
        if not os.path.exists(json_dir):
            os.makedirs(json_dir)
        self.JsonOutFilePath = json_dir + 'sub-' + f"{self.SubID:03}" + '_ses-' +  f"{self.SesID:02}" + '_run-' +  f"{self.RunID:02}" + '_config.json'
    
    def set_param_value(self, user_value, param):
        if user_value is not None:
            return user_value
        elif param["default"] is not None:
            return param["default"]
        elif param["range"] is not None:
            return random.uniform(*param['range'])
        else:
            raise ValueError("No value is parsed by the user nor default value or range are available in the config.json file you provided.")

    def set_noise_value(self, user_value, param):
        if user_value is not None:
            return user_value
        elif param["default"] is not None:
            return param["default"]
        elif param["range"] is not None:
            return np.random.choice(np.logspace(np.log10(param['range'][0]),np.log10(param['range'][1]), num=1000))
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

    def set_fabian_orientation(self):
        # not in use for now
        try:
            eng = matlab.engine.start_matlab()
            eng.rng("shuffle")
            eng.addpath('matlab/Utilities')   
            eng.addpath('matlab/')

            self.Orientation = eng.set_orientation(self.FetalBrainModelPath,self.FetalModel,self.SubID,self.Orientation,self.Background,nargout=1)

        except Exception as e:
            print("Error: FaBIAN Orientation simulation parameters generated FaBIAN crash:", e)
    
        finally:
            eng.quit()

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
            print("Error: FabIAN Motion simulation parameters generated FaBIAN crash:", e)
    
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
            print("Error: Brain properties simulation parameters generated FaBIAN crash:", e)
        
        finally:
            eng.quit()

    def set_fabian_backgroundproperties(self,background):

        try:
            eng = matlab.engine.start_matlab()
            eng.rng("shuffle")
            eng.addpath('matlab/Utilities')   
            eng.addpath('matlab/')
            if background:
                self.Background  = eng.set_backgroundproperties(background, self.T1_FAT, self.T1_SKULL, self.T1_BG, self.T2_FAT, self.T2_SKULL, self.T2_BG, nargout=1)
            else:
                self.Background  = eng.set_backgroundproperties(background, nargout=1)

        except Exception as e:
            print("Error: Background simulation parameters generated FaBIAN crash:", e)
        
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

    def run_simulation(self,log=Logging):

            for attribute, value in vars(self).items():
                print(f"{attribute}: {value}")

            
            if is_model_in(self.FetalBrainModelPath):
                start_time = time.time()
                self.to_json()  
                self.call_fabian(log)
                log.logger.info(f"sub-{self.SubID:03}_ses-{self.SesID:02}_run-{self.RunID:02} Computational Time: {time.time()-start_time}")
            else:
                log.logger.info(f"sub-{self.SubID:03}_ses-{self.SesID:02}_run-{self.RunID:02} Missing files in directory: simulation is skipped")
            
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
                                            self.Background,
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
            log.logger.error(f"sub-{self.SubID:03}_ses-{self.SesID:02}_run-{self.RunID:02} MATLAB Execution Error: {matlab_error}")

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
    parser.add_argument('--sim', type=int, help='ID of the simulation', required = True)
    parser.add_argument('--nruns', type=int, help='Number of run per subject within atlas', required=False)

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
    parser.add_argument('--T1_FAT', type=float, help='T1 Fat Property', required=False)
    parser.add_argument('--T1_SKULL', type=float, help='T1 Skull Property', required=False)
    parser.add_argument('--T1_BG', type=float, help='T1 Background Property', required=False)
    parser.add_argument('--T2_WM', type=float, help='T2 WM Tissue Property', required=False)
    parser.add_argument('--T2_GM', type=float, help='T2 GM Tissue Property', required=False)
    parser.add_argument('--T2_CSF', type=float, help='T2 CSF Tissue Property', required=False)
    parser.add_argument('--T2_FAT', type=float, help='T2 Fat Property', required=False)
    parser.add_argument('--T2_SKULL', type=float, help='T2 Skull Property', required=False)
    parser.add_argument('--T2_BG', type=float, help='T2 Background Property', required=False)
    parser.add_argument('--ClipValue', type=float, help='control value set not to deviate T1 and T2 values more than a specific percentage', required=False)
    # Background simulation
    parser.add_argument('--Background', action='store_true', help='Enable background simulation', required=False)

    args = parser.parse_args()

    return args

def is_model_in(model_path):
    model_dir = model_path.split("/")[-2]
    if not os.path.isdir(model_path):
        return False # ValueError(f'Missing directory: {model_path}')
    
    elif (not os.path.isfile(model_path + model_dir + '_tissue.nii.gz') or
          not os.path.isfile(model_path + model_dir + '_WM_pve_0.nii.gz') or 
          not os.path.isfile(model_path + model_dir + '_WM_pve_1.nii.gz') or
          not os.path.isfile(model_path + model_dir + '_WM_pve_2.nii.gz') #or
          #not os.path.isfile(model_path + model_dir + '_tissue_BG.nii.gz')
          ):
        
        return False #ValueError(f'Missing segmentation file(s): {model_dir}_tissue.nii.gz or {model_dir}_WM_pve_X.nii.gz')

    else:
        return True

def get_top_dir(path):
    # Use os.path.split to split the path into head and tail
    head, tail = os.path.split(path)
    # If the path ends with a separator, get the directory before it
    if tail == '':
        head, tail = os.path.split(head)

    return tail

def get_subs(directory_path):
    # Check if the input is a valid directory
    if not os.path.isdir(directory_path):
        raise ValueError('Input is not a valid directory.')

    # Get the directory contents
    fetal_model = get_top_dir(directory_path)
    dir_contents = os.listdir(directory_path)
    if fetal_model == "STA":
         # Extract numbers from folder names using regular expression
        folder_numbers = [int(re.search(r'STA(\d+)', folder).group(1)) for folder in dir_contents if re.search(r'STA(\d+)', folder)]
    else:
        # Extract numbers from folder names using regular expression
        folder_numbers = [int(re.search(r'sub-(\d+)', folder).group(1)) for folder in dir_contents if re.search(r'sub-(\d+)', folder)]

    return sorted(folder_numbers)

def is_simulated(args,sub_id,ses_id,run_id):

    json_config = args.out + 'code/config/' + 'sub-' + f"{sub_id:03}" + '_ses-' +  f"{ses_id:02}" + '_run-' +  f"{run_id:02}" + '_config.json'

    if os.path.exists(json_config):
        return True
    else:
        return False

def set_out_dir(out_dir,sim_id):

    sim_dir = out_dir + 'sim-' + f'{sim_id:03}/'
    if not os.path.exists(sim_dir):
        os.makedirs(sim_dir)
    if not os.path.exists(sim_dir + 'code/'):
        os.makedirs(sim_dir + 'code/')
    if not os.path.exists(sim_dir + 'code/log/'):
        os.makedirs(sim_dir + 'code/log/')
    if not os.path.exists(sim_dir + 'code/config/'):
        os.makedirs(sim_dir + 'code/config/')

def random_simulation_physical(args):
    """random_simulation_physical runs a simulation for a specific atlas (STA/FETA_CHUV/FIDON_CHUV). 
    It will run N simulation per subject within atlas given the number of runs specified."""
    
    sim_id = args.sim
    ses_id = 1

    set_out_dir(args.out, sim_id)
    
    # update session ID if current session ID already simualated + set logfilename
    log_filename = args.out + f'sim-{sim_id:03}/code/log/' + 'sim-' + f'{sim_id:03}' + '_ses-' + f'{ses_id:02}' + '.log'
    while os.path.exists(log_filename):
        ses_id += 1
        log_filename = args.out + f'sim-{sim_id:03}/code/log/' + 'sim-' + f'{sim_id:03}' + '_ses-' + f'{ses_id:02}' + '.log'

    # Log initialization
    log = Logging(log_filename)
    if args.FabianBrainProperties:
        log.logger.info(f"FaBIAN Physical Random Simulation sim-{sim_id:03}_ses{ses_id:02} - Number of run per subject: {args.nruns}")
    else:
        log.logger.info(f"FaBIAN++ Random Simulation sim-{sim_id:03}_ses-{ses_id:02} - Number of runs per subject: {args.nruns}")

    # Launch simulation runs (N runs per sub/GA specified in arguments)
    for run_id in range(1,args.nruns+1):        
        for sub_id in get_subs(args.model):

            if is_simulated(args,sub_id,ses_id,run_id):
                continue
            else:

                ids = {'SimID': sim_id, 'SubID': sub_id, 'SesID': ses_id, 'RunID': run_id}
                sim = Simulation(args,ids)

                log.logger.info(f"Starting Simulation : sub-{sim.SubID:03}_ses-{ses_id:02}_run-{run_id:02}")

                sim.run_simulation(log) 

    # Below an example command to run the simulation on MIALtron
    """
    python run_fabian.py 
    --config /home/mroulet/Documents/PYTHON/fabian_utils/code/haste_range_config.json 
    --out /home/mroulet/Documents/Data/FaBIAN/sim-007/ 
    --model /home/mroulet/Documents/PYTHON/fabian_utils/atlas/STA 
    --FabianBrainProperties 
    --FetalModel FIDON_CHUV
    --sim 12 
    --nruns 30
    """
#**********************************************************
def main():
    
    # Parse optional arguments
    args = parse_arguments()

    # RANDOM SIMULATION
    random_simulation_physical(args)

if __name__ == "__main__":
    main()