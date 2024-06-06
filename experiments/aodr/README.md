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

# What units are these?
# They seem centered on FP?
# But different by an unknown factor (10?)
# Are these partially ecode-encoded, like with a scale but not the 6000 offset?
# Could we send them plain, as floats?
# "fp_x": 0.0
# "fp_y": 0.0
# "t1_x": 71.0
# "t1_y": 71.0
# "t2_x": 71.0
# "t2_y": -71.0
# "sample_x": 81.0
# "sample_y": 59.0

# I added several ecodes to the default_ecode_rules.csv
# I started here: https://github.com/TheGoldLab/Lab_Rex/blob/master/sset/lcode.h
# and guessed at reasonable variable names.

# Trial get_one() and get_time() are working from CustomEnhancer!
# They are not so graceful from trial expressions.
# Bind these in as callable utils?