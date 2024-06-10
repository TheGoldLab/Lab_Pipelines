conda activate gold_pipelines

pyramid graph \
--search-path /home/ninjaben/open-ephys/from_lowell \
--experiment AODR_experiment.yaml \
--graph-file aodr-test.png

pyramid gui \
--search-path /home/ninjaben/open-ephys/from_lowell \
--experiment AODR_experiment.yaml \
--subject AODR_subject.yaml \
--trial-file aodr-test.json

pyramid convert \
--search-path /home/ninjaben/open-ephys/from_lowell \
--experiment AODR_experiment.yaml \
--subject AODR_subject.yaml \
--trial-file aodr-test.hdf5


# I added several ecodes to the default_ecode_rules.csv
# I started here: https://github.com/TheGoldLab/Lab_Rex/blob/master/sset/lcode.h
# and guessed at reasonable variable names and scales.

# Trial get_one() and get_time() are working from CustomEnhancer!
# They are not so graceful from trial expressions.
# Bind these in as callable utils?

# 2024-06-10 13:54:57,294 [INFO] Route until 2641.2591 AKA 2641.2591 - 0.0
# 2024-06-10 13:54:57,294 [INFO] Route until 2641.2591 AKA 99.24783333333335 - -2542.011266666667
# 2024-06-10 13:54:57,301 [INFO] Recorded sync for message_reader at time 99.248 with key 2641.2431666666666 (9 total).
# 2024-06-10 13:54:57,306 [INFO] Route until 2641.2591 AKA 2641.2591 - 0.0
# 2024-06-10 13:54:57,306 [INFO] ttl_reader offset up to 2641.2591 AKA 2641.2591
# 2024-06-10 13:54:57,306 [INFO] offset 2641.2591 - 2641.2591 = 0.0
# 2024-06-10 13:54:57,307 [INFO] message_reader offset up to 2641.2591 AKA 99.24783333333335
# 2024-06-10 13:54:57,307 [INFO] offset 95.553 - 2637.5634949502933 = -2542.0104949502934
# 2024-06-10 13:54:57,307 [INFO] ttl copy 2637.5634949502933 to 2641.2591
# 2024-06-10 13:54:57,307 [INFO] messages copy 95.55299999999988 to 99.24860504970684
# 2024-06-10 13:54:57,307 [INFO] gaze copy 2637.5634949502933 to 2641.2591
# Trial 10 ends at TTL time 2641.2591
# It would be nice to include with this the corresponding sync event pair right at TTL 2641.2591 == message 99.248.
# However, the offset from trial to trial is not rock solid, varying by around 1-2ms.
# This is the same size as the timing "fuzz" around the ends of trials, so it matters.
# At the time we're looking for sync events, we're using the previous offset.
# This happens to cap our range of interest at 99.24783333333335, which excludes the 99.248 we want.
# So we calculate a just-barely-wrong trial end time for messages,
# And we lump things that belong to trial 11 into trial 10.
#
# Is there a natural way to include 99.248 in the search?
# Maybe just add some fuzz.
#
# Getting closer, I think I got the most recent sync event in there.
# 2024-06-10 15:23:20,999 [INFO] Route until 2641.2591 AKA 2641.2591 - 0.0
# 2024-06-10 15:23:20,999 [INFO] Route until 2641.2591 AKA 99.24860504970684 - -2542.0104949502934
# 2024-06-10 15:23:21,014 [INFO] Recorded sync for message_reader at time 99.248 with key 2641.2431666666666 (9 total).
# 2024-06-10 15:23:21,028 [INFO] Route until 2641.2591 AKA 2641.2591 - 0.0
# 2024-06-10 15:23:21,028 [INFO] ttl_reader offset up to 2641.2591 AKA 2641.2591
# 2024-06-10 15:23:21,028 [INFO] offset 2641.2591 - 2641.2591 = 0.0
# 2024-06-10 15:23:21,029 [INFO] message_reader offset up to 2641.2591 AKA 99.24860504970684
# 2024-06-10 15:23:21,029 [INFO] offset 99.248 - 2641.2591 = -2542.0111
# 2024-06-10 15:23:21,029 [INFO] ttl copy 2637.5634949502933 to 2641.2591
# 2024-06-10 15:23:21,029 [INFO] messages copy 95.55239495029309 to 99.24800000000005
# 2024-06-10 15:23:21,029 [INFO] gaze copy 2637.5634949502933 to 2641.2591
# So this 99.24800000000005 is much closer to the end time we want,
#         99.248, where it had been
#         99.24860504970684, with the older sync event.
# But we are still rolling the dice on floating point rounding error:
# will the computed end time be greater or less than the exact delimiter time we want.
#
# Is there a natural way to know what's right?
# Maybe snap to a known sync event time, if there is one?
# This is getting really weedy and annoying.
#
# Maybe sketch that out, and if it works here, make it real, with tests?
#
# This might be getting there
# 2024-06-10 16:00:48,559 [INFO] Route until 2641.2591 AKA 2641.2591 - 0.0
# 2024-06-10 16:00:48,559 [INFO] ttl_reader offset up to 2641.2591 AKA 2641.2591
# 2024-06-10 16:00:48,559 [INFO] offset 2641.2591 - 2641.2591 = 0.0
# 2024-06-10 16:00:48,559 [INFO] message_reader offset up to 2641.2591 AKA 99.24860504970684
# 2024-06-10 16:00:48,559 [INFO] offset 99.248 - 2641.2591 = -2542.0111
# 2024-06-10 16:00:48,559 [INFO] ttl copy 2637.5634949502933 to 2641.2591
# 2024-06-10 16:00:48,560 [INFO] messages copy 95.55239495029309 to 99.248
# 2024-06-10 16:00:48,560 [INFO] gaze copy 2637.5634949502933 to 2641.2591
#
# I ran the whole file, and I think this worked.
# I'm only seeing duplicate ecodes now when expected, like for all_off, unknown_2 and unknown_3
# Except on trial 302:
# Warning: found >1 events for all_off on trial 302
# Warning: found >1 events for hazard on trial 302
# I wonder if this is real in the data.
# I think I can check with my spreadsheet business.
#
# It looks like a real time shift in the data, around line 13895 of this sheet:
# https://docs.google.com/spreadsheets/d/13FrVX2aakZeipZ62OS2uKJJR_C8PG_qdoPwf2_mxWac/edit#gid=0
#
# So, I think a 10ms delay between sync and trial params would help.
# And can also continue or not with fancy stuff in Pyramid.

# Also, dumbly, it looks like we're losing a decimal place when Rex timestamps get over 1000.
# This must be in UDPEvents!
