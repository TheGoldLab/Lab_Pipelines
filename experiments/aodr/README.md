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

# Plot saccade XY pairs from list of saccades, not just single dict?

# Want the ecodes event lists to end up as named enhancements, not obscure event lists.
# Or named events lists is fine?
# An alias enhancer?
