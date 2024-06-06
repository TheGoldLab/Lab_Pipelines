import logging

import numpy as np

from pyramid.model.model import BufferData
from pyramid.model.events import TextEventList
from pyramid.neutral_zone.transformers.transformers import Transformer


class UDPEventParser(Transformer):
    """Parse timestamp info that our Open Ephys UDPEvents plugin appended to text messsages.

    The UDPEvents plugin is how we're enriching a small number of physical TTL lines with extra TTL and text events:

    https://github.com/benjamin-heasly/UDPEvents

    UDPEvents receives sync and text messages via UDP, then writes text messages like these
    with @timestamp and =sample_number appended to the text message bodies:

        - UDP Events sync on line 4@0.251607=79808
        - name=matlab,value=rSet('dXtarget',[4],'visible',1.00);draw_flag=1;,type=string@842.356=4212348
        - name=4930,type=unsigned long@842.369=4212738

    This parses out the @timestamps and updates each event's timestamp with the parsed value.
    """

    def __init__(
        self,
        timestamp_delimiter: str = "@",
        sample_number_delimiter: str = "=",
        **kwargs
    ) -> None:
        self.timestamp_delimiter = timestamp_delimiter
        self.sample_number_delimiter = sample_number_delimiter
        return None

    def parse_events(self, events: TextEventList) -> TextEventList:
        # Parse incoming events to choose a new timestamp and text messages for each.
        timestamp_data = []
        text_data = []
        for raw_timestamp, raw_text in events.each():
            # Split up raw text around delimiters, like this:
            # <raw_message>@<messge_timestamp>=<sample_number>
            (message, timing_info) = raw_text.split(self.timestamp_delimiter, maxsplit=1)
            (messge_timestamp, sample_number) = timing_info.split(self.sample_number_delimiter, maxsplit=1)

            # New events will take their timestamps from parsed input text.
            timestamp_data.append(float(messge_timestamp))

            if message.startswith("UDP Events sync"):
                # Sync events are a special case.
                # Write the original message timetamp into the new message text
                # to make it easier to pair up sync events from different readers.
                # Choose a format with key=value pairs separated by pipes |
                # This just makes it easier for downstram code to read sync events along with other events from Rex.
                text_data.append(f"name=sync|value={raw_text}|key={raw_timestamp}")
            else:
                text_data.append(message)

        # Return a new event list with the parsed timestamps and messages.
        # Using a new list lets us change the text string sizes.
        return TextEventList(np.array(timestamp_data), np.array(text_data, dtype=np.str_))

    def transform(self, data: BufferData):
        if isinstance(data, TextEventList):
            return self.parse_events(data)
        else:
            logging.warning(f"UDPEventsMessageTimes doesn't know how to apply to {data.__class__.__name__}")
        return data
