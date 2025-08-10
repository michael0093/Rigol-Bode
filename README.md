# Rigol Bode Plotter
Python script for csv Bode plot generation using Rigol DS1000Z scope and DG1000Z siggen
Refer to the .py file header comments for setup instructions.

- Fully automated measurement and calculation of magnitude and phase
- Configurable start/stop frequency and voltage level
- Optional automatic control of scope timebase and vertical scale 
- CSV output with chart post-processing example for MS Excel and LibreOffice

## Limitations/Notes
The LibreOffice example is more recent - the MS Excel one is missing the delta-dB based calculation of the 3dB point, and it doesn't handle 180deg phase wraparound either. 