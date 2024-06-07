% Adapted from the oe-matlab-tools repository by LWT to read session data
% from a 16 channel RHD headstage
% LWT: 2/26/30
save_file = 1;
basedir = '/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Recordings/Testing/';
tag = 'AODR';
converter = 'Pyramid';
monkey = 'Anubis';
daq_sample_rate = 1000; % Hz
oe_sample_rate = 30000; % Hz

% For NWB
filename = fullfile(basedir,'Anubis_2024-03-27_13-36-24');
trial_file = '/Users/lowell/Data/Physiology/AODR/Data/Anubis/Converted/Unsorted/Pyramid/OE_Test_Pyramid_Out.hdf5';

%% Convert data from a single session, using Pyramid python hybrid (default: debugging extremely limited)
% fprintf('\nConverting files using pyramid...\n');
% [data, obj] = goldLabDataSession.convertSession(trial_file, ...
%     'tag',          tag, ...
%     'monkey',       monkey, ...
%     'forceConvert', true, ...
%     'convertSpecs', 'AODR_test_nwb_experiment', ...
%     'matlabFormat', 'dataSession',...
%     'sortType',     'Unsorted', ...
%     'delimiter_fname',    filename,...
%     'gaze_x_fname', filename,...
%     'gaze_y_fname', filename);
% 
% if save_file
%     fprintf('\nSaving converted session: %s\n', obj.convertedFilename)
%     obj.save(data);
% end

%% Show latest data file converted using FIRA
plotAODR_sessionBehavior( ...
        'filename', trial_file,...
        'convertSpecs','AODR_test_nwb_experiment')


%% Get basic delimited file:
trialFile = TrialFile(trial_file);
trials = trialFile.read();
%% Plot some eye data
figure; hold on;
for ith_trial = 1:length(trials)
    subplot(1,3,1); hold on;
    plot(trials(ith_trial).signals.gaze_x.signal_data(:))
    subplot(1,3,2); hold on;
    plot(trials(ith_trial).signals.gaze_y.signal_data(:))
    subplot(1,3,3); hold on;
    plot(trials(ith_trial).signals.gaze_x.signal_data(:), trials(ith_trial).signals.gaze_y.signal_data(:))
end