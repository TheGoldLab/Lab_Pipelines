# Lab_Pipelines

Config and pipeline definitions for spike sorting, trials, etc.

# Conda environment setup

We have a [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) environment called `gold_pipelines` defined here in `environment.yml`.  If you create this environment locally and activate it, you should be all set to work with pipelines here in this repo.
This should meet dependenices for two main Python projects:

 - [Proceed](https://github.com/benjamin-heasly/proceed) (Docker-based pipelines)
 - [Pyramid](https://github.com/benjamin-heasly/pyramid) (Data synthesis and trial files)


Here are some commands for setting up the Conda environment.

```
# get this repo
git clone https://github.com/TheGoldLab/Lab_Pipelines
cd Lab_Pipelines

# create a fresh environment -- can take several minutes
conda env create -f environment.yml

# if the environment already exists, you can make sure it's up to date like this:
conda env update -f environment.yml --prune

# you can also delete the environment and start fresh
conda remove -n gold_pipelines --all

# don't forget to ACTIVATE the environment before trying to use stuff
conda activate gold_pipelines
```

# Related
Here are a few related repos that we've been working on for the Gold lab in 2022 / 2023.

## this repo

 - https://github.com/TheGoldLab/Lab_Pipelines

## repose used indirectly from here

 - https://github.com/benjamin-heasly/pyramid
 - https://github.com/benjamin-heasly/proceed
 - https://github.com/benjamin-heasly/plx-to-kilosort
 - https://github.com/benjamin-heasly/kilosort3-docker
 - https://github.com/benjamin-heasly/Kilosort
 - https://github.com/benjamin-heasly/phy-to-fira

## scenery we learned about, we might revisit

 - https://github.com/benjamin-heasly/spikeglx-tools-poc
 - https://github.com/benjamin-heasly/signac-poc
