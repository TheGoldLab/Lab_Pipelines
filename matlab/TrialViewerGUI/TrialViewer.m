classdef TrialViewer < matlab.apps.AppBase

    properties (Access = public)
        UIFigure                     matlab.ui.Figure
        GridLayout                   matlab.ui.container.GridLayout
        LeftPanel                    matlab.ui.container.Panel
        RewardedLamp_2               matlab.ui.control.Lamp
        RewardedLampLabel_2          matlab.ui.control.Label
        TrialNumberSpinner           matlab.ui.control.Spinner
        TrialNumberSpinnerLabel      matlab.ui.control.Label
        RewardedLamp                 matlab.ui.control.Lamp
        RewardedLampLabel            matlab.ui.control.Label
        CompletedLamp                matlab.ui.control.Lamp
        CompletedLampLabel           matlab.ui.control.Label
        RightPanel                   matlab.ui.container.Panel
        TabGroup                     matlab.ui.container.TabGroup
        AnalogDigitalTab             matlab.ui.container.Tab
        UIAxes_3                     matlab.ui.control.UIAxes
        UIAxes_2                     matlab.ui.control.UIAxes
        UIAxes                       matlab.ui.control.UIAxes
        NeuralTab                    matlab.ui.container.Tab
        AftermsEditField             matlab.ui.control.NumericEditField
        AftermsEditFieldLabel        matlab.ui.control.Label
        BeforemsEditField            matlab.ui.control.NumericEditField
        BeforemsEditFieldLabel       matlab.ui.control.Label
        EventAlignmentDropDown            matlab.ui.control.DropDown
        EventAlignmentDropDownLabel       matlab.ui.control.Label
        AnalogEventAlignmentDropDown      matlab.ui.control.DropDown
        AnalogEventAlignmentDropDownLabel matlab.ui.control.Label
        AnalogBeforemsEditField           matlab.ui.control.NumericEditField
        AnalogBeforemsEditFieldLabel      matlab.ui.control.Label
        AnalogAftermsEditField            matlab.ui.control.NumericEditField
        AnalogAftermsEditFieldLabel       matlab.ui.control.Label
        UnitDropDown                      matlab.ui.control.DropDown
        UnitDropDownLabel            matlab.ui.control.Label
        RasterAxes                   matlab.ui.control.UIAxes
    end

    properties (Access = private)
        onePanelWidth = 576;
        data
    end

    methods (Access = private)

        function data = localPrepareTrialViewerData(app, data)
            if ~isstruct(data)
                error('TrialViewer:InvalidInput', 'Input must be a struct.');
            end
            if ~isfield(data, 'times') || ~istable(data.times)
                error('TrialViewer:MissingTimes', 'Input must include table field: times.');
            end

            data.times = app.localNormalizeTimesTable(data.times);
            nTrials = height(data.times);

            requiredEvents = {'fp_on', 'fix_acq', 'sample_on', 'fp_off', 'sac_on', 'all_off', 'trial_start'};
            for ii = 1:numel(requiredEvents)
                evName = requiredEvents{ii};
                if ~ismember(evName, data.times.Properties.VariableNames)
                    data.times.(evName) = nan(nTrials, 1);
                end
            end

            if ~isfield(data, 'ids') || ~isstruct(data.ids)
                data.ids = struct();
            end
            if ~isfield(data, 'values') || ~isstruct(data.values)
                data.values = struct();
            end
            if ~isfield(data, 'header') || ~isstruct(data.header)
                data.header = struct();
            end

            if ~isfield(data.header, 'validTrials') || isempty(data.header.validTrials)
                data.header.validTrials = nTrials;
            end
            if ~isfield(data.ids, 'choice') || isempty(data.ids.choice)
                data.ids.choice = nan(nTrials, 1);
            end
            if ~isfield(data.ids, 'score') || isempty(data.ids.score)
                data.ids.score = nan(nTrials, 1);
            end
            if ~isfield(data.values, 'online_score') || isempty(data.values.online_score)
                data.values.online_score = nan(nTrials, 1);
            end
            if ~isfield(data.values, 'hazard') || isempty(data.values.hazard)
                data.values.hazard = nan(nTrials, 1);
            end

            if ~isfield(data, 'dio') || isempty(data.dio)
                data.dio = repmat(struct('line_num', [], 'state', [], 'timestamp', []), nTrials, 1);
            end

            if ~isfield(data, 'spikes') || ~isstruct(data.spikes)
                data.spikes = struct();
            end
            if ~isfield(data.spikes, 'id') || isempty(data.spikes.id)
                data.spikes.id = [];
            end
        end

        function times = localNormalizeTimesTable(app, times)
            if isempty(times)
                return
            end
            varNames = times.Properties.VariableNames;
            for vv = 1:numel(varNames)
                values = times.(varNames{vv});
                if isnumeric(values) && isvector(values)
                    values = values(:);
                    values(~isfinite(values)) = nan;
                    times.(varNames{vv}) = values;
                    continue
                end

                normalized = nan(height(times), 1);
                for rr = 1:height(times)
                    normalized(rr) = app.localScalarOrNaN(values(rr));
                end
                times.(varNames{vv}) = normalized;
            end
        end

        function value = localScalarOrNaN(~, raw)
            value = nan;

            if istable(raw)
                if isempty(raw)
                    return
                end
                raw = raw{1, 1};
            end

            if iscell(raw)
                if isempty(raw)
                    return
                end
                raw = raw{1};
            end

            if ischar(raw) || isstring(raw)
                raw = str2double(string(raw));
            end

            if ~isnumeric(raw) || isempty(raw)
                return
            end

            flat = raw(:);
            flat = flat(isfinite(flat));
            if isempty(flat)
                return
            end
            value = flat(1);
        end

        function trialCount = getNumTrials(app)
            trialCount = 1;
            if isfield(app.data, 'header') && isstruct(app.data.header) && isfield(app.data.header, 'validTrials')
                trialCount = max(1, app.data.header.validTrials);
                return
            end
            if isfield(app.data, 'times') && istable(app.data.times)
                trialCount = max(1, height(app.data.times));
                return
            end
            if isfield(app.data, 'signals') && isfield(app.data.signals, 'data')
                trialCount = max(1, size(app.data.signals.data, 1));
            end
        end

        function hasNeural = canPlotNeural(app)
            hasSpikeMat = isfield(app.data, 'spike_time_mat') && ~isempty(app.data.spike_time_mat);
            hasSpikeTable = isfield(app.data, 'spikes') && isstruct(app.data.spikes) ...
                && isfield(app.data.spikes, 'data') && ~isempty(app.data.spikes.data);
            hasIds = isfield(app.data, 'spikes') && isstruct(app.data.spikes) ...
                && isfield(app.data.spikes, 'id') && ~isempty(app.data.spikes.id);
            hasNeural = hasIds && (hasSpikeMat || hasSpikeTable);
        end

        function names = getAvailableEvents(app)
            names = {};
            if isfield(app.data, 'times') && istable(app.data.times)
                names = app.data.times.Properties.VariableNames;
            end
        end

        function [eventNames, eventLabels] = getEyeEventSpec(app)
            preferred = {'fp_on', 'fix_acq', 'sample_on', 'fp_off', 'sac_on', 'all_off';
                'trial_start', 'fix_acq', 'sample_on', 'fp_off', 'sac_on', 'all_off'};
            preferredLabels = {'Fix On', 'Fix Acq', 'Sample On', 'Fix Off', 'Saccade On', 'All Off';
                'Trial Start', 'Fix Acq', 'Sample On', 'Fix Off', 'Saccade On', 'All Off'};

            allNames = app.getAvailableEvents();
            if isempty(allNames)
                eventNames = {};
                eventLabels = {};
                return
            end

            for idx = 1:size(preferred, 1)
                row = preferred(idx, :);
                keep = ismember(row, allNames);
                if any(keep)
                    eventNames = row(keep);
                    eventLabels = preferredLabels(idx, keep);
                    return
                end
            end

            maxEvents = min(6, numel(allNames));
            eventNames = allNames(1:maxEvents);
            eventLabels = allNames(1:maxEvents);
        end

        function [resolvedEvent, resolvedIdx, notice] = resolveAlignmentEvent(app, tr, requestedEvent, fallbackCandidates, noneToken)
            if nargin < 4 || isempty(fallbackCandidates)
                fallbackCandidates = app.getAvailableEvents();
            end
            if nargin < 5
                noneToken = '';
            end

            resolvedEvent = '';
            resolvedIdx = NaN;
            notice = '';

            if isempty(requestedEvent)
                return
            end
            if ~isempty(noneToken) && strcmp(requestedEvent, noneToken)
                return
            end

            requestedIdx = getEventIndex(app.data, tr, requestedEvent);
            if isfinite(requestedIdx) && requestedIdx > 0
                resolvedEvent = requestedEvent;
                resolvedIdx = requestedIdx;
                return
            end

            availableEvents = app.getAvailableEvents();
            filteredFallback = {};
            for ii = 1:numel(fallbackCandidates)
                candidate = fallbackCandidates{ii};
                if isempty(candidate)
                    continue
                end
                if strcmp(candidate, noneToken)
                    continue
                end
                if ~ismember(candidate, availableEvents)
                    continue
                end
                if any(strcmp(filteredFallback, candidate))
                    continue
                end
                filteredFallback{end+1} = candidate; %#ok<AGROW>
            end

            for ii = 1:numel(filteredFallback)
                candidate = filteredFallback{ii};
                candidateIdx = getEventIndex(app.data, tr, candidate);
                if isfinite(candidateIdx) && candidateIdx > 0
                    resolvedEvent = candidate;
                    resolvedIdx = candidateIdx;
                    notice = sprintf('Selected event "%s" not detected. Using "%s".', requestedEvent, resolvedEvent);
                    return
                end
            end

            notice = sprintf('Selected event "%s" not detected. No fallback event found; using default window.', requestedEvent);
        end

        function showAlignmentNotice(~, ax, notice)
            if isempty(notice)
                return
            end
            hold(ax, 'on');
            text(ax, 0.01, 0.98, notice, ...
                'Units', 'normalized', ...
                'VerticalAlignment', 'top', ...
                'HorizontalAlignment', 'left', ...
                'Color', [0.85 0.33 0.10], ...
                'FontSize', 10, ...
                'FontWeight', 'bold', ...
                'Interpreter', 'none');
            hold(ax, 'off');
        end

        function value = tryGetNestedField(~, source, parentField, childField, defaultValue)
            value = defaultValue;
            if ~isfield(source, parentField)
                return
            end
            parent = source.(parentField);
            if ~isstruct(parent) || ~isfield(parent, childField)
                return
            end
            value = parent.(childField);
        end

        function values = getTrialVector(app, parentField, childField, defaultValue)
            nTrials = app.getNumTrials();
            values = defaultValue .* ones(nTrials, 1);
            value = app.tryGetNestedField(app.data, parentField, childField, []);
            if isempty(value)
                return
            end
            value = value(:);
            n = min(nTrials, numel(value));
            values(1:n) = value(1:n);
        end

        function score = getOfflineScore(app)
            score = app.getTrialVector('ids', 'score', NaN);
            if all(isnan(score))
                score = app.getTrialVector('values', 'online_score', NaN);
            end
        end

        function choice = getChoice(app)
            choice = app.getTrialVector('ids', 'choice', NaN);
            if all(isnan(choice))
                score = app.getOfflineScore();
                choice(~isnan(score)) = 1;
            end
        end

        function hazard = getHazard(app)
            hazard = app.getTrialVector('values', 'hazard', NaN);
        end

        function color = getTrialColor(app, tr)
            color = 'k';
            hazard = app.getHazard();
            if tr > numel(hazard) || isnan(hazard(tr))
                return
            end
            if abs(hazard(tr) - 0.05) < 1e-9
                color = [4 94 167] ./ 255;
            elseif abs(hazard(tr) - 0.50) < 1e-9
                color = [194 0 77] ./ 255;
            end
        end

        function updateStatusLamps(app, tr)
            choice = app.getChoice();
            if tr <= numel(choice) && ~isnan(choice(tr))
                app.CompletedLamp.Color = [0 1 0];
            else
                app.CompletedLamp.Color = [1 0 0];
            end

            score = app.getOfflineScore();
            if tr <= numel(score)
                if score(tr) < 0
                    app.RewardedLamp.Color = [1 1 0];
                elseif score(tr) == 0
                    app.RewardedLamp.Color = [1 0 0];
                elseif score(tr) == 1
                    app.RewardedLamp.Color = [0 1 0];
                else
                    app.RewardedLamp.Color = [0.7 0.7 0.7];
                end
            end

            % Check for online_correct/online_error event timestamps first
            hasCorrectCol = isfield(app.data, 'times') && istable(app.data.times) && ...
                ismember('online_correct', app.data.times.Properties.VariableNames);
            hasErrorCol = isfield(app.data, 'times') && istable(app.data.times) && ...
                ismember('online_error', app.data.times.Properties.VariableNames);
            if hasCorrectCol || hasErrorCol
                isCorrect = hasCorrectCol && tr <= height(app.data.times) && ...
                    isfinite(app.data.times.online_correct(tr));
                isError = hasErrorCol && tr <= height(app.data.times) && ...
                    isfinite(app.data.times.online_error(tr));
                if isCorrect
                    app.RewardedLamp_2.Color = [0 1 0];
                elseif isError
                    app.RewardedLamp_2.Color = [1 0 0];
                else
                    app.RewardedLamp_2.Color = [0.7 0.7 0.7];
                end
            else
                rexScore = app.getTrialVector('values', 'online_score', NaN);
                if tr <= numel(rexScore)
                    if rexScore(tr) < 0
                        app.RewardedLamp_2.Color = [1 0 0];
                    elseif rexScore(tr) == 0
                        app.RewardedLamp_2.Color = [1 1 0];
                    elseif rexScore(tr) == 1
                        app.RewardedLamp_2.Color = [0 1 0];
                    else
                        app.RewardedLamp_2.Color = [0.7 0.7 0.7];
                    end
                end
            end
        end

        function plotAllEye(app, ~)
            tr = app.TrialNumberSpinner.Value;

            if ~isfield(app.data, 'signals') || ~isfield(app.data.signals, 'data') || isempty(app.data.signals.data)
                cla(app.UIAxes); cla(app.UIAxes_2); cla(app.UIAxes_3);
                updateStatusLamps(app, tr);
                return
            end

            sampleRate = 1;
            if isfield(app.data.signals, 'sampleRates') && ~isempty(app.data.signals.sampleRates)
                sampleRate = app.data.signals.sampleRates(1);
            end

            x_data = app.localSignalVector(app.data.signals.data{tr, 1});
            y_data = app.localSignalVector(app.data.signals.data{tr, 2});
            hasPupil = size(app.data.signals.data, 2) >= 3;
            if hasPupil
                p_data = app.localSignalVector(app.data.signals.data{tr, 3});
            else
                p_data = [];
            end

            xLen = numel(x_data);
            yLen = numel(y_data);
            if xLen == 0 && yLen == 0
                cla(app.UIAxes);
                msg = sprintf('Trial %d: no x/y data', tr);
                text(app.UIAxes, 0.1, 0.5, msg, 'Units', 'normalized');
                fprintf('[TrialViewer] %s\n', msg);
                cla(app.UIAxes_2);
                text(app.UIAxes_2, 0.1, 0.5, 'No pupil channel found', 'Units', 'normalized');
                cla(app.UIAxes_3);
                text(app.UIAxes_3, 0.1, 0.5, 'No DIO events available', 'Units', 'normalized');
                updateStatusLamps(app, tr);
                return
            elseif xLen == 0
                msg = sprintf('Trial %d: missing x analog data (y length=%d)', tr, yLen);
                fprintf('[TrialViewer] %s\n', msg);
                minLenXY = yLen;
            elseif yLen == 0
                msg = sprintf('Trial %d: missing y analog data (x length=%d)', tr, xLen);
                fprintf('[TrialViewer] %s\n', msg);
                minLenXY = xLen;
            else
                minLenXY = min([xLen, yLen]);
            end

            % Collect all eye-event markers
            [evtNames, evtLabels] = app.getEyeEventSpec();
            all_event_idxs = [];
            all_event_labels = {};
            if ~isempty(evtNames)
                all_event_idxs = nan(1, numel(evtNames));
                for i = 1:numel(evtNames)
                    all_event_idxs(i) = getEventIndex(app.data, tr, evtNames{i});
                end
                keep = isfinite(all_event_idxs) & all_event_idxs >= 1 & all_event_idxs <= minLenXY;
                all_event_idxs = all_event_idxs(keep);
                all_event_labels = evtLabels(keep);
            end

            % Determine time window and offset from alignment dropdown
            align_event = app.AnalogEventAlignmentDropDown.Value;
            before_ms = app.AnalogBeforemsEditField.Value;
            after_ms = app.AnalogAftermsEditField.Value;
            fallbackCandidates = [{'trial_start'}, evtNames, app.getAvailableEvents()];
            [~, alignIdx, alignNotice] = app.resolveAlignmentEvent(...
                tr, align_event, fallbackCandidates, '(none)');

            if isfinite(alignIdx) && alignIdx >= 1 && alignIdx <= minLenXY
                before_samp = round(before_ms / 1000 * sampleRate);
                after_samp  = round(after_ms  / 1000 * sampleRate);
                idxStart    = max(1, round(alignIdx) - before_samp);
                idxEnd      = min(minLenXY, round(alignIdx) + after_samp);
                timeOffset  = alignIdx / sampleRate;
                timeScale   = 1000;
                timeUnits   = 'ms';
            else
                if ~isempty(all_event_idxs)
                    idxStart = max(1, floor(min(all_event_idxs)));
                    idxEnd   = min(minLenXY, ceil(max(all_event_idxs)));
                else
                    idxStart = 1;
                    idxEnd   = minLenXY;
                end
                if idxEnd < idxStart
                    idxStart = 1; idxEnd = minLenXY;
                end
                timeOffset = 0;
                timeScale  = 1;
                timeUnits  = 's';
            end

            samplenums = idxStart:idxEnd;
            lineColor  = app.getTrialColor(tr);

            % Convert event indices to display time coordinates
            if ~isempty(all_event_idxs)
                ev_times_disp = (all_event_idxs ./ sampleRate - timeOffset) .* timeScale;
            else
                ev_times_disp = [];
            end

            % --- XY Eye position ---
            cla(app.UIAxes);
            hold(app.UIAxes, 'on');
            plottedXY = false;
            if ~isempty(x_data)
                xSamp = samplenums(samplenums <= numel(x_data));
                plot(app.UIAxes, (xSamp ./ sampleRate - timeOffset) .* timeScale, x_data(xSamp), 'Color', 'r', 'LineWidth', 1.5);
                plottedXY = true;
            end
            if ~isempty(y_data)
                ySamp = samplenums(samplenums <= numel(y_data));
                plot(app.UIAxes, (ySamp ./ sampleRate - timeOffset) .* timeScale, y_data(ySamp), 'Color', 'b', 'LineWidth', 1.5);
                plottedXY = true;
            end
            if ~isempty(ev_times_disp)
                xline(app.UIAxes, ev_times_disp, '--', all_event_labels);
            end
            if isfinite(alignIdx)
                hl = xline(app.UIAxes, 0, '-'); hl.Color = [1 0 0]; hl.LineWidth = 3;
            end
            xlabel(app.UIAxes, sprintf('Time (%s)', timeUnits));
            app.showAlignmentNotice(app.UIAxes, alignNotice);
            if ~plottedXY
                msg = sprintf('Trial %d: x/y data exists but no plottable samples', tr);
                text(app.UIAxes, 0.1, 0.5, msg, 'Units', 'normalized');
                fprintf('[TrialViewer] %s\n', msg);
            end
            hold(app.UIAxes, 'off');

            % --- Pupil diameter ---
            cla(app.UIAxes_2);
            if hasPupil && ~isempty(p_data)
                pSamp = samplenums(samplenums <= numel(p_data));
                plot(app.UIAxes_2, (pSamp ./ sampleRate - timeOffset) .* timeScale, p_data(pSamp), 'Color', lineColor, 'LineWidth', 1.5);
                if ~isempty(ev_times_disp)
                    xline(app.UIAxes_2, ev_times_disp, '--', all_event_labels);
                end
                if isfinite(alignIdx)
                    hl = xline(app.UIAxes_2, 0, '-'); hl.Color = [1 0 0]; hl.LineWidth = 3;
                end
                xlabel(app.UIAxes_2, sprintf('Time (%s)', timeUnits));
                app.showAlignmentNotice(app.UIAxes_2, alignNotice);
                xl = xlim(app.UIAxes_2);
            else
                text(app.UIAxes_2, 0.1, 0.5, 'No pupil channel found', 'Units', 'normalized');
                xl = xlim(app.UIAxes);
            end

            % --- TTL / DIO ---
            ttlColors = [...
                0.12 0.47 0.71; 1.00 0.50 0.05; 0.17 0.63 0.17; 0.84 0.15 0.16; ...
                0.58 0.40 0.74; 0.55 0.34 0.29; 0.89 0.47 0.76; 0.50 0.50 0.50];
            cla(app.UIAxes_3);
            if isfield(app.data, 'dio') && ~isempty(app.data.dio) && tr <= numel(app.data.dio)
                trialDio = app.data.dio(tr);
                if isfield(trialDio, 'line_num') && isfield(trialDio, 'state') && isfield(trialDio, 'timestamp')
                    dioLines = unique(trialDio.line_num(trialDio.state > 0));
                    for l = 1:length(dioLines)
                        ci = mod(dioLines(l) - 1, size(ttlColors, 1)) + 1;
                        lc = ttlColors(ci, :);
                        ons  = trialDio.timestamp(trialDio.line_num == dioLines(l) & trialDio.state == 1);
                        offs = trialDio.timestamp(trialDio.line_num == dioLines(l) & trialDio.state == 0);
                        n_pairs = min(length(ons), length(offs));
                        for p = 1:n_pairs
                            tOn  = (ons(p)  - timeOffset) .* timeScale;
                            tOff = (offs(p) - timeOffset) .* timeScale;
                            plot(app.UIAxes_3, [tOn, tOff], [dioLines(l), dioLines(l)], '-', 'Color', lc, 'LineWidth', 2);
                            hold(app.UIAxes_3, 'on');
                        end
                        if length(ons) > n_pairs
                            tOn = (ons(end) - timeOffset) .* timeScale;
                            plot(app.UIAxes_3, tOn, dioLines(l), '>', 'Color', lc, 'MarkerSize', 4);
                            hold(app.UIAxes_3, 'on');
                        end
                    end
                    if ~isempty(ev_times_disp)
                        xline(app.UIAxes_3, ev_times_disp, '--', all_event_labels);
                    end
                    if isfinite(alignIdx)
                        hl = xline(app.UIAxes_3, 0, '-'); hl.Color = [1 0 0]; hl.LineWidth = 3;
                    end
                    xlabel(app.UIAxes_3, sprintf('Time (%s)', timeUnits));
                    app.showAlignmentNotice(app.UIAxes_3, alignNotice);
                    xlim(app.UIAxes_3, xl);
                    hold(app.UIAxes_3, 'off');
                else
                    text(app.UIAxes_3, 0.1, 0.5, 'DIO format not supported', 'Units', 'normalized');
                end
            else
                text(app.UIAxes_3, 0.1, 0.5, 'No DIO events available', 'Units', 'normalized');
            end

            updateStatusLamps(app, tr);
        end

        function values = localSignalVector(~, raw)
            values = [];
            if isempty(raw)
                return
            end
            if iscell(raw)
                if isempty(raw)
                    return
                end
                raw = raw{1};
            end
            if ~isnumeric(raw)
                return
            end
            values = raw(:)';
        end

        function plotRaster(app, ~)
            cla(app.RasterAxes);
            if ~app.canPlotNeural()
                text(app.RasterAxes, 0.1, 0.5, 'No neural data available', 'Units', 'normalized');
                return
            end

            tr = app.TrialNumberSpinner.Value;
            align_to = app.EventAlignmentDropDown.Value;
            [align_to_used, ~, alignNotice] = app.resolveAlignmentEvent( ...
                tr, align_to, [{'trial_start'}, app.getAvailableEvents()], '');
            unitText = app.UnitDropDown.Value;
            unit_id = str2double(unitText);
            unit_index = find(app.data.spikes.id == unit_id, 1, 'first');
            if isempty(unit_index)
                text(app.RasterAxes, 0.1, 0.5, 'Selected unit not found', 'Units', 'normalized');
                return
            end

            if isempty(align_to_used)
                rasterEvent = [];
            else
                rasterEvent = align_to_used;
            end

            raster(app.data, unit_index, rasterEvent, ...
                app.BeforemsEditField.Value, ...
                app.AftermsEditField.Value, ...
                tr, app.RasterAxes);

            app.showAlignmentNotice(app.RasterAxes, alignNotice);
        end
    end

    methods (Access = private)

        function startupFcn(app, data)
            app.data = app.localPrepareTrialViewerData(data);

            nTrials = app.getNumTrials();
            app.TrialNumberSpinner.Limits = [1 nTrials];
            app.TrialNumberSpinner.Value = 1;

            eventNames = app.getAvailableEvents();
            if isempty(eventNames)
                app.EventAlignmentDropDown.Items = {'trial_start'};
                app.EventAlignmentDropDown.Value = 'trial_start';
            else
                app.EventAlignmentDropDown.Items = eventNames;
                app.EventAlignmentDropDown.Value = eventNames{1};
            end

            % Initialize analog alignment dropdown
            analogItems = [{'(none)'}, eventNames];
            app.AnalogEventAlignmentDropDown.Items = analogItems;
            app.AnalogEventAlignmentDropDown.Value = '(none)';

            if app.canPlotNeural()
                ids = arrayfun(@num2str, app.data.spikes.id, 'UniformOutput', false);
                app.UnitDropDown.Items = ids;
                app.UnitDropDown.Value = ids{1};
            else
                app.UnitDropDown.Items = {'N/A'};
                app.UnitDropDown.Value = 'N/A';
            end

            plotAllEye(app);
        end

        function TrialNumberSpinnerValueChanged(app, event)
            if strcmp(app.TabGroup.SelectedTab.Title, app.AnalogDigitalTab.Title)
                plotAllEye(app, event);
            else
                plotRaster(app, event);
            end
        end

        function EventAlignmentDropDownOpening(app, ~)
            app.EventAlignmentDropDown.Items = app.getAvailableEvents();
        end

        function UnitDropDownOpening(app, ~)
            if app.canPlotNeural()
                ids = arrayfun(@num2str, app.data.spikes.id, 'UniformOutput', false);
                app.UnitDropDown.Items = ids;
            end
        end

        function UnitDropDownValueChanged(app, event)
            plotRaster(app, event);
        end

        function EventAlignmentDropDownValueChanged(app, event)
            plotRaster(app, event);
        end

        function AnalogEventAlignmentDropDownOpening(app, ~)
            items = [{'(none)'}, app.getAvailableEvents()];
            app.AnalogEventAlignmentDropDown.Items = items;
        end

        function AnalogEventAlignmentDropDownValueChanged(app, event)
            plotAllEye(app, event);
        end

        function AnalogBeforeAfterValueChanged(app, event)
            plotAllEye(app, event);
        end

        function updateAppLayout(app, ~)
            currentFigureWidth = app.UIFigure.Position(3);
            if currentFigureWidth <= app.onePanelWidth
                app.GridLayout.RowHeight = {477, 477};
                app.GridLayout.ColumnWidth = {'1x'};
                app.RightPanel.Layout.Row = 2;
                app.RightPanel.Layout.Column = 1;
            else
                app.GridLayout.RowHeight = {'1x'};
                app.GridLayout.ColumnWidth = {155, '1x'};
                app.RightPanel.Layout.Row = 1;
                app.RightPanel.Layout.Column = 2;
            end
        end
    end

    methods (Access = private)

        function createComponents(app)
            app.UIFigure = uifigure('Visible', 'off');
            app.UIFigure.AutoResizeChildren = 'off';
            app.UIFigure.Position = [100 100 713 477];
            app.UIFigure.Name = 'Trial Viewer';
            app.UIFigure.SizeChangedFcn = createCallbackFcn(app, @updateAppLayout, true);

            app.GridLayout = uigridlayout(app.UIFigure);
            app.GridLayout.ColumnWidth = {155, '1x'};
            app.GridLayout.RowHeight = {'1x'};
            app.GridLayout.ColumnSpacing = 0;
            app.GridLayout.RowSpacing = 0;
            app.GridLayout.Padding = [0 0 0 0];
            app.GridLayout.Scrollable = 'on';

            app.LeftPanel = uipanel(app.GridLayout);
            app.LeftPanel.Layout.Row = 1;
            app.LeftPanel.Layout.Column = 1;

            app.CompletedLampLabel = uilabel(app.LeftPanel);
            app.CompletedLampLabel.Position = [18 400 68 22];
            app.CompletedLampLabel.Text = 'Completed';

            app.CompletedLamp = uilamp(app.LeftPanel);
            app.CompletedLamp.Position = [82 401 20 20];

            app.RewardedLampLabel = uilabel(app.LeftPanel);
            app.RewardedLampLabel.Position = [18 359 60 22];
            app.RewardedLampLabel.Text = 'Rewarded';

            app.RewardedLamp = uilamp(app.LeftPanel);
            app.RewardedLamp.Position = [82 360 20 20];

            app.TrialNumberSpinnerLabel = uilabel(app.LeftPanel);
            app.TrialNumberSpinnerLabel.HorizontalAlignment = 'right';
            app.TrialNumberSpinnerLabel.Position = [1 435 70 22];
            app.TrialNumberSpinnerLabel.Text = 'Trial Number';

            app.TrialNumberSpinner = uispinner(app.LeftPanel);
            app.TrialNumberSpinner.Limits = [1 Inf];
            app.TrialNumberSpinner.ValueChangedFcn = createCallbackFcn(app, @TrialNumberSpinnerValueChanged, true);
            app.TrialNumberSpinner.Position = [76 435 74 22];
            app.TrialNumberSpinner.Value = 1;

            app.RewardedLampLabel_2 = uilabel(app.LeftPanel);
            app.RewardedLampLabel_2.Position = [15 324 61 22];
            app.RewardedLampLabel_2.Text = 'Rex Score';

            app.RewardedLamp_2 = uilamp(app.LeftPanel);
            app.RewardedLamp_2.Position = [82 325 20 20];

            app.RightPanel = uipanel(app.GridLayout);
            app.RightPanel.Layout.Row = 1;
            app.RightPanel.Layout.Column = 2;

            app.TabGroup = uitabgroup(app.RightPanel);
            app.TabGroup.Position = [1 6 551 471];

            app.AnalogDigitalTab = uitab(app.TabGroup);
            app.AnalogDigitalTab.Title = 'Analog/Digital';

            app.AnalogEventAlignmentDropDownLabel = uilabel(app.AnalogDigitalTab);
            app.AnalogEventAlignmentDropDownLabel.Position = [8 443 38 22];
            app.AnalogEventAlignmentDropDownLabel.Text = 'Align';

            app.AnalogEventAlignmentDropDown = uidropdown(app.AnalogDigitalTab);
            app.AnalogEventAlignmentDropDown.DropDownOpeningFcn = createCallbackFcn(app, @AnalogEventAlignmentDropDownOpening, true);
            app.AnalogEventAlignmentDropDown.ValueChangedFcn = createCallbackFcn(app, @AnalogEventAlignmentDropDownValueChanged, true);
            app.AnalogEventAlignmentDropDown.Items = {'(none)'};
            app.AnalogEventAlignmentDropDown.Position = [50 443 120 22];

            app.AnalogBeforemsEditFieldLabel = uilabel(app.AnalogDigitalTab);
            app.AnalogBeforemsEditFieldLabel.Position = [178 443 66 22];
            app.AnalogBeforemsEditFieldLabel.Text = 'Before (ms)';

            app.AnalogBeforemsEditField = uieditfield(app.AnalogDigitalTab, 'numeric');
            app.AnalogBeforemsEditField.Limits = [0 Inf];
            app.AnalogBeforemsEditField.ValueChangedFcn = createCallbackFcn(app, @AnalogBeforeAfterValueChanged, true);
            app.AnalogBeforemsEditField.Position = [248 443 55 22];
            app.AnalogBeforemsEditField.Value = 500;

            app.AnalogAftermsEditFieldLabel = uilabel(app.AnalogDigitalTab);
            app.AnalogAftermsEditFieldLabel.Position = [308 443 50 22];
            app.AnalogAftermsEditFieldLabel.Text = 'After (ms)';

            app.AnalogAftermsEditField = uieditfield(app.AnalogDigitalTab, 'numeric');
            app.AnalogAftermsEditField.Limits = [0 Inf];
            app.AnalogAftermsEditField.ValueChangedFcn = createCallbackFcn(app, @AnalogBeforeAfterValueChanged, true);
            app.AnalogAftermsEditField.Position = [362 443 55 22];
            app.AnalogAftermsEditField.Value = 500;

            app.UIAxes = uiaxes(app.AnalogDigitalTab);
            title(app.UIAxes, 'XY Eye Position')
            xlabel(app.UIAxes, 'Time (s)')
            ylabel(app.UIAxes, 'Position (dva)')
            app.UIAxes.Position = [8 291 449 143];

            app.UIAxes_2 = uiaxes(app.AnalogDigitalTab);
            title(app.UIAxes_2, 'Pupil Diameter')
            xlabel(app.UIAxes_2, 'Time (s)')
            ylabel(app.UIAxes_2, 'Diameter (a.u.)')
            app.UIAxes_2.Position = [10 149 449 133];

            app.UIAxes_3 = uiaxes(app.AnalogDigitalTab);
            title(app.UIAxes_3, 'TTL')
            xlabel(app.UIAxes_3, 'Time (s)')
            ylabel(app.UIAxes_3, 'Line')
            app.UIAxes_3.Position = [9 5 449 135];

            app.NeuralTab = uitab(app.TabGroup);
            app.NeuralTab.Title = 'Neural';

            app.RasterAxes = uiaxes(app.NeuralTab);
            title(app.RasterAxes, 'Raster')
            xlabel(app.RasterAxes, 'Time (ms)')
            ylabel(app.RasterAxes, 'Trial Num')
            app.RasterAxes.Position = [2 97 306 219];

            app.UnitDropDownLabel = uilabel(app.NeuralTab);
            app.UnitDropDownLabel.Position = [25 408 27 22];
            app.UnitDropDownLabel.Text = 'Unit';

            app.UnitDropDown = uidropdown(app.NeuralTab);
            app.UnitDropDown.DropDownOpeningFcn = createCallbackFcn(app, @UnitDropDownOpening, true);
            app.UnitDropDown.ValueChangedFcn = createCallbackFcn(app, @UnitDropDownValueChanged, true);
            app.UnitDropDown.Position = [67 408 75 22];

            app.EventAlignmentDropDownLabel = uilabel(app.NeuralTab);
            app.EventAlignmentDropDownLabel.Position = [25 380 92 22];
            app.EventAlignmentDropDownLabel.Text = 'Event Alignment';

            app.EventAlignmentDropDown = uidropdown(app.NeuralTab);
            app.EventAlignmentDropDown.DropDownOpeningFcn = createCallbackFcn(app, @EventAlignmentDropDownOpening, true);
            app.EventAlignmentDropDown.ValueChangedFcn = createCallbackFcn(app, @EventAlignmentDropDownValueChanged, true);
            app.EventAlignmentDropDown.Position = [118 380 100 22];

            app.BeforemsEditFieldLabel = uilabel(app.NeuralTab);
            app.BeforemsEditFieldLabel.Position = [25 352 66 22];
            app.BeforemsEditFieldLabel.Text = 'Before (ms)';

            app.BeforemsEditField = uieditfield(app.NeuralTab, 'numeric');
            app.BeforemsEditField.Limits = [0 Inf];
            app.BeforemsEditField.ValueChangedFcn = createCallbackFcn(app, @TrialNumberSpinnerValueChanged, true);
            app.BeforemsEditField.Position = [94 352 57 22];
            app.BeforemsEditField.Value = 100;

            app.AftermsEditFieldLabel = uilabel(app.NeuralTab);
            app.AftermsEditFieldLabel.Position = [25 322 56 22];
            app.AftermsEditFieldLabel.Text = 'After (ms)';

            app.AftermsEditField = uieditfield(app.NeuralTab, 'numeric');
            app.AftermsEditField.Limits = [0 Inf];
            app.AftermsEditField.ValueChangedFcn = createCallbackFcn(app, @TrialNumberSpinnerValueChanged, true);
            app.AftermsEditField.Position = [95 322 57 22];
            app.AftermsEditField.Value = 100;

            app.UIFigure.Visible = 'on';
        end
    end

    methods (Access = public)

        function app = TrialViewer(varargin)
            createComponents(app)
            registerApp(app, app.UIFigure)
            runStartupFcn(app, @(app)startupFcn(app, varargin{:}))
            if nargout == 0
                clear app
            end
        end

        function delete(app)
            delete(app.UIFigure)
        end
    end
end
