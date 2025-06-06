% Add Lab_Matlab_Utilities to Matlab path.
% https://github.com/TheGoldLab/Lab_Matlab_Utilities
%
% Add matlab/ subfolder of Pyramid to the Matlab path.
% https://github.com/benjamin-heasly/pyramid/tree/main/matlab

clear classes
close all
clear
clc

data_dir = '../';

%% Test some reading and conversion steps in isolation.

% disp('Reading trial file.')
% trial_file = TrialFile(trial_file_path);
% trials = trial_file.read()
% 
% disp('Converting to FIRA.')
% FIRA = convertTrialFileToFIRA(trials, trial_file_path)

%% Put it all together with AODR behavior figures.

disp('Plotting AODR behavior figures.')

% For pyramid converted files
% trial_file_path = '/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/MrM/Converted/Sorted/Pyramid/MM_2023_01_19_V-ProRec_Sorted-04.hdf5'; %fullfile(data_dir, 'aodr-test.hdf5');
trial_file_path ='/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/Anubis/Converted/Behavior/Pyramid/Anubis_2024-09-16_13-41-27.hdf5';
names = dir('/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/Anubis/Converted/Behavior/Pyramid/*.hdf5');
for fnum= 1:length(names)
    trial_file_path = '/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/MrM/tmp/MM_2023_01_19_V-ProRec_Sorted-04.hdf5'; %fullfile(names(fnum).folder, names(fnum).name);
    [pyramid_fits(:,fnum), pyramid_data(fnum)] = plotAODR_sessionBehavior( ...
        'filename', trial_file_path, ...
        'monkey', 'MrM', ...
        'convertSpecs', 'AODR_experiment_testing');
    % bias is just log((1-H)/H) -- see Glaze et al 2015
    sub_haz(fnum,:) = 1./(1+exp(-pyramid_fits(1:2, fnum)));
end



% For plx files to convert with FIRA
plx_file_path = '/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/MrM/Sorted/MM_2023_01_19_V-ProRec_Sorted-04.plx';


% plx file converted with pyramid
plx_pyramid_out = '/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/MrM/Converted/Sorted/Pyramid/MM_2023_01_19_V-ProRec_Sorted-04.hdf5';
% plx_pyramid_out = '/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/MrM/tmp/MM_2023_01_19_V-ProRec_Sorted-04.hdf5'; %'/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/MrM/Converted/Sorted/Pyramid/MM_2023_01_19_V-ProRec_Sorted-04.hdf5';
[plx_fits, plx_data] = plotAODR_sessionBehavior( ...
    'filename', plx_pyramid_out, ...
    'monkey', 'MrM', ...
    'convertSpecs', 'spmAODR');



% Can files converted with the proceed pipeline (some weird combination of
% pyramid and phy) be converted into this dataSession format?
proc_file_path = '/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/MrM/Converted/Sorted/MM_2023_01_19_CV-ProRec_Sorted-01.mat';
[proceed_fit, proceed_data] = plotAODR_sessionBehavior( ...
        'filename', proc_file_path, ...
        'monkey', 'MrM', ...
        'converter', 'FIRA', ...
        'convertSpecs', 'spmAODR',...
        'forceConvert',false);

% Anubis example behavior
trial_file_path =  '/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/Anubis/Converted/Behavior/Pyramid/Anubis_2024-11-21_12-48-59.hdf5';
[pyramid_fits, pyramid_data] = plotAODR_sessionBehavior( ...
        'filename', trial_file_path, ...
        'monkey', 'Anubis',...
        'forceConvert',false);