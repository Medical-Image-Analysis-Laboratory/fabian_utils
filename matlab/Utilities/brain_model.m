%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%  Function that reads the segmented high-resolution anatomical MR        %
%  images of the fetal brain from which the simulated images will be      %
%  derived at a given gestational age (GA).                               %
%  Here, we consider segmented high-resolution images from Gholipour, A.  %
%  et al. A normative spatiotemporal MRI atlas of the fetal brain for     %
%  automatic segmentation and analysis of early brain growth. Scientific  %
%  Reports 7, 476 (2017). https://doi.org/10.1038/s41598-017-00525-w      %
%                                                                         %
%                   Fetal_Brain = brain_model(path, GA);                  %
%                                                                         %
%  inputs:  - path: folder where the segmented high-resolution MR images  %
%                   of the fetal brain from which our simulations are     %
%                   derived are stored                                    %
%           - GA: gestational age of the fetus (in weeks)                 %
%                                                                         %
%  output:  - Fetal_Brain: segmented high-resolution 3D volume of the     %
%                          fetal brain at gestational age GA              %
%                                                                         %
%                                                                         %
%  Hélène Lajous, 2021-04-30                                              %
%  helene.lajous@unil.ch                                                  %
%                                                                         %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


function [Fetal_Brain, nifti_info] = brain_model(  path, ...
                                                  model, ...
                                                 sub_id)

% Input check
if nargin < 3
    error('Missing input(s).');
elseif nargin > 3
    error('Too many inputs.');
end

% Load segmented high-resolution anatomical MR images of the fetal brain at
% gestational age GA
switch model
    case 'STA'
        nifti_info = niftiinfo(strcat(path, 'STA', sprintf('%02s', num2str(sub_id)), '_tissue.nii.gz'));
        Fetal_Brain = niftiread(nifti_info);
    case 'FeTA_CHUV'
        nifti_info = niftiinfo(strcat(path, sub_id, '/anat/', sub_id, '_rec-mial_dseg.nii.gz'));
        Fetal_Brain = niftiread(nifti_info);
    case 'FeTA'
        nifti_info = niftiinfo(strcat(path, sub_id, '/parcellation.nii.gz'));
        Fetal_Brain = niftiread(nifti_info);
    case 'Custom'
        % note finalized: here path = path to the STA directory ./STA/STAXX
        atlas_id = strsplit(path,'/');
        fprintf(strcat(path,atlas_id{end-1}, '_tissue.nii.gz'));
        nifti_info = niftiinfo(strcat(path,atlas_id{end-1}, '_tissue.nii.gz'));
        Fetal_Brain = niftiread(nifti_info);
        clear atlas_id
end

end