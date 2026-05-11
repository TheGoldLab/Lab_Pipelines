# TrialViewerGUI

Generic MATLAB trial viewer for converted Pyramid sessions.

## Files

- `TrialViewer.m`: class-based app (call as `TrialViewer(pyramid_data)`)
- `TrialViewer.mlapp`: original App Designer file from AODR (for visual editing)
- `raster.m`, `getEventIndex.m`, `plotEye.m`: helper functions used by the viewer
- `launchTrialViewer.m`: convenience wrapper

## Usage

```matlab
addpath('/Users/lowell/Documents/GitHub/Lab_Pipelines/matlab/TrialViewerGUI');
TrialViewer(pyramid_data);
```

Equivalent wrapper:

```matlab
app = launchTrialViewer(pyramid_data);
```

## Supported input expectations

`TrialViewer` requires only:

- `pyramid_data.times` (table)

Optional fields are auto-filled if missing:

- `header.validTrials`
- `ids.choice`, `ids.score`
- `values.hazard`, `values.online_score`
- `dio`
- `spikes.id`, `spike_time_mat`

This allows the GUI to open for behavior-only sessions (e.g., DDRT) while gracefully disabling neural plotting when spike data is not present.

## Edge-case behavior

- Raster plotting supports either:
	- `spike_time_mat` (unit x spikes x trials), or
	- `spikes.data` (trial x unit table/cell where each entry is spike times for that trial+unit)
- If only `spikes.data` is present, the Neural tab stays enabled and rasters are generated directly from that table.
- Eye plotting supports sessions with only X/Y analog channels.
	- If channel 3 (pupil) is missing, X/Y still plot normally and the pupil axis shows `No pupil channel found`.

## Lamp behavior

- `Completed` lamp:
	- Green when `ids.choice(tr)` exists and is finite for the current trial.
	- Red otherwise.
- `Rewarded` lamp (offline score):
	- Yellow when `ids.score(tr) < 0`.
	- Red when `ids.score(tr) == 0`.
	- Green when `ids.score(tr) == 1`.
	- Gray when score is unavailable or not recognized.
	- If `ids.score` is missing, it falls back to `values.online_score`.
- `Rex Score` lamp (online outcome):
	- Green when `times.online_correct(tr)` is present/finite.
	- Red when `times.online_error(tr)` is present/finite.
	- Gray when neither event is present for that trial.
	- If `online_correct`/`online_error` fields are not available, it falls back to `values.online_score` mapping:
		- `< 0` red, `== 0` yellow, `== 1` green, otherwise gray.

## Analog/Digital alignment behavior

- The Analog/Digital tab has an `Align` dropdown and `Before/After (ms)` window controls.
- When `Align` is set to `(none)`:
	- No alignment event is used.
	- The panel uses the default trial window in seconds.
	- No red alignment line is drawn.
- When an alignment event is selected and detected in the trial:
	- X/Y, pupil, and TTL are plotted in milliseconds relative to that event.
	- A red vertical alignment line is drawn at `t = 0`.
- When the selected event is not detected in the current trial:
	- The GUI shows an in-plot notice indicating the selected event was not found.
	- It attempts fallback alignment (preferring `trial_start`, then other available events).
	- If no fallback event is found, it falls back to the default unaligned window.
- TTL line colors are deterministic by line number, so repeated pulses on the same TTL line keep the same color.

## Neural alignment behavior

- The Neural tab uses `Event Alignment` plus `Before/After (ms)`.
- If the selected event is missing for the current trial, the raster shows an in-plot notice and tries fallback alignment (preferring `trial_start`, then other available events).
- If no fallback event is found, the raster falls back to unaligned plotting for that trial.
