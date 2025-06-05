import kilosort
from kilosort import io
import spikeinterface as si
import spikeinterface.widgets as sw
from spikeinterface_gui import run_mainwindow
from spikeinterface.extractors import read_phy
import subprocess, sys, os
from AODR_session_sorters import OpenEphysSessionSorter as OES
import numpy as np
import matplotlib

# Experiment directory top level - should contain the subfolders like ecodes, python, matlab.
expDir = "C:/Users/lt711/Documents/GitHub/Lab_Pipelines/experiments/aodr"
os.chdir(expDir) # regular python files will run from the first open folder in your tree, but notebooks will work from wherever the notebook is stored.
# Directory where the raw files are stored to be converted/sorted
#dataSearchPath = "C:/Users/GoldLab/Box/GoldLab/Data/Physiology/AODR/Data/Anubis/Raw/Behavior/"
dataSearchPath = "C:/Users/lt711/Documents/Anubis_2024-09-16_13-41-27/Record Node 106/"
# Where the rules for ecodes are stored
pyramidSearchPath = expDir+"/ecodes"
# Conversion specifications
convertSpecs = expDir+"/AODR_experiment_LC.yaml"
# Base directory to save the output files from pyramid (hdf5 files)
#baseSaveDir = "C:/Users/GoldLab/Box/GoldLab/Data/Physiology/AODR/Data/Anubis/Converted/Behavior/Pyramid/"
baseSaveDir = "C:/Users/lt711/Documents/Docker_Tetrode_Test/" # test output folder
# The Open Ephys session directory (technically not a file, but a folder)
#currentFile = "Anubis_2024-08-05_12-06-56"
currentFile = "experiment1.nwb"
# Full directory to save the output files from pyramid (hdf5 files)
trialFileOutputName = baseSaveDir+currentFile+".hdf5"
# Directory to save the output files from sorting
#sorted_out = dataSearchPath.split("Raw")[0]+"Sorted/"+currentFile
sorted_out = baseSaveDir
sys.path.append(expDir+"/python") # to make sure pyramid can access the custom collectors/enhancers/functions?

my_rec = OES(session_dir=dataSearchPath+currentFile, channel_names=[2,3,4,5],
             out_folder=sorted_out,
             sorter_name='kilosort4',
             step_names=[
                 'clean_tree',
                 'read_data',                       # Has to be included to do anything else
                 'set_tetrode',
                 'bandpass'])

# For this test recording using a fake neuron, it was not stable until ~3600 seconds in.
my_end_time = my_rec.recording.get_end_time()
new_rec = my_rec.recording.time_slice(start_time=3600, end_time=my_end_time) 

# Convert the Open Ephys data to a binary file for kilosort
dtype = np.int16
filename, N, c, s, fs, probe_path = io.spikeinterface_to_binary(
        new_rec, my_rec.out_folder, data_name='data.bin', dtype=dtype,
        chunksize=60000, export_probe=True, probe_name='probe.prb')

#sw.plot_traces(new_rec, backend="matplotlib", mode="line", show_channel_ids=True)

# Run kilosort on the binary file
subprocess.run(["python", "-m", "kilosort"])

# Create an SI sorting extractor from the kilosort output
phy_sorting = read_phy(my_rec.out_folder+my_rec.sorter_name)

# Create an SI sorting analyzer from the kilosort output/raw recording
# Job arguments for parallel processing
# Note: the default job_kwargs are n_jobs=1, progress_bar=False, chunk_duration="1s", pool_engine="multiprocessing"
# HOWEVER, the default pool_engine causes this entire script to rerun (e.g., it'll rerun kilosort), so we need to set it to "thread".
'''
job_kwargs = dict(n_jobs=-1, progress_bar=True, chunk_duration="1s", pool_engine="thread")

sorting_analyzer = si.create_sorting_analyzer(
                                        phy_sorting, new_rec,
                                        folder=my_rec.out_folder+"analyzer", 
                                        overwrite=True
                                        )

sorting_analyzer.compute("random_spikes", method="uniform", max_spikes_per_unit=500)
sorting_analyzer.compute("waveforms", **job_kwargs)
sorting_analyzer.compute("templates", **job_kwargs)
sorting_analyzer.compute("noise_levels")
sorting_analyzer.compute("unit_locations", method="monopolar_triangulation")
sorting_analyzer.compute("isi_histograms")
sorting_analyzer.compute("correlograms", window_ms=100, bin_ms=5.)
sorting_analyzer.compute("principal_components", n_components=3, mode='by_channel_global', whiten=True, **job_kwargs)
sorting_analyzer.compute("quality_metrics", metric_names=["snr", "firing_rate"])
sorting_analyzer.compute("template_similarity")
sorting_analyzer.compute("spike_amplitudes", **job_kwargs)

#run_mainwindow(sorting_analyzer)
'''

# Check phy output
os.system("phy template-gui "+my_rec.out_folder+my_rec.sorter_name+"/params.py")
