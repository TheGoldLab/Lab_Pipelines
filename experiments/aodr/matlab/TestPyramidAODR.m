% Add Lab_Matlab_Utilities to Matlab path.
% https://github.com/TheGoldLab/Lab_Matlab_Utilities

clear
clc

data_dir = '../';
trial_file_path = fullfile(data_dir, 'aodr-test.hdf5');

%% Test some reading and conversion steps in isolation.

% disp('Reading trial file.')
% trial_file = TrialFile(trial_file_path);
% trials = trial_file.read()
%
% disp('Converting to FIRA and plotting.')
% FIRA = convertTrialFileToFIRA(trials, trial_file_path, {}, {'matlab_time', 'ttl'})


%% Put it all together and plot something.

% task_id is coming as a "value" rather than an "id".
% Pyramid could fix this.
%   - rename enhancement_categories to just "categories"
%   - use this to annotate buffers as well as enhancements.
%   - RenameRescale enhancer add categories from CSV to this.
%   - Annoying, but possible, to rummage around in existing categories.
%   - convertTrialFileToFIRA check categories for numeric event ecodes.

% For the moment, I changed the local plotAODR_sessionBehavior to look at
% data.values.task_id instead of data.ids.task_id

plotAODR_sessionBehavior( ...
    'filename', trial_file_path, ...
    'monkey', 'Anubis', ...
    'convertSpecs', 'AODR_experiment_testing')
