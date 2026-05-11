function raster(session, unit_index, event, time_before, time_after, example_trial, ax)
arguments
    session = [];
    unit_index = 1;
    event = [];
    time_before = 200;
    time_after = 500;
    example_trial = [];
    ax = [];
end

if isempty(ax)
    figure;
    ax = gca;
end
hold(ax, 'off');

if isfield(session, 'spike_time_mat') && ~isempty(session.spike_time_mat)
    spike_times = session.spike_time_mat;
    if ndims(spike_times) ~= 3
        text(ax, 0.1, 0.5, 'Unsupported spike_time_mat shape', 'Units', 'normalized');
        return
    end

    num_units = size(spike_times, 1);
    num_time_steps = size(spike_times, 2);
    num_trials = size(spike_times, 3);
    if unit_index < 1 || unit_index > num_units
        text(ax, 0.1, 0.5, 'Unit index out of range', 'Units', 'normalized');
        return
    end

    event_times = getEventTimesMs(session, event, num_trials);

    for trial = 1:num_trials
        if isempty(event)
            plot_spikes = true(1, num_time_steps);
        else
            plot_spikes = spike_times(unit_index, :, trial) >= (event_times(trial) - time_before) & ...
                spike_times(unit_index, :, trial) <= (event_times(trial) + time_after);
        end

        if any(plot_spikes)
            yaxis = ones(1, sum(plot_spikes)) * trial;
            xvals = spike_times(unit_index, plot_spikes, trial) - event_times(trial);
            if ~isempty(example_trial) && trial == example_trial
                scatter(ax, xvals, yaxis, 8, 'r', 'filled');
            else
                scatter(ax, xvals, yaxis, 3, 'k', 'filled');
            end
            hold(ax, 'on');
        end
    end
else
    if ~isfield(session, 'spikes') || ~isstruct(session.spikes) || ~isfield(session.spikes, 'data') || isempty(session.spikes.data)
        text(ax, 0.1, 0.5, 'Missing neural data: spike_time_mat or spikes.data', 'Units', 'normalized');
        return
    end

    spikesByTrialUnit = session.spikes.data;
    if istable(spikesByTrialUnit)
        spikesByTrialUnit = table2cell(spikesByTrialUnit);
    end
    if ~iscell(spikesByTrialUnit)
        text(ax, 0.1, 0.5, 'Unsupported spikes.data format', 'Units', 'normalized');
        return
    end

    [num_trials, num_units] = size(spikesByTrialUnit);
    if unit_index < 1 || unit_index > num_units
        text(ax, 0.1, 0.5, 'Unit index out of range', 'Units', 'normalized');
        return
    end

    event_times = getEventTimesMs(session, event, num_trials);

    for trial = 1:num_trials
        trialSpikes = spikesByTrialUnit{trial, unit_index};
        if isempty(trialSpikes)
            continue
        end
        trialSpikes = trialSpikes(:);
        trialSpikes = trialSpikes(isfinite(trialSpikes));
        if isempty(trialSpikes)
            continue
        end

        trialSpikes = normalizeSpikeUnits(trialSpikes, event_times(trial));

        if isempty(event)
            xvals = trialSpikes;
        else
            keep = trialSpikes >= (event_times(trial) - time_before) & ...
                trialSpikes <= (event_times(trial) + time_after);
            xvals = trialSpikes(keep) - event_times(trial);
        end

        if ~isempty(xvals)
            yaxis = ones(size(xvals)) * trial;
            if ~isempty(example_trial) && trial == example_trial
                scatter(ax, xvals, yaxis, 8, 'r', 'filled');
            else
                scatter(ax, xvals, yaxis, 3, 'k', 'filled');
            end
            hold(ax, 'on');
        end
    end
end

if ~isempty(event)
    eventLabel = event;
    if isstring(eventLabel) || ischar(eventLabel)
        eventLabel = strrep(char(eventLabel), '_', ' ');
    end
    hline = xline(ax, 0, '--', eventLabel);
    hline.Color = [1 0 0];
    hline.LineWidth = 3;
    hline.LineStyle = '--';
    xlim(ax, [-time_before, time_after]);
end
end

function event_times = getEventTimesMs(session, event, num_trials)
event_times = zeros(num_trials, 1);
if ~isempty(event) && isfield(session, 'times') && istable(session.times) && ...
        ismember(event, session.times.Properties.VariableNames)
    event_times = session.times.(event);
    event_times = event_times(:);
    if numel(event_times) < num_trials
        event_times(end+1:num_trials) = 0;
    end
    event_times = event_times(1:num_trials) * 1000;
end
end

function spikesMs = normalizeSpikeUnits(spikes, eventTimeMs)
spikesMs = spikes;
maxAbsSpike = max(abs(spikesMs));

if eventTimeMs > 0 && maxAbsSpike < (eventTimeMs / 10)
    spikesMs = spikesMs * 1000;
elseif maxAbsSpike < 100
    spikesMs = spikesMs * 1000;
end
end
