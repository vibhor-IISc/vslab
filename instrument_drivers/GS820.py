from qcodes.instrument_drivers.yokogawa.Yokogawa_GS200 import YokogawaGS200
from qcodes.instrument_drivers.yokogawa.Yokogawa_GS200 import ModeType


from functools import partial


class GS820(YokogawaGS200):
    """
    This is the QCoDeS driver for the Yokogawa GS820 dual-channel voltage and current source.
    
    Args:
        name: What this instrument is called locally.
        address: The GPIB or USB address of this instrument
        kwargs: kwargs to be passed to the VisaInstrument class
    """

    def __init__(self, name: str, address: str, **kwargs):
        super().__init__(name, address, **kwargs)
        
        # Update channel-specific methods
        self.voltage_range.set_cmd = partial(self._set_range_channel, "VOLT", "CH1:")
        self.current_range.set_cmd = partial(self._set_range_channel, "CURR", "CH1:")
        self.voltage.set_cmd = partial(self._get_set_output_channel, "VOLT", "CH1:")
        self.current.set_cmd = partial(self._get_set_output_channel, "CURR", "CH1:")

    def _set_range_channel(self, mode: ModeType, output_range: float, channel: str) -> None:
        """
        Set the range for a given channel.
        """
        self._assert_mode(mode)
        output_range = float(output_range)
        self.write(f"{channel}:SOUR:RANG {output_range}")

    def _get_set_output_channel(self, mode: ModeType, output_level: float | None = None, channel: str = "CH1:") -> float | None:
        """
        Get or set the output level for a given channel.
        """
        self._assert_mode(mode)
        if output_level is not None:
            self.write(f"{channel}:SOUR:LEV {output_level:.5e}")
            return None
        return float(self.ask(f"{channel}:SOUR:LEV?"))
    
    def on(self) -> None:
        """Turn output on for both channels"""
        self.write("CH1:OUTPUT 1")
        self.write("CH2:OUTPUT 1")
        self.measure._output = True

    def off(self) -> None:
        """Turn output off for both channels"""
        self.write("CH1:OUTPUT 0")
        self.write("CH2:OUTPUT 0")
        self.measure._output = False

    def state(self) -> int:
        """Check state of both channels"""
        state_ch1 = int(self.ask("CH1:OUTPUT?"))
        state_ch2 = int(self.ask("CH2:OUTPUT?"))
        self.measure._output = bool(state_ch1 or state_ch2)
        return state_ch1, state_ch2
