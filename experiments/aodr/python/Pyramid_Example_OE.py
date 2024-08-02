from pyramid import cli
import pandas as pd
import os

# Directory where the sorted plexon data files are stored
dataSearchPath = "/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/Anubis/Raw/Behavior/"
# Where the rules for ecodes are stored
pyramidSearchPath = "/Users/lowell/Documents/GitHub/Lab_Pipelines/experiments/aodr/ecodes/"
# Conversion specifications
convertSpecs = "/Users/lowell/Documents/GitHub/Lab_Pipelines/experiments/aodr/AODR_experiment_LC.yaml"
# Base directory to save the output files from pyramid (hdf5 files)
baseSaveDir = "/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/Anubis/Converted/Behavior/Pyramid/"

currentFile = "Anubis_2024-06-25_13-40-57"
outputFname = baseSaveDir+currentFile+".hdf5"
cli.main(["convert", 
        "--trial-file", outputFname, 
        "--search-path", pyramidSearchPath, 
        "--experiment", convertSpecs, 
        "--readers", 
        "ttl_reader.session_dir="+dataSearchPath+currentFile,
        "message_reader.session_dir="+dataSearchPath+currentFile,
        "gaze_x_reader.session_dir="+dataSearchPath+currentFile,
        "gaze_y_reader.session_dir="+dataSearchPath+currentFile,
        "pupil_reader.session_dir="+dataSearchPath+currentFile,
        "phy_reader.params_file="+"/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/Anubis/Sorted/"+currentFile+"/spykingcircus2/phy/params.py"])

