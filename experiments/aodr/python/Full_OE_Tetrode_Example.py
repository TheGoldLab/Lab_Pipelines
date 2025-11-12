import spikeinterface.widgets as sw
from AODR_session_sorters import OpenEphysSessionSorter as OES
from pyramid import cli
import pandas as pd
import sys, os

# Paths and file names
expDir = "C:/Users/lt711/Documents/GitHub/Lab_Pipelines/experiments/aodr"
sessDir = "MrM_2025-10-31_11-31-10" #"MrM_2025-09-26-Trimmed"
os.chdir(expDir)
dataSearchPath = "C:/Users/lt711/Box/GoldLab/Data/Physiology/AODR/dlPFC/MrM/Raw/Neuronal/Tetrode/"
pyramidSearchPath = expDir+"/ecodes"
convertSpecs = expDir+"/AODR_experiment_tetrode.yaml"
baseSaveDir = "C:/NeuronalData/Converted/"
currentFile = "experiment1.nwb"
trialFileOutputName = baseSaveDir+sessDir+".hdf5"
sorted_out = 'C:/NeuronalData/Sorted/'+sessDir+"/"
sys.path.append(expDir+"/python")

def run_pipeline():
    # Set up and run sorter
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
    # Convert to pyramid format
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