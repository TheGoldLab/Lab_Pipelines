import sys, os
import spikeinterface.widgets as sw
from AODR_session_sorters import OpenEphysSessionSorter as OES
from pyramid import cli
import pandas as pd

# Usage:
# Run initial steps: python Kilo4_Neuropixel_Example.py initial
# Then manually run Kilosort4 GUI to curate and save results: python -m kilosort
# After running Kilosort4 GUI, run post-processing: python Kilo4_Neuropixel_Example.py postkilosort (overwrite timestamps after manual curation in phy)
# Run conversion: python Kilo4_Neuropixel_Example.py convert
# Having issues using multiprocessing/threading, especially during writing? 
# Try a different terminal like cmd, powershell, anaconda prompt, or git bash. I had luck with cmd prompt.

# Paths and file names
expDir = "C:/Users/lt711/Documents/GitHub/Lab_Pipelines/experiments/aodr"
sessDir = "MrM_NP_2025-11-14_12-39-27"
os.chdir(expDir)
dataSearchPath = "C:/NeuronalData/Raw/"
pyramidSearchPath = expDir+"/ecodes"
convertSpecs = expDir+"/AODR_experiment_neuropixel.yaml"
baseSaveDir = "C:/NeuronalData/Converted/"
currentFile = "experiment1.nwb"
trialFileOutputName = baseSaveDir+sessDir+".hdf5"
sorted_out = 'C:/NeuronalData/Sorted/'+sessDir+"/"
sys.path.append(expDir+"/python")
params_path = sorted_out+"kilosort4/sorter_output/params.py"


def run_initial_pipeline():
    sorter = OES(session_dir=dataSearchPath+sessDir+"/",
                 out_folder=sorted_out,
                 stream_name = 'ProbeA-AP',
                 sorter_name='kilosort4')
    sorter.clean_tree()
    sorter.read_data()
    sorter.bandpass()
    # Really 2 methods to run Kilosort4: either call the GUI manually, or run it programmatically below.
    # 1) Run Kilosort4 programmatically through spikeinterface:
    sorter.run_kilosort4()
    # 2) Alternatively, you can run the Kilosort4 GUI manually by uncommenting the line below and commenting out the sorter.run_kilosort4() line:
    #sorter.convert_to_binary()
    # In a terminal to run the gui you need to run: python -m kilosort
    print("Kilosort4 sorting complete")


def run_postkilosort():
    sorter = OES(session_dir=dataSearchPath+sessDir+"/",
                 out_folder=sorted_out,
                 stream_name = 'ProbeA-AP',
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