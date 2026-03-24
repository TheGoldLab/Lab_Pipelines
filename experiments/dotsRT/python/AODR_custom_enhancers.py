from typing import Any
import math
import numpy as np

from pyramid.trials.trials import Trial, TrialEnhancer

# We can define utility functions for the TrialEnhancer to use.
def ang_deg(x: float, y: float) -> float:
    """Compute an angle in degrees, in [0, 360)."""
    degrees = math.atan2(y, x) * 180 / math.pi
    return math.fmod(degrees + 360, 360)

def ang_diff(a1: float, a2: float) -> float:
    """Compute angular difference"""
    return 180.0 - abs(abs(a1 - a2) - 180.0)

def log10(x: float) -> float:
    """Compute log10 of x, allowing for log10(0.0) -> -inf."""
    if x == 0.0:
        return float("-inf")
    else:
        return math.log10(x)

# This is a rough version of the trial compute code from spmADPODR.m.
# It's incomplete and wrong!
# I'm hoping it shows the Pyramid version of how to get and set the same per-trial data as in FIRA.
class CustomEnhancer(TrialEnhancer):

    def __init__(
        self,
        min_angular_distance_to_target_deg: float = 25
    ) -> None:
        self.tacp = 0
        self.previous_correct_target = 0
        self.previous_choice = -1
        self.min_angular_distance_to_target_deg = min_angular_distance_to_target_deg
   
    def enhance(
        self,
        trial: Trial,
        trial_number: int,
        experiment_info: dict[str: Any],
        subject_info: dict[str: Any]
    ) -> None:

        task_id = trial.get_one("task_id")
        if task_id is None:
            return

        # Use trial.add_enhancement() to set new values from custom computations.
        # You can set a category like "time", "id", or "value" (the default).

        # Save target angles
        t1_angle = ang_deg(trial.get_one('t1_x'), trial.get_one('t1_y'))
        trial.add_enhancement('t1_angle', t1_angle, "id")
        t2_angle = ang_deg(trial.get_one('t2_x', 0), trial.get_one('t2_y', 0))
        trial.add_enhancement('t2_angle', t2_angle, "id")

        # Check for spike data, if so, add spike category enhancement, boolean true value for each spike source (channel usually)
        a = []
        for k,v in trial.numeric_events.items():
            if k.startswith('spike'):
                a.append(k)
                trial.add_enhancement(k, 1, "spikes")

        if 'phy_clusters' in trial.numeric_events.keys():
            trial.add_enhancement('phy_clusters', 1, "spikes")
 

        if task_id == 1:

            # For MSAC, set target
            correct_target = 1
            target_angles = [t1_angle]
            trial.add_enhancement("correct_target", correct_target, "id")

        elif task_id in (2, 3, 4, 5):

            # For AODR, figure out sample angle, correct/error target, LLR
            sample_angle = ang_deg(trial.get_one("sample_x"), trial.get_one("sample_y"))
            trial.add_enhancement("sample_angle", sample_angle)

            # parse trial id
            trial_id = trial.get_one("trial_id") - 100 * task_id

            # Parse LLR
            # task_adaptiveODR3.c "Task Info" menu has P1-P9, which
            #   corresponds to the probability of showing the cue
            #   at locations far from (P1) or close to (P9) the true
            #   target

            # Pyramid passes in the subject_info, which we can check for conditional computations.
            # This info came from the command line as "--subject subject.yaml"

            # 0-8 for T1/T2, used below
            llr_id = int(trial_id) % 9
            if experiment_info.get("monkey") == "Mr Miyagi":
                ps = [0.0, 0.0, 0.0, 0.10, 0.20, 0.30, 0.15, 0.15, 0.10]
            else:  # Currently identical for other monkeys...
                ps = [0.0, 0.0, 0.0, 0.10, 0.20, 0.30, 0.15, 0.15, 0.10]

            # Compute LLR, - favors T1, + favors T2
            if trial_id < 9: # T1 is correct
                target_angles = [t1_angle, t2_angle]
                correct_target = 1
                sample_id = llr_id - 4
                llr = log10(ps[llr_id]) - log10(ps[-(llr_id+1)])
            else:   # T2 is correct
                target_angles = [t2_angle, t1_angle]
                correct_target = 2
                sample_id = -(llr_id - 4)
                llr = log10(ps[-(llr_id+1)]) - log10(ps[llr_id])

            # Save as enhancements
            trial.add_enhancement("correct_target", correct_target, "id")
            # neg are close to T1, pos are close to T2
            trial.add_enhancement("sample_id", sample_id, "id")
            # evidence for T1 (-) vs T2 (+)
            trial.add_enhancement("llr", llr)

            # Add other computed enhancements
            # 1. trials after change-point
            if self.previous_correct_target != correct_target:
                self.tacp = 0
            else:
                self.tacp += 1
            trial.add_enhancement("tacp", self.tacp, "id")
            # Keep track of correct target for next time
            self.previous_correct_target = correct_target
            
            # 2. llr for switch
            # llr encodes favoring T1 (-) or T2 (+) 
            llr_for_switch = llr

            # First convert to favoring current target (+) or not (-)
            if correct_target == 1:
                llr_for_switch = -llr_for_switch

            # Second flip sign on non-cp trials
            if self.tacp != 0:
                llr_for_switch = -llr_for_switch

            # Save as value
            trial.add_enhancement("llr_for_switch", llr_for_switch)

        # Use trial.get_enhancement() to get saccade info already parsed by SaccadesEnhancer.
        broken_fixation = trial.get_time("fp_off") is None
        saccades = trial.get_enhancement("saccades")
        score = -1
        if broken_fixation:
            # Broken fixation
            score = -2
        elif not saccades or not math.isfinite(saccades[0]["t_start"]):
            # "No choice" error
            score = -1
        else:
            # Find choice from sacccades
            target_index = -1
            min_angular_distance = 360
            for i in range(len(saccades)):
                sac_angle = ang_deg(saccades[i]["x_end"], saccades[i]["y_end"])
                for j in range(len(target_angles)):
                    angular_distance = ang_diff(target_angles[j], sac_angle)
                    # print(f'i={i}, j={j}, angular_distance = {angular_distance}')
                    if ((angular_distance <= self.min_angular_distance_to_target_deg) &
                        (angular_distance < min_angular_distance)):
                        min_angular_distance = angular_distance
                        saccade_index = i
                        target_index = j            

            # Set score
            if target_index == -1:
                score = -1 # no choice
            else:
                if (len(target_angles)==1) or (target_index==0):
                    score = 1
                    trial.add_enhancement("choice", correct_target, "id")
                else:
                    score = 0                
                    trial.add_enhancement("choice", 3-correct_target, "id")

                trial.add_enhancement("scored_saccade_index", saccade_index, "id")      # index of the closest saccade
                trial.add_enhancement("all_saccades", saccades, "value")                # copy of all the saccades
                trial.add_enhancement("saccades", saccades[saccade_index], "value")     # overwrite with the closest saccade to work with existing code
                saccade_start = saccades[saccade_index]["t_start"]
                trial.add_enhancement("sac_on", saccade_start, "time")

                fp_off_time = trial.get_time("fp_off")
                rt_millis = (saccade_start - fp_off_time)*1000
                if rt_millis<0:
                    print("RT somehow negative...")
                trial.add_enhancement("RT", rt_millis, "value")

                # Debugging: why do RT values seem small?
                # Seeing like 138ms, 152ms, 140ms
                # Expecting more like 250ms
                # Are these real in the data?
                # print(f"ttl 2 {trial.numeric_events['ttl'].times(2)}")
                # print(f"fp_on {trial.get_time('fp_on')}")
                # print(f"ttl 3 {trial.numeric_events['ttl'].times(3)}")
                # print(f"fp_off {trial.get_time('fp_off')}")
                # print(f"sac_on {saccade_start}")
                # print(f"RT {rt_millis}")

        # 1=correct, 0=error, -1=nc, -2=brfix,-3=sample
        trial.add_enhancement("score", score, "id")

        # Use trial.get_one() to grab the first timestamp from each "time" enhancement.
        score_times = [
            trial.get_time("online_brfix", default=None),
            trial.get_time("online_ncerr", default=None),
            trial.get_time("online_error", default=None),
            trial.get_time("online_correct", default=None),
        ]

        # We can use Python list comprehension to search for the non-None times.
        l_score = [index for index, time in enumerate(score_times) if time is not None]
        if l_score:
            # convert to -2 -> 1
            online_score = l_score[0] - 2 # LWT changed from -3 to -2 on 3/5/24
            # online score: 1=correct, 0=error, -1=nc, -2=brfix
            # NORMAL ENHANCEMENT
            trial.add_enhancement("online_score", online_score)
            trial.add_enhancement("score_match", score == online_score)

class SaccadesEnhancer(TrialEnhancer):
    """Parse saccades from the x,y eye position traces in a trial using velocity and acceleration thresholds.
    This is adapted from the stand_enhancer SaccadeEnhancer, but modified to match "findSaccadesAODR.m" used in FIRA

    Args:
        max_saccades:                           Parse this number of saccades, at most (default 1).
        center_at_fp:                           Whether to re-zero gaze position at fp off time (default True).
        x_buffer_name:                          Name of a Trial buffer with gaze signal data (default "gaze").
        x_channel_id:                           Channel id to use within x_buffer_name (default "x").
        y_buffer_name:                          Name of a Trial buffer with gaze signal data (default "gaze").
        y_channel_id:                           Channel id to use within y_buffer_name (default "y").
        fp_off_name:                            Name of a trial enhancement with time to start saccade parsing (default "fp_off").
        all_off_name:                           Name of a trial enhancement with time to end saccade parsing (default "all_off").
        fp_x_name:                              Name of a trial enhancement with fixation x position (default "fp_x").
        fp_y_name:                              Name of a trial enhancement with fixation y position (default "fp_y").
        position_smoothing_kernel_size_ms:      Width of kernel to smooth gaze position samples (default 0 -- ie no smoothing).
        velocity_smoothing_kernel_size_ms:      Width of kernel to smooth gaze velocity samples (default 10 -- ie smoothing).
        acceleration_smoothing_kernel_size_ms:  Width of kernel to smooth gaze acceleration samples (default 0 -- no ie smoothing).
        velocity_threshold_deg_per_s:           Threshold for detecting saccades by velocity in gaze deg/s (default 300).
        acceleration_threshold_deg_per_s2:      Threshold for detecting saccades by acceleration in gaze deg/s^2 (default 8).
        min_length_deg:                         Minimum length for a saccade to count in gaze deg (default 3.0).
        min_latency_ms: float = 10,             Minimum latency in ms that must elapse before a saccade for it to count (default 10).
        min_duration_ms: float = 5.0,           Minimum duration in ms of a saccade for it to count (default 5.0).
        max_duration_ms: float = 90.0,          Maximum duration in ms of a saccade for it to count (default 90.0).
        saccades_name:                          Trial enhancement name to use when adding detected saccades (default "saccades").
        saccades_category:                      Trial category to use when adding detected saccades (default "saccades").
    """

    def __init__(
        self,
        max_saccades: int = 1,
        center_at_fp: bool = True,
        x_buffer_name: str = "gaze",
        x_channel_id: str | int = "x",
        y_buffer_name: str = "gaze",
        y_channel_id: str | int = "y",
        fp_off_name: str = "fp_off",
        all_off_name: str = "all_off",
        fp_x_name: str = "fp_x",
        fp_y_name: str = "fp_y",
        position_smoothing_kernel_size_ms: int = 0,
        velocity_smoothing_kernel_size_ms: int = 10,
        acceleration_smoothing_kernel_size_ms: int = 0,
        velocity_threshold_deg_per_ms: float = 0.3,
        velocity_peak_threshold_deg_per_ms: float = 0.04,
        acceleration_threshold_deg_per_ms2: float = 4,
        min_length_deg: float = 3.0,
        min_latency_ms: float = 10,
        min_duration_ms: float = 5.0,
        max_duration_ms: float = 90.0,
        saccades_name: str = "saccades",
        saccades_category: str = "saccades"
    ) -> None:
        self.max_saccades = max_saccades
        self.center_at_fp = center_at_fp
        self.x_buffer_name = x_buffer_name
        self.x_channel_id = x_channel_id
        self.y_buffer_name = y_buffer_name
        self.y_channel_id = y_channel_id
        self.fp_off_name = fp_off_name
        self.all_off_name = all_off_name
        self.fp_x_name = fp_x_name
        self.fp_y_name = fp_y_name
        self.position_smoothing_kernel_size_ms = position_smoothing_kernel_size_ms
        self.velocity_smoothing_kernel_size_ms = velocity_smoothing_kernel_size_ms
        self.acceleration_smoothing_kernel_size_ms = acceleration_smoothing_kernel_size_ms
        self.velocity_threshold_deg_per_ms = velocity_threshold_deg_per_ms
        self.velocity_peak_threshold_deg_per_ms = velocity_peak_threshold_deg_per_ms
        self.acceleration_threshold_deg_per_ms2 = acceleration_threshold_deg_per_ms2
        self.min_length_deg = min_length_deg
        self.min_latency_ms = min_latency_ms
        self.min_duration_ms = min_duration_ms
        self.max_duration_ms = max_duration_ms
        self.saccades_name = saccades_name
        self.saccades_category = saccades_category

    def enhance(self, trial: Trial, trial_number: int, experiment_info: dict, subject_info: dict) -> None:

        # Get event times from trial enhancements to delimit saccade parsing.
        fp_off_time = trial.get_time(self.fp_off_name)
        all_off_time = trial.get_time(self.all_off_name)
        targAcq_time = trial.get_time("targ_acq")
        if fp_off_time is None or all_off_time is None or targAcq_time is None:
            return

        # Use trial.signals for gaze signal chunks.
        if self.x_buffer_name not in trial.signals or self.y_buffer_name not in trial.signals:  # pragma: no cover
            return
        x_signal = trial.signals[self.x_buffer_name]
        y_signal = trial.signals[self.y_buffer_name]
        if x_signal.end() < fp_off_time or y_signal.end() < fp_off_time:  # pragma: no cover
            return

        # Possibly center at fp.
        x_channel_index = x_signal.channel_index(self.x_channel_id)
        y_channel_index = y_signal.channel_index(self.y_channel_id)
        if self.center_at_fp is True:
            x_signal.apply_offset_then_gain(-x_signal.at(fp_off_time, x_channel_index), 1)
            y_signal.apply_offset_then_gain(-y_signal.at(fp_off_time, y_channel_index), 1)

        # Get x,y data from the relevant time range, fp_off to all_off.
        x_position = x_signal.values(x_channel_index, fp_off_time, all_off_time)
        y_position = y_signal.values(y_channel_index, fp_off_time, all_off_time)

        # default return
        saccades = []

        # for smoothing
        smf   = np.array([0.0033, 0.0238, 0.0971, 0.2259, 0.2998, 0.2259, 0.0971, 0.0238, 0.0033])
        hsmf  = (smf.size - 1) // 2
        t_int = 1000 / x_signal.sample_frequency  # sample interval, in ms

        # make sure there's data to be parsed
        if len(x_position) != len(y_position) or len(x_position) < len(smf):
            return saccades

        # smooth the curves
        x_position = np.convolve(x_position, smf, mode='same')
        y_position = np.convolve(y_position, smf, mode='same')

        # get velocity, sub out median
        vel  = np.concatenate(([0], np.sqrt(np.diff(x_position)**2 + np.diff(y_position)**2) / t_int))
        vels = vel - np.median(vel)
        acc  = np.convolve([0.2, 0.2, 0.2, 0.2, 0.2], np.diff(vels), mode='valid')

        # find all instantaneous velocities >= min peak
        vps = np.where(vels >= self.velocity_peak_threshold_deg_per_ms)[0]

        # so we don't have to keep checking the same samples
        last_end = 0

        while len(saccades) < self.max_saccades:
            # find first string of 5 consecutive velocities bigger than peak
            while len(vps) > 4 and vps[4] - vps[0] != 4:
                vps = np.delete(vps, 0)

            if len(vps) < 5:
                break
            
            sac_begin = np.nan
            # sac begins at earliest of acc > A_MIN &
            # vel > VI_MIN -OR- acc < -A_MIN & vel < VP_MIN
            acc_thresh = np.where(acc[last_end:vps[0]] < self.acceleration_threshold_deg_per_ms2)
            other_thresh = np.where(np.logical_or(vels[last_end:vps[0]] <= self.velocity_threshold_deg_per_ms,
                                                                np.logical_and(acc[last_end:vps[0]] < -self.acceleration_threshold_deg_per_ms2,
                                                                                vels[last_end:vps[0]] < self.velocity_peak_threshold_deg_per_ms)))
            if acc_thresh[0].size !=0:
                acc_thresh = acc_thresh[0][-1]
                
                if other_thresh[0].size != 0:
                    # other threshold also passed
                    sac_begin = last_end + min(acc_thresh,other_thresh[0][-1])
                else:
                    # No other threshold besides acc
                    sac_begin = last_end + acc_thresh
            elif other_thresh[0].size != 0:
                # other threshold passed
                # ignore the acc_thresh possibility
                inds = other_thresh[0][-1]
                if inds.size > 1:
                    sac_begin = last_end + min(inds)
                else:
                    sac_begin = last_end + inds

            # sac ends at first acc > -A_MIN after deceleration. the -5 accounts
            # for the acc smoothing.
            acc_thresh = np.where(acc[vps[4]+1:] < self.acceleration_threshold_deg_per_ms2)
            if acc_thresh[0].size !=0:
                decel = vps[4] + acc_thresh[0][0]
            else:
                decel = np.nan

            # check if any found
            if np.isnan(sac_begin) or np.isnan(decel):
                # new start point
                last_end = vps[4]
                vps = vps[4:]
            else:
                # new start point
                acc_decel_thresh = np.where(acc[decel+1:-1] > -self.acceleration_threshold_deg_per_ms2)
                vels_decel_thresh = np.where(vels[decel:-2] <= 0.005)

                if acc_decel_thresh[0].size !=0 and vels_decel_thresh[0].size !=0:
                    acc_decel_thresh = acc_decel_thresh[0][0]
                    vels_decel_thresh = vels_decel_thresh[0][0]
                    sac_end = decel - 5 + max(acc_decel_thresh,vels_decel_thresh)
                elif acc_decel_thresh[0].size !=0:
                    acc_decel_thresh = acc_decel_thresh[0][0]
                    sac_end = decel - 5 + acc_decel_thresh
                elif vels_decel_thresh[0].size !=0:
                    vels_decel_thresh = vels_decel_thresh[0][0]
                    sac_end = decel - 5 + vels_decel_thresh
                else:
                    sac_end = decel - 5
                    
                # vector distance
                len_ = np.sqrt((x_position[sac_end] - x_position[sac_begin-1])**2 +
                            (y_position[sac_end] - y_position[sac_begin-1])**2)
                # technically, the saccade could be sufficiently long, but not end up in a reasonable spot
                end_pos_len = np.sqrt((x_position[sac_end])**2 +
                            (y_position[sac_end])**2)

                # Saccades must meet multiple criteria in addition to exceeding our velocity/acceleration thresholds:
                # 1) The length of the saccade exceeds some threshold
                # 2) The end position of the saccade is greater than a minimum distance threshold
                # 3) The end position of the saccade is less than a maximum distance threshold
                # 4) MAYBE: The saccade latency cannot be greater than Rex's recorded time that the target was acquired
                # Get start/end times wrt fixation off.
                sac_start_time = fp_off_time + (sac_begin + 1) / x_signal.sample_frequency
                sac_end_time = fp_off_time + (sac_end + 1) / x_signal.sample_frequency
                sac_duration = sac_end_time - sac_start_time
                targAcq_latency = trial.get_time("targ_acq") - fp_off_time
                if len_ >= self.min_length_deg and end_pos_len>5 and end_pos_len<18: #and (sac_end_time-fp_off_time)<targAcq_latency:
                    # return stuff
                    saccades.append({
                        "t_start": sac_start_time,
                        "t_end": sac_end_time,
                        "v_max": np.max(vels[sac_begin:sac_end]),
                        "v_avg": len_ / sac_duration,
                        "x_start": x_position[sac_begin],
                        "y_start": y_position[sac_begin],
                        "x_end": x_position[sac_end],
                        "y_end": y_position[sac_end],
                        "raw_distance": np.sum(vels[sac_begin:sac_end])/x_signal.sample_frequency,
                        "vector_distance": len_,
                    })

                # new start point
                vps = vps[vps > sac_end]
                last_end = sac_end + 1

        # add final sac if eye position of final sac is different
        # than position at 300 ms
        if len(saccades) < self.max_saccades and (len(saccades) == 0 or saccades[-1]["t_end"] + saccades[-1]["t_start"] < 500):
            saccades.append({
                        "t_start": np.nan,
                        "t_end": np.inf,
                        "v_max": np.nan,
                        "v_avg": np.nan,
                        "x_start": np.nan,
                        "y_start": np.nan,
                        "x_end": np.nan,
                        "y_end": np.nan,
                        "raw_distance": np.nan,
                        "vector_distance": np.nan,
                    })
        # Add the list of saccade dictionaries to trial enhancements.
        trial.add_enhancement(self.saccades_name, saccades, self.saccades_category)