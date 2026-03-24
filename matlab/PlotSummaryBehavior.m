% Author: Victoria Subritzky Katz, Lowell, Josh
% Modified by LWT for hdf5 files converted with pyramid
% Date: October 2023
% Description: Plots summary data and fits for multiple files stored in a
% given directory ("files") for the AODR task

options.filename     = -1; % tag for latest file
options.converter    = 'Pyramid';
options.convertSpecs = 'AODR_experiment';
options.axs          = [];

% choose your character
monkeys(1).string = 'Anubis';

% iterate through monkeys
for m=1:length(monkeys)
    monkey = monkeys(m).string;

    files = dir('/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/Anubis/Converted/Behavior/Pyramid/*.hdf5');

    hazard_est = []; % array for estimated hazard rates for each session
    % iterate through files
    for ifile = 1:length(files)
        trial_file_path = fullfile(files(ifile).folder, files(ifile).name);
        % Get the data
        [data, obj] = goldLabDataSession.convertSession( ...
            trial_file_path, ...
            'tag',          'AODR', ...
            'monkey',       monkeys(m).string, ...
            'converter',    options.converter, ...
            'convertSpecs', options.convertSpecs);


        %% Collect relevant data
        % PMF
        % Independent variable is "signed cues" -- which is cue location
        %   signed by corresponding "LLR for switch"
        hazards    = nonanunique(data.values.hazard);
        numHazards = length(hazards);
        sCues      = sign(data.values.llr_for_switch).*abs(data.ids.sample_id);
        cues       = nonanunique(sCues);
        numCues    = length(cues);

        % Dependent variable is choice switch re: previous TRUE STATE
        %   (note that this is not the same as a choice switch, because
        %   the previous choice might have been in error).
        prevState = [nan; data.ids.correct_target(1:end-1)];
        choice_switch = zeros(size(prevState));
        choice_switch(data.ids.choice~=prevState)=1;
        choice_switch(~ismember(data.ids.choice, [1 2]) | ~ismember(prevState,[1 2])) = nan;
        Lswitch = choice_switch==1;
        Lstay   = choice_switch==0;

        % collect data in pdat
        %   dim 1 is LLR
        %   dim 2 is pmf, cmf T1/T2 choices
        %   dim 3 is hazard
        %   dim 4 is for data, ns, sem
        pdat  = nans(numCues, 3, numHazards, 3);
        Lc1   = data.ids.choice==1;
        Lc2   = data.ids.choice==2;
        Ltask = data.ids.task_id>=2;
        Lgood = Ltask & data.ids.score>=0;
        if ~any(Lgood)
            %axes(axs(1));
            % title(sprintf('%s: %d trials', strrep(data.fileName, '_', '-'), sum(Lgood)))
            fprintf('%s: NO TRIALS', files(ifile).name)
            continue
        end

        % For each cue location
        for ll = 1:numCues
            Lcue = Lgood & sCues==cues(ll);

            % For each hazard
            for hh = 1:numHazards
                Lh = Lcue & data.values.hazard == hazards(hh);

                % collect data
                pdat(ll,:,hh,1) = [ ...
                    sum(Lh&Lswitch)./sum(Lh&(Lswitch|Lstay)).*100, ...
                    nanmean(data.values.RT(Lh&Lc1)), ...
                    nanmean(data.values.RT(Lh&Lc2))];

                % collect ns
                pdat(ll,:,hh,2) = [ ...
                    sum(Lh&(Lswitch|Lstay)), sum(Lh&Lc1), sum(Lh&Lc2)];

                % collect sems
                pdat(ll,2:3,hh,3) = [ ...
                    nanse(data.values.RT(Lh&Lc1)), ...
                    nanse(data.values.RT(Lh&Lc2))];
            end
        end

        % First get logistic fit
        %   input matrix is h1_bias, h2_bias, llr for switch, choice switch
        ldat = cat(2, zeros(sum(Lgood), 2), sCues(Lgood), choice_switch(Lgood));
        for hh = 1:numHazards
            ldat(data.values.hazard(Lgood)==hazards(hh), hh) = 1;
        end
        ldat = ldat(isfinite(ldat(:,4)),:);
        fits = logist_fit(ldat, 'lu1');

        %estimate hazards for this file
        if hazards(1) == .05
            hazard_est(ifile,1) = 1./(1+exp(-fits(1)));
            hazard_est(ifile,2) = 1./(1+exp(-fits(2)));
        else
            hazard_est(ifile,2) = 1./(1+exp(-fits(1)));
            hazard_est(ifile,1) = 1./(1+exp(-fits(2)));
        end

        %collect data
        if ifile == 1
            pdat_tot = pdat;
            fits_tot = fits;
            count = 1;
        else
            pdat_tot = (pdat + pdat_tot);
            fits_tot = (fits + fits_tot);
            count = count +1;
        end

    end

    %find the average
    pdat_tot = pdat_tot ./count;
    fits_tot = fits_tot ./count;

    %% Plotz
    co = {[4 94 167]./255, [194 0 77]./255};

    %%PMF
    plot([-4 4], [50 50], 'k:');
    plot([0 0], [0 100], 'k:');
    xax = (-4:0.01:4)';
    lx  = cat(2, ones(size(xax)), xax);
    maxn = max(reshape(pdat_tot(:,1,:,2),[],1));
    % For each hazard

    figure
    for hh = 1:numHazards
        % Plot raw data per LLR
        for ll = 1:numCues
            if pdat_tot(ll,1,hh,2) > 0
                plot(cues(ll), pdat_tot(ll,1,hh,1), '.', 'MarkerSize', pdat_tot(ll,1,hh,2)/maxn*50, ...
                    'Color', co{hh});
                hold on;
            end
        end
        plot(xax, logist_valLU1(fits_tot([hh 3 4]), lx).*100, '-', 'Color', co{hh}, 'LineWidth', 2);
        hold on;

        % bias is just log((1-H)/H) -- see Glaze et al 2015
        h=text(-3.5, 75+(hh-1)*15, sprintf('H=%0.2f (%.2f)', ...
            1./(1+exp(-fits_tot(hh))), hazards(hh)));
        set(h, 'Color', co{hh})
    end
    axis([-4 4 0 100]);
    xlabel('Cue location(-=stay, +=switch)')
    ylabel('Prob(switch)');
    title(sprintf('%s Behaviour Across %3d Sessions',monkeys(m).string, count))
    hold off;


    %box plot
    boxColors = [co{1};co{2}];
    figure
    boxplot(hazard_est, 'Labels', {'Hazard = 0.05', 'Hazard = 0.5'}, 'Colors', boxColors, 'Notch', 'on');
    hold on;
    scatter(ones(size(hazard_est(:,1))), hazard_est(:,1),'MarkerFaceColor', boxColors(1,:), 'MarkerEdgeColor', boxColors(1,:)); %'Color', co{1}, 'filled');
    scatter(2 * ones(size(hazard_est(:,2))), hazard_est(:,2), 'MarkerFaceColor', boxColors(2,:), 'MarkerEdgeColor', boxColors(2,:)); % 'Color', co{2}, 'filled');
    hold off;

    % Add labels and title
    % xlabel('Hazard Condition');
    ylabel('Estimated Hazard Rate');
    title(sprintf('%s Estimated Hazard Rates Across %3d Sessions',monkeys(m).string, count))


end

