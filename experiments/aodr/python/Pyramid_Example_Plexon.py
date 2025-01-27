# This isn't "optimized" to run on all machines.
# Removing << >> portion of pyramidSearchPath = "/Users/lowell/Documents/GitHub/Lab_Pipelines/experiments/aodr/<<ecodes/>>"
# was necessary on one machine but not another. 

from pyramid import cli
import pandas as pd
import os

# Directory where the sorted plexon data files are stored
dataSearchPath = "/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/MrM/Sorted/Plexon-sorted/"
# Directory where pyramid can find your ecode rules
pyramidSearchPath = "/Users/lowell/Documents/GitHub/Lab_Pipelines/experiments/aodr/ecodes/"
# Conversion specifications
convertSpecs = "/Users/lowell/Documents/GitHub/Lab_Pipelines/experiments/aodr/AODR_plex_experiment.yaml"
# Base directory to save the output files from pyramid (hdf5 files)
baseSaveDir = "/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/MrM/tmp/" #"/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/MrM/Converted/Sorted/Pyramid/"
# Name of the plexon file you want to use.
currentPlx = "MM_2023_01_19_V-ProRec_Sorted-04.plx"
# The name you'd like for the .hdf5 output file
outputFname = baseSaveDir+os.path.splitext(currentPlx)[0]+".hdf5"

# Run the file through pyramid
cli.main(["convert", 
          "--trial-file", outputFname, 
          "--search-path", pyramidSearchPath, 
          "--experiment", convertSpecs, 
          "--readers", 
          "plexon_reader.plx_file="+dataSearchPath+currentPlx])

