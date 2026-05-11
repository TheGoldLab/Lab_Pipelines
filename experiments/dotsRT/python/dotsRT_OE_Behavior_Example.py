from pyramid import cli
import sys, os

# Example processing script for converting behavioral data from a dotsRT experiment using Pyramid.
# Written: LWT 03-20-2026
# Define some paths,
# Define some methods (in this case just convert)
# Run the methods in a main function or call them directly.

# Paths and file names
expDir = "/Users/lowell/Documents/GitHub/Lab_Pipelines/experiments/dotsRT" # This is the top level of your path in VS Code
sessDir = "Ducky_2026-04-16_12-53-31" # This is the name of your session folder that contains the raw data. It should be in the dataSearchPath below.
os.chdir(expDir)
dataSearchPath = "C:/NeuronalData/Experiments/Dots/Ducky/Raw/" # The folder that contains your sessDir folder.
pyramidSearchPath = expDir+"/ecodes"
convertSpecs = expDir+"/dotsRT_experiment_behavior.yaml"
baseSaveDir = "C:/NeuronalData/Experiments/Dots/Ducky/Raw/"+sessDir+"/Converted/" # Where you want the converted files to go.
trialFileOutputName = baseSaveDir+sessDir+".hdf5" # The name of the converted file.
sys.path.append(expDir+"/python") # Sometimes necessary...

# Imagine you have multiple steps, this is just for converting behavioral data so there is only 1 step: conversion.
def run_conversion():
    # Convert to pyramid format - this requires sorted data and the raw data.
    # cli is pyramid's command line interface, but you can also run it programmatically as below. Make sure to set the correct paths above.
    cli.main(["convert", 
            "--trial-file", trialFileOutputName, 
            "--search-path", pyramidSearchPath, 
            "--experiment", convertSpecs, 
            "--readers", 
            "ttl_reader.session_dir="+dataSearchPath+sessDir,
            "message_reader.session_dir="+dataSearchPath+sessDir,
            "gaze_x_reader.session_dir="+dataSearchPath+sessDir,
            "gaze_y_reader.session_dir="+dataSearchPath+sessDir,
            "pupil_reader.session_dir="+dataSearchPath+sessDir])

if __name__ == "__main__":
    run_conversion()