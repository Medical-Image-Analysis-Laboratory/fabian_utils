function [Orientation] = set_orientation(FetalBrainModelPath, FetalModel, SubID, Orientation)

% Quick fix to FaBIAN to be able to do simulation on FETA_CHUV atlas. With
% manual orientation initialization, reorient_volume can fail.

% Load segmented high-resolution anatomical MR images of the fetal brain at
% gestational age GA
[FetalBrain, ModelNiiinfo] = brain_model(FetalBrainModelPath,FetalModel,SubID);

% Read the resolution of the 3D anatomical model
SimRes = ModelNiiinfo.PixelDimensions;

% Axis direction codes for the affine orientation matrix of the anatomical
% model of the fetal brain
Affine = ModelNiiinfo.Transform.T';
ModelAxcodes = aff2axcodes(Affine);

orient_bool = [false, false, false];
for orient=1:3
    % The slice thickness direction will be encoded in the 3. dimension
    switch orient
        case 1  %sagittal: slice thickness L-R
            SliceDir_idx = find(ismember(ModelAxcodes, ["R","L"]));
            InPlane_idx = find(ismember(ModelAxcodes, ["A","P","S","I"]));
        case 2  %coronal: slice thickness A-P
            SliceDir_idx = find(ismember(ModelAxcodes, ["A","P"]));
            InPlane_idx = find(ismember(ModelAxcodes, ["R","L","S","I"]));
        case 3  %axial: slice thickness S-I
            SliceDir_idx = find(ismember(ModelAxcodes, ["S","I"]));
            InPlane_idx = find(ismember(ModelAxcodes, ["R","L","A","P"]));
    end
    AxcodesReo = ModelAxcodes([InPlane_idx SliceDir_idx]);
    
    % Reorient the original 3D anatomical model of the fetal brain so that the
    % slice thickness direction is encoded in the 3. dimension
    [~, AffineReo, ~] = reorient_volume(FetalBrain,Affine,SimRes,AxcodesReo);

    if all(ismember(aff2axcodes(Affine), aff2axcodes(AffineReo)))
        orient_bool(orient) = true; 
    end
end

if orient_bool(Orientation)
    disp('Initial Orientation compatible with FetalModel.');
elseif any(orient_bool)
    % Find the indices where the boolean vector is true
    trueIndices = find(orient_bool);
    Orientation = trueIndices(randi(length(trueIndices)));
    disp(['Initial Orientation not compatible with FetalModel modified to :', sprintf('%01d',Orientation)]);
    clear trueIndices
else
    error('ERROR: FetalModel not compatible with any possible simulation orientation. Simulation is skipped.');
end

end