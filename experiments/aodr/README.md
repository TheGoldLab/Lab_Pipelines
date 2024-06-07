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