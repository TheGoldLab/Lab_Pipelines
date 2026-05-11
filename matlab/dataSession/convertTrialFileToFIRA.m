function dataInFIRAFormat = convertTrialFileToFIRA(dataInTrialFileFormat, filename, spikeCategories)
% function dataInFIRAFormat = convertTrialFileToFIRA(dataInTrialFileFormat)
%
% Convert trialFile to FIRA
%

if nargin < 2 || isempty(filename)
    filename = 'Converted from trialFile';
end

if nargin < 3 || isempty(spikeCategories)
    spikeCategories = {'spikes', 'phy_clusters'};
end

% Get numTrials -- remember first and last are dummies
numTrials = size(dataInTrialFileFormat, 2)-2;

%% Set up FIRA
%
dataInFIRAFormat = struct( ...
    'header', struct(...
    'filename', filename, ...
    'filetype', 'Converted from trialFile', ...
    'paradigm', 'xxx', ...
    'subject', [], ...
    'session', [], ...
    'spmF', [], ...
    'numTrials', numTrials, ...
    'date', date, ...
    'messageH', [], ...
    'flags', []), ...
    'spm', 'Converted from trialFile', ...
    'ecodes', struct( ...
    'name', {{}}, ...
    'type', {{}}, ...
    'data', []), ...
    'spikes', struct( ...
    'channel', [], ...
    'unit', [], ...
    'id', [], ...
    'data', {{}}), ...
    'analog', struct( ...
    'name', {{}}, ...
    'acquire_rate', [], ...
    'store_rate', [], ...
    'gain', [], ...
    'offset', [], ...
    'zero', {{}}, ...
    'error', {{}}, ...
    'data', []), ...
    'dio', struct(...
    'line_num',[],'timestamp',[],'state',[]));

% Return if no data given
if numTrials < 1
    return
end

%% Add ecodes from trial enhancements.
%
% Start with four "standard" fields
dataInFIRAFormat.ecodes.name = {'trial_num', 'trial_begin', 'trial_end', 'trial_wrt'};
dataInFIRAFormat.ecodes.type = {'value', 'time', 'time', 'time'};
dataInFIRAFormat.ecodes.data = nan(numTrials, 4);
dataInFIRAFormat.ecodes.data(:,1) = 1:numTrials;
dataInFIRAFormat.ecodes.data(:,2) = [dataInTrialFileFormat(2:end-1).start_time]';
dataInFIRAFormat.ecodes.data(:,3) = [dataInTrialFileFormat(2:end-1).end_time]';
dataInFIRAFormat.ecodes.data(:,4) = [dataInTrialFileFormat(2:end-1).wrt_time]';

% Use trial "categories" to indicate which trial fields,
% including events and enhancements, contain ecodes.
% Categories have names like "id", "value", and "time".
% Event and enhancement fields have names like "fp_on", and "t1_angle".

% Loop through the trials
for tt = 1:numTrials

    % Loop through the categories present in each trial.
    categories = dataInTrialFileFormat(tt+1).categories;
    if ~isempty(categories)

        % Treat categories that aren't for spikes as ecodes.
        ecodeCategoryNames = setdiff(fieldnames(categories), spikeCategories);
        for cc = 1:length(ecodeCategoryNames)

            % Get names of trial enhancements in this category.
            categoryName = ecodeCategoryNames{cc};
            fieldsInCategory = categories.(categoryName );
            enhancements = dataInTrialFileFormat(tt+1).enhancements;
            enhancementNames = {};
            if ~isempty(enhancements)
                enhancementNames = fieldnames(enhancements);
            end
            enhancementsInCategory = intersect(fieldsInCategory, enhancementNames);
            numEnhancements = length(enhancementsInCategory);

            % Loop through the enhancements in this category.
            for ee = 1:numEnhancements
                enhancementName = enhancementsInCategory{ee};
                value = dataInTrialFileFormat(tt+1).enhancements.(enhancementName);
                if isstruct(value)

                    % Loop through
                    doubleSecretEnhancements = fieldnames(value);
                    numDoubleSecretEnhancements = length(doubleSecretEnhancements);

                    for dd = 1:numDoubleSecretEnhancements

                        % Save the name/type (always "value", just cuz)
                        name = [enhancementName '_' doubleSecretEnhancements{dd}];
                        Lcolumn = strcmp(name, dataInFIRAFormat.ecodes.name);
                        if ~any(Lcolumn)
                            dataInFIRAFormat.ecodes.name(end+1) = {name};
                            dataInFIRAFormat.ecodes.type(end+1) = {'value'};
                            dataInFIRAFormat.ecodes.data(:,end+1) = nan;
                            Lcolumn(end+1) = true;
                        end

                        % Save the data
                        value = dataInTrialFileFormat(tt+1).enhancements.(enhancementName).(doubleSecretEnhancements{dd});
                        if isempty(value)
                            fprintf('Warning: found no values for %s at trial file index %d, FIRA index %d\n', name, tt+1, tt)
                            value = nan;
                        elseif length(value) > 1
                            fprintf('Warning: found >1 values for %s at trial file index %d, FIRA index %d\n', name, tt+1, tt)
                            value = value(1);
                        end
                        dataInFIRAFormat.ecodes.data(tt,Lcolumn) = value;
                    end

                else

                    % Save the name/type (always "value", just cuz)
                    Lcolumn = strcmp(enhancementName, dataInFIRAFormat.ecodes.name);
                    if ~any(Lcolumn)
                        dataInFIRAFormat.ecodes.name{end+1} = enhancementName;
                        dataInFIRAFormat.ecodes.type{end+1} = categoryName;
                        dataInFIRAFormat.ecodes.data(:,end+1) = nan;
                        Lcolumn(end+1) = true;
                    end

                    % Save the data
                    if isempty(value)
                        value = nan;
                    elseif length(value) > 1
                        fprintf('Warning: found >1 values for %s at trial file index %d, FIRA index %d\n', enhancementName, tt+1, tt)
                        value = value(1);
                    end
                    dataInFIRAFormat.ecodes.data(tt,Lcolumn) = value;
                end
            end

            % Get names of trial numeric event buffers in this category.
            numeric = dataInTrialFileFormat(tt+1).numeric_events;
            numericNames = {};
            if ~isempty(numeric)
                numericNames = fieldnames(numeric);
            end
            numericInCatecory = intersect(fieldsInCategory, numericNames);
            numNumeric = length(numericInCatecory);

            % Loop through the numeric events in this category.
            for nn = 1:numNumeric
                numericName = numericInCatecory{nn};
                eventData = dataInTrialFileFormat(tt+1).numeric_events.(numericName);

                if isempty(eventData)
                    ecodeValue = nan;
                else
                    if size(eventData, 1) > 1
                        fprintf('Warning: found >1 values for %s at trial file index %d, FIRA index %d\n', numericName, tt+1, tt)
                    end
                    % Each event can have multiple values, like:
                    %   [timestamp]
                    %   [timestamp, value]
                    %   [timestamp, value1, value2, ...]
                    % Take the last one available.
                    ecodeValue = eventData(1,end);
                end

                % Create the new ecode and save the data.
                Lcolumn = strcmp(numericName, dataInFIRAFormat.ecodes.name);
                if ~any(Lcolumn)
                    dataInFIRAFormat.ecodes.name{end+1} = numericName;
                    dataInFIRAFormat.ecodes.type{end+1} = categoryName;
                    dataInFIRAFormat.ecodes.data(:,end+1) = nan;
                    Lcolumn(end+1) = true;
                end
                dataInFIRAFormat.ecodes.data(tt,Lcolumn) = ecodeValue;
            end

            % Get names of trial text event buffers in this category.
            text = dataInTrialFileFormat(tt+1).text_events;
            textNames = {};
            if ~isempty(text)
                textNames = fieldnames(text);
            end
            textInCategory = intersect(fieldsInCategory, textNames);
            numText = length(textInCategory);

            % Loop through the text events in this category.
            for tx = 1:numText
                textName = textInCategory{tx};
                eventData = dataInTrialFileFormat(tt+1).text_events.(textName);

                if isempty(eventData)
                    ecodeValue = nan;
                else
                    if size(eventData.timestamp_data, 1) > 1
                        fprintf('Warning: found >1 values for %s at trial file index %d, FIRA index %d\n', textName, tt+1, tt)
                    end
                    % Text events have a timestamp and a text string.
                    % Take the first timestamp.
                    ecodeValue = eventData.timestamp_data(1);
                end

                % Create the new ecode and save the data.
                Lcolumn = strcmp(textName, dataInFIRAFormat.ecodes.name);
                if ~any(Lcolumn)
                    dataInFIRAFormat.ecodes.name{end+1} = textName;
                    dataInFIRAFormat.ecodes.type{end+1} = categoryName;
                    dataInFIRAFormat.ecodes.data(:,end+1) = nan;
                    Lcolumn(end+1) = true;
                end
                dataInFIRAFormat.ecodes.data(tt,Lcolumn) = ecodeValue;
            end
        end
    end
end

% convention is names are row vector
dataInFIRAFormat.ecodes.name = dataInFIRAFormat.ecodes.name(:)';

%% Add analog signals
% For continuous data sources that only have sample values
if ~isempty(dataInTrialFileFormat(2).signals)
    signalNames = fieldnames(dataInTrialFileFormat(2).signals);
    signalNames = intersect(signalNames, {'gaze_x', 'gaze_y', 'pupil'});
    numSignals = length(signalNames);
    if isfield(dataInTrialFileFormat(2).signals.(signalNames{1}),'type')
        if any(dataInTrialFileFormat(2).signals.(signalNames{1}).type == 'SignalTimeChunk')
            dataInFIRAFormat.analog.data = struct( ...
                'length', [], ...
                'values', []);
        else
            dataInFIRAFormat.analog.data = struct( ...
                'start_time', cell(numTrials, numSignals), ...
                'length', [], ...
                'values', []);
        end
    else
        dataInFIRAFormat.analog.data = struct( ...
                'start_time', cell(numTrials, numSignals), ...
                'length', [], ...
                'values', []);
    end

    % Loop through each signal type
    for ss = 1:numSignals

        % Add name, sample rate
        dataInFIRAFormat.analog.name = ...
            cat(2, dataInFIRAFormat.analog.name, signalNames{ss});
        dataInFIRAFormat.analog.acquire_rate = ...
            cat(2, dataInFIRAFormat.analog.acquire_rate, ...
            dataInTrialFileFormat(2).signals.(signalNames{ss}).sample_frequency);
        dataInFIRAFormat.analog.store_rate = dataInFIRAFormat.analog.acquire_rate;

        % Add data
        for tt = 1:numTrials
            if ~isfield(dataInTrialFileFormat(2).signals.(signalNames{ss}),'type')
                % if ~any(dataInTrialFileFormat(tt+1).signals.(signalNames{ss}).type == 'SignalTimeChunk')
                    dataInFIRAFormat.analog.data(tt,ss).start_time = ...
                        dataInTrialFileFormat(tt+1).signals.(signalNames{ss}).first_sample_time;
                % end
            end
            dataInFIRAFormat.analog.data(tt,ss).values = ...
                dataInTrialFileFormat(tt+1).signals.(signalNames{ss}).signal_data;
            dataInFIRAFormat.analog.data(tt,ss).length = ...
                length(dataInFIRAFormat.analog.data(tt,ss).values);
        end
    end
end
%% Add spikes from trial numeric events.
%

% Start the data celery
% Mmmm, celery...
dataInFIRAFormat.spikes.data = {};

% Keep track of channel,unit pairs to see if we have already added them
channelUnits = [NaN;NaN];

% Placeholder for Phy units when per-cluster channel is not yet known.
% Overwritten later in this section when we look for metadata.
phyChannelPlaceholder = -1; 

% Loops through the trials and collect the data
for tt = 1:numTrials

    % Get spikes from trial numeric event lists.
    numeric = dataInTrialFileFormat(tt+1).numeric_events;
    numericNames = {};
    if ~isempty(numeric)
        numericNames = fieldnames(numeric);
    end

    % But only the numeric event lists that are in spike categories.
    % spikeNames = {};
    % categories = dataInTrialFileFormat(tt+1).categories;
    % if ~isempty(categories)
    %     for sc = 1:length(spikeCategories)
    %         spikeCategory = spikeCategories{sc};
    %         if isfield(categories, spikeCategory)
    %             spikeNames = cat(1, spikeNames, categories.(spikeCategory));
    %         end
    %     end
    % end
    spikeChannelNames = intersect(numericNames, spikeCategories);

    % Loop through the channels to count units
    numSpikeChannels = length(spikeChannelNames);
    for ss = 1:numSpikeChannels

        % Parse channel number
        if strcmp(spikeChannelNames{ss},'phy_clusters')
            channelNumber = phyChannelPlaceholder;
        else
            channelNumber = str2double(spikeChannelNames{ss}(end-2:end));
        end

        % Keep track of where we're storing the data
        channelRowStart = 0;

        % Get the data
        trialSpikes = dataInTrialFileFormat(tt+1).numeric_events.(spikeChannelNames{ss});

        if ~isempty(trialSpikes)

            % Get the units
            units = unique(trialSpikes(:,end)); % for both plexon and phy files, the unit ID is the last column
            numUnits = length(units);

            % Loop through the units
            for uu = 1:numUnits

                % Check if we need to add the unit (check that both channel
                % and unit can be found
                if ~any(ismember(channelUnits',[channelNumber, units(uu)],'rows'))

                    % Add to lists of channels/units/ids
                    if strcmp(spikeChannelNames{ss},'phy_clusters')
                        dataInFIRAFormat.spikes.channel = cat(2, dataInFIRAFormat.spikes.channel, phyChannelPlaceholder); % Placeholder until metadata backfill
                        dataInFIRAFormat.spikes.unit = cat(2, dataInFIRAFormat.spikes.unit, units(uu)); % 
                        dataInFIRAFormat.spikes.id = cat(2, dataInFIRAFormat.spikes.id, units(uu));
                        % Add to list
                        channelUnits = cat(2, channelUnits, [phyChannelPlaceholder; units(uu)]);
                    else
                        dataInFIRAFormat.spikes.channel = cat(2, dataInFIRAFormat.spikes.channel, channelNumber);
                        dataInFIRAFormat.spikes.unit = cat(2, dataInFIRAFormat.spikes.unit, units(uu));
                        dataInFIRAFormat.spikes.id = cat(2, dataInFIRAFormat.spikes.id, channelNumber*1000+units(uu));
                        % Add to list
                        channelUnits = cat(2, channelUnits, [channelNumber; units(uu)]);
                    end
                    
                    % Add data column
                    dataInFIRAFormat.spikes.data = ...
                        cat(2, dataInFIRAFormat.spikes.data, cell(numTrials, 1));
                end

                % Now add the spike data
                Lunit = trialSpikes(:,end) == units(uu); % for both plexon and phy files, the unit ID is the last column
                % since channels/units may not be added sequentially, you
                % must find the appropriate column number
                ind = find(ismember([dataInFIRAFormat.spikes.channel; dataInFIRAFormat.spikes.unit]',[channelNumber, units(uu)],'rows'));
                dataInFIRAFormat.spikes.data{tt,ind} = trialSpikes(Lunit,1);
            end
        end
    end

    % Update the row counter
    channelRowStart = size(dataInFIRAFormat.spikes.data, 2);
end

%% Add per-unit phy cluster metadata to spikes.
%
% Look for trial enhancement "phy_cluster_info" (stored as a struct keyed
% by cluster id) and map metadata into parallel spikes fields, one value per
% unit in dataInFIRAFormat.spikes.
phyClusterInfo = [];
for tt = 1:numTrials
    enhancements = dataInTrialFileFormat(tt+1).enhancements;
    if ~isempty(enhancements) && isfield(enhancements, 'phy_cluster_info')
        phyClusterInfo = enhancements.phy_cluster_info;
        break
    end
end

if ~isempty(phyClusterInfo) && isstruct(phyClusterInfo) && ~isempty(dataInFIRAFormat.spikes.id)
    clusterInfoFieldNames = fieldnames(phyClusterInfo);
    clusterIds = [];
    clusterMeta = {};
    metadataFieldNames = {};

    % Build lookup lists from cluster id -> metadata struct.
    for ff = 1:length(clusterInfoFieldNames)
        fieldName = clusterInfoFieldNames{ff};
        xPrefixedMatch = regexp(fieldName, '^x(\d+)$', 'tokens', 'once');
        numericMatch = regexp(fieldName, '^(\d+)$', 'tokens', 'once');
        if ~isempty(xPrefixedMatch)
            clusterId = str2double(xPrefixedMatch{1});
        elseif ~isempty(numericMatch)
            clusterId = str2double(numericMatch{1});
        else
            continue
        end

        if isnan(clusterId)
            continue
        end

        clusterValue = phyClusterInfo.(fieldName);
        if ~isstruct(clusterValue)
            continue
        end

        clusterIds(end+1) = clusterId; %#ok<AGROW>
        clusterMeta{end+1} = clusterValue; %#ok<AGROW>
        metadataFieldNames = union(metadataFieldNames, fieldnames(clusterValue));
    end

    % Initialize one metadata field per Phy column, parallel to spikes.id.
    numSpikeUnits = length(dataInFIRAFormat.spikes.id);
    for mm = 1:length(metadataFieldNames)
        metadataName = metadataFieldNames{mm};
        safeMetadataName = matlab.lang.makeValidName(metadataName);
        targetFieldName = ['phy_' safeMetadataName];
        dataInFIRAFormat.spikes.(targetFieldName) = cell(1, numSpikeUnits);
    end

    % Fill metadata values for Phy-derived units (placeholder channel).
    for uu = 1:numSpikeUnits
        if dataInFIRAFormat.spikes.channel(uu) ~= phyChannelPlaceholder
            continue
        end

        thisClusterId = dataInFIRAFormat.spikes.id(uu);
        clusterIndex = find(clusterIds == thisClusterId, 1);
        if isempty(clusterIndex)
            continue
        end

        thisMeta = clusterMeta{clusterIndex};

        % If cluster metadata has channel info, backfill it.
        if isfield(thisMeta, 'channel') && isnumeric(thisMeta.channel)
            dataInFIRAFormat.spikes.channel(uu) = thisMeta.channel;
        elseif isfield(thisMeta, 'ch') && isnumeric(thisMeta.ch)
            dataInFIRAFormat.spikes.channel(uu) = thisMeta.ch;
        end

        for mm = 1:length(metadataFieldNames)
            metadataName = metadataFieldNames{mm};
            safeMetadataName = matlab.lang.makeValidName(metadataName);
            targetFieldName = ['phy_' safeMetadataName];

            if isfield(thisMeta, metadataName)
                dataInFIRAFormat.spikes.(targetFieldName){uu} = thisMeta.(metadataName);
            end
        end
    end

    dataInFIRAFormat.spikes.phy_metadata_fields = strcat('phy_', matlab.lang.makeValidName(metadataFieldNames));
end

%% Build unit-level spikes table.
%
% Make a table with one row per unit and core ids plus optional phy metadata.
numSpikeUnits = length(dataInFIRAFormat.spikes.id);
if numSpikeUnits > 0
    spikesTable = table( ...
        dataInFIRAFormat.spikes.id(:), ...
        dataInFIRAFormat.spikes.channel(:), ...
        dataInFIRAFormat.spikes.unit(:), ...
        'VariableNames', {'id', 'channel', 'unit'});

    nSpikes = zeros(numSpikeUnits, 1);
    for uu = 1:numSpikeUnits
        spikeTimesByTrial = dataInFIRAFormat.spikes.data(:, uu);
        nSpikes(uu) = sum(cellfun(@numel, spikeTimesByTrial));
    end
    spikesTable.nSpikes = nSpikes;

    if isfield(dataInFIRAFormat.spikes, 'phy_metadata_fields')
        phyMetadataFields = dataInFIRAFormat.spikes.phy_metadata_fields;
        for ff = 1:length(phyMetadataFields)
            fieldName = phyMetadataFields{ff};
            if ~isfield(dataInFIRAFormat.spikes, fieldName)
                continue
            end

            fieldValue = dataInFIRAFormat.spikes.(fieldName);
            if iscell(fieldValue)
                spikesTable.(fieldName) = fieldValue(:);
            elseif isnumeric(fieldValue) || islogical(fieldValue)
                spikesTable.(fieldName) = num2cell(fieldValue(:));
            elseif isstring(fieldValue)
                spikesTable.(fieldName) = cellstr(fieldValue(:));
            else
                spikesTable.(fieldName) = num2cell(fieldValue(:));
            end
        end
    end

    dataInFIRAFormat.spikes.phy_info = spikesTable;
else
    dataInFIRAFormat.spikes.phy_info = table([], [], [], [], 'VariableNames', {'id', 'channel', 'unit', 'nSpikes'});
end

% Keep spikes metadata only in spikes.phy_info; remove transient phy_* fields.
if isfield(dataInFIRAFormat.spikes, 'phy_metadata_fields')
    fieldsToRemove = dataInFIRAFormat.spikes.phy_metadata_fields;
    if isstring(fieldsToRemove)
        fieldsToRemove = cellstr(fieldsToRemove);
    end
    for ff = 1:length(fieldsToRemove)
        if isfield(dataInFIRAFormat.spikes, fieldsToRemove{ff})
            dataInFIRAFormat.spikes = rmfield(dataInFIRAFormat.spikes, fieldsToRemove{ff});
        end
    end
    dataInFIRAFormat.spikes = rmfield(dataInFIRAFormat.spikes, 'phy_metadata_fields');
end

%% Add dio or ttl data
% % Get ttl/dio signals from numeric events
% In Open Ephys GUI 0.6.7 pyramid saves these as [timestamp, line_number, line_state, processor_id]
numeric = dataInTrialFileFormat(tt+1).numeric_events;
numericNames = {};
if ~isempty(numeric)
    numericNames = fieldnames(numeric);
end
%
% % But only the numeric event lists that are ttl.
if ismember('ttl',numericNames)
    for tt = 1:numTrials
        dataInFIRAFormat.dio(tt).timestamp = dataInTrialFileFormat(tt+1).numeric_events.ttl(:,1);
        dataInFIRAFormat.dio(tt).line_num = dataInTrialFileFormat(tt+1).numeric_events.ttl(:,2);
        dataInFIRAFormat.dio(tt).state = dataInTrialFileFormat(tt+1).numeric_events.ttl(:,3);
    end
end
