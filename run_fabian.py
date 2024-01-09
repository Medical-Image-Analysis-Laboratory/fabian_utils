import numpy as np
import json
import argparse
import random
import matlab.engine
import os

class Simulation:
    def __init__(self,args, ids):

        self.ConfigFilePath = args.config
        self.OutputFolder = args.out

        with open(self.ConfigFilePath, 'r') as file:
            config_dict = json.load(file)

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
        self.MotionLevel = self.set_param_value(args.MotionLevel, config_dict.get('MotionLevel'))
        self.SubID = self.GA
        self.SesID = ids['SesID']
        self.RunID = ids['RunID']

        self.FetalBrainModelPath = args.model + self.FetalModel + str(self.GA) + '/'

    def set_param_value(self, user_value, param):
        if user_value is not None:
            return user_value
        elif param["default"] is not None:
            return param["default"]
        elif param["range"] is not None:
            return random.uniform(*param['range'])
        else:
            raise ValueError("No value is parsed by the user nor default value or range are available in the config.json file you provided.")
    
    def to_json(self):
        json_data = {}
        for attribute, value in vars(self).items():
            json_data[attribute] = value
        
        json_dir = self.OutputFolder + 'code/'
        if not os.path.exists(json_dir):
            os.makedirs(json_dir)
        json_flnm = 'sub-' + str(self.SubID) + '_ses-' +  f"{self.SesID:02}" + '_run-' +  f"{self.RunID:02}" + '_sim_config.json'
        with open(json_dir + json_flnm, "w") as json_file:
            json.dump(json_data, json_file, indent=4)
        print(f"Simulation parameters written to : {json_dir + json_flnm}")
    #def set_subID(path):

    #def set_ga(path):

def parse_arguments():
    parser = argparse.ArgumentParser(description='Configuration Parser')
    parser.add_argument('--config', help='Path to the configuration file', required=True)
    parser.add_argument('--out', help='Path to the output directory', required=True)
    parser.add_argument('--model', help='Path to the atlas fetal brain model directory ../STA/', required= True)
    # Fetal Model
    parser.add_argument('--FetalModel', help='Fetal Model: [STA, Custom (when ready)] (default = STA)',required=False)
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
    parser.add_argument("--MotionLevel", type=int, choices=[0, 1, 2, 3, 4, 5], help="Motion level: 0 - none , 1 - little, 2 - moderate, 3 - strong, 4 - hyper, 5 - custom (default=0)")
    parser.add_argument("--MotionBounds", type=float, nargs='?', default=None, help="Used if motionlevel=5, Motion Bounds for Translation and Rotation and the ratio of corrupted slice: [5,5,5,20,0.05]")

    args = parser.parse_args()

    return args

def motion_arguments(MotionBounds, MotionLevel=1):
    if MotionLevel == 5 and MotionBounds is None:
        raise argparse.ArgumentTypeError("MotionBounds is obligatory when MotionLevel is set to 5 (custom motion bounds).")

#**********************************************************
def call_fabian(sim):
    try:
        eng = matlab.engine.start_matlab()
        eng.rng("shuffle")
        eng.addpath('matlab/Utilities')   
        eng.addpath('matlab/')        
        [T1_WM,T2_WM,T1_GM,T2_GM,T1_CSF,T2_CSF] = eng.set_brainproperties(sim.B0,nargout=6)
        
        # Set motion translation and rotation amplitude, and ratio of corrupted slice number
        if sim.MotionLevel == 5:
            Motion = eng.set_motion(sim.MotionLevel,sim.MotionBounds,nargout=1)
        else:
            Motion = eng.set_motion(sim.MotionLevel,nargout=1)
        
        # call fabian
        imgs = eng.FaBiAN_main_CHUV_DA( sim.FetalBrainModelPath,
                                        sim.FetalModel,
                                        sim.SubID,
                                        sim.SesID,
                                        sim.RunID,
                                        sim.Shift_mm,
                                        sim.Orientation,
                                        sim.INU,
                                        sim.SamplingFactor,
                                        sim.B0,
                                        sim.ESP,
                                        sim.ETL,
                                        sim.PhaseOversampling,
                                        sim.SliceThickness,
                                        sim.SliceGap,
                                        sim.FOVRead,
                                        sim.FOVPhase,
                                        sim.BaseResolution,
                                        sim.PhaseResolution,
                                        sim.TR,
                                        sim.TEeff,
                                        sim.FlipAngle,
                                        sim.ACF,
                                        sim.RefLines,
                                        Motion,
                                        sim.ZIP,
                                        sim.ReconMatrix,
                                        sim.SDnoise,
                                        sim.SimResampling,
                                        sim.SimCrop,
                                        sim.OutputFolder,
                                        sim.WMheterogeneity,
                                        T1_WM,
                                        T2_WM,
                                        T1_GM,
                                        T2_GM,
                                        T1_CSF,
                                        T2_CSF,
                                        sim.GA)

    except Exception as e:
        print("Error: simulation parameters generated FaBIAN crash:", e)
    
    finally:
        # Stop matlab engine
        eng.quit()


def is_model_in(model_path):
    model_dir = model_path.split("/")[-2]
    
    if not os.path.isdir(model_path):
        return False # ValueError(f'Missing directory: {model_path}')
    
    elif (not os.path.isfile(model_path + model_dir + '_tissue.nii.gz') or
          not os.path.isfile(model_path + model_dir + '_WM_pve_0.nii.gz') or 
          not os.path.isfile(model_path + model_dir + '_WM_pve_1.nii.gz') or
          not os.path.isfile(model_path + model_dir + '_WM_pve_2.nii.gz')):
        
        return False #ValueError(f'Missing segmentation file(s): {model_dir}_tissue.nii.gz or {model_dir}_WM_pve_X.nii.gz')

    else:
        return True


#**********************************************************
def main():
    
    # Only sample code below: Set sesID and runID according to your nomenclature
    
    args = parse_arguments()
    ids = {'SubID': args.GA, 'SesID': 1, 'RunID': 1} # SubID only for STA atlas to be modified asap
    sim = Simulation(args,ids)
    
    for attribute, value in vars(sim).items():
        print(f"{attribute}: {value}")

    if is_model_in(sim.FetalBrainModelPath):
        call_fabian(sim)
        sim.to_json()
        
    else:
        print('Missing files in directory: simulation is skipped')
    

if __name__ == "__main__":
    main()