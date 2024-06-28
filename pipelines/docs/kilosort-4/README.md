# First Steps With Kilosort 4

This page is here to document our initial look at Kilosort 4 -- helpful links, installation steps, test results, and overall impressions.

In short my (Ben H) initial impressions are very positive!
As a software project Kilosort 4 seems much better thought-out and healthier than Kilosort 3.
I'll call out examples of this, below.

It will probably make sense to adopt Kilosort 4 going forward.
There would be a few steps to making this work with our existing [proceed-spike-sorting](../proceed-spike-sorting/README.md).
I'll try to list these at the end.

# Highlights

There's a Nature methods paper about Kilosort 4, with comparisons to previous versions and other spike sorters: [Spike sorting with Kilosort4
](https://www.nature.com/articles/s41592-024-02232-7).

I'm picking out points from a software project point of view (as opposed to science domain):

 - Python, not Matlab
 - [Pytorch](https://pytorch.org/), including CPU mode, not limited to NVIDIA GPU and CUDA libs
 - straightforward dependency management and install with [pip install kilosort](https://pypi.org/project/kilosort/)
 - inputs are:
   - a binary data file
   - a probe description
   - any non-default GPU and sorting parameter settings
 - recommened (and documented!) way to convert data from other formats is with [SpikeInterface](https://github.com/MouseLand/Kilosort/blob/main/docs/tutorials/load_data.ipynb)
  - outputs are a collection of numpy files that can be loaded and viewed using [Phy](https://phy.readthedocs.io/en/latest/)

There's also the main Git repo: [MouseLand/Kilosort](https://github.com/MouseLand/Kilosort).

 - includes pretty good [tutorials](https://kilosort.readthedocs.io/en/latest/tutorials/tutorials.html) with sample data and step-by-step instructions
 - official support is for Windows and Linux 64, although macOS [works fine](https://github.com/MouseLand/Kilosort/issues/674) in CPU mode
 - cryptic comment: [Kilosort4 might fail for 1 channel.](https://kilosort.readthedocs.io/en/latest/hardware.html)

Installation steps for both CPU-only mode and GPU-accelerated mode were easy to follow.
More on these, below.
In short, I was able to do both and get results on my notebook -- even with AMD graphics, and this was very encouraging.

The main repo contains several [unit tests](https://github.com/MouseLand/Kilosort/tree/main/tests) and a full [end-to-end test](https://github.com/MouseLand/Kilosort/blob/main/tests/test_full_pipeline.py) based on a sample, 500MB Neuropixels recording.
More on these below.
In short, I was able to run and pass all the tests on my notebook, and this is very encouraging!

In less than a day, I was able to make nontrivial progress with Kilosort and feel confident in my installation.
As a developer, this was a very different experience from working with Kilosort 3:
 - no Matlab installation or licensing to mess around with
 - no forums and issues to sift through looking for similar error messages
 - no strict hardware requirements just to get things to run at all
 - separation of concerns between the spike sorting domian code and the Pytorch backend
 - documentation that felt straightforward, to the point, and easy to follow
 - actual test coverage for the project itself

# Installation on Thinkpad T14

I used the main README [instructions](https://github.com/MouseLand/Kilosort?tab=readme-ov-file#installation) to install Kilosort 4 on my [Thinkpad T14](https://www.reddit.com/r/thinkpad/comments/xm1aot/very_long_thinkpad_t14_amd_gen_3_review/).
This model has "AMD Ryzen 7 PRO 6850U with Radeon Graphics × 8" processor and "Advanced Micro Devices, Inc. [AMD/ATI] Rembrandt" graphics card.
It's running Linux Mint 21.3 Cinnamon.
I'd call this a pretty boring Linux setup, not cutting-edge, and not chosen with spike sorting in mind.

Nevertheless, I was able to follow the basic instructions and do some sorting with Kilosort 4.

We're not aiming to do spike sorting on Thinkpads, but we probably do need to develop and test things on laptops, and I see this as an encouraging data point.

## CPU mode

The default installation will put Pytorch and Kilosort into CPU-only mode.
This was slow to run, but it did run.

The installation instructions are based on popular package managers [Anaconda](https://www.anaconda.com/download) and [pip](https://pypi.org/project/pip/).
I installed Anaconda and ran the following:

```
conda create --name kilosort python=3.10
conda activate kilosort
python -m pip install kilosort
```

I got no errors so I went on to set up for testing.

```
conda activate kilosort
pip install pytest

git clone https://github.com/MouseLand/Kilosort.git
cd Kilosort
pip install -e .
```

This installs Kilosort from the git repo instead of the public `pip` repo called PyPi.

With that I was able to run the Kilosort unit and end-to-end tests.

```
pytest --runslow
```

These all paseed.
In CPU mode on the T14 the tests took about 15 minutes.
This was almost entirely spent in the full, end-to-end test, which is fair enough.

This was very encouraging!
If we get into pipeline automation and remote server deployments, we'll have a way to test our installation and confugration up front, instead of stumbling over errors later and weeding through comments and replies later, when we're trying to do actual work.

The end-to-end test downloaded some [sample Neuropixels](https://www.kilosort.org/downloads/ZFM-02370_mini.imec0.ap.short.zip) data and [expcted results](https://www.kilosort.org/downloads/pytest.zip).
I found they were placed in a default folder at `~/.kilosort` along with some downloaded probe definitions:
 - input binary: `~/.kilosort/.test_data/ZFM-02370_mini.imec0.ap.short.bin`
 - output Phy: `~/.kilosort/.test_data/saved_results`
 - probe definitions: `~/.kilosort/probes`

These proved useful to have on hand later.

## GPU mode

The main installation instructions assume an NVIDIA GPU and the corresponding [CUDA](https://developer.nvidia.com/cuda-toolkit) libraries.
In Kilosort 3, NVIDIA and CUDA were mandatory.
We successfully worked through these dependencies for our [neuropixels-machine-setup](../neuropixels-machine-setup/).

Kilosort 4 is based on Pytorch, which abstracts Kilosort from some of the underlying details.
Pytorch itself supports other hardware and libraries in addition to NVIDIA and CUDA.
In particular, Pytorch now supports the AMD competetor for CUDA, called [ROCm](https://en.wikipedia.org/wiki/ROCm).

I was able to install the ROCm libs on my Thinkpad and, with some debugging, run Kilosort 4 on the same data set as the tests above with a significant GPU performance boost.
It's not clear we'll ever need to work with an AMD / ROCm system for production runs in the lab.
But stepping back slightly, it's very encouraging that the sorter can succeed with different backend configurations!

Here are some details of what it took to set up Pytorch and Kilosort with the AMD GPU.

I installed [ROCm](https://rocm.docs.amd.com/projects/install-on-linux/en/latest/tutorial/quick-start.html) itself.

```
sudo apt update
sudo apt install wget
sudo apt install "linux-headers-$(uname -r)" "linux-modules-extra-$(uname -r)"
sudo usermod -a -G render,video $LOGNAME
wget https://repo.radeon.com/amdgpu-install/6.1.2/ubuntu/jammy/amdgpu-install_6.1.60102-1_all.deb
sudo apt install ./amdgpu-install_6.1.60102-1_all.deb
# N: Download is performed unsandboxed as root as file '/home/ninjaben/Kilosort/amdgpu-install_6.1.60102-1_all.deb' couldn't be accessed by user '_apt'. - pkgAcquire::Run (13: Permission denied)
# This might be a nothing warning, since I'm using a manually downloaded .deb
# eg https://docs.docker.com/desktop/install/ubuntu/#install-docker-desktop
sudo apt update
sudo apt install amdgpu-dkms rocm
```

I ran the recommended [post-install steps](https://rocm.docs.amd.com/projects/install-on-linux/en/latest/how-to/native-install/post-install.html).

```
sudo tee --append /etc/ld.so.conf.d/rocm.conf <<EOF
/opt/rocm/lib
/opt/rocm/lib64
EOF
sudo ldconfig

vim ~/.bashrc
# add at end: export PATH=$PATH:/opt/rocm-6.1.2/bin

dkms status
# amdgpu/6.7.0-1781449.22.04, 5.15.0-112-generic, amd64: installed

# REBOOT

/opt/rocm-6.1.2/bin/rocminfo
# lots of GPU info

/opt/rocm-6.1.2/bin/clinfo
# lots of info

sudo apt list --installed | grep -i rocm
# lots of "rocm" dependencies installed
```

The [rocminfo](./rocminfo.txt) and [clinfo](./clinfo.txt) returned lots of GPU and other info, which I took to mean success.

I used a Pytorch [getting-started widget](https://pytorch.org/get-started/locally/) to figure out how to install Pytorch with AMD and ROCm support, using `pip`.
It told me to use:

```
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0
```

I followed the main [Kilosort instructions](https://github.com/MouseLand/Kilosort?tab=readme-ov-file#instructions) to uninstall the default, CPU-only Pytorch and install a ROCm version, instead.  As recommended, I omitted the `torchvision` and `torchaudio` components that Kilosort doesn't use.

```
conda activate kilosort
pip uninstall torch
pip3 install torch --index-url https://download.pytorch.org/whl/rocm6.0
```

With this in place, I was able to re-run the Kilosort tests, as above.

```
pytest --runslow
```

This passed, but initially it still took about 15 minutes.
It turned out to be in a CPU-only fallback mode and enabling GPU spport took a bit more debugging, below.

# Test Script and GPU support.

I wrote a test script to invoke Kilosort directly, instead of using `pytest` as above: [test_kilosort.py](./test_kilosort.py).
This gives us more control over config and debugging.
It was not hard to put this script together, following the Kilosort [basic_example](https://kilosort.readthedocs.io/en/latest/tutorials/basic_example.html
).
The existence of this example is another encouraging aspect of Kilosort 4 as a leveled-up software project.

We can use `torch.cuda.is_available()` to check whether Pytorch thinks CUDA is available (ROCm counts as CUDA in this case), and then try to do GPU-accelerated sorting.
This didn't work right away, so I'll summarize some debugging and workarounds.

I encountered an instance of [RuntimeError: HIP error: invalid device function](https://github.com/ROCm/ROCm/issues/2536).
Following the linked advice and some trial an error, I made progress by setting the environment variable `HSA_OVERRIDE_GFX_VERSION=10.3.0`.
From the output of [rocminfo](./rocminfo.txt) think my actual gfx version is 10.3.5.
It's not clear why the installed ROCm libs would fail to work with this minor verison difference.
It might just point to relative immaturity of the ROCm project.
But the `HSA_OVERRIDE` workaround seemed to work.

After this, Kilosort could begin to sort, then quickly run out of memory.
This is fair enough, Kilosort clearly asks for 8GB of GPU RAM in its [system requirements](https://github.com/MouseLand/Kilosort?tab=readme-ov-file#system-requirements).
According to the output of [rocminfo](./rocminfo.txt), my Thinkpad T14 has only 1GB.

However, I was also able to work around this constraint.
[General advice](https://stackoverflow.com/questions/59129812/how-to-avoid-cuda-out-of-memory-in-pytorch) seems to be that decreasing the batch size of jobs sent to the GPU can be a way to conserve GPU RAM.
And Kilosort has a [batch_size](https://github.com/MouseLand/Kilosort/blob/main/kilosort/parameters.py#L42) setting that we can adjust.
The default `batch_size` is 60000, corresponding to 2 seconds or Neuropixels data.
Through trial and error, I found `batch_size` of 5000 allowed the sorting to complete within 1GB of GPU RAM.

With GPU acceleration, the same sorting of test data took 5 minutes instead of 15.
This is a significant improvement!

It's very encouraging that I was able to run through all of this locally, on modest and hardware that's not officially supported.
Kilosort had enough configuration flexibility to run in the constrained environment, and didn't just fall over.

The choice to use Pytorch as a backend means that *Pytorch*, not Kilosort, was able to add support for my AMD hardware.
Because Kilosort now makes a separation of concerns between the spike sorting domain code, vs the Pytorch backend, Kilosort was able to benefit from progress in Pytorch, for free.

In contrast, imagine submitting an "AMD ROCm support" feature request to the Kilosort 3 project.
This would have been been a non-starter.

# Docker

We've been using Docker to capture processing step dependencies.
I looked at the Docker situation for Kilosort 4.
SpikeInterface has been working in this space already, for [multiple sorters](https://hub.docker.com/u/spikeinterface), and they have a good [Kilosort 4 Docker image](https://hub.docker.com/r/spikeinterface/kilosort4-base).

Their [Dockerfile](https://github.com/SpikeInterface/spikeinterface-dockerfiles/blob/main/kilosort4/Dockerfile
) is much like the main installation instructions:
 - start with an NVIDIA / CUDA base image
 - install anaconda
 - install pytorch (in this case using CUDA for GPU support) with pip
 - install kilosort with pip

Using this base image along with [test_kilosort_docker.sh](./test_kilosort_docker.sh), I was able to run the same sorting as above, but inside the SpikeInterface Kilosort 4 container instead of using my local install.
This ran in CPU-only fallback mode because the SpikeInterface image is build for NVIDIA and CUDA library support.
But it did run!

We could probably use this SpikeInterface Kilosort 4 image for our pipelines, when we're in an NVIDIA / CUDA environment, like the [Neuropixels machine](../neuropixels-machine-setup/).
More on that, below.

## ROCm with Docker?
If it ever came up, we could probably make a Kilosort Docker image similar to the SpikeInterface image above.
There's an offical [ROCm Pytorch](https://hub.docker.com/r/rocm/pytorch) image we could start from, then install anaconda and kilosort.

At runtime, Docker supports NVIDIA and CUDA automatically via the `docker --gpus` option.
It looks like runtime support for AMD and ROCm would look different, but is at least [documented](https://rocm.docs.amd.com/projects/install-on-linux/en/latest/how-to/docker.html).
This is encouraging, though I havent tried it.

# Lab Pipelines

We could probably use the SpikeInterface Kilosort 4 Docker image in our lab pipelines.
The inputs (binary recording file, probe definitoin, and dictionary of sorting params) and outputs (directory of numpy files for Phy) are just about the same.
The sorting params would probably differ, by design, for Kilosort 3 vs 4.
But the format of these could probably continue to be a JSON file or similar.

We could try to use the image as-is.
This might become unwieldy, with a long, ugly, inscrutable shell command to pass as the step container's command to run.
This is because the image doesn't come with a convenient entry-point script -- something like [test_kilosort.py](./test_kilosort.py) that can choose default optoins, check configuration, wrangle file paths, print progress messages, etc.

We could write a convenient entry-point script and add this to the container, perhaps at runtime, or perhaps with a new container image that uses the SpikeInterface image as its base.

This seems like the shortest path to getting Kilosort 4 into lab pipelines.

## Spike Interface

Possibly we could think bigger and use more of what Spike Interface has to offer.
If this worked out, we'd potentially be able to swap out different sorters at runtime, instead of building pipelines with one sorter in mind.
I'll write out some (rambling) thoughts on this.
I think we could probably achieve this as a somewhat larger effort.

### entry point and installing SpikeInterface in containers

I mentioned that the SpikeInterface Kilosort4 image doesn't have a convenient entry-point script.
The reason for this is that SpikeInterface *installs SpikeInterface into the sorting container at runtime*.
From there it can construct a command for the container to run that's based on various SpikeInterface utilities.
To me, this is a weird thing to do!

If the SpikeInterface utilities are required, they should be installed as part of the container image in the first place, along with other dependencies.
This way, the image could close over all the dependenices and versions involved, including the version of SpikeInterface itself.
I think this would be a saner way to think about containers as a tool, and to achieve goals like auditability and reproducibility.

But the SpikeInterface team is at least clear about this as a choice: [What version of SpikeInterface is run in the container?](https://spikeinterface.readthedocs.io/en/latest/modules/sorters.html#what-version-of-spikeinterface-is-run-in-the-container)
The idea is that SpikeInterface itself migh be a quickly evolving thing, and users might want to quickly iterate on changes to SpikeInterface without building or dowloading new sorter containers.
I still think this is a weird thing to do -- sort of a developer-y way to hack on things, twisted into a choice pushed on all users.
If we care about auditability and reproducibility, then users probably should not be hacking on SpikeInterface itself.
Just pull a new image version.
And if the only change was in the last last image layer that contains the SpikeInterface code, then the pull will be quick and small.

They've probably heard this before.
The main `run_sorter()` command takes a `docker_image` argument which would allow us to use our own, compatible Docker images instead of the default images, like the Kilosort 4 image I tried above.
So if we wanted, we could build alternatives that have a known version of SpikeInterface already installed.
This could address my concerns about auditability and reproducibility.

A side note about reproducibility: it looks like the SpikeInterface [wrapper around Kilosort 4](https://github.com/SpikeInterface/spikeinterface/blob/main/src/spikeinterface/sorters/external/kilosort4.py#L247) is setting CPU and GPU random seeds before sorting.
Is Kilosort 4 deterministic now?
I haven't checked.

A side note about passing an alternative `docker_image` to `run_sorter()`: If we found ourselves in a strange environment, say with AMD rather than NVIDIA hardware, we could potentially use `docker_image` to choose an image approproate for the hardware environment.
It's good they included this option, it could allow us to have it both ways: choose images we want, and use SpikeInterface utilities.

### what we'd do

I'll try to list out "todo" items we'd need to think through and build, if we were to rework our pipelines around SpikeInterface.

#### inputs
SpikeInterface has utils around various sorters -- it also has utils around various input data formats.
We could try to use the format utils, too.
My sense is we should treat these as separate steps, upstram of the sorter step.
This would give us the option to continue using our existing data conversion steps.
We might want to do this because eg the Plexon converter used by SpikeInterface turned out to be very slow and memory-hungy.
We had better luck with our own converter that loaded less into memory at once.

So for the sorting steps themselves, the inputs could be:
 - a binary data file, like we have now
 - a probe definition in some format supported by [ProbeInterface](https://probeinterface.readthedocs.io/en/main/format_spec.html), similar to now, maybe we'd need to make some changes
 - an optional dictionary of sorter-specific parameters in some format supported by SpikeInterface, similar to JSON we use now, maybe we'd need to make some changes

#### docker in docker

In our [proceed](https://github.com/benjamin-heasly/proceed) Pipelines, we use Docker to run each step in a container.
We might create a container image for SpikeInterface itself, which we'd invoke from our pipelines.

In turn, SpikeInterface would try to pull a spike sorter image and run a container to do the sorting.
So SpikeInterface-in-a-container would need to be able to create containers itself.

This kind of docker-in-docker workflow is possible.
A typical approach that we could use here is to let the Docker client inside the container talk to the Docker service on the host.
So there'd just be one Docker service overall.

We'd need proceed to support this for pipeline steps, and we'd need to test it.

#### outputs

Unlike Kilosort, SpikeInterface doesn't always create Phy files as output.
But it is able to [export results to Phy](https://spikeinterface.readthedocs.io/en/latest/modules/exporters.html).
We'd need to add this as a last step after sorting, perhaps as part of the SpikeInterface image we create and invoke from our pipelines.

#### environment detection and config

At some point we might need the sorting step to be smart enough to detect things like CUDA vs ROCm, and choose an appropriate, equivalent container image to use at runtime.

Likewise the same step might need to choose different docker arguments at runtime, for example `docker --gpus` vs [other](https://rocm.docs.amd.com/projects/install-on-linux/en/latest/how-to/) GPU-related arguments.
