conda activate gold_pipelines

pyramid graph \
--search-path /home/ninjaben/open-ephys/from_lowell \
--experiment AODR_experiment.yaml \
--graph-file aodr-test.png

pyramid convert \
--search-path /home/ninjaben/open-ephys/from_lowell \
--experiment AODR_experiment.yaml \
--subject AODR_subject.yaml \
--trial-file aodr-test.json
