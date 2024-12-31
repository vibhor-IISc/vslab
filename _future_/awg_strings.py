import textwrap

class AWG_Strings:
  readout_pulse = textwrap.dedent(
    """\
wave wave1 = rect(6000*5, 1);
while (true) 
  {
    waitDigTrigger(1, 1);
    setTrigger(0b0010);
    // waitDemodOscPhase(4);
    playWave(wave1, wave1);
    waitWave();
    setTrigger(0b0000);
    wait(200e-6/4.4e-9);
  }
    """
    )
      
  control_pulse = textwrap.dedent(
    """\
wave wave1 = rect(6000*5, 1);
    """
    )