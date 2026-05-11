function plotEye(data, byTrial)
arguments
    data = [];
    byTrial logical = false;
end

if isempty(data) || ~isfield(data, 'signals') || ~isfield(data.signals, 'data')
    error('plotEye:MissingData', 'Input must contain signals.data');
end

numTrials = size(data.signals.data, 1);
y_labs = ["Horizontal Position" "Vertical Position" "Pupil"];

eventNames = {};
if isfield(data, 'times') && istable(data.times)
    preferred = {'fp_on', 'fix_acq', 'sample_on', 'fp_off', 'sac_on', 'all_off'};
    eventNames = preferred(ismember(preferred, data.times.Properties.VariableNames));
end

for tr = 1:numTrials
    if byTrial
        figure;
    end

    event_idxs = [];
    if byTrial && ~isempty(eventNames)
        event_idxs = nan(1, numel(eventNames));
        for i = 1:numel(eventNames)
            event_idxs(i) = getEventIndex(data, tr, eventNames{i});
        end
        event_idxs = event_idxs(isfinite(event_idxs));
    end

    for col = 1:min(3, size(data.signals.data, 2))
        subplot(3, 1, col);
        cur_eye_data = data.signals.data{tr, col};
        plot(cur_eye_data, 'LineWidth', 0.4);
        xlabel('Sample');
        ylabel(y_labs(col));
        if byTrial && ~isempty(event_idxs)
            xline(event_idxs, '--');
        else
            hold on;
        end
    end

    if byTrial
        sgtitle(sprintf('Trial %d', tr));
    end
end

if ~byTrial
    sgtitle('Eye data (all trials)');
end
end
