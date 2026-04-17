import sys, os
import phy
import spikeinterface.widgets as sw
from AODR_session_sorters import OpenEphysSessionSorter as OES
from pyramid import cli
import pandas as pd

# Usage:
# This script can be customized however you like, but it is currently divided into 3 main steps that can be run separately.
# In a terminal, activate the gold_pipelines environment and cd to directory containing this python script and run:
# 1) Initial Kilosort4 processing: python Kilo4_Neuropixel_Binary_Example.py initial
# 2) Post-Kilosort4 manual curation and timestamp overwriting: python Kilo4_Neuropixel_Binary_Example.py postkilosort
# 3) Conversion to pyramid trial file (hdf5): python Kilo4_Neuropixel_Binary_Example.py convert
# Having issues using multiprocessing/threading, especially while writing the binary file for kilosort? 
# Try a different terminal like cmd, powershell, anaconda prompt, or git bash. I had luck with cmd prompt.
# Notes on each step:
# 1) Currently using kilosort4 programmatically through spikeinterface. Alternatively you can convert to binary and run the kilosort gui manually (recommended for first time users).
# 2) # Phy GUI has some documented issues with Template and Feature views when installed in an environment with other stuff.
    # Currently I am creating a new conda environment just for phy to get around this using
    # the phy2_local.yml file in this repo. It seems to work fine if phy is installed in a clean environment:
    # https://github.com/cortex-lab/phy/issues/1356
        # cd path/to/my/spikesorting/output
        # phy template-gui params.py
    # Once you finish manual curation in phy, run this script with the postkilosort argument to overwrite timestamps. These timestamps will be more accurate
    # than the original ones from kilosort since kilosort assumes samples are taken at a constant linear rate, which is not always true.
# 3) Conversion step uses pyramid cli to convert the session to a pyramid trial file (hdf5). Make sure to set the correct paths below.

# Paths and file names
expDir = "C:/Users/lt711/Documents/GitHub/Lab_Pipelines/experiments/dotsRT" # This is the top level of your path in VS Code
sessDir = "Ducky_2026-04-16_12-53-31" # This is the name of your session folder that contains the raw data. It should be in the dataSearchPath below.
os.chdir(expDir)
dataSearchPath = "C:/NeuronalData/Experiments/Dots/Ducky/Raw/" # The folder that contains your sessDir folder.
pyramidSearchPath = expDir+"/ecodes"
convertSpecs = expDir+"/dotsRT_experiment_neuropixel_binary.yaml"
baseSaveDir = "C:/NeuronalData/Experiments/Dots/Ducky/Raw/"+sessDir+"/Converted/" # Where you want the converted files to go.
trialFileOutputName = baseSaveDir+sessDir+".hdf5" # The name of the converted file.
sorted_out = "C:/NeuronalData/Experiments/Dots/Ducky/Sorted/"+sessDir+"/"
sys.path.append(expDir+"/python")
params_path = sorted_out+"kilosort4/sorter_output/params.py"
stream_name = 'Record Node 102#OneBox-109.ProbeA-AP'

def run_initial_pipeline(): 
    # If you aren't sure about the stream_name, it will usually error out and print the available stream names in the error message. These change depending on equipment and save settings.
    sorter = OES(session_dir=dataSearchPath+sessDir+"/",
                 out_folder=sorted_out,
                 stream_name = stream_name,
                 sorter_name='kilosort4')
    sorter.clean_tree() # Delete previous sorting results if they exist
    sorter.read_data() # Reads data and sets the neuropixel probe (binary files come with probe attached already!)
    sorter.bandpass() # Bandpass filter the data
    # Really 2 methods to run Kilosort4: either call the GUI manually, or run it programmatically below.
    # 1) Run Kilosort4 programmatically through spikeinterface:
    sorter.run_kilosort4()
    # 2) Alternatively, you can run the Kilosort4 GUI manually by commenting out the sorter.run_kilosort4() line above
    # Then, in a terminal to run the gui: python -m kilosort
    print("Kilosort4 sorting complete")


def run_postkilosort():
    sorter = OES(session_dir=dataSearchPath+sessDir+"/",
                 out_folder=sorted_out,
                 stream_name = stream_name,
                 sorter_name='kilosort4')
    sorter.read_data()
    # Phy GUI has some documented issues with Template and Feature views when installed in an environment with other stuff.
    # Currently I am creating a new conda environment just for phy to get around this using
    # the phy2_local.yml file in this repo. It seems to work fine if phy is installed in a clean environment:
    # https://github.com/cortex-lab/phy/issues/1356
    # If it's fixed you should be able to use the following line to open the phy GUI programmatically:
    #sorter.open_phy(alt_path=sorter.out_folder+"/"+sorter.sorter_name+"/sorter_output/")
    sorter.overwrite_timestamps(alt_path=sorter.out_folder+"/"+sorter.sorter_name+"/sorter_output/")

def run_conversion():
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
        "phy_reader.params_file="+params_path])
    print("Conversion complete.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python Kilo4_Neuropixel_Example.py [initial|postkilosort|convert], running all steps...")
        run_initial_pipeline()
        run_postkilosort()
        run_conversion()
    else:
        step = sys.argv[1].lower()
        if step == "initial":
            run_initial_pipeline()
        elif step == "postkilosort":
            run_postkilosort()
        elif step == "convert":
            run_conversion()
        else:
            print("Unknown step. Use: initial, postkilosort, or convert.")