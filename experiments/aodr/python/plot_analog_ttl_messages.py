import spikeinterface.extractors as se
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector
import numpy as np
from open_ephys.analysis import Session
from collections import defaultdict


# --- CONFIG ---
NWB_FILE = r"C:\NeuronalData\Raw\MrM_NP_2025-11-14_12-39-27\Record Node 107\experiment1.nwb"  # Set this to your NWB file
SESSION_DIR = r"C:\NeuronalData\Raw\MrM_NP_2025-11-14_12-39-27"  # Set this to your Open Ephys session folder
ANALOG_CHANNELS = [0, 1]  # Acquisition board channels to plot
WINDOW_SEC = 5.0  # Default view window in seconds

# --- LOAD session data ---
session = Session(SESSION_DIR)
recording = session.recordnodes[0].recordings[0]

# --- LOAD ANALOG DATA ---
# Use recording.nwb['acquisition'] to get analog data and timestamps efficiently
analog_data = None
analog_timestamps = None
sampling_rate = None
additional_analog_data = None
additional_analog_timestamps = None
additional_sampling_rate = None
datasets = list(recording.nwb["acquisition"].keys())
for item in datasets:
    # Acquisition board stream
    if "acquisition_board" in item and "TTL" not in item:
        cont = recording.Continuous(recording.nwb, item)
        analog_data = cont.samples[:, ANALOG_CHANNELS]
        analog_timestamps = cont.timestamps
        if len(analog_timestamps) > 1:
            sampling_rate = 1.0 / np.mean(np.diff(analog_timestamps))
        else:
            sampling_rate = None
    # NI-DAQmx stream
    elif "PXIe-6363" in item and "TTL" not in item:
        cont = recording.Continuous(recording.nwb, item)
        additional_analog_data = cont.samples[:, ANALOG_CHANNELS]
        additional_analog_timestamps = cont.timestamps
        if len(additional_analog_timestamps) > 1:
            additional_sampling_rate = 1.0 / np.mean(np.diff(additional_analog_timestamps))
        else:
            additional_sampling_rate = None


# Get TTL events (only when bit is high)
ttl_events = recording.events
ttl_pulses = []  # List of (timestamp, line) for TTL high events
for _, row in ttl_events.iterrows():
    if row.state == 1:  # Only plot when bit is high
        ttl_pulses.append((row.timestamp, row.line))

# Get messages
messages = []  # List of (timestamp, text)
if 'messages' in recording.nwb['acquisition']:
    message_count = len(recording.nwb['acquisition']['messages']['data'])
    for index in range(message_count):
        text = recording.nwb['acquisition']['messages']['data'][index]
        timestamp = recording.nwb['acquisition']['messages']['timestamps'][index]
        messages.append((timestamp, text))

# --- PLOTTING ---
class InteractivePlot:
    def __init__(self, analog_data, ttl_pulses, messages, sampling_rate, window_sec, additional_analog_data=None, additional_sampling_rate=None, additional_start_time=0.0):
        self.analog_data = analog_data
        self.ttl_pulses = ttl_pulses
        self.messages = messages
        self.sampling_rate = sampling_rate
        self.window_sec = window_sec
        self.n_samples = analog_data.shape[0]
        self.additional_analog_data = additional_analog_data
        self.additional_sampling_rate = additional_sampling_rate
        self.additional_start_time = additional_start_time
        # Get the actual start time from the recording object
        if hasattr(recording_analog, 'get_start_time'):
            self.start_time = recording_analog.get_start_time()
        else:
            self.start_time = 0.0
        self.t = self.start_time + np.arange(self.n_samples) / sampling_rate
        self.start_idx = 0
        self.end_idx = int(window_sec * sampling_rate)
        from matplotlib.widgets import Slider, TextBox
        if self.additional_analog_data is not None:
            self.fig, (self.ax_analog, self.ax_additional, self.ax_ttl) = plt.subplots(3, 1, figsize=(12, 10), sharex=True,
                                                              gridspec_kw={'height_ratios': [3, 3, 1]})
        else:
            self.fig, (self.ax_analog, self.ax_ttl) = plt.subplots(2, 1, figsize=(12, 8), sharex=True,
                                                              gridspec_kw={'height_ratios': [3, 1]})
        # Add slider and text box below the plots
        plt.subplots_adjust(bottom=0.25)
        ax_slider = self.fig.add_axes((0.15, 0.10, 0.7, 0.05))
        self.slider = Slider(
            ax=ax_slider,
            label='Time (s)',
            valmin=self.t[0],
            valmax=self.t[-1] - self.window_sec,
            valinit=self.t[0],
            valstep=self.window_sec/2
        )
        self.slider.on_changed(self._on_slider)
        ax_text = self.fig.add_axes((0.15, 0.02, 0.2, 0.05))
        self.textbox = TextBox(ax_text, 'Jump to Time (s):', initial=str(self.t[0]))
        self.textbox.on_submit(self._on_textbox)

    def _on_textbox(self, text):
        try:
            val = float(text)
        except ValueError:
            print(f"Invalid time value: {text}")
            return
        # Clamp to valid range
        val = max(self.t[0], min(val, self.t[-1] - self.window_sec))
        self.slider.set_val(val)
        self.message_lines = []
        self._plot_window()
        self._connect_events()
        self.fig.canvas.mpl_connect('key_press_event', self._on_key)
        plt.show()
    def _on_slider(self, val):
        # Move window to slider value
        self.start_idx = int((val - self.t[0]) * self.sampling_rate)
        self.end_idx = self.start_idx + int(self.window_sec * self.sampling_rate)
        # Clamp indices to valid range
        self.start_idx = max(0, min(self.start_idx, self.n_samples - int(self.window_sec * self.sampling_rate)))
        self.end_idx = min(self.n_samples, self.start_idx + int(self.window_sec * self.sampling_rate))
        self._plot_window()

    def _plot_window(self):
        # Only update the visible window, avoid full axis clearing
        self.ax_analog.cla()
        if hasattr(self, 'ax_additional'):
            self.ax_additional.cla()
        self.ax_ttl.cla()
        t_start = self.t[self.start_idx]
        t_end = self.t[self.end_idx-1] if self.end_idx > 0 else self.t[self.start_idx]
        # Plot analog channels (top)
        for i in range(self.analog_data.shape[1]):
            self.ax_analog.plot(self.t[self.start_idx:self.end_idx],
                               self.analog_data[self.start_idx:self.end_idx, i],
                               label=f"Analog {ANALOG_CHANNELS[i]}")
        # Plot additional analog channels if present
        if self.additional_analog_data is not None and hasattr(self, 'ax_additional'):
            # Calculate time axis for additional analog data
            n_samples_additional = self.additional_analog_data.shape[0]
            t_additional = self.additional_start_time + np.arange(n_samples_additional) / self.additional_sampling_rate
            # Find indices for window
            start_idx_additional = np.searchsorted(t_additional, t_start, side='left')
            end_idx_additional = np.searchsorted(t_additional, t_end, side='right')
            for i in range(self.additional_analog_data.shape[1]):
                self.ax_additional.plot(t_additional[start_idx_additional:end_idx_additional],
                                       self.additional_analog_data[start_idx_additional:end_idx_additional, i],
                                       label=f"NI-DAQmx Ch {i}")
            self.ax_additional.set_ylabel("Additional Analog Value")
            self.ax_additional.set_title("NI-DAQmx-131.PXIe-6363 Analog Data")
            self.ax_additional.legend(loc='upper right')
        # Plot message lines (vertical lines on analog)
        self.message_lines = []
        msg_in_window = False
        for ts, msg in self.messages:
            if t_start <= ts < t_end:
                # Decode bytes to string if needed
                if isinstance(msg, bytes):
                    msg_str = msg.decode(errors='replace')
                else:
                    msg_str = str(msg)
                label_text = None
                if 'UDP' in msg_str:
                    color = 'green'
                    # Extract timestamp between '@' and '='
                    try:
                        at_idx = msg_str.index('@')
                        eq_idx = msg_str.index('=', at_idx)
                        extracted = msg_str[at_idx+1:eq_idx]
                        extracted_ts = float(extracted)
                        udp_diff_val = ts - extracted_ts
                        label_text = f"{udp_diff_val:.6f}"
                    except Exception:
                        label_text = None
                elif 'name=4913' in msg_str:
                    color = 'blue'
                    # Try to extract udp_diff_val if possible
                    udp_diff_val = None
                    try:
                        at_idx = msg_str.index('@')
                        eq_idx = msg_str.index('=', at_idx)
                        extracted = msg_str[at_idx+1:eq_idx]
                        extracted_ts = float(extracted)
                        udp_diff_val = ts - extracted_ts
                    except Exception:
                        udp_diff_val = None
                    # Plot udp_diff_val label if found
                    if udp_diff_val is not None:
                        ylim = self.ax_analog.get_ylim()
                        y_pos = ylim[1] - 0.05 * (ylim[1] - ylim[0])
                        self.ax_analog.text(ts, y_pos, f"{udp_diff_val:.6f}", color='blue', fontsize=8, rotation=90, va='top', ha='left', backgroundcolor='white')
                else:
                    continue
                line = self.ax_analog.axvline(ts, color=color, linestyle='--', alpha=0.7)
                # Add label next to the vertical line for UDP messages
                if label_text is not None:
                    ylim = self.ax_analog.get_ylim()
                    y_pos = ylim[1] - 0.05 * (ylim[1] - ylim[0])
                    self.ax_analog.text(ts, y_pos, label_text, color='green', fontsize=8, rotation=90, va='top', ha='left', backgroundcolor='white')
                self.message_lines.append((line, msg_str))
                msg_in_window = True
        # Plot TTL pulses (bottom)\
        ttl_in_window = False
        ttl_lines = set()
        for line in range(16):
            # Separate events for ProbeA-AP and acquisition_board
            probe_events = [(row.timestamp, row.state) for _, row in ttl_events.iterrows() if row.line == line and row.stream_name == "ProbeA-AP" and row.timestamp < t_end]
            acq_events = [(row.timestamp, row.state) for _, row in ttl_events.iterrows() if row.line == line and row.stream_name == "acquisition_board" and row.timestamp < t_end]

            # Handle ProbeA-AP (only line 1, plotted at y=0)
            if line == 1:
                # Find last state before window start for ProbeA-AP
                prev_state_probe = 0
                for ts, state in probe_events:
                    if ts < t_start:
                        prev_state_probe = state
                i = 0
                while i < len(probe_events) and probe_events[i][0] < t_start:
                    i += 1
                if prev_state_probe == 1:
                    end_ts = t_end
                    for j in range(i, len(probe_events)):
                        if probe_events[j][1] == 0:
                            end_ts = probe_events[j][0]
                            break
                    self.ax_ttl.hlines(0, t_start, end_ts, color=f"C{line%10}", alpha=0.8, linewidth=2)
                    ttl_lines.add(0)
                    ttl_in_window = True
                # Plot new rising edges in window for ProbeA-AP
                while i < len(probe_events):
                    if probe_events[i][1] == 1:
                        start_ts = probe_events[i][0]
                        end_ts = t_end
                        j_found = False
                        for j in range(i+1, len(probe_events)):
                            if probe_events[j][1] == 0:
                                end_ts = probe_events[j][0]
                                i = j
                                j_found = True
                                break
                        self.ax_ttl.hlines(0, start_ts, end_ts, color=f"C{line%10}", alpha=0.8, linewidth=2)
                        ttl_lines.add(0)
                        ttl_in_window = True
                        if not j_found:
                            i += 1
                    else:
                        i += 1

            # Handle acquisition_board (all lines except ProbeA-AP)
            prev_state_acq = 0
            for ts, state in acq_events:
                if ts < t_start:
                    prev_state_acq = state
            i = 0
            while i < len(acq_events) and acq_events[i][0] < t_start:
                i += 1
            if prev_state_acq == 1:
                end_ts = t_end
                for j in range(i, len(acq_events)):
                    if acq_events[j][1] == 0:
                        end_ts = acq_events[j][0]
                        break
                self.ax_ttl.hlines(line, t_start, end_ts, color=f"C{line%10}", alpha=0.8, linewidth=2)
                ttl_lines.add(line)
                ttl_in_window = True
            # Plot new rising edges in window for acquisition_board
            while i < len(acq_events):
                if acq_events[i][1] == 1:
                    start_ts = acq_events[i][0]
                    end_ts = t_end
                    j_found = False
                    for j in range(i+1, len(acq_events)):
                        if acq_events[j][1] == 0:
                            end_ts = acq_events[j][0]
                            i = j
                            j_found = True
                            break
                    self.ax_ttl.hlines(line, start_ts, end_ts, color=f"C{line%10}", alpha=0.8, linewidth=2)
                    ttl_lines.add(line)
                    ttl_in_window = True
                    if not j_found:
                        i += 1
                else:
                    i += 1
        # Set axis labels and limits
        self.ax_analog.set_ylabel("Analog Value")
        self.ax_analog.set_title("Analog Data + Messages")
        self.ax_ttl.set_xlabel("Time (s)")
        self.ax_ttl.set_ylabel("TTL Line")
        self.ax_ttl.set_title("TTL Pulses")
        self.ax_ttl.set_yticks(sorted(ttl_lines) if ttl_lines else range(16))
        self.ax_ttl.set_ylim(-1, 16)
        self.ax_analog.set_xlim(t_start, t_end)
        self.ax_ttl.set_xlim(t_start, t_end)
        # Only update legend if analog data is present
        if self.analog_data.shape[1] > 0:
            self.ax_analog.legend(loc='upper right')
        self.fig.canvas.draw_idle()
        if not ttl_in_window:
            print("No TTL events in this window.")
        if not msg_in_window:
            print("No messages in this window.")
    def _on_key(self, event):
        window_size = self.end_idx - self.start_idx
        if event.key in ['right', 'd']:
            # Scroll forward
            if self.end_idx + window_size < self.n_samples:
                self.start_idx += window_size
                self.end_idx += window_size
                self._plot_window()
        elif event.key in ['left', 'a']:
            # Scroll backward
            if self.start_idx - window_size >= 0:
                self.start_idx -= window_size
                self.end_idx -= window_size
                self._plot_window()

    def _connect_events(self):
        self.fig.canvas.mpl_connect('button_press_event', self._on_click)
        self.span = SpanSelector(self.ax_analog, self._on_select, 'horizontal', useblit=True,
                     props=dict(alpha=0.5, facecolor='red'))

    def _on_click(self, event):
        # Check if click is near a message line
        for line, msg in self.message_lines:
            if abs(event.xdata - line.get_xdata()[0]) < 0.01:
                print(f"Message at {line.get_xdata()[0]:.3f}s: {msg}")

    def _on_select(self, xmin, xmax):
        # Scroll to selected window
        self.start_idx = int(xmin * self.sampling_rate)
        self.end_idx = int(xmax * self.sampling_rate)
        self._plot_window()



def plot_full_data_with_linked_zoom():
    n_plots = 4 if additional_analog_data is not None else 2
    fig, axes = plt.subplots(n_plots, 1, figsize=(14, 2.5*n_plots), sharex=True,
                            gridspec_kw={'height_ratios': [3, 3, 1, 2] if n_plots == 4 else [3, 1]})
    ax_analog = axes[0]
    if n_plots == 4:
        ax_additional = axes[1]
        ax_ttl = axes[2]
        ax_corr = axes[3]
    else:
        ax_ttl = axes[1]
        ax_additional = None
        ax_corr = None
    # If additional analog data is present, plot cross-correlation over time
    if ax_corr is not None and additional_analog_data is not None:
        # Use first channel from each source for comparison
        # Downsample both signals to the same rate and length
        main = analog_data[:, 0]
        add = additional_analog_data[:, 0]
        # Resample to lowest sampling rate
        min_rate = min(sampling_rate, additional_sampling_rate)
        # Use timestamps arrays directly for time vectors
        t_main = analog_timestamps
        t_add = additional_analog_timestamps
        # Interpolate both to common time base
        t_common_start = max(t_main[0], t_add[0])
        t_common_end = min(t_main[-1], t_add[-1])
        t_common = np.arange(t_common_start, t_common_end, 1.0/min_rate)
        main_interp = np.interp(t_common, t_main, main)
        add_interp = np.interp(t_common, t_add, add)
        # Sliding window cross-correlation
        window_sec = 10.0
        step_sec = 2.0
        window_samples = int(window_sec * min_rate)
        step_samples = int(step_sec * min_rate)
        corrs = []
        lags = []
        times = []
        from scipy.signal import correlate, correlation_lags
        try:
            from tqdm import tqdm
            use_tqdm = True
        except ImportError:
            use_tqdm = False
        loop_range = range(0, len(t_common) - window_samples, step_samples)
        if use_tqdm:
            loop_range = tqdm(loop_range, desc='Cross-correlation')
        for start in loop_range:
            seg_main = main_interp[start:start+window_samples]
            seg_add = add_interp[start:start+window_samples]
            corr = correlate(seg_main - np.mean(seg_main), seg_add - np.mean(seg_add), mode='full')
            lags_arr = correlation_lags(len(seg_main), len(seg_add), mode='full') / min_rate
            peak_idx = np.argmax(corr)
            peak = corr[peak_idx] / (np.std(seg_main) * np.std(seg_add) * window_samples)
            lag = lags_arr[peak_idx]
            corrs.append(peak)
            lags.append(lag)
            times.append(t_common[start + window_samples//2])
        ax_corr.plot(times, corrs, label='Peak Correlation', color='purple')
        ax_corr.plot(times, lags, label='Lag (s)', color='orange')
        ax_corr.set_ylabel('Correlation / Lag (s)')
        ax_corr.set_title('Cross-correlation (windowed)')
        ax_corr.legend(loc='upper right')
        ax_corr.set_xlabel('Time (s)')

    # Plot all analog data using timestamps array, downsample if needed
    n_samples = analog_data.shape[0]
    max_points = 100_000
    ds_factor = max(1, n_samples // max_points)
    idxs = np.arange(0, n_samples, ds_factor)
    t_analog = analog_timestamps[idxs]
    for i in range(analog_data.shape[1]):
        ax_analog.plot(t_analog, analog_data[idxs, i], label=f"Analog {ANALOG_CHANNELS[i]}")
    ax_analog.set_ylabel("Analog Value")
    ax_analog.set_title(f"Full Analog Data (downsampled by {ds_factor}x)")
    ax_analog.legend(loc='upper right')
    ax_analog.set_xlabel("Time (s)")

    # Add vertical lines for 'UDP' and 'name=4913' messages to all subplots (no text)
    udp_color = f"C{1%10}"  # TTL line 1 color
    name4913_color = f"C{3%10}"  # TTL line 3 color
    udp_lines = [ts for ts, msg in messages if 'UDP' in (msg.decode(errors='replace') if isinstance(msg, bytes) else str(msg))]
    name4913_lines = [ts for ts, msg in messages if 'name=4913' in (msg.decode(errors='replace') if isinstance(msg, bytes) else str(msg))]
    # Plot UDP lines
    for ts in udp_lines:
        ax_analog.axvline(ts, color=udp_color, linestyle='--', alpha=0.5)
    if ax_additional is not None and additional_analog_data is not None and additional_analog_timestamps is not None:
        for ts in udp_lines:
            ax_additional.axvline(ts, color=udp_color, linestyle='--', alpha=0.5)
    for ts in udp_lines:
        ax_ttl.axvline(ts, color=udp_color, linestyle='--', alpha=0.5)
    if ax_corr is not None:
        for ts in udp_lines:
            ax_corr.axvline(ts, color=udp_color, linestyle='--', alpha=0.5)
    # Plot name=4913 lines
    for ts in name4913_lines:
        ax_analog.axvline(ts, color=name4913_color, linestyle='--', alpha=0.5)
    if ax_additional is not None and additional_analog_data is not None and additional_analog_timestamps is not None:
        for ts in name4913_lines:
            ax_additional.axvline(ts, color=name4913_color, linestyle='--', alpha=0.5)
    for ts in name4913_lines:
        ax_ttl.axvline(ts, color=name4913_color, linestyle='--', alpha=0.5)
    if ax_corr is not None:
        for ts in name4913_lines:
            ax_corr.axvline(ts, color=name4913_color, linestyle='--', alpha=0.5)

    # Plot all additional analog data if present, downsample if needed
    if ax_additional is not None and additional_analog_data is not None and additional_analog_timestamps is not None:
        n_samples_additional = additional_analog_data.shape[0]
        ds_factor_add = max(1, n_samples_additional // max_points)
        idxs_add = np.arange(0, n_samples_additional, ds_factor_add)
        t_additional = additional_analog_timestamps[idxs_add]
        for i in range(additional_analog_data.shape[1]):
            ax_additional.plot(t_additional, additional_analog_data[idxs_add, i], label=f"NI-DAQmx Ch {i}")
        ax_additional.set_ylabel("Additional Analog Value")
        ax_additional.set_title(f"Full NI-DAQmx-131.PXIe-6363 Analog Data (downsampled by {ds_factor_add}x)")
        ax_additional.legend(loc='upper right')
        ax_additional.set_xlabel("Time (s)")

    # Plot all TTL events
    ttl_lines = set()
    for line in range(16):
        probe_events = [(row.timestamp, row.state) for _, row in ttl_events.iterrows() if row.line == line and row.stream_name == "ProbeA-AP"]
        acq_events = [(row.timestamp, row.state) for _, row in ttl_events.iterrows() if row.line == line and row.stream_name == "acquisition_board"]
        # ProbeA-AP (line 1)
        if line == 1:
            prev_state_probe = 0
            for ts, state in probe_events:
                prev_state_probe = state
            i = 0
            while i < len(probe_events):
                if probe_events[i][1] == 1:
                    start_ts = probe_events[i][0]
                    end_ts = analog_timestamps[-1]
                    j_found = False
                    for j in range(i+1, len(probe_events)):
                        if probe_events[j][1] == 0:
                            end_ts = probe_events[j][0]
                            i = j
                            j_found = True
                            break
                    ax_ttl.hlines(0, start_ts, end_ts, color=f"C{line%10}", alpha=0.8, linewidth=2)
                    ttl_lines.add(0)
                    if end_ts == analog_timestamps[-1]:
                        i += 1
                else:
                    i += 1
        # acquisition_board (all lines except ProbeA-AP)
        i = 0
        while i < len(acq_events):
            if acq_events[i][1] == 1:
                start_ts = acq_events[i][0]
                end_ts = analog_timestamps[-1]
                j_found = False
                for j in range(i+1, len(acq_events)):
                    if acq_events[j][1] == 0:
                        end_ts = acq_events[j][0]
                        i = j
                        j_found = True
                        break
                ax_ttl.hlines(line, start_ts, end_ts, color=f"C{line%10}", alpha=0.8, linewidth=2)
                ttl_lines.add(line)
                if end_ts == analog_timestamps[-1]:
                    i += 1
            else:
                i += 1

    # If additional analog data is present, plot PXIe-6363 TTL events at negative line numbers
    if ax_additional is not None and additional_analog_data is not None and additional_analog_timestamps is not None:
        for line in range(16):
            pxi_events = [(row.timestamp, row.state) for _, row in ttl_events.iterrows() if row.line == line and row.stream_name == "PXIe-6363"]
            i = 0
            while i < len(pxi_events):
                if pxi_events[i][1] == 1:
                    start_ts = pxi_events[i][0]
                    end_ts = additional_analog_timestamps[-1]
                    for j in range(i+1, len(pxi_events)):
                        if pxi_events[j][1] == 0:
                            end_ts = pxi_events[j][0]
                            i = j
                            break
                    ax_ttl.hlines(-line, start_ts, end_ts, color=f"C{line%10}", alpha=0.8, linewidth=2)
                    ttl_lines.add(-line)
                    if end_ts == additional_analog_timestamps[-1]:
                        i += 1
                else:
                    i += 1
    ax_ttl.set_xlabel("Time (s)")
    ax_ttl.set_ylabel("TTL Line")
    ax_ttl.set_title("Full TTL Pulses")
    ax_ttl.set_yticks(sorted(ttl_lines) if ttl_lines else range(16))
    ax_ttl.set_ylim(-2, 16)

    # Link zoom/pan across all subplots
    # Prevent recursion by using a flag
    syncing = {'active': False}
    def on_xlim_changed(event_ax):
        if syncing['active']:
            return
        syncing['active'] = True
        new_xlim = event_ax.get_xlim()
        # Plot all TTL events (full recording, not windowed)
        ttl_lines = set()
        for line in range(16):
            probe_events = [(row.timestamp, row.state) for _, row in ttl_events.iterrows() if row.line == line and row.stream_name == "ProbeA-AP"]
            acq_events = [(row.timestamp, row.state) for _, row in ttl_events.iterrows() if row.line == line and row.stream_name == "acquisition_board"]
            # ProbeA-AP (line 1)
            if line == 1:
                i = 0
                while i < len(probe_events):
                    if probe_events[i][1] == 1:
                        start_ts = probe_events[i][0]
                        # Find next falling edge or end of recording
                        end_ts = recording_analog.get_start_time() + (n_samples - 1) / sampling_rate
                        for j in range(i+1, len(probe_events)):
                            if probe_events[j][1] == 0:
                                end_ts = probe_events[j][0]
                                i = j
                                break
                        ax_ttl.hlines(0, start_ts, end_ts, color=f"C{line%10}", alpha=0.8, linewidth=2)
                        ttl_lines.add(0)
                        if end_ts == recording_analog.get_start_time() + (n_samples - 1) / sampling_rate:
                            i += 1
                    else:
                        i += 1
            # acquisition_board (all lines except ProbeA-AP)
            i = 0
            while i < len(acq_events):
                if acq_events[i][1] == 1:
                    start_ts = acq_events[i][0]
                    end_ts = recording_analog.get_start_time() + (n_samples - 1) / sampling_rate
                    for j in range(i+1, len(acq_events)):
                        if acq_events[j][1] == 0:
                            end_ts = acq_events[j][0]
                            i = j
                            break
                    ax_ttl.hlines(line, start_ts, end_ts, color=f"C{line%10}", alpha=0.8, linewidth=2)
                    ttl_lines.add(line)
                    if end_ts == recording_analog.get_start_time() + (n_samples - 1) / sampling_rate:
                        i += 1
                else:
                    i += 1
        # ...existing code...
    # ...existing code...
    plt.tight_layout()
    plt.show()
    plt.close(fig)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1].lower() == "interactive":
        plotter = InteractivePlot(
            analog_data,
            ttl_pulses,
            messages,
            sampling_rate,
            WINDOW_SEC,
            additional_analog_data=additional_analog_data,
            additional_sampling_rate=additional_sampling_rate,
            additional_start_time=additional_start_time
        )
    # Always show static full-data plot when not interactive
    plot_full_data_with_linked_zoom()
    # --- STATIC UDP TIMESTAMP DIFFERENCE PLOT ---
    udp_ts = []
    udp_diff = []
    rex_diff = []
    synced_diff = []
    extracted_diff = []
    rex_offset = None
    for ts, msg in messages:
        # Decode bytes to string if needed
        if isinstance(msg, bytes):
            msg_str = msg.decode(errors='replace')
        else:
            msg_str = str(msg)
        if 'UDP' in msg_str:
            # Extract timestamp between '@' and '='
            try:
                at_idx = msg_str.index('@')
                eq_idx = msg_str.index('=', at_idx)
                extracted = msg_str[at_idx+1:eq_idx]
                extracted_ts = float(extracted)
                # Extract REX timestamp after '='
                rex_str = msg_str[eq_idx+1:]
                rex_ts = float(rex_str.split()[0])
                if rex_offset is None:
                    rex_offset = rex_ts
                rex_ts -= rex_offset
                udp_ts.append(ts)
                udp_diff.append(ts - extracted_ts)
                rex_diff.append(ts - rex_ts)
                extracted_diff.append(extracted_ts - rex_ts)
            except Exception:
                continue
    if udp_ts:
        fig = plt.figure(figsize=(10, 8))
        ax1 = plt.subplot(3, 1, 1)
        line1, = ax1.plot(udp_ts, udp_diff, marker='o', linestyle='-', color='green')
        plt.xlabel('Message Timestamp (s)')
        plt.ylabel('Recorded - extracted [s]')
        plt.title('UDP Message Timestamp Difference Over Time')
        plt.grid(True)

        ax2 = plt.subplot(3, 1, 2)
        line2, = ax2.plot(udp_ts, rex_diff, marker='o', linestyle='-', color='blue')
        plt.xlabel('Message Timestamp (s)')
        plt.ylabel('Recorded - REX [s] (offset)')
        plt.title('UDP Message vs REX Timestamp (relative)')
        plt.grid(True)

        ax3 = plt.subplot(3, 1, 3)
        line3, = ax3.plot(udp_ts, extracted_diff, marker='o', linestyle='-', color='orange')
        plt.xlabel('Message Timestamp (s)')
        plt.ylabel('Extracted - REX [s] (offset)')
        plt.title('Extracted UDP vs REX Timestamp (relative)')
        plt.grid(True)

        plt.tight_layout()

        def on_click(event):
            if event.inaxes in [ax1, ax2, ax3]:
                # Find nearest data point
                ax = event.inaxes
                if ax == ax1:
                    xdata, ydata = np.array(line1.get_xdata()), np.array(line1.get_ydata())
                elif ax == ax2:
                    xdata, ydata = np.array(line2.get_xdata()), np.array(line2.get_ydata())
                else:
                    xdata, ydata = np.array(line3.get_xdata()), np.array(line3.get_ydata())
                if xdata.size == 0:
                    return
                # Find closest point
                dist = np.abs(xdata - event.xdata)
                idx = np.argmin(dist)
                x, y = xdata[idx], ydata[idx]
                print(f"Clicked at X={x:.3f}, Y={y:.3f}")
                # Annotate on plot
                ax.annotate(f"({x:.2f}, {y:.2f})", (x, y), textcoords="offset points", xytext=(10,10),
                            ha='center', color='red', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.5))
                fig.canvas.draw()

        fig.canvas.mpl_connect('button_press_event', on_click)
        plt.show()
        print("Done")
