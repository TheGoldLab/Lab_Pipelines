# Repo Madness

I (Ben H) recently (Oct 2023) reorgnized the repos and environments we've been working with.
Hopefully the new organization is good going forward, but we'll have to do some annoying swapping over from the old.

Here are some notes for how to do the swap.

If you're setting up a machine after Oct 2023, you can ignore this and just use the main [README.md](README.md).

# Summary of Changes

## repos

We had been working with [gold-lab-nwb-conversions](https://github.com/benjamin-heasly/gold-lab-nwb-conversions).
This repo contained:

 - the Pyrmaid project for making raw data into trial files
 - lab-specific proof of concept code for working with NWB files

The `gold-lab-nwb-conversions` repository is kaput!  We decided not to focus on NWB, which made the name seem dumb, and anyway it seems good to move Pyramid out to own repo.

Now we should switch to [pyramid](https://github.com/benjamin-heasly/pyramid) for the Pyramid project itself, and [Lab_Pipelines](https://github.com/TheGoldLab/Lab_Pipelines) for lab-specific code, experiment and subject YAML files, etc.

## environments

Likewise, we had been working with Conda environments named `pipeline-stuff` and/or `gold_nwb`.
These environments are kaput!

Going forward, we should switch to using `gold_pipelines`, which should be equivalent, and is defined here in this `Lab_Pipelines` repo.

# Steps for Proceed pipelines (NP machine?)

Here are some steps we can follow for machines where we've been running the spike sorting pipeline with [Proceed](https://github.com/benjamin-heasly/proceed).

## repo `gold-lab-nwb-conversions` -> `Lab_Pipelines`

Check on the status of the existing `gold-lab-nwb-conversions` code.

```
cd /mnt/d/repos/gold-lab-nwb-conversions
git staus
```

If the status is clean, we can just go ahead.
If there are local changes or new files, we need to review those and decide what's important to keep.
Make a note of the local files we want to carry forward.

Get this `Lab_Pipelines` repo, which should be a 1:1 replacement for `gold-lab-nwb-conversions` including Proceed config and pipeline definitions.

```
cd /mnt/d/repos
git clone https://github.com/TheGoldLab/Lab_Pipelines
```

If we had changes to carry forward, copy those from `/mnt/d/repos/gold-lab-nwb-conversions` into the corresponding places within `/mnt/d/repos/Lab_Pipelines`.

To commit those changes (please!), see the neuropixels-machine-setup [README.md](pipelines/docs/neuropixels-machine-setup/README.md) which has instructions for setting up credentials for `git push`.

Now to avoid confusion we should delete `/mnt/d/repos/gold-lab-nwb-conversions` or move it to the Windows trash.

## environments `gold_nwb` or `pipeline-stuff` -> `gold_pipelines`

From this `Lab_Pipelines` repo we can set up the new `gold_pipelines` Conda environment.

```
cd /mnt/d/repos/Lab_Pipelines
conda env create -f environment.yml
```

To avoid confusion, we should also delete the old environments.

```
conda remove -n gold_nwb --all
conda remove -n pipeline-stuff --all
```

## local scripts, notes, etc.

I tried to update instructions in this repo to refer to the `Lab_Pipelines` repo and `gold_pipelines` environment going forward.

I'm not sure what other scripts, notes, etc. we have that refer to the old stuff.  Some changes to look out for would be like:
 - `cd /mnt/d/repos/gold-lab-nwb-conversions` -> `cd /mnt/d/repos/Lab_Pipelines`
 - `conda activate gold_nwb` -> `conda activate gold_pipelines`
 - `conda activate pipeline-stuff` -> `conda activate gold_pipelines`

That might be all.
After those changes, do things that worked before still work?

# Steps for Pyramid trial files (Josh's laptop?)

Here are some steps we can follow for machines where we've been making Pyramid trial files.

## repo `gold-lab-nwb-conversions` -> `pyramid`

Check on the status of the existing `gold-lab-nwb-conversions` code.

```
cd gold-lab-nwb-conversions
git staus
```

If the status is clean, we can just go ahead.
If there are local changes or new files, we need to review those and decide what's important to keep.
Make a note of the local files we want to carry forward.

Get the `pyramid` repo, which is the new home of the Pyramid project.

```
git clone https://github.com/benjamin-heasly/pyramid
```

If we had changes to carry forward, copy those from `gold-lab-nwb-conversions/pyramid` into the corresponding places within the new `pyramid`, and let's figure out if we need to commit the changes to GitHub.

Now to avoid confusion we should delete `gold-lab-nwb-conversions` or move it to the trash.

## environment `gold_nwb` -> `gold_pipelines`

With this `Lab_Pipelines` repo we can set up the new `gold_pipelines` Conda environment.

```
git clone https://github.com/TheGoldLab/Lab_Pipelines
cd Lab_Pipelines
conda env create -f environment.yml
```

To avoid confusion we should also delete the old environment.

```
conda remove -n gold_nwb --all
```

## local scripts, notes, etc.

I'm not sure what other local scripts, notes, etc. might refer to the old stuff.
The changes to look out for would be like:
 - `cd gold-lab-nwb-conversions/pyramid` -> `cd pyramid`
 - `conda activate gold_nwb` -> `conda activate gold_pipelines`

That might be all.
After making those changes, do things that worked before still work?

Depending on what's there, we might want to add and commit some of these files to this repo under `Lab_Pipelines/experiments`.
