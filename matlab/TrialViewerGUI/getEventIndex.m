function idx = getEventIndex(data, tr, col, wrt)
arguments
    data = [];
    tr = [];
    col = 1;
    wrt = 'trial_start';
end

idx = NaN;
if isempty(data) || ~isfield(data, 'times') || ~istable(data.times)
    return
end
if isempty(tr) || tr < 1 || tr > height(data.times)
    return
end

if isnumeric(col)
    if col < 1 || col > width(data.times)
        return
    end
    eventValue = data.times{tr, col};
else
    if ~ismember(col, data.times.Properties.VariableNames)
        return
    end
    eventValue = data.times.(col)(tr);
end
eventValue = toScalarDouble(eventValue);
if ~isfinite(eventValue)
    return
end

sampleRate = 1;
if isfield(data, 'signals') && isfield(data.signals, 'sampleRates') && ~isempty(data.signals.sampleRates)
    sampleRate = data.signals.sampleRates(1);
end

referenceTime = 0;
if ischar(wrt) || isstring(wrt)
    wrt = char(wrt);
    if ismember(wrt, data.times.Properties.VariableNames)
        referenceTime = toScalarDouble(data.times.(wrt)(tr));
        if ~isfinite(referenceTime)
            referenceTime = 0;
        end
    end
end

relativeTime = eventValue - referenceTime;
idx = relativeTime * sampleRate;
idx = idx + 1;
idx = round(idx);
if idx < 1
    idx = NaN;
end
end

function value = toScalarDouble(raw)
value = NaN;

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
