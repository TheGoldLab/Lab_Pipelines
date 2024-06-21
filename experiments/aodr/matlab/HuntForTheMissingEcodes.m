function HuntForTheMissingEcodes

data_dir = '../';
trial_file_path = fullfile(data_dir, 'aodr-test.hdf5');

disp('Reading trial file.')
trial_file = TrialFile(trial_file_path);
trials = trial_file.read();

%%

% Trials w/task event value: 263 – what’s causing this?
% trial.numeric_events.task_id
has.task_id = has_numeric_event(trials, 'task_id');

% Trials w/Hazard event ID: 280  - equally strange
% trial.numeric_events.hazard
has.hazard = has_numeric_event(trials, 'hazard');

% Trials w/Targ 1 probability value: 281 – equally strange
% trial.numeric_events.prob_tp1
has.prob_tp1 = has_numeric_event(trials, 'prob_tp1');

% Trials w/Targ 2 probability value: 282 – equally strange
% trial.numeric_events.prob_tp2
has.prob_tp2 = has_numeric_event(trials, 'prob_tp2');

% Trials w/sample ID: 263
% trial.enhancements.sample_id
has.sample_id = has_enhancement(trials, 'sample_id');

% Trials w/sample X value: 316
% trial.numeric_events.sample_x
has.sample_x = has_numeric_event(trials, 'sample_x');

% Trials w/sample Y value: 319
% trial.numeric_events.sample_y
has.sample_y = has_numeric_event(trials, 'sample_y');

% Trials w/sample_on time: 381 (doesn’t mean he completed the trial)
% trial.numeric_events.sample_on
has.sample_on = has_numeric_event(trials, 'sample_on');

%%

has_names = fieldnames(has);
for ff = 1:numel(has_names)
    name = has_names{ff};
    trials = find(has.(name));
    rows = ff * ones(size(trials));
    line(trials, rows, 'Marker', '|', 'LineStyle', 'none');
end
set(gca(), 'TickLabelInterpreter', 'none');
yticklabels(has_names);
ylim([0, numel(has_names) + 1]);

%%

function has_it = has_numeric_event(trials, name)
trial_count = numel(trials);
has_it = false([1, trial_count]);
for tt = 1:trial_count
    has_it(tt) = isfield(trials(tt).numeric_events, name);
end

function has_it = has_enhancement(trials, name)
trial_count = numel(trials);
has_it = false([1, trial_count]);
for tt = 1:trial_count
    has_it(tt) = isfield(trials(tt).enhancements, name);
end
