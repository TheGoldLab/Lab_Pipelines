from pyramid import cli
import pandas as pd
import os

# Directory where the sorted plexon data files are stored
dataSearchPath = "/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/MrM/Sorted/"
#dataSearchPath = "/Users/lowell/Data/Physiology/AODR/Data/Anubis/Raw/Sorted/"
pyramidSearchPath = "/Users/lowell/Documents/GitHub/Lab_Pipelines/experiments/aodr/ecodes/"
# Name of the excel file that documents the sessions (plx files) we want to include
sessionRecord = "/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Analysis/AODR/MrM_Ci_Units.xlsx"
# Conversion specifications
convertSpecs = "/Users/lowell/Documents/GitHub/Lab_Pipelines/experiments/aodr/AODR_plex_experiment.yaml"
# Base directory to save the output files from pyramid (hdf5 files)
#baseSaveDir = "/Users/lowell/Data/Physiology/AODR/Data/Anubis/Converted/Pyramid/"
baseSaveDir = "/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/MrM/Converted/Sorted/Pyramid/"

currentPlx = "MM_2023_01_19_V-ProRec_Sorted-04.plx"
outputFname = baseSaveDir+os.path.splitext(currentPlx)[0]+".hdf5"
cli.main(["convert", 
          "--trial-file", outputFname, 
          "--search-path", pyramidSearchPath, 
          "--experiment", convertSpecs, 
          "--readers", 
          "plexon_reader.plx_file="+dataSearchPath+currentPlx])

