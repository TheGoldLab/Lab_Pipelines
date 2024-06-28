from pathlib import Path

import torch

from kilosort.utils import download_probes
from kilosort.io import load_probe
from kilosort import run_kilosort

# Only needs to run once.
download_probes()

# What does torch think of our ROCm installation?
if torch.cuda.is_available():
    print("We think CUDA or ROCm is available.")
    # Although torch.cuda.is_available() was True, the cuda device fails
    #   RuntimeError: HIP error: invalid device function
    #   HIP kernel errors might be asynchronously reported at some other API call, so the stacktrace below might be incorrect.
    #   For debugging consider passing AMD_SERIALIZE_KERNEL=3.
    #   Compile with `TORCH_USE_HIP_DSA` to enable device-side assertions.
    #
    # This seemed to help
    #   HSA_OVERRIDE_GFX_VERSION=10.3.0 python test_kilosort.py
    device = torch.device('cuda')

    # Reduced batch size from 60000 to 5000 to accomodate wimpy notebook GPU with only 1GB memory.
    # But it ran, and 3x faster than CPU mode!
    settings = {
        'n_chan_bin': 385,
        'batch_size': 5000
    }
else:
    print("We think only CPU is available.")
    device = torch.device('cpu')
    settings = {
        'n_chan_bin': 385
    }
print(f"device {device}")
print(f"settings {settings}")

# Choose neural data to sort.
input_bin = Path('~', '.kilosort', '.test_data', 'ZFM-02370_mini.imec0.ap.short.bin').expanduser()
print(f"input bin {input_bin}")

# Configure the probe geometry.
probe_name = 'neuropixPhase3B1_kilosortChanMap.mat'
probe_path = Path('~', '.kilosort', 'probes', probe_name).expanduser()
print(f"probe_path {probe_path}")

probe = load_probe(probe_path)
print(f"probe {probe}")

# Sort.
results_dir = Path("~", '.kilosort', "results").expanduser()
print(f"results_dir {results_dir}")
results = run_kilosort(
    device=device,
    settings=settings,
    filename=input_bin,
    probe=probe,
    results_dir=results_dir
)
print(f"results? {len(results)}")
