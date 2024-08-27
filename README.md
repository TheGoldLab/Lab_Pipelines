# Lab_Pipelines

Goal: Install all required software, packages, and dependencies for data preprocessing in the Gold Lab.

## Installing GitHub Repositories
We use Git, software that tracks versions of files, to manage the versions of our code. Repositories ("repos") hold a set of files and extra information about those files. GitHub is the standard website that uses Git to allow developers to create, store, manage and share their code. This way, we can easily use the same code and keep track of changes each person made.

To run data through our pipeline you will need 3 primary repositories:

1) The [Pyramid](https://github.com/benjamin-heasly/pyramid) repository contains code that takes raw data (like neural, eye, and behavioral) and creates a file where data are aligned by trial (a "TrialFile" with .hdf5 extension). This is custom preprocessing that largely depends on how you are communicating across devices to indicate when different events (e.g., fixation onset or stimulus onset) are occuring.

2) The [Lab_Matlab_Utilities](https://github.com/TheGoldLab/Lab_Matlab_Utilities) repository contains custom utilities specifically for the Gold Lab. These include operations to deal with data files, plotting, etc.

3) This Lab_Pipelines repository contains documents and configurations for lab data pipelines (spike sorting, trial deliniation, etc.).

## Install Git/Github Desktop for retrieving the repositories
The only change you'll need to make to the default installation is to configure the terminal emulator to use with Git Bash. For Windows, choose the default console window.
Install GitHub desktop and sign in.
In the "Current repository" dropdown menu, click "Add," then "Clone repository..." to add pyramid from benjamin-heasly's GitHub: https://github.com/benjamin-heasly/pyramid.
Click "Clone a repository from the Internet..." and add Lab_Matlab_Utilities from The Gold Lab GitHub: https://github.com/TheGoldLab/Lab_Matlab_Utilities.
Do the same to add Lab_Pipelines from The Gold Lab GitHub: https://github.com/TheGoldLab/Lab_Pipelines.

## Installing Pyramid
Documentation and installation instructions are included in the [Pyramid](https://github.com/benjamin-heasly/pyramid) readme, but the below steps should be sufficient.

If you don't already have Python, install it from python.org or the Microsoft Store.

Miniconda is a smaller installation of anaconda, a package manager and environment management system. An environment is an isolated virtual space to install a set of software packages for a project. This allows you to avoid conflicts between packages. Pyramid has its own environment that contains Python dependencies. Here, we will install and activate the environment where pyramid runs. If you have a Mac, you can also just use regular Anaconda instead of miniconda.

1) Install miniconda and follow setup instructions.
2) Write down its location for later.
3) Launch Anaconda Prompt (miniconda3) from the Start menu/applications folder. You can use a standard terminal for Mac.
4) To set up the pyramid environment, copy and paste this code into Anaconda Prompt (or terminal) and run it:
```
cd <your_parent_path>\GitHub\pyramid
conda env create -f environment.yml
```
5) Activate the environment on your machine. Copy and paste this code into Anaconda Prompt and run it:
```
conda activate pyramid
pip install .
pyramid --help
```

This helps ensure that you are able to use pyramid independent of the Lab Pipeline repo.

## Testing Pyramid
Now, we will see if you can use the new pipeline with pyramid on some raw data. There are example scripts written in the Python programming language that pass data through pyramid. These allow you to specify the locations of folders on your computer and the file you want to convert and then run pyramid, avoiding having to interact with the computer through the command line as suggested in the pyramid documentation/readme.

Older data were likely collected with a Plexon system and have a .plx file extension. On the other hand, OpenEphys is the software that accepts data from Neuropixels probes (large-scale neural recording), and these files have an .nwb extension (although it can also save binary files). These different formats require different "readers" to extract data into pyramid. We are also using a different spike sorting algorithm for OpenEphys data. There are separate Python scripts depending on whether you're converting a .plx or .nwb file.

Open Visual Studio Code (VS Code) or another integrated development environment (IDE) for editing code.
Install the Python extension for VS Code (also under the Extensions tab on the left) to make it work as a Python editor.
The custom Python code works within the gold_pipelines conda environment. You must first create this environment, similar to what you did for pyramid.
In the terminal, copy and paste the code below, after subsituting your parent directory, to create and activate the gold_pipelines conda environment. You can read more about activation here.
```
cd <your_parent_path>\GitHub\Lab_Pipelines
conda env create -f environment.yml
```
### don't forget to ACTIVATE the environment before trying to use stuff in VS Code
```
conda activate gold_pipelines
```
You should see "gold_pipelines" in the bottom right corner of VS Code now. You can also select the interpreter by clicking the bottom right corner and then "gold_pipelines" from the dropdown menu that appears under the search bar in the top middle of the screen.
Now: File>Open Folder> select GitHub\Lab_Pipelines\experiments\aodr (you could make a new folder for your experiment - the example is based on the AODR paradigm).
Open Pyramid_Example_Plexon.py for .plx files or spikeinterface_testing_v2.ipynb for OpenEphys.
Follow the documentation written in the spikeinterface notebook to run OpenEphys data through pyramid. If using Pyramid_Example_Plexon.py, change the path names and file name to the corresponding locations and files on your computer. You might want to create a separate, new folder for output.
Run.

## Installing MATLAB and running test scripts
MATLAB is the standard programming language for scientific computing in the neurosciences. Custom scripts for data analysis (after preprocessing with pyramid) are written in MATLAB.

Here, we will get MATLAB ready to run data analysis scripts by updating paths and installing toolboxes. Adding files, such as our data and GitHub repositories, to MATLAB's search path allows it to "see" and use them. Toolboxes are packages of MATLAB functions that extend its capabilities. These toolboxes contain specific functions needed for the data analysis we will perform.

Install MATLAB. You may need to create a MathWorks account.
Licensing information if you need it: Licensing 353265 - MATLAB (Individual), Master License 30353265
Add the GitHub repositories to the current path. Under the home tab, go to environment, then Set Path. Click Add with Subfolders... and locate the GitHub folder (ex. C:\Users\marazita\Documents\GitHub). This allows MATLAB to use the Lab_Matlab_Utilities and Pyramid repositories we cloned earlier.
Add the path where you saved the data produced from Pyramid in the previous section.
Install the following toolboxes from Add-On Explorer:
Mapping Toolbox
Optimization Toolbox
Curve Fitting Toolbox
Statistics and Machine Learning Toolbox
Testing MATLAB Analysis

Now that MATLAB is set up, we should be able to run one of the custom analysis scripts. We will test plotAODR_sessionBehavior, a custom MATLAB plotting function that takes behavior data from the trial file created by pyramid and plots logistic fits, performance over trials, reaction time by choice and hazard, and eye positions. Reproducing this figure indicates that things are working.

In MATLAB:
1) Change goldLabDataSessionLocalPathnames in the dataSession folder of this repository
2) Open testMATLAB.m, located in Box\GoldLab\Analysis\AODR\scripts.
3) Change the Filename variable to the full file path of the location of the trial file (session) you want to use.
4) Update the Monkey variable if necessary.
5) Right-click the testMATLAB.m tab and change your current folder to its location.
6) Important: Remove the dataSession folder within the Lab_Matlab_Utilities folder from your path. It has a different version of plotAODR_sessionBehavior, and will be removed once this repository is confirmed to work.
7) Add the Box\GoldLab\Analysis\AODR folder and subfolders to your path.
8) Click Run.
