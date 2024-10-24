function [Background] = set_backgroundproperties(background, varargin)
% SET_BACKGROUND set the T2 values of the background based on json_file
% available in subject atlas

Background = struct('Background', background, ...
                        'T1_BG1', 0,... 
                        'T1_BG2', 0,... 
                        'T1_BG3', 0,...
                        'T2_BG1', 0,... 
                        'T2_BG2', 0,... 
                        'T2_BG3', 0);
if background
    Background.T1_BG1 = varargin{1};
    Background.T1_BG2 = varargin{2};
    Background.T1_BG3 = varargin{3}; 
    Background.T2_BG1 = varargin{4};
    Background.T2_BG2 = varargin{5};
    Background.T2_BG3 = varargin{6};
end
end