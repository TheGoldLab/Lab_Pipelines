function pathname = goldLabDataSessionLocalPathnames(tag)
% function pathname = goldLabDataSessionLocalPathnames(tag)
%
% Resource file to define local pathnames used by goldLabDataSession
%   utilities

if strcmp(tag, 'baseDataDirectory')
    pathname = '/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/';

elseif strcmp(tag, 'pythonSearchPath')
    pathname = '/Users/lowell/miniconda3/bin:/Users/lowell/miniconda3/condabin:';

elseif strcmp(tag, 'pyramidSearchPath')
    pathname = '/Users/lowell/Documents/GitHub/Lab_Matlab_Utilities/dataSession/test/pyramid';
end

