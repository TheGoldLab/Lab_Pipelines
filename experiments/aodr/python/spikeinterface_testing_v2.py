import spikeinterface.widgets as sw
from AODR_session_sorters import OpenEphysSessionSorter as OES
from pyramid import cli
import pandas as pd
import sys, os
# %matplotlib ipympl

# Experiment directory top level - should contain the subfolders like ecodes, python, matlab.
expDir = "/Users/lowell/Documents/GitHub/Lab_Pipelines/experiments/aodr"
os.chdir(expDir) # regular python files will run from the first open folder in your tree, but notebooks will work from wherever the notebook is stored.
# Directory where the raw files are stored to be converted/sorted
dataSearchPath = "/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/Anubis/Raw/Behavior/"
# Where the rules for ecodes are stored
pyramidSearchPath = expDir+"/ecodes"
# Conversion specifications
convertSpecs = expDir+"/AODR_experiment_LC.yaml"
# Base directory to save the output files from pyramid (hdf5 files)
baseSaveDir = "/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/Anubis/Converted/Behavior/Pyramid/"
# The Open Ephys session directory (technically not a file, but a folder)
currentFile = "Anubis_2024-08-05_12-06-56"
# Full directory to save the output files from pyramid (hdf5 files)
trialFileOutputName = baseSaveDir+currentFile+".hdf5"
# Directory to save the output files from sorting
sorted_out = "/Users/lowell/Data/Physiology/AODR/Data/Anubis/Sorted/"+currentFile 

#sys.path.append(expDir+"/python") # to make sure pyramid can access the custom collectors/enhancers/functions?

sorter = OES(session_dir=dataSearchPath+currentFile, channel_names=[2],
             out_folder=sorted_out,
             sorter_name='single_channel',
             step_names=[
                 'clean_tree',                      # This removes everything from the output folder!!!
                 'read_data',                       # Has to be included to do anything else
                 'set_single',
                 'bandpass',
                 'single_ch_sorter_and_analyzer',     # Runs one spike sorter which is an optional parameter (default spikecyrcus2) and one analyzer
                 'open_sigui',                      # Opens a gui to view the sorting results to help with manual refinement
                 'export_to_phy'                    # Currently pyramid supports Phy output or plexon
             ])