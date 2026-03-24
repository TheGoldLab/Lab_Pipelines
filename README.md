# Lab_Pipelines

Goal: Install all required software, packages, and dependencies for data preprocessing in the Gold Lab.

## Installing GitHub Repositories
We use Git, software that tracks versions of files, to manage the versions of our code. Repositories ("repos") hold a set of files and extra information about those files. GitHub is the standard website that uses Git to allow developers to create, store, manage and share their code. This way, we can easily use the same code and keep track of changes each person made.

To run data through our pipeline you will need 3 primary repositories:

1) The [Pyramid](https://github.com/lwthompson2/pyramid.git) repository contains code that takes raw data (like neural, eye, and behavioral) and creates a file where data are aligned by trial (a "TrialFile" with .hdf5 extension). This is custom preprocessing that largely depends on how you are communicating across devices to indicate when different events (e.g., fixation onset or stimulus onset) are occurings.

IMPORTANT: If you make changes to the pyramid repository, your changes will not be reflected in the environment. You will need to uninstall pyramid from your environment and reinstall it with the updated version. If you make changes to the pyramid files that are installed in your environment directly (bad idea) they will be overwritten if you ever update the environment and your changes will be lost. If you make changes to pyramid, I recommend you make your own branch of the repo. You can simply activate your environment, cd to the pyramid repo directory, and type "install ."

2) The [Lab_Matlab_Utilities](https://github.com/TheGoldLab/Lab_Matlab_Utilities) repository contains custom utilities specifically for the Gold Lab. These include operations to deal with data files, plotting, etc.

3) This Lab_Pipelines repository contains documents and configurations for lab data pipelines (spike sorting, trial deliniation, etc.).

## Install Git/Github Desktop for retrieving the repositories
The only change I made to defaults was in configuring the terminal emulator to use with Git Bash. I chose to use Windows' default console window.
Install GitHub desktop and sign in.
In the "Current repository" dropdown menu, click "Add," then "Clone repository..." to add pyramid: https://github.com/lwthompson2/pyramid.git.
Click "Clone a repository from the Internet..." and add Lab_Matlab_Utilities from The Gold Lab GitHub: https://github.com/TheGoldLab/Lab_Matlab_Utilities.
Do the same to add Lab_Pipelines from The Gold Lab GitHub: https://github.com/TheGoldLab/Lab_Pipelines.

## Installing Pyramid Tools
Using anaconda or miniconda will make life easier for creating python environments and should provide you with the base packages.
Miniconda is a smaller installation of anaconda, a package manager and environment management system. An environment is an isolated virtual space to install a set of software packages for a project. This allows you to avoid conflicts between packages.

1) Install miniconda and follow setup instructions.
2) Write down its location for later.
3) Install Visual Studio Code

Open Visual Studio Code (VS Code) or another integrated development environment (IDE) for editing code.
Install the Python extension for VS Code (also under the Extensions tab on the left) to make it work as a Python editor.
The custom Python code works within the gold_pipelines conda environment. You must first create this environment.
In the terminal, or Anaconda Prompt, copy and paste the code below after subsituting your parent directory to create and activate the gold_pipelines conda environment. You can read more about activation here.
```
cd <your_parent_path>\GitHub\Lab_Pipelines
conda env create -f environment.yml
```
### don't forget to ACTIVATE the environment before trying to use stuff in VS Code
```
conda activate gold_pipelines
```
You should see "gold_pipelines" in the bottom right corner of VS Code now. Select the interpreter by clicking the bottom right corner and then "gold_pipelines" from the dropdown menu that appears under the search bar in the top middle of the screen.
Now File>Open Folder> select GitHub\Lab_Pipelines\experiments\your_experiment (or make a new one)

When you run some example scripts, you will likely encounter some errors related to fiass depending on your system. Google is your friend to resolve those issues.
If you want to use kilosort4 you will likely want to follow their instructions for getting the GPU CUDA drivers up and running.

The thing that you will likely change the most are the "yaml" experiment files, so for more information see this reference:
https://github.com/lwthompson2/pyramid/blob/main/docs/reference/yaml-config.md

## Installing MATLAB and running test scripts
MATLAB is the standard programming language for scientific computing in the neurosciences. Custom scripts for data analysis (after preprocessing with pyramid) are written in MATLAB.

Here, we will get MATLAB ready to run data analysis scripts by updating paths and installing toolboxes. Adding files, such as our data and GitHub repositories, to MATLAB's search path allows it to "see" and use them. Toolboxes are packages of MATLAB functions that extend its capabilities. These toolboxes contain specific functions needed for the data analysis we will perform.

Install MATLAB. You may need to create a MathWorks account.
Contact your PI for licensing information if you need it.
Add the GitHub repositories to the current path. This allows MATLAB to use the Lab_Matlab_Utilities and Pyramid repositories we cloned earlier.
Add the path where you saved the data produced from Pyramid in the previous section.
Install the following toolboxes from Add-On Explorer:
Mapping Toolbox
Optimization Toolbox
Curve Fitting Toolbox
Statistics and Machine Learning Toolbox
Testing MATLAB Analysis

In MATLAB:
1) Change goldLabDataSessionLocalPathnames in the dataSession folder of this repository to match your system settings. I believe this is largely obsolete since we run Pyramid in python directly and usually specify data paths separately as well.
