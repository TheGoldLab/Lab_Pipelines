# This Python script can help us dig in to raw event data coming from Open Ephys.
# It'll read an Open Ephys session and print out a line of delimited text for each TTL event and each text event.
# We can dump all these lines into a file and import it into Google Sheets for sharing and exploration.
#
# Here's how I've been using this script (Ben H, June 2024).
#
# Download a data session from Penn Box to the local machine
# Edit edit "directory" below to point to the session.
#
# Run this script with Python and dump the printed output to a file.
#
#   cd Lab_Pipelines/experiments/aodr/python
#   conda activate gold_pipelines
#   python open_ephys_event_dump.py > events.csv
#
# Make a new Google Sheet.
# Import events.csv:
#   - replace the current sheet
#   - custom delimiter "&" (ampersand "&" avoids conflicts with commas "," and pipes "|" within the event data)
#
# Some formatting:
#   - bold the header row
#   - select columns A-E and auto resize to fit column width
#
# Sort by Open Ephys timestamp, break ties by event index:
#   - select columns A-E
#   - sort range with advanced sorting options
#   - check data has header row
#   - sort by timestamp, then by stream name, then by stream index
#
# Select column E and apply some conditional formatting to highlight trials:
#   - text contains "4904" have blue background
#   - text contains "8072" have green background
#   - text contains "8049" have green background
#   - text contains "8050" have green background
#   - text contains "name=2" have orange background
#   - text contains "name=3" have yellow background
#   - text is exactly "1=1" have magenta background
#   - text contains "UDP Events sync" have purple background
#
# Estimate the FIRA trial index that each event would go to.
#   - cell F1 add header: "approx FIRA index"
#   - cell F2 add number: 1
#   - cell F3 add formula: =F2+and(A3="TTL Rhythm Data", E3="1=1")
#   - fill down column F with this formula
#
# Select column F and apply some conditional formatting to distinguish trials:
#   - custom formula is: =isodd(F1) have gray background

from open_ephys.analysis import Session

# Edit this to be your local path to a data session.
directory = '/Users/benjaminheasly/open-ephys/from_lowell/Anubis_2024-06-20_12-48-42'
session = Session(directory)

# Lower this limit if CSV size is unmanageable.
end_time = 1e6

# Print a CSV header row.
print("stream name&stream index&timestamp&sample number&data")

# Dump out TTL events.
recording = session.recordnodes[0].recordings[0]
ttl_events = recording.events
for index, row in ttl_events.iterrows():
    if row.timestamp <= end_time:
        print(f"TTL {row.stream_name}&{index}&{row.timestamp}&{row.sample_number}&{row.line}={row.state}")

# Dump out text events.
message_count = len(recording.nwb['acquisition']['messages']['data'])
for index in range(message_count):
    text = recording.nwb['acquisition']['messages']['data'][index]
    timestamp = recording.nwb['acquisition']['messages']['timestamps'][index]
    sync = recording.nwb['acquisition']['messages']['sync'][index]
    if timestamp <= end_time:
        print(f"TEXT&{index}&{timestamp}&{sync}&{text}")
