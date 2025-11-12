from __future__ import annotations
from pathlib import Path
import platform
import shutil
import json
import spikeinterface.full as si
import kilosort
from kilosort import io, run_kilosort
from kilosort.gui.launch import launcher as launch_gui
import spikeinterface_gui
import spikeinterface.extractors as se
import spikeinterface.preprocessing as spre
import spikeinterface.sorters as ss
import spikeinterface.postprocessing as spost
import spikeinterface.qualitymetrics as sqm
import spikeinterface.exporters as sexp
import spikeinterface.curation as scur
from spikeinterface.curation import apply_curation
from spikeinterface.widgets import plot_sorting_summary
import spikeinterface.sortingcomponents as sc
import spikeinterface.widgets as sw
from probeinterface import generate_tetrode, ProbeGroup, Probe, generate_linear_probe
from probeinterface import write_probeinterface, read_probeinterface
from probeinterface.plotting import plot_probe, plot_probe_group
import subprocess, random, string, os
import numpy as np
import matplotlib.pyplot as plt
import logging
from open_ephys.analysis import Session
from phy.apps.template import template_gui


class OpenEphysSessionSorter():
    """Read continuous signal data from an Open Ephys session.

    This is based on the Open Ephys Python Tools Analysis module:
    https://github.com/open-ephys/open-ephys-python-tools/blob/main/src/open_ephys/analysis/README.md

    Args:
        session_dir:                        The open ephys session folder you'd like to sort
        stream_name:                        The data source you want to sort (e.g., 'Rhythm Data' for Open Ephys Intan Headstages)
        channel_names:                      List of integers specifying the channel numbers
        step_names:                         List of strings that correspond to steps/methods of the current class, in order, to implement
        result_name:                        Not currently used
        sorter_name:                        The sorting engine to use, e.g., 'spykingcircus2', limited by the sorters installed
        out_folder:                         String indicating the output folder
        freq_min:                           Min frequency (Hz) for the bandpass filter
        freq_max:                           Max frequency (Hz) for the bandpass filter            
    """

    def __init__(
        self,
        session_dir: str = None,
        stream_name: list[str] = ['Rhythm Data'],
        channel_names: list[int] = None,
        step_names: list[str] = None,
        result_name: str = None,
        sorter_name: str = 'spykingcircus2',
        out_folder: str = None,
        freq_min: int = 300,
        freq_max: int = 6000
    ) -> None:
        self.session_dir = session_dir
        self.stream_name = stream_name
        self.channel_names = channel_names
        self.step_names = step_names
        self.result_name = result_name
        self.sorter_name = sorter_name
        self.out_folder = out_folder
        self.freq_min = freq_min
        self.freq_max = freq_max

    def clean_tree(self):
        print("Cleaning output folder...")
        # clean
        folders = [
            self.out_folder
        ]
        for folder in folders:
            if Path(folder).exists():
                shutil.rmtree(folder)
    
    def read_data(self):
        print("Reading data from Open Ephys session...")
        # Currently assumes Open Ephys GUI saved as nwb, limited to Intan headstages or Neuropixels connected to an NI Box
        self.logger = logging.getLogger(__name__)
        
        if self.stream_name == 'Rhythm Data' or self.stream_name == 'acquisition_board':
            # For Open Ephys Intan Headstages
            if not os.path.isfile(self.session_dir):
                self.recording_file = self.session_dir + os.listdir(self.session_dir)[0] + "/experiment1.nwb"
            else:
                self.recording_file = self.session_dir
            data_source: str = 'acquisition/Acquisition Board-106.acquisition_board'
            self.recording = se.read_nwb_recording(file_path=self.recording_file, electrical_series_path=data_source)
        elif self.stream_name == 'ProbeA-AP':
            # Using Neuropixels probe with Open Ephys GUI saved as nwb
            if not os.path.isfile(self.session_dir):
                self.recording_file = self.session_dir + os.listdir(self.session_dir)[0] + "/experiment1.nwb"
            else:
                self.recording_file = self.session_dir
            data_source: str = 'acquisition/Neuropix-PXI-122.ProbeA-AP' # If wrong, output error will list available series options
            self.recording = se.read_nwb_recording(file_path=self.recording_file, electrical_series_path=data_source)
            probe_dir = Path(self.session_dir + os.listdir(self.session_dir)[0] + "/") # assuming your probe file is in this directory
            self.np_probe = next(probe_dir.glob("*.json"), None)  # returns a Path or None
            if self.np_probe is None:
                raise FileNotFoundError(f"No Neuropixels probe .json file found in {probe_dir}")
            else:
                pgroup = read_probeinterface (self.np_probe)
                self.recording.set_probegroup(pgroup, in_place=True)
    
    def set_tetrode(self):
        print("Setting tetrode probe...")
        probegroup = ProbeGroup()
        tetrode = generate_tetrode()
        tetrode.set_device_channel_indices(self.channel_names)
        probegroup.add_probe(tetrode)
        #probegroup.set_global_device_channel_indices(self.channel_names)
        # set this to the recording
        self.recording = self.recording.set_probegroup(probegroup, group_mode='by_probe')

    def set_linear(self):
        print("Setting linear probe...")
        linear_probe = generate_linear_probe(num_elec=len(self.channel_names), ypitch=30)
        linear_probe.set_device_channel_indices(self.channel_names)
        self.recording = self.recording.set_probe(linear_probe)

    def set_single(self):
        print("Setting single channel probe...")
        probe = Probe(ndim=2, si_units='um')
        ch_positions = np.zeros((1, 2))
        probe.set_contacts(positions=ch_positions, shapes='circle', shape_params={'radius': 5})
        probe.set_device_channel_indices(self.channel_names)
        self.recording = self.recording.set_probe(probe)

    def bandpass(self):
        print("Applying bandpass filter...")
        # Filter w/bandpass
        self.recording = spre.bandpass_filter(recording=self.recording, freq_min=self.freq_min, freq_max=self.freq_max)

    def single_ch_sorter_and_analyzer(self):
        print("Running MountainSort5 sorter for single channel data...")
        job_kwargs = dict(n_jobs=1, progress_bar=True)
        si.set_global_job_kwargs(**job_kwargs)
        params = si.get_default_sorter_params('mountainsort5')
        #params['detect_threshold'] = 4.75 # I usually start lower than default for first sort then move up
        params['npca_per_channel'] = 5 # Haven't found much of a meaningful difference changing this for single electrode
        params['scheme2_training_recording_sampling_mode'] = 'uniform' # uniform, initial
        params['filter'] = True  # For some reason,  making this false changes the detect sign. But leaving true and not using my preprocessing filter results in the data not being filtered?
        self.sorting = si.run_sorter('mountainsort5', self.recording,
                                            folder=self.out_folder+"/"+self.sorter_name, 
                                            verbose=True, remove_existing_folder=True, **params)
        #sorting = si.run_sorter(self.sorter_name, self.recording,
        #                                    folder=self.out_folder+"/"+self.sorter_name, 
        #                                    verbose=True, remove_existing_folder=True, **params)
        self.sorting_analyzer = si.create_sorting_analyzer(self.sorting, self.recording,
                                                    format="binary_folder", folder=self.out_folder+"/analyzer", 
                                                    overwrite=True,
                                                    **job_kwargs)
        self.sorting_analyzer.compute("random_spikes", method="uniform", max_spikes_per_unit=500)
        self.sorting_analyzer.compute("waveforms", **job_kwargs)
        self.sorting_analyzer.compute("templates")
        self.sorting_analyzer.compute("template_similarity")
        self.sorting_analyzer.compute("noise_levels")
        self.sorting_analyzer.compute("unit_locations", method="monopolar_triangulation")
        self.sorting_analyzer.compute("correlograms", window_ms=100, bin_ms=5.)
        self.sorting_analyzer.compute("isi_histograms")
        self.sorting_analyzer.compute("principal_components", n_components=3, mode='by_channel_global', whiten=True, **job_kwargs)
        self.sorting_analyzer.compute("quality_metrics", metric_names=["snr", "firing_rate"])
        self.sorting_analyzer.compute("spike_amplitudes", **job_kwargs)

    def run_kilosort4(self):
        # Does not use the gui, but instead runs kilosort4 directly from the API using default parameters.
        job_kwargs = dict(n_jobs=1, progress_bar=True)
        #si.set_global_job_kwargs(**job_kwargs)
        params = si.get_default_sorter_params('kilosort4')
        self.sorting = si.run_sorter_by_property('kilosort4', self.recording,
                                            grouping_property='group',     
                                            folder=self.out_folder+"/"+self.sorter_name, 
                                            verbose=True, docker_image=False, **params)
        # Now use parallelization?
        job_kwargs = dict(n_jobs=-1, progress_bar=True)
        self.sorting_analyzer = si.create_sorting_analyzer(self.sorting, self.recording,
                                                    format="binary_folder", folder=self.out_folder+"/analyzer", 
                                                    overwrite=True,
                                                    **job_kwargs)
        self.sorting_analyzer.compute("random_spikes", method="uniform", max_spikes_per_unit=500)
        self.sorting_analyzer.compute("waveforms", **job_kwargs)
        self.sorting_analyzer.compute("templates")
        self.sorting_analyzer.compute("template_similarity")
        self.sorting_analyzer.compute("noise_levels")
        self.sorting_analyzer.compute("unit_locations", method="monopolar_triangulation")
        self.sorting_analyzer.compute("correlograms", window_ms=100, bin_ms=5.)
        self.sorting_analyzer.compute("isi_histograms")
        self.sorting_analyzer.compute("principal_components", n_components=3, mode='by_channel_global', whiten=True, **job_kwargs)
        self.sorting_analyzer.compute("quality_metrics", metric_names=["snr", "firing_rate"])
        self.sorting_analyzer.compute("spike_amplitudes", **job_kwargs)
                                                    
    def convert_to_binary(self):
        # Create a new binary file and copy the data to it 60,000 samples at a time.
        # Depending on your system’s memory, you could increase or decrease the number of samples
        # loaded on each iteration. This will also export the associated probe information as a
        # ‘.prb’ file, if present.
        
        # Note: Data will be saved as np.int16 by default since that is the standard
        #       for ephys data. If you need a different data type for whatever reason
        #       such as `np.uint16`, be sure to update this.
        
        # If no probe information was loaded through spikeinterface, you will need to specify
        # the probe yourself, either as a .prb file or as a .json with Kilosort4’s expected
        # format.
        print("Converting to binary for kilosort (this might take a bit)...")
        dtype = np.int16
        self.filename, N, c, s, fs, probe_path = io.spikeinterface_to_binary(
            self.recording, self.out_folder, data_name=self.sorter_name+'.bin', dtype=dtype,
            chunksize=60000, export_probe=True, probe_name='kilosort_probe.prb')
        
        # At this point, it’s a good idea to open the Kilosort gui and check that the data
        # and probe appear to have been loaded correctly and no settings need to be tweaked.
        # You will need to input the path to the binary datafile, the folder where results
        # should be saved, and select a probe file.

    def run_kilosort4_gui(self):
        # Best practice for Kilosort4 on Windows:

        # Always launch the Kilosort4 GUI in a separate Python process or kernel, not from within a script that also runs other code or uses multiprocessing/threading.
        # Avoid running heavy data processing and GUI code in the same script/session.
        # How to do this:

        # Run your pipeline up to the point of binary conversion.
        # Manually launch the Kilosort4 GUI from a separate terminal or kernel, pointing it to the binary and probe files.
        # After sorting, continue with downstream analysis in your main script.
        # Why?

        # This avoids Windows DLL/threadpool conflicts and GUI event loop issues.
        # It matches the recommended workflow in the Kilosort documentation.
        # If you want, I can help you refactor your script to separate the GUI launch step, or provide a command to launch the GUI manually. Let me know your preference!
        
        # Try to Run Kilosort4 GUI, it will probably open but when you run the program it will throw a long error.
        try:
        # Attempt to launch the Kilosort GUI
            launch_gui(filename=self.filename, reset=False, skip_load=False)
        except SystemExit as e:
        # Check if the error is the specific 'NoneType' issue
            if e.code==0:
                print("Caught and ignored the Kilosort closing error...")
            else:
            # Re-raise the exception if it's not the expected one
                raise
        

    def open_sigui(self):
        plot_sorting_summary(sorting_analyzer=self.sorting_analyzer, curation=True, backend='spikeinterface_gui')

        # Potentially load the curation JSON file
        curation_json = os.path.join(self.out_folder, 'analyzer', 'spikeinterface_gui', 'curation_data.json')
        if os.path.isfile(curation_json):
            print("Applying curation from GUI...")
            with open(curation_json, 'r') as f:
                curation_dict = json.load(f)

            # apply the curation to the sorting output
            self.cured_sorting = apply_curation(self.sorting, curation_dict_or_model=curation_dict)

            # apply the curation to the sorting analyzer
            self.cured_sorting_analyzer = apply_curation(self.sorting_analyzer, curation_dict_or_model=curation_dict)

    def export_to_phy(self):
        print("Exporting to Phy...")
        if hasattr(self, 'cured_sorting'):
            # self.cured_sorting exists
            print("cured_sorting is available")
            si.export_to_phy(self.cured_sorting_analyzer, output_folder=self.out_folder+"phy", verbose=False)
        else:
            # self.cured_sorting does not exist
            print("cured_sorting is not available")
            si.export_to_phy(self.sorting_analyzer, output_folder=self.out_folder+"phy", verbose=False)

    def overwrite_timestamps(self, alt_path=None):
        print("Overwriting timestamps in Phy params.py...")
        first_sample_time = self.recording.get_start_time()
        # Overwrite the params.py file to set the first time stamp for the first sample
        if alt_path is None:
            params_path = self.out_folder+"phy/params.py"
        else:
            params_path = alt_path+"params.py"

        if not os.path.exists(params_path):
            print(f"ERROR: {params_path} does not exist.")
            return
        else:
            with open(params_path, "r") as f:
                lines = f.readlines()
            with open(params_path, "w") as f:
                for line in lines:
                    if line.startswith("offset"):
                        f.write(f"offset = {first_sample_time}\n")
                    else:
                        f.write(line)

    def open_phy(self,alt_path=None):
        if alt_path is None:
            template_gui(self.out_folder+"phy/params.py")
        else:
            template_gui(alt_path+"params.py")
