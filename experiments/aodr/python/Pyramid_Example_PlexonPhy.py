# In some cases, we used lienar electrode arrays where an automatic sorting routine might be better suited.
# For the dlPFC recordings in Monkey MrM, an S-Probe was utilized and Kilsort 3. The spike output is therefore saved as a phy file.
# In this case we need 2 file "readers"
# 1) A version of the plexon file with event and eye data
# 2) A phy folder with the spike-sorted data

from pyramid import cli
import pandas as pd
import os

# Directory where the sorted plexon data files are stored
dataSearchPath = "/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/MrM/Sorted/"
# Directory where pyramid can find your ecode rules
pyramidSearchPath = "/Users/lowell/Documents/GitHub/Lab_Pipelines/experiments/aodr/ecodes/"
# Conversion specifications
convertSpecs = "/Users/lowell/Documents/GitHub/Lab_Pipelines/experiments/aodr/AODR_plex_phy_experiment.yaml"
# Base directory to save the output files from pyramid (hdf5 files)
baseSaveDir = "/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/MrM/Converted/Sorted/Pyramid/"
# Name of the plexon file you want to use.
currentPlx = "MM_2022_11_30_BV-ProRec_Sorted-03.plx"
# Name of the phy folder containing the params.py file
phyFolder = dataSearchPath+"/Phy folders/MM_2022_11_30_BV-ProRec/phy/params.py"
# The name you'd like for the .hdf5 output file
outputFname = baseSaveDir+os.path.splitext(currentPlx)[0]+".hdf5"

# Run the file through pyramid
cli.main(["convert", 
          "--trial-file", outputFname, 
          "--search-path", pyramidSearchPath, 
          "--experiment", convertSpecs, 
          "--readers", 
          "plexon_reader.plx_file="+dataSearchPath+currentPlx,
          "phy_reader.params_file="+phyFolder])

