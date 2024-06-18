# AODR Pyramid Configuration

This folder has Pyramid config and a little custom Python code for processing AODR data from Open Ephys.

It should work in the `gold_pipelines` Conda environment.
The top-level [README](../../README.md) for this repo has instructions to set that up.

Don't forget to activate the Conda environment!

```
conda activate gold_pipelines
```

## Data location

Right now the Pyramid config defaults to run a session of data from 2024-06-05: [Anubis_2024-06-17_13-58-27](https://upenn.box.com/s/xwq8tood2wtlapso0j8inadx2x2oo3ps).

If you don't have it already, you should get this folder on your local machine and note the path leading up to it.

If the full folder path is

```
/Users/benjaminheasly/open-ephys/from_lowell/Anubis_2024-06-17_13-58-27
```

Then the path leading up to it is

```
/Users/benjaminheasly/open-ephys/from_lowell/
```

We'll want to use this leading path, below.

## Running Pyramid

You can run Pyramid to process the Open Ephys NWB data into a Pyramid Trial file.
In the commands below, replace the `--search-path` with your own path leading up to the data folder.

Don't forget to cd to this folder!

```
cd experiments/aodr
```

This command will draw a sweet graph of the Pyramid config:

```
pyramid graph \
--search-path /Users/benjaminheasly/open-ephys/from_lowell \
--experiment AODR_experiment.yaml \
--graph-file aodr-test.png
```

This command will run through trials and update several plot figures for each trial:

```
pyramid gui \
--search-path /Users/benjaminheasly/open-ephys/from_lowell \
--experiment AODR_experiment.yaml \
--subject AODR_subject.yaml \
--trial-file aodr-test.hdf5
```

This command will run through trials as fast as it can, with no plots:

```
pyramid convert \
--search-path /Users/benjaminheasly/open-ephys/from_lowell \
--experiment AODR_experiment.yaml \
--subject AODR_subject.yaml \
--trial-file aodr-test.hdf5
```

The output file will be here in this folder, `aodr-test.hdf5`.

## Running Matlab

With that trial file in hand, `aodr-test.hdf5`, you can press on into Matlab and use some lab Matlab utilities.

You'll need a couple of dependencies in Matlab:

 - Locate and update, or clone [Lab_Matlab_Utilities](https://github.com/TheGoldLab/Lab_Matlab_Utilities) and add the whole thing with subfolders to your Matlab path.
 - Locate and update, or clone [Pyramd](https://github.com/benjamin-heasly/pyramid/tree/main/matlab) and add the `pyramid/matlab/` folder to your Matlab path.

From there you should be able to create a Gold lab data session for `aodr-test.hdf5` and plot things.

Here in this repo, [TestPyramidAODR.m](./matlab/TestPyramidAODR.m) shows one way to do load the Pyramid trial file, convert to a FIRA struct, and make AODR figures.

In Matlab you could try:

```
>> cd experiments/aodr/matlab
>> TestPyramidAODR
```

Or run/copy/modify individual sections of `TestPyramidAODR.m`.
