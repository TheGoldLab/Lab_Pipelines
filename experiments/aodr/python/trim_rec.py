from pynwb import NWBHDF5IO, NWBFile, TimeSeries
from pynwb.misc import AnnotationSeries
from pynwb.ecephys import ElectricalSeries, ElectrodeGroup, Device
from datetime import datetime

input_path = "/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/dlPFC/MrM/Raw/Neuronal/SingleEL/MrM_2025-09-26_13-28-03/Record Node 107/experiment1.nwb"
output_path = "/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/dlPFC/MrM/Raw/Neuronal/SingleEL/MrM_2025-09-26-Trimmed/Record Node 107/experiment1.nwb"
cutoff_time = 5000

with NWBHDF5IO(input_path, 'r') as io:
    nwb_in = io.read()

    # Create new NWBFile, copying metadata
    nwb_out = NWBFile(
        session_description=nwb_in.session_description,
        identifier=nwb_in.identifier + "_trimmed",
        session_start_time=nwb_in.session_start_time,
        experimenter=nwb_in.experimenter,
        lab=nwb_in.lab,
        institution=nwb_in.institution,
        experiment_description=nwb_in.experiment_description,
        subject=nwb_in.subject,
    )

    # Trim and add TTL events
    ttl = nwb_in.acquisition['Acquisition Board-106.acquisition_board.TTL']
    mask = ttl.timestamps[:] >= cutoff_time
    trimmed_ttl = TimeSeries(
        name=ttl.name,
        data=ttl.data[mask],
        timestamps=ttl.timestamps[mask],
        unit=ttl.unit,
        description=ttl.description
    )
    nwb_out.add_acquisition(trimmed_ttl)

    # Trim and add messages
    messages = nwb_in.acquisition['messages']
    mask = messages.timestamps[:] >= cutoff_time
    trimmed_messages = AnnotationSeries(
        name=messages.name,
        data=messages.data[mask],
        timestamps=messages.timestamps[mask],
        description=messages.description
    )
    nwb_out.add_acquisition(trimmed_messages)

    # Trim and add continuous data
    cont = nwb_in.acquisition['Acquisition Board-106.acquisition_board']
    mask = cont.timestamps[:] >= cutoff_time
    
    channel_conversion = getattr(cont, 'channel_conversion', None)

    if 'sync' in cont.fields:
        sync_data = cont.fields['sync']
    else:
        sync_data = None

    # Copy devices first
    for dev in nwb_in.devices.values():
        new_dev = Device(name=dev.name, description=getattr(dev, 'description', ''))
        nwb_out.add_device(new_dev)

    # Copy electrode groups
    for eg in nwb_in.electrode_groups.values():
        new_eg = ElectrodeGroup(
            name=eg.name,
            description=eg.description,
            location=eg.location,
            device=nwb_out.devices[eg.device.name]
        )
        nwb_out.add_electrode_group(new_eg)
    # Add all custom columns from the original electrodes table
    default_cols = {'x', 'y', 'z', 'imp', 'location', 'filtering', 'group', 'group_name'}
    for col in nwb_in.electrodes.colnames:
        if col not in default_cols:
            nwb_out.add_electrode_column(name=col, description=nwb_in.electrodes.columns[col].description)

    # Copy electrodes
    for idx in range(len(nwb_in.electrodes)):
        electrode_kwargs = {}
        for col in nwb_in.electrodes.colnames:
            val = nwb_in.electrodes[col][idx]
            if isinstance(val, bytes):
                val = val.decode('utf-8')
            electrode_kwargs[col] = val
        # Fix group reference
        electrode_kwargs['group'] = nwb_out.electrode_groups[electrode_kwargs['group_name']]
        nwb_out.add_electrode(**electrode_kwargs)

    # Create the DynamicTableRegion for the new file
    from hdmf.common.table import DynamicTableRegion
    electrodes_region = DynamicTableRegion(
        name='electrodes',
        data=cont.electrodes.data,
        description=cont.electrodes.description,
        table=nwb_out.electrodes
    )

    trimmed_cont = ElectricalSeries(
        name=cont.name,
        data=cont.data[mask],
        timestamps=cont.timestamps[mask],
        electrodes=electrodes_region,
        description=cont.description,
    )
    trimmed_cont.channel_conversion = channel_conversion
    if sync_data is not None:
        trimmed_cont.sync = sync_data[mask]  # If sync is an array and needs trimming
    else:
        trimmed_cont.sync = None
    nwb_out.add_acquisition(trimmed_cont)

    # Save the new NWB file
    with NWBHDF5IO(output_path, 'w') as out_io:
        out_io.write(nwb_out)