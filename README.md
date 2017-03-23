# Real-Time Graphical Equalizer

The code base here is part of my project for Speech Signal Processing (EE658) course at OHSU.

Goals:

1.  Display input waveform with vertical bar scrolling along during playback.
2.  Display current log-mag spectrum and EQ-modified spectrum.
3.  Have 8 sliders to adjust the equalizer
4.  Display log-mag spectrum of filter
5.  Adjust playback of original signal to take into account modifications (firwin2)

Note:  There will need to be an independent thread that ongoingly reads a chunk from the input waveform, filters it in accordance to the current filter coefficients, and plays it (pyaudio).
 
