function [Motion] = set_motion(motion_level, varargin)
%S ET_MOTION set the transaltion and rotation amplitude as well as the
% number of corrupted slice number and pass the variable to FaBIAN main and
% motion_transform functions.

Motion = struct('MotionLevel', motion_level, ...
                'TranslationAmplitudeX', 0,... 
                'TranslationAmplitudeY', 0,... 
                'TranslationAmplitudeZ', 0,... 
                'RotationAmplitude', 0, ...
                'CorruptedSlicesRatio',0);

switch motion_level
    case 1  %slight motion
        Motion.TranslationAmplitudeX = 1;
        Motion.TranslationAmplitudeY = 1;
        Motion.TranslationAmplitudeZ = 1;
        Motion.RotationAmplitude = 2;
        Motion.CorruptedSlicesRatio = 5/100;
    case 2  %moderate motion
        Motion.TranslationAmplitudeX = 3;
        Motion.TranslationAmplitudeY = 3;
        Motion.TranslationAmplitudeZ = 3;
        Motion.RotationAmplitude = 5;
        Motion.CorruptedSlicesRatio = 5/100;
    case 3  %strong motion
        Motion.TranslationAmplitudeX = 4;
        Motion.TranslationAmplitudeY = 4;
        Motion.TranslationAmplitudeZ = 4;
        Motion.RotationAmplitude = 8;
        Motion.CorruptedSlicesRatio = 5/100;
    case 4 %hyper motion
        Motion.TranslationAmplitudeX = 10;
        Motion.TranslationAmplitudeY = 10;
        Motion.TranslationAmplitudeZ = 10;
        Motion.RotationAmplitude = 45;
        Motion.CorruptedSlicesRatio = 5/100;
    case 5 % custom motion bounds
        Motion.TranslationAmplitudeX = varargin{1}{1};
        Motion.TranslationAmplitudeY = varargin{1}{2};
        Motion.TranslationAmplitudeZ = varargin{1}{3};
        Motion.RotationAmplitude = varargin{1}{4};
        Motion.CorruptedSlicesRatio = varargin{1}{5};
end
end