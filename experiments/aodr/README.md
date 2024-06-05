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

# Trial util to get one time from a named enhancement or event list
# Trial util to get one value from a named enhancement or event list
# Saccades parser code use the time util
# Other users of get_enhancement() use these utils

# Plot saccade XY pairs from list of saccades, not just single dict?
