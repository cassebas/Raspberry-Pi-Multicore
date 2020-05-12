# Command to attach to running Raspberry Pi with a JLink debug probe
openocd -f /usr/share/openocd/scripts/interface/jlink.cfg -f rpi3.cfg

# For the pi to be able to 'listen' to the JTAG probe, the correct ALT alternate functions
# must be used. In my configuration, I'm using ALT4 which can be easily configured
# with a oneliner in the config.txt boot file:
enable_jtag_gpio=1

# An alternative way is to configure the GPIO alt functions 'online', by
# running a small program (like JtagEnabler.cpp). This is not used in my
# setup though.
