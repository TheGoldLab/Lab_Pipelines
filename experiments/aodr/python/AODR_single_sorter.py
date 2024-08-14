from __future__ import annotations

from spikeinterface.sorters.internal.si_based import ComponentsBasedSorter
import shutil
import numpy as np
import random, string, os
import numpy as np
from spikeinterface.core import NumpySorting
from spikeinterface.core.job_tools import fix_job_kwargs
from spikeinterface.core.recording_tools import get_noise_levels
from spikeinterface.core.template import Templates
from spikeinterface.core.waveform_tools import estimate_templates
from spikeinterface.preprocessing import common_reference, whiten, bandpass_filter, correct_motion
from spikeinterface.sortingcomponents.tools import cache_preprocessing
from spikeinterface.core.basesorting import minimum_spike_dtype
from spikeinterface.core.sparsity import compute_sparsity
from spikeinterface.core.sortinganalyzer import create_sorting_analyzer
from spikeinterface.curation.auto_merge import get_potential_auto_merge
from spikeinterface.core.analyzer_extension_core import ComputeTemplates
from spikeinterface.core.sparsity import ChannelSparsity
from spikeinterface.sortingcomponents.features_from_peaks import compute_features_from_peaks
from spikeinterface.sortingcomponents.clustering.clustering_tools import remove_duplicates, remove_duplicates_via_matching, remove_duplicates_via_dip
from spikeinterface.core.waveform_tools import extract_waveforms_to_buffers
from spikeinterface.core import estimate_templates_with_accumulator, Templates
from spikeinterface.core import get_global_tmp_folder, get_noise_levels
from pathlib import Path

try:
    import hdbscan

    HAVE_HDBSCAN = True
except:
    HAVE_HDBSCAN = False

class SingleChannelSorter(ComponentsBasedSorter):
    sorter_name = "single_channel"

    _default_params = {
        "general": {"ms_before": 2, "ms_after": 2, "radius_um": 100},
        "sparsity": {"method": "ptp", "threshold": 0.25},
        "filtering": {"freq_min": 150, "freq_max": 7000, "ftype": "bessel", "filter_order": 2},
        "detection": {"peak_sign": "neg", "detect_threshold": 4},
        "selection": {
            "method": "uniform",
            "n_peaks_per_channel": 5000,
            "min_n_peaks": 100000,
            "select_per_channel": False,
            "seed": 42,
        },
        "apply_motion_correction": True,
        "motion_correction": {"preset": "nonrigid_fast_and_accurate"},
        "merging": {
            "similarity_kwargs": {"method": "cosine", "support": "union", "max_lag_ms": 0.2},
            "correlograms_kwargs": {},
            "auto_merge": {
                "min_spikes": 10,
                "corr_diff_thresh": 0.25,
            },
        },
        "clustering": {"legacy": True, "method": 'FeaturesClustering'},
        "matching": {"method": "wobble"},
        "apply_preprocessing": True,
        "matched_filtering": True,
        "cache_preprocessing": {"mode": "memory", "memory_limit": 0.5, "delete_cache": True},
        "multi_units_only": False,
        "job_kwargs": {"n_jobs": 0.8},
        "debug": False,
    }

    handle_multi_segment = True

    _params_description = {
        "general": "A dictionary to describe how templates should be computed. User can define ms_before and ms_after (in ms) \
                                        and also the radius_um used to be considered during clustering",
        "sparsity": "A dictionary to be passed to all the calls to sparsify the templates",
        "filtering": "A dictionary for the high_pass filter to be used during preprocessing",
        "detection": "A dictionary for the peak detection node (locally_exclusive)",
        "selection": "A dictionary for the peak selection node. Default is to use smart_sampling_amplitudes, with a minimum of 20000 peaks\
                                         and 5000 peaks per electrode on average.",
        "clustering": "A dictionary to be provided to the clustering method. By default, random_projections is used, but if legacy is set to\
                            True, one other clustering called circus will be used, similar to the one used in Spyking Circus 1",
        "matching": "A dictionary to specify the matching engine used to recover spikes. The method default is circus-omp-svd, but other engines\
                                          can be used",
        "merging": "A dictionary to specify the final merging param to group cells after template matching (get_potential_auto_merge)",
        "motion_correction": "A dictionary to be provided if motion correction has to be performed (dense probe only)",
        "apply_preprocessing": "Boolean to specify whether circus 2 should preprocess the recording or not. If yes, then high_pass filtering + common\
                                                    median reference + zscore",
        "cache_preprocessing": "How to cache the preprocessed recording. Mode can be memory, file, zarr, with extra arguments. In case of memory (default), \
                         memory_limit will control how much RAM can be used. In case of folder or zarr, delete_cache controls if cache is cleaned after sorting",
        "multi_units_only": "Boolean to get only multi units activity (i.e. one template per electrode)",
        "job_kwargs": "A dictionary to specify how many jobs and which parameters they should used",
        "debug": "Boolean to specify if internal data structures made during the sorting should be kept for debugging",
    }

    sorter_description = """Spyking Circus 2 is a rewriting of Spyking Circus, within the SpikeInterface framework
    It uses a more conservative clustering algorithm (compared to Spyking Circus), which is less prone to hallucinate units and/or find noise.
    In addition, it also uses a full Orthogonal Matching Pursuit engine to reconstruct the traces, leading to more spikes
    being discovered."""

    @classmethod
    def get_sorter_version(cls):
        return "2.0"

    @classmethod
    def _run_from_folder(cls, sorter_output_folder, params, verbose):
        try:
            import hdbscan

            HAVE_HDBSCAN = True
        except:
            HAVE_HDBSCAN = False

        assert HAVE_HDBSCAN, "spykingcircus2 needs hdbscan to be installed"

        # this is importanted only on demand because numba import are too heavy
        from spikeinterface.sortingcomponents.peak_detection import detect_peaks
        from spikeinterface.sortingcomponents.peak_selection import select_peaks
        from spikeinterface.sortingcomponents.clustering import find_cluster_from_peaks
        from spikeinterface.sortingcomponents.matching import find_spikes_from_templates
        from spikeinterface.sortingcomponents.tools import remove_empty_templates
        from spikeinterface.sortingcomponents.tools import get_prototype_spike, check_probe_for_drift_correction
        from spikeinterface.sortingcomponents.tools import get_prototype_spike

        job_kwargs = params["job_kwargs"]
        job_kwargs = fix_job_kwargs(job_kwargs)
        job_kwargs.update({"progress_bar": verbose})

        recording = cls.load_recording_from_folder(sorter_output_folder.parent, with_warnings=False)

        sampling_frequency = recording.get_sampling_frequency()
        num_channels = recording.get_num_channels()
        ms_before = params["general"].get("ms_before", 2)
        ms_after = params["general"].get("ms_after", 2)
        radius_um = params["general"].get("radius_um", 100)
        exclude_sweep_ms = params["detection"].get("exclude_sweep_ms", max(ms_before, ms_after) / 2)

        recording_f = recording
        recording_f.annotate(is_filtered=True)

        motion_folder = None # no motion correction

        ## We need to whiten before the template matching step, to boost the results
        # DO NOT WHITEN FOR SINGLE CHANNEL
        # recording_w = whiten(recording_f, mode="local", radius_um=radius_um, dtype="float32", regularize=True)
        recording_w = recording_f
        noise_levels = get_noise_levels(recording_w, return_scaled=False)

        if recording_w.check_serializability("json"):
            recording_w.dump(sorter_output_folder / "preprocessed_recording.json", relative_to=None)
        elif recording_w.check_serializability("pickle"):
            recording_w.dump(sorter_output_folder / "preprocessed_recording.pickle", relative_to=None)

        recording_w = cache_preprocessing(recording_w, **job_kwargs, **params["cache_preprocessing"])

        ## Then, we are detecting peaks with a locally_exclusive method
        detection_params = params["detection"].copy()
        detection_params.update(job_kwargs)

        detection_params["radius_um"] = detection_params.get("radius_um", 50)
        detection_params["exclude_sweep_ms"] = exclude_sweep_ms
        detection_params["noise_levels"] = noise_levels

        fs = recording_w.get_sampling_frequency()
        nbefore = int(ms_before * fs / 1000.0)
        nafter = int(ms_after * fs / 1000.0)

        peaks = detect_peaks(recording_w, "locally_exclusive", **detection_params)

        if params["matched_filtering"]:
            prototype = get_prototype_spike(recording_w, peaks, ms_before, ms_after, **job_kwargs)
            detection_params["prototype"] = prototype
            detection_params["ms_before"] = ms_before

            for value in ["chunk_size", "chunk_memory", "total_memory", "chunk_duration"]:
                if value in detection_params:
                    detection_params.pop(value)

            detection_params["chunk_duration"] = "100ms"

            peaks = detect_peaks(recording_w, "matched_filtering", **detection_params)

        if verbose:
            print("We found %d peaks in total" % len(peaks))

        if params["multi_units_only"]:
            sorting = NumpySorting.from_peaks(peaks, sampling_frequency, unit_ids=recording_w.unit_ids)
        else:
            ## We subselect a subset of all the peaks, by making the distributions os SNRs over all
            ## channels as flat as possible
            selection_params = params["selection"]
            selection_params["n_peaks"] = params["selection"]["n_peaks_per_channel"] * num_channels
            selection_params["n_peaks"] = max(selection_params["min_n_peaks"], selection_params["n_peaks"])

            selection_params.update({"noise_levels": noise_levels})
            selected_peaks = select_peaks(peaks, **selection_params)

            if verbose:
                print("We kept %d peaks for clustering" % len(selected_peaks))

            ## We launch a clustering (using hdbscan) relying on positions and features extracted on
            ## the fly from the snippets
            clustering_params = params["clustering"].copy()
            clustering_params["waveforms"] = {}
            clustering_params["sparsity"] = params["sparsity"]
            clustering_params["radius_um"] = radius_um
            clustering_params["waveforms"]["ms_before"] = ms_before
            clustering_params["waveforms"]["ms_after"] = ms_after
            clustering_params["job_kwargs"] = job_kwargs
            clustering_params["noise_levels"] = noise_levels
            clustering_params["ms_before"] = exclude_sweep_ms
            clustering_params["ms_after"] = exclude_sweep_ms
            clustering_params["tmp_folder"] = sorter_output_folder / "clustering"

            legacy = clustering_params.get("legacy", True)

            if legacy:
                clustering_method = "circus"
            else:
                clustering_method = "random_projections"

            # instead of "find_cluster from peaks", we call our clustering method manually (to avoid changing SI)
            #labels, peak_labels = find_cluster_from_peaks(
            #    recording_w, selected_peaks, method=clustering_method, method_kwargs=clustering_params
            #)
            outputs = FeaturesClustering.main_function(recording_w, peaks, clustering_params)

            if len(outputs) > 2:
                outputs = outputs[:2]
            labels, peak_labels = outputs

            ## We get the labels for our peaks
            mask = peak_labels > -1

            labeled_peaks = np.zeros(np.sum(mask), dtype=minimum_spike_dtype)
            labeled_peaks["sample_index"] = selected_peaks[mask]["sample_index"]
            labeled_peaks["segment_index"] = selected_peaks[mask]["segment_index"]
            for count, l in enumerate(labels):
                sub_mask = peak_labels[mask] == l
                labeled_peaks["unit_index"][sub_mask] = count
            unit_ids = np.arange(len(np.unique(labeled_peaks["unit_index"])))
            sorting = NumpySorting(labeled_peaks, sampling_frequency, unit_ids=unit_ids)

            clustering_folder = sorter_output_folder / "clustering"
            clustering_folder.mkdir(parents=True, exist_ok=True)

            if not params["debug"]:
                shutil.rmtree(clustering_folder)
            else:
                np.save(clustering_folder / "labels", labels)
                np.save(clustering_folder / "peaks", selected_peaks)

            templates_array = estimate_templates(
                recording_w, labeled_peaks, unit_ids, nbefore, nafter, return_scaled=False, job_name=None, **job_kwargs
            )

            templates = Templates(
                templates_array=templates_array,
                sampling_frequency=sampling_frequency,
                nbefore=nbefore,
                sparsity_mask=None,
                channel_ids=recording_w.channel_ids,
                unit_ids=unit_ids,
                probe=recording_w.get_probe(),
                is_scaled=False,
            )

            sparsity = compute_sparsity(templates, noise_levels, **params["sparsity"])
            templates = templates.to_sparse(sparsity)
            templates = remove_empty_templates(templates)

            if params["debug"]:
                templates.to_zarr(folder_path=clustering_folder / "templates")
                sorting = sorting.save(folder=clustering_folder / "sorting")

            ## We launch a OMP matching pursuit by full convolution of the templates and the raw traces
            matching_method = params["matching"].pop("method")
            matching_params = params["matching"].copy()
            matching_params["templates"] = templates
            matching_job_params = job_kwargs.copy()

            if matching_method is not None:
                for value in ["chunk_size", "chunk_memory", "total_memory", "chunk_duration"]:
                    if value in matching_job_params:
                        matching_job_params[value] = None
                matching_job_params["chunk_duration"] = "100ms"

                spikes = find_spikes_from_templates(
                    recording_w, matching_method, method_kwargs=matching_params, **matching_job_params
                )

                if params["debug"]:
                    fitting_folder = sorter_output_folder / "fitting"
                    fitting_folder.mkdir(parents=True, exist_ok=True)
                    np.save(fitting_folder / "spikes", spikes)

                if verbose:
                    print("We found %d spikes" % len(spikes))

                ## And this is it! We have a spyking circus
                sorting = np.zeros(spikes.size, dtype=minimum_spike_dtype)
                sorting["sample_index"] = spikes["sample_index"]
                sorting["unit_index"] = spikes["cluster_index"]
                sorting["segment_index"] = spikes["segment_index"]
                sorting = NumpySorting(sorting, sampling_frequency, unit_ids)

        sorting_folder = sorter_output_folder / "sorting"
        if sorting_folder.exists():
            shutil.rmtree(sorting_folder)

        merging_params = params["merging"].copy()

        if len(merging_params) > 0:
            if params["motion_correction"] and motion_folder is not None:
                from spikeinterface.preprocessing.motion import load_motion_info

                motion_info = load_motion_info(motion_folder)
                motion = motion_info["motion"]
                max_motion = max(
                    np.max(np.abs(motion.displacement[seg_index])) for seg_index in range(len(motion.displacement))
                )
                merging_params["max_distance_um"] = max(50, 2 * max_motion)

            # peak_sign = params['detection'].get('peak_sign', 'neg')
            # best_amplitudes = get_template_extremum_amplitude(templates, peak_sign=peak_sign)
            # guessed_amplitudes = spikes['amplitude'].copy()
            # for ind in unit_ids:
            #     mask = spikes['cluster_index'] == ind
            #     guessed_amplitudes[mask] *= best_amplitudes[ind]

            if params["debug"]:
                curation_folder = sorter_output_folder / "curation"
                if curation_folder.exists():
                    shutil.rmtree(curation_folder)
                sorting.save(folder=curation_folder)
                # np.save(fitting_folder / "amplitudes", guessed_amplitudes)

            sorting = final_cleaning_circus(recording_w, sorting, templates, **merging_params)

            if verbose:
                print(f"Final merging, keeping {len(sorting.unit_ids)} units")

        folder_to_delete = None
        cache_mode = params["cache_preprocessing"].get("mode", "memory")
        delete_cache = params["cache_preprocessing"].get("delete_cache", True)

        if cache_mode in ["folder", "zarr"] and delete_cache:
            folder_to_delete = recording_w._kwargs["folder_path"]

        del recording_w
        if folder_to_delete is not None:
            shutil.rmtree(folder_to_delete)

        sorting = sorting.save(folder=sorting_folder)

        return sorting


def create_sorting_analyzer_with_templates(sorting, recording, templates, remove_empty=True):
    sparsity = templates.sparsity
    templates_array = templates.get_dense_templates().copy()

    if remove_empty:
        non_empty_unit_ids = sorting.get_non_empty_unit_ids()
        non_empty_sorting = sorting.remove_empty_units()
        non_empty_unit_indices = sorting.ids_to_indices(non_empty_unit_ids)
        templates_array = templates_array[non_empty_unit_indices]
        sparsity_mask = sparsity.mask[non_empty_unit_indices, :]
        sparsity = ChannelSparsity(sparsity_mask, non_empty_unit_ids, sparsity.channel_ids)
    else:
        non_empty_sorting = sorting

    sa = create_sorting_analyzer(non_empty_sorting, recording, format="memory", sparsity=sparsity)
    sa.extensions["templates"] = ComputeTemplates(sa)
    sa.extensions["templates"].params = {"ms_before": templates.ms_before, "ms_after": templates.ms_after}
    sa.extensions["templates"].data["average"] = templates_array
    return sa


def final_cleaning_circus(recording, sorting, templates, **merging_kwargs):

    from spikeinterface.core.sorting_tools import apply_merges_to_sorting

    sa = create_sorting_analyzer_with_templates(sorting, recording, templates)

    sa.compute("unit_locations", method="monopolar_triangulation")
    similarity_kwargs = merging_kwargs.pop("similarity_kwargs", {})
    sa.compute("template_similarity", **similarity_kwargs)
    correlograms_kwargs = merging_kwargs.pop("correlograms_kwargs", {})
    sa.compute("correlograms", **correlograms_kwargs)
    auto_merge_kwargs = merging_kwargs.pop("auto_merge", {})
    merges = get_potential_auto_merge(sa, resolve_graph=True, **auto_merge_kwargs)
    sorting = apply_merges_to_sorting(sa.sorting, merges)

    return sorting


# """Sorting components: clustering"""
class FeaturesClustering:
    """
    hdbscan clustering on peak_locations previously done by localize_peaks()
    """

    _default_params = {
        "peak_localization_kwargs": {"method": "center_of_mass"},
        "hdbscan_kwargs": {
            "min_cluster_size": 50,
            "allow_single_cluster": True,
            "core_dist_n_jobs": -1,
            "cluster_selection_method": "leaf",
        },
        "cleaning_kwargs": {},
        "radius_um": 100,
        "max_spikes_per_unit": 200,
        "selection_method": "random",
        "ms_before": 1.5,
        "ms_after": 1.5,
        "cleaning_method": "dip",
        "job_kwargs": {"n_jobs": -1, "chunk_memory": "10M", "progress_bar": True},
    }

    @classmethod
    def main_function(cls, recording, peaks, params):
        from sklearn.preprocessing import QuantileTransformer

        assert HAVE_HDBSCAN, "twisted clustering needs hdbscan to be installed"

        if "n_jobs" in params["job_kwargs"]:
            if params["job_kwargs"]["n_jobs"] == -1:
                params["job_kwargs"]["n_jobs"] = os.cpu_count()

        if "core_dist_n_jobs" in params["hdbscan_kwargs"]:
            if params["hdbscan_kwargs"]["core_dist_n_jobs"] == -1:
                params["hdbscan_kwargs"]["core_dist_n_jobs"] = os.cpu_count()

        d = params

        peak_dtype = [("sample_index", "int64"), ("unit_index", "int64"), ("segment_index", "int64")]

        fs = recording.get_sampling_frequency()
        nbefore = int(params["ms_before"] * fs / 1000.0)
        nafter = int(params["ms_after"] * fs / 1000.0)
        num_samples = nbefore + nafter

        position_method = d["peak_localization_kwargs"]["method"]
        
        '''
        feature_list: list, default: ["ptp"]
        List of features to be computed. Possible features are:
            - amplitude
            - ptp
            - center_of_mass
            - energy
            - std_ptp
            - ptp_lag
            - random_projections_ptp
            - random_projections_energy
        '''

        features_list = [
            position_method,
            "ptp",
        ]
        
        features_params = {
            position_method: {"radius_um": params["radius_um"]},
            "ptp": {"all_channels": False, "radius_um": params["radius_um"]},
            "amplitude": {"all_channels": False}
        }

        features_data = compute_features_from_peaks(
            recording, peaks, features_list, features_params, ms_before=1, ms_after=1, **params["job_kwargs"]
        )

        hdbscan_data = np.zeros((len(peaks), 3), dtype=np.float32)
        hdbscan_data[:, 0] = features_data[0]["x"]
        hdbscan_data[:, 1] = features_data[0]["y"]
        hdbscan_data[:, 2] = features_data[1]

        preprocessing = QuantileTransformer(output_distribution="uniform")
        hdbscan_data = preprocessing.fit_transform(hdbscan_data)

        clusterer = hdbscan.HDBSCAN(**d["hdbscan_kwargs"])
        clusterer.fit(X=hdbscan_data)
        peak_labels = clusterer.labels_

        labels = np.unique(peak_labels)
        labels = labels[labels >= 0]  #  Noisy samples are given the label -1 in hdbscan

        best_spikes = {}
        num_spikes = 0

        all_indices = np.arange(0, peak_labels.size)

        max_spikes = params["max_spikes_per_unit"]
        selection_method = params["selection_method"]

        import sklearn

        for unit_ind in labels:
            mask = peak_labels == unit_ind
            if selection_method == "closest_to_centroid":
                data = hdbscan_data[mask]
                centroid = np.median(data, axis=0)
                distances = sklearn.metrics.pairwise_distances(centroid[np.newaxis, :], data)[0]
                best_spikes[unit_ind] = all_indices[mask][np.argsort(distances)[:max_spikes]]
            elif selection_method == "random":
                best_spikes[unit_ind] = np.random.permutation(all_indices[mask])[:max_spikes]
            num_spikes += best_spikes[unit_ind].size

        spikes = np.zeros(num_spikes, dtype=peak_dtype)

        mask = np.zeros(0, dtype=np.int32)
        for unit_ind in labels:
            mask = np.concatenate((mask, best_spikes[unit_ind]))

        idx = np.argsort(mask)
        mask = mask[idx]

        spikes["sample_index"] = peaks[mask]["sample_index"]
        spikes["segment_index"] = peaks[mask]["segment_index"]
        spikes["unit_index"] = peak_labels[mask]

        cleaning_method = params["cleaning_method"]

        print("We found %d raw clusters, starting to clean with %s..." % (len(labels), cleaning_method))

        if cleaning_method == "cosine":
            num_chans = recording.get_num_channels()
            wfs_arrays = extract_waveforms_to_buffers(
                recording,
                spikes,
                labels,
                nbefore,
                nafter,
                mode="shared_memory",
                return_scaled=False,
                folder=None,
                dtype=recording.get_dtype(),
                sparsity_mask=None,
                copy=True,
                **params["job_kwargs"],
            )

            noise_levels = get_noise_levels(recording, return_scaled=False)
            labels, peak_labels = remove_duplicates(
                wfs_arrays, noise_levels, peak_labels, num_samples, num_chans, **params["cleaning_kwargs"]
            )

        elif cleaning_method == "dip":
            wfs_arrays = {}
            for label in labels:
                mask = label == peak_labels
                wfs_arrays[label] = hdbscan_data[mask]

            labels, peak_labels = remove_duplicates_via_dip(wfs_arrays, peak_labels, **params["cleaning_kwargs"])

        elif cleaning_method == "matching":
            name = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
            tmp_folder = Path(os.path.join(get_global_tmp_folder(), name))

            sorting = NumpySorting.from_times_labels(spikes["sample_index"], spikes["unit_index"], fs)

            nbefore = int(params["ms_before"] * fs / 1000.0)
            nafter = int(params["ms_after"] * fs / 1000.0)
            templates_array = estimate_templates_with_accumulator(
                recording,
                sorting.to_spike_vector(),
                sorting.unit_ids,
                nbefore,
                nafter,
                return_scaled=False,
                **params["job_kwargs"],
            )
            templates = Templates(
                templates_array=templates_array,
                sampling_frequency=fs,
                nbefore=nbefore,
                sparsity_mask=None,
                probe=recording.get_probe(),
                is_scaled=False,
            )

            labels, peak_labels = remove_duplicates_via_matching(
                templates, peak_labels, job_kwargs=params["job_kwargs"], **params["cleaning_kwargs"]
            )
            shutil.rmtree(tmp_folder)

        print("We kept %d non-duplicated clusters..." % len(labels))

        return labels, peak_labels