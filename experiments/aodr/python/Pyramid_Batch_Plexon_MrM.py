from pyramid import cli
import pandas as pd
import os, sys

# Directory where the sorted plexon data files are stored
dataSearchPath = "C:/Users/GoldLab/Box/GoldLab/Data/Physiology/AODR/Data/MrM/Sorted/"
pyramidSearchPath = "C:/Users/GoldLab/OneDrive/Documents/GitHub/Lab_Pipelines/experiments/aodr/ecodes/"
# Name of the excel file that documents the sessions (plx files) we want to include
sessionRecord = pd.read_excel("C:/Users/GoldLab/Box/GoldLab/Analysis/AODR/MrM_Ci_Units.xlsx")
sessionNames = sessionRecord['Name']
sessionNames = [sessionName.split('.')[0] for sessionName in sessionNames] # Get names of valid files
# Conversion specifications
convertSpecs = "C:/Users/GoldLab/OneDrive/Documents/GitHub/Lab_Pipelines/experiments/aodr/AODR_plex_experiment.yaml"
# Base directory to save the output files from pyramid (hdf5 files)
baseSaveDir = "C:/Users/GoldLab/Box/GoldLab/Data/Physiology/AODR/Data/MrM/Converted/Sorted/Pyramid/"
sys.path.append("C:/Users/GoldLab/OneDrive/Documents/GitHub/Lab_Pipelines/lwthompson2/experiments/aodr/python") # to make sure pyramid can access the custom collectors/enhancers/functions?

# Check that the current session file is one we want to use (is valid)
filenames = os.listdir(dataSearchPath)
valid_filenames = []
# For each file name in the directory
for filename in filenames:
    # Must be sorted
    if "Sorted" in filename:
        # Must be in the excel
        if any(base_name in filename for base_name in sessionNames):
            valid_filenames.append(filename)
# Sort ascending so that most recent versions are later (ex. 01 comes before 02 of the same session)
valid_filenames.sort()

# Keep only the most recently sorted version
final_filenames = []
i = 0
# For each valid filename
while i < len(valid_filenames)-1:
    
    # Get its name except the last digit and extension
    cur_file_base = valid_filenames[i][:-5]

    # If there's at least one file left to check, and the next file is a newer version
    while i < len(valid_filenames)-1 and valid_filenames[i+1][:-5] == cur_file_base:
        # Keep going
        i += 1
    # Now whatever is at position i is most recent, so save it
    final_filenames.append(valid_filenames[i])

    # Increment
    i += 1

print(len(final_filenames), "valid, sorted, and non-duplicate files out of", len(filenames), "in directory")

# For each Plexon file in dataSearchPath
for filename in final_filenames:

    print("\n", filename)
    f = os.path.join(dataSearchPath, filename)
    outputFname = baseSaveDir+os.path.splitext(filename)[0]+".hdf5"
    cli.main(["convert", 
      "--trial-file", outputFname, 
      "--search-path", pyramidSearchPath, 
      "--experiment", convertSpecs, 
      "--readers", 
      "plexon_reader.plx_file="+dataSearchPath+filename])