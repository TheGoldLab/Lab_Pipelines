% Add Lab_Matlab_Utilities to Matlab path.
% https://github.com/TheGoldLab/Lab_Matlab_Utilities
%
% Add matlab/ subfolder of Pyramid to the Matlab path.
% https://github.com/benjamin-heasly/pyramid/tree/main/matlab


close all
clear
clc

data_dir = '../';
trial_file_path = fullfile(data_dir, 'aodr-test.hdf5');


%% Test some reading and conversion steps in isolation.

disp('Reading trial file.')
trial_file = TrialFile(trial_file_path);
trials = trial_file.read()

disp('Converting to FIRA.')
FIRA = convertTrialFileToFIRA(trials, trial_file_path)


%% Plot some eye data.

disp('Plotting gaze from trial file.')

figure; hold on;
for ii = 1:length(trials)
    gazeX = trials(ii).signals.gaze.signal_data(:,1);
    gazeY = trials(ii).signals.gaze.signal_data(:,2);

    subplot(1,3,1); hold on;
    plot(gazeX)
    subplot(1,3,2); hold on;
    plot(gazeY)
    subplot(1,3,3); hold on;
    plot(gazeX, gazeY)
end


%% Put it all together with AODR behavior figures.

disp('Plotting AODR behavior figures.')

plotAODR_sessionBehavior( ...
    'filename', trial_file_path, ...
    'monkey', 'Anubis', ...
    'convertSpecs', 'AODR_experiment_testing')
