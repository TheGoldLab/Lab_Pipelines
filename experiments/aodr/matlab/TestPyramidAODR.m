clear
clc

%% Read a trial file into Matlab using the Pyramid TrialFile util. class.
data_dir = '../';
data_file = fullfile(data_dir, 'aodr-test.hdf5');
trial_file = TrialFile(data_file);
trials = trial_file.read()

%% Convert the trial file to FIRA format.
FIRA = convertTrialFileToFIRA(trials, data_file, {}, {'matlab_time', 'ttl'})
