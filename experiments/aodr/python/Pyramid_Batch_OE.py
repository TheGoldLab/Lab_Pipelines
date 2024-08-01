from pyramid import cli
import pandas as pd
import os

# Directory where the sorted plexon data files are stored
dataSearchPath = "/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/Anubis/Raw/Behavior/"
pyramidSearchPath = "/Users/lowell/Documents/GitHub/Lab_Pipelines/experiments/aodr/ecodes/"
# Name of the excel file that documents the sessions (plx files) we want to include
sessionRecord = "/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Analysis/AODR/MrM_Ci_Units.xlsx"
# Conversion specifications
convertSpecs = "/Users/lowell/Documents/GitHub/Lab_Pipelines/experiments/aodr/AODR_experiment.yaml"
# Base directory to save the output files from pyramid (hdf5 files)
baseSaveDir = "/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/Anubis/Converted/Behavior/Pyramid/"

files = os.listdir(dataSearchPath)
for currentFile in files:
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
            "pupil_reader.session_dir="+dataSearchPath+currentFile])


