from pyramid import cli
import pandas as pd
import os

# Directory where the sorted plexon data files are stored
dataSearchPath = "/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/Anubis/Raw/Behavior/"
pyramidSearchPath = "/Users/lowell/Documents/GitHub/Lab_Pipelines/experiments/aodr/ecodes/"
# Conversion specifications
convertSpecs = "/Users/lowell/Documents/GitHub/Lab_Pipelines/experiments/aodr/AODR_experiment.yaml"
# Base directory to save the output files from pyramid (hdf5 files)
baseSaveDir = "/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Data/Anubis/Converted/Behavior/Pyramid/"
# Overwrite existing files or not
overwrite = False
# List of files to process
files = os.listdir(dataSearchPath)
# Loop through the files and process them
if not files:
    print("No files found in the specified directory.")
    exit()
f_num = 0
for currentFile in files:
    f_num += 1
    outputFname = baseSaveDir+currentFile+".hdf5"
    if os.path.exists(outputFname) and not overwrite:
        print(f"\nOutput file already exists, skipping: {currentFile}\n")
        continue
    else:
        print(f"\nProcessing file: {f_num}/{len(files)} {currentFile}\n")
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
    
print("\nAll files processed.\n")


