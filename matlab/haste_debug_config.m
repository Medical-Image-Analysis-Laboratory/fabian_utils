%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%  This script simulates T2-weighted MR images of the fetal brain.        %
%  Subjects from the CHUV testing set of the FeTA challenge 2022 serve    %
%  as anatomical models after white matter segmentation using FAST-FSL.   %
%  Common acquisition parameters were retrieved from 15 cases scanned at  %
%  Kispi using an SS-FSE sequence on two GE MR scanners. The sequence     %
%  parameters are chosen randomly among the list of possible parameters.  %
%                                                                         %
%  NB: All data will be upsampled to 0.8mm isotropic in the in-plane      %
%  orientation before SR reconstruction.                                  %
%                                                                         %
%                                                                         %
%  Hélène Lajous, 2023-03-24                                              %
%  helene.lajous@unil.ch                                                  %
%                                                                         %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Fetal brain model
FetalModel = 'FETA_CHUV';
FetalBrainModelPath = './dataverse_files/'; %using STA for now
% Non-linear slowly-varying intensity non-uniformity (INU) fields (b1+)
INU = './rf20_B.rawb';

% Session ID
SesID = 1;

% Define a sampling factor to subdivide the volume in the slice thickness
% orientation
SamplingFactor = 2;
% Motion
MotionLevel = 0;
Motion = set_motion(MotionLevel);

% Implement WM changes
WMheterogeneity =1;

% Depending on the application, resampling of the simulated images might be
% needed
SimResampling = 'false';
% Depending on the application, the simulated images can be cropped to the
% size of the original anatomical model
SimCrop = 'true';

% gestational age
GA = 26;
%SubID = GA;

% field
B0 = 1.5;

%refocusing flip angle (in degrees)
FlipAngle = randi([150 180], 1, 1); 

% field-of-view
FOVRead = 120;
FOVPhase = 120;

% Brain properties given B0=1.5
[T1_WM,T2_WM,T1_GM,T2_GM,T1_CSF,T2_CSF] = set_brainproperties(B0);

% Haste Contrast Parameters
TEeff = 90;
TR = 6.12;  %ms
% Acquisition parameters
ESP = 6.12;  %ms
ETL = 150;
% Geometry
PhaseOversampling = 0.803571;
SliceThickness = 0.8; %mm
SliceGap = 0; %mm
% Resolution
BaseResolution = 150;   %voxels
PhaseResolution = 0.7;
% Acceleration technique !!! 1 -0
ACF = 2;
RefLines = 42;
% Scanner zero-interpolation filling (ZIP)
% (0: no ZIP; 1: Fermi filtering in k-space and ZIP)
ZIP = 1;
ReconMatrix = BaseResolution;

% SNR
SDnoise = 0.0001;

Shift_mm = 0;
%axial orientation
Orientation = 3;

RunID = 1;


