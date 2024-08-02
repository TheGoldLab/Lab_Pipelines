from pathlib import Path
import platform
import shutil
import argparse
import spikeinterface.full as si
import spikeinterface_gui
import spikeinterface.extractors as se
import spikeinterface.preprocessing as spre
import spikeinterface.sorters as ss
import spikeinterface.postprocessing as spost
import spikeinterface.qualitymetrics as sqm
import spikeinterface.exporters as sexp
import spikeinterface.curation as scur
import spikeinterface.sortingcomponents as sc
import spikeinterface.widgets as sw
from probeinterface import generate_tetrode, ProbeGroup
from probeinterface.plotting import plot_probe
import os
import numpy as np
import matplotlib.pyplot as plt
import logging

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
        stream_name: str = 'Rhythm Data',
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

        for step in self.step_names:
            try:
                func = self.__getattribute__(step)
                func()
                done = '...OK'
            except Exception as err:
                done = f'...Fail, Error: {err}'
            print(step, done)
    
    def read_data(self):
        self.logger = logging.getLogger(__name__)
        self.recording_file = self.session_dir+"/Record Node 104/experiment1.nwb"
        if self.stream_name == 'Rhythm Data':
            data_source: str = 'acquisition/OE FPGA Acquisition Board-100.Rhythm Data'
        self.recording = se.read_nwb(file_path=self.recording_file, electrical_series_path=data_source)

    def set_tetrode(self):
        probegroup = ProbeGroup()
        tetrode = generate_tetrode()
        tetrode.set_device_channel_indices(self.channel_names)
        probegroup.add_probe(tetrode)
        # set this to the recording
        self.recording = self.recording.set_probegroup(probegroup, group_mode='by_probe')

    def bandpass(self):
        # Filter w/bandpass
        self.recording = spre.bandpass_filter(recording=self.recording, freq_min=self.freq_min, freq_max=self.freq_max)

    def run_one_sorter_and_analyzer(self):
        # I believe a custom compute json-like file could also be used.
        job_kwargs = dict(n_jobs=4, progress_bar=True, chunk_duration="1s")
        si.set_global_job_kwargs(**job_kwargs)
        sorting = si.run_sorter(self.sorter_name, self.recording, output_folder=self.out_folder+"/"+self.sorter_name, 
                                verbose=True, remove_existing_folder=True)
        sorting_analyzer = si.create_sorting_analyzer(sorting, self.recording,
                                                    format="binary_folder", folder=self.out_folder+"/analyzer", 
                                                    overwrite=True,
                                                    **job_kwargs)
        sorting_analyzer.compute("random_spikes", method="uniform", max_spikes_per_unit=500)
        sorting_analyzer.compute("waveforms", **job_kwargs)
        sorting_analyzer.compute("templates")
        sorting_analyzer.compute("template_similarity")
        sorting_analyzer.compute("noise_levels")
        sorting_analyzer.compute("unit_locations", method="monopolar_triangulation")
        sorting_analyzer.compute("correlograms", window_ms=100, bin_ms=5.)
        sorting_analyzer.compute("isi_histograms")
        sorting_analyzer.compute("principal_components", n_components=3, mode='by_channel_global', whiten=True, **job_kwargs)
        sorting_analyzer.compute("quality_metrics", metric_names=["snr", "firing_rate"])
        sorting_analyzer.compute("spike_amplitudes", **job_kwargs)

    def open_sigui(self):
        analyzer = si.load_sorting_analyzer(self.out_folder+"/analyzer")
        app = spikeinterface_gui.mkQApp()
        win = spikeinterface_gui.MainWindow(analyzer)
        win.show()
        app.exec_()

    def export_to_phy(self):
        analyzer = si.load_sorting_analyzer(self.out_folder+"/analyzer")
        si.export_to_phy(analyzer, output_folder=self.out_folder+"/phy", verbose=False)

    def open_phy():
        os.system("phy template-gui ./phy_example/params.py")





