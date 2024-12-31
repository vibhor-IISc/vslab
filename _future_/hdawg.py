import time
import os
import zhinst.utils
from vslab.rack import HDAWG_ADDRESS

(daq, device, _) = zhinst.utils.create_api_session(HDAWG_ADDRESS, 6)
zhinst.utils.api_server_version_check(daq)
#zhinst.utils.disable_everything(daq, device)

# Configure how many independent sequencers
    #   should run on the AWG and how the outputs are grouped by sequencer.
    #   0 : 4x2 with HDAWG8; 2x2 with HDAWG4.
    #   1 : 2x4 with HDAWG8; 1x4 with HDAWG4.
    #   2 : 1x8 with HDAWG8.
    # Configure the HDAWG to use one sequencer with the same waveform on all output channels.
daq.setInt(f"/{device}/system/awg/channelgrouping", 1)

awgModule = daq.awgModule()
awgModule.set("device", device)
awgModule.execute()



def compile_n_upload(awg_sourcefile):
    """
    Connect to a Zurich Instruments HDAWG, compile, and upload.
    Use run_awg() -> to enable outputs and to trigger RUN AWG
    sequence program.
    """

    # Get the LabOne user data directory (this is read-only).
    data_dir = awgModule.getString("directory")
    # The AWG Tab in the LabOne UI also uses this directory for AWG seqc files.
    src_dir = os.path.join(data_dir, "awg", "src")
    if not os.path.isdir(src_dir):
        # The data directory is created by the AWG module and should always exist. If this exception is raised,
        # something might be wrong with the file system.

        # IN FUTURE ADD SEQC flder within scripts
        raise Exception(f"AWG module wave directory {src_dir} does not exist or is not a directory")

    
    else:
        if not os.path.exists(os.path.join(src_dir, awg_sourcefile)):
            raise Exception(
                f"The file {awg_sourcefile} does not exist, this must be specified via an absolute or relative path."
            )

    # print("Will compile and load", awg_sourcefile, "from", src_dir)

    # Transfer the AWG sequence program. Compilation starts automatically.
    awgModule.set("compiler/sourcefile", awg_sourcefile)
    # Note: when using an AWG program from a source file (and only then), the compiler needs to
    # be started explicitly:
    awgModule.set("compiler/start", 1)
    timeout = 20
    t0 = time.time()
    while awgModule.getInt("compiler/status") == -1:
        time.sleep(0.1)
        if time.time() - t0 > timeout:
            Exception("Timeout")

    if awgModule.getInt("compiler/status") == 1:
        # compilation failed, raise an exception
        raise Exception(awgModule.getString("compiler/statusstring"))
    if awgModule.getInt("compiler/status") == 0:
        pass
        # print("Compilation successful with no warnings, will upload the program to the instrument.")
    if awgModule.getInt("compiler/status") == 2:
        print("Compilation successful with warnings, will upload the program to the instrument.")
        print("Compiler warning: ", awgModule.getString("compiler/statusstring"))

    # Wait for the waveform upload to finish
    time.sleep(0.2)
    i = 0
    while (awgModule.getDouble("progress") < 1.0) and (awgModule.getInt("elf/status") != 1):
        # print(f"{i} progress: {awgModule.getDouble('progress'):.2f}")
        time.sleep(0.5)
        i += 1
    # print(f"{i} progress: {awgModule.getDouble('progress'):.2f}")
    if awgModule.getInt("elf/status") == 0:
        pass
        # print("Upload to the instrument successful. Use run_awg()  to run_single and enable")
    if awgModule.getInt("elf/status") == 1:
        raise Exception("Upload to the instrument failed.")
    else:
        pass



def run_awg():
    '''
    This is the preferred method of using the AWG: 
    Run in single mode continuous waveform playback 
    is best achieved by using an infinite loop 
    (e.g., while (true)) in the sequencer program.
    '''
    daq.setInt(f"/{HDAWG_ADDRESS}/awgs/0/single", 1)
    daq.setInt(f"/{HDAWG_ADDRESS}/awgs/0/enable", 1)
    pass


def awg_safety_check():
    pass
