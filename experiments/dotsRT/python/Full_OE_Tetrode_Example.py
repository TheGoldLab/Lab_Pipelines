import spikeinterface.widgets as sw
from AODR_session_sorters import OpenEphysSessionSorter as OES
from pyramid import cli
import pandas as pd
import sys, os

# Paths and file names
expDir = "C:/Users/lt711/Documents/GitHub/Lab_Pipelines/experiments/dotsRT" # This is the top level of your path in VS Code
sessDir = "MrM_2025-10-31_11-31-10" # This is the name of your session folder that contains the raw data. It should be in the dataSearchPath below.
os.chdir(expDir)
dataSearchPath = "C:/Users/lt711/Box/GoldLab/Data/Physiology/AODR/dlPFC/MrM/Raw/Neuronal/Tetrode/" # TODO: update to your data path
pyramidSearchPath = expDir+"/ecodes"
convertSpecs = expDir+"/dotsRT_experiment_tetrode.yaml"
baseSaveDir = "C:/NeuronalData/Converted/" # Where you want the converted files to go.
trialFileOutputName = baseSaveDir+sessDir+".hdf5" # The name of the converted file.
sorted_out = 'C:/NeuronalData/Sorted/'+sessDir+"/" # The output of the sorted neuronal data.
sys.path.append(expDir+"/python") # Sometimes necessary...

def run_pipeline():
    # Set up and run sorter - this is only grabbing neuronal data
    sorter = OES(session_dir=dataSearchPath+sessDir+"/", channel_names=[1,2,3,4],
                 out_folder=sorted_out,
                 stream_name='acquisition_board',
                 overwrite_timestamps=True,
                 sorter_name='single_channel',
                 step_names=[
                     'clean_tree',
                     'read_data',
                     'set_tetrode',
                     'bandpass',
                     'single_ch_sorter_and_analyzer',
                     'open_sigui',
                     'export_to_phy'
                 ])

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
            "pupil_reader.session_dir="+dataSearchPath+sessDir,
            "phy_reader.params_file="+sorted_out+"/phy/params.py"])

if __name__ == "__main__":
    run_pipeline()
    run_conversion()