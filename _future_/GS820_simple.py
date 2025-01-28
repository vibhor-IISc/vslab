from enum import Enum
from typing import TYPE_CHECKING, Any, Literal


import qcodes.validators as vals
from qcodes.instrument import (
    Instrument,
    InstrumentChannel,
    VisaInstrument,
    VisaInstrumentKWArgs,
)
from qcodes.parameters import (
    ArrayParameter,
    Parameter,
    create_on_off_val_mapping,
)


class YokogawaChannel(InstrumentChannel):
    """
    Update later

    """

    def __init__(
        self,
        parent: Instrument,
        name,
        channel,
        **kwargs):
        """
        Args:
            parent: The Instrument instance to which the channel is
                to be attached.
            name: The 'colloquial' name of the channel
            channel: The name used by the Yokogawa, i.e. either
                'CH1' or 'CH2'
            **kwargs: Forwarded to base class.

        """

        if channel not in ["CHAN1", "CHAN2"]:
            raise ValueError('channel must be either "CHAN1" or "CHAN2"')

        super().__init__(parent, name, **kwargs)
        # self.model = self._parent.model



        self.mode = self.add_parameter(
            "mode",
            get_cmd=f"{channel}:SOUR:FUNC?;*WAI",
            get_parser=str.strip,
            set_cmd=f"{channel}:SOUR:FUNC {{}}",
            val_mapping={"current": "CURR", "voltage": "VOLT"},
            docstring="Selects the type of source e.g. 'voltage' or 'current' .",
        )
        """Parameter mode"""

        self.output = self.add_parameter(
            "output",
            get_cmd=f"{channel}:SOUR:OUTP?;*WAI",
            get_parser=bool,
            set_cmd=f"{channel}.source.output={{:d}}",
            val_mapping={"on": 1, "off": 0},
            docstring="Get/Set output to  ON (1)/OFF(0)",
        )
        """Parameter output"""

        self.channel = channel
             

class GS820(VisaInstrument):
    default_terminator = "\n"
    def __init__(
        self, name: str, address: str, **kwargs):
        """
        Args:
            name: Name to use internally in QCoDeS
            address: VISA ressource address
            **kwargs: kwargs are forwarded to the base class.

        """
        super().__init__(name, address, **kwargs)


        # Add the channel to the instrument
        for ch in ["CHAN1", "CHAN2"]:
            ch_name = f"{ch}"
            channel = YokogawaChannel(self, ch_name, ch_name)
            self.add_submodule(ch_name, channel)
    
        self.connect_message()



        
        
    




