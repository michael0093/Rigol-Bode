# Michael0093 Sept 2024
import time
import datetime
import pyvisa
import math

##########################################
# Channel 1 = Vin
# Channel 3 = Vout
# Set up your instruments at the start frequency with the source output on and the scope measuring a reasonable signal
# Set the starting frequency and the multiplying incriment below. ie: 100 = 100Hz and 1.05 = 5% increase per step.
# Set the stop frequency and stop Vout, when either the frequency exceeds STOP_FREQ or the measured Vout falls below STOP_VOUT, the test terminates. 
# You can also stop manually with CtrlC (break). For my DS1000Z and 10X probe, when Vout is about 5mV or lower the measurements are too noisy and the results become wrong
START_FREQ = 100        # Start frequency: 100 = 100Hz
FREQ_MULTIPLIER = 1.05  # Step increment: 1.05 = 5% incriment per step
STEP_TIME = 0.7           # Settling time in sec. Best case is about 0.7s for my setup but if you are AC-coupled to remove DC for example this will likely need to be much larger
STOP_FREQ = 1e6         # Stop frequency: 1e6 = 1MHz. OR'd with the STOP_VOUT
STOP_VOUT = 5e-6        # Stop Vout voltage: 5e-3 = 5mV. OR'd with the STOP_FREQ
##########################################

# The user first must set the source and scope to display a full scale 
input("Configure the equipment and press enter to connect...")

# Connect and identify the VISA equipment
rm = pyvisa.ResourceManager()
print(rm.list_resources())          # List all VISA instruments and copy-paste yours into the open_resource() below
instSource = rm.open_resource('USB0::0x1AB1::0x0642::DG1ZA200500518::INSTR') 
instScope = rm.open_resource('USB0::0x1AB1::0x04CE::DS1ZA194017266::INSTR') 
print(instSource.query("*IDN?"))    # Print VISA instrument details useful for debugging
print(instScope.query("*IDN?"))

# Open file to write to, start timer
f = open(time.strftime('%Y%m%d_%H%M%S_') + "Bode.csv", "x")
print('Time,Milliseconds,Index,Freq,Vin,Vout,dB,Phase')
f.write('Time,Milliseconds,Index,Freq,Vin,Vout,dB,Phase\n')
millisbase = int(round(time.time() * 1000))
millis = 0

freqSource = START_FREQ
numTests = 0

while True:
    # Set the stimulus source frequency then wait a little for the DUT to settle and the measurement to appear on the scope
    instSource.write(':SOUR1:FREQ {}'.format(freqSource))
    timebase = (0.4 / freqSource)   # Sets the X timebase to the period of the input frequency times a factor to get multiple periods on the screen (recommend about 3 periods)
    instScope.write(':TIM:MAIN:SCAL {}'.format(timebase))   # DS1000Z will round up to nearest timebase
    time.sleep(STEP_TIME + timebase*12*10)   # Settling time, 0.6s or less can give some repeated measurements I believe due to the vertical scale adjustment speed. Long timebases require extra time, 12 H divs and then measured about 10x this. Your instruments might be faster.

    # Read the measurement from the scope
    MeasVin = float(instScope.query(':MEAS:ITEM? VRMS,CHAN1'))  # These will be automatically added to the scope display if you haven't got them already
    MeasVout = float(instScope.query(':MEAS:ITEM? VRMS,CHAN3'))
    MeasPhase = float(instScope.query(':MEAS:ITEM? RPH,CHAN3,CHAN1'))
    MeasDB = 20*math.log(MeasVout/MeasVin,10)

    # Adjust the vertical scale for the next measurement. Complex waveforms might mess this up so you might need to comment out.
    instScope.write(':CHAN1:SCAL {}'.format((MeasVin*3.2)/8))     # Theory is 2*sqrt(2) but 3 gives a little extra vertical margin if your signal is large with small DC offset. For small signals I've been using 3.5. Will be vernier scale despite the DS1000Z documentation.
    instScope.write(':CHAN3:SCAL {}'.format((MeasVout*3.2)/8))
    
    # If you have disabled auto ranging above, you may like to generate a beep when the signal might need manual intervention. The DG1000Z can give a beep on command, the DS cannot.
    # currVoutScale = float(instScope.query(':CHAN3:SCAL?'))
    # if (MeasVout*3.2)/8 > currVoutScale:
    #     instSource.write(':SYST:BEEP:IMM')

    # Get the timestamps
    millis = int(round(time.time() * 1000))
    t = datetime.datetime.now()

    # Write data to file
    print('{},{},{},{},{},{},{},{}'.format(t, millis-millisbase, numTests, freqSource, MeasVin, MeasVout, MeasDB, MeasPhase))
    f.write('{},{},{},{},{},{},{},{}\n'.format(t, millis-millisbase, numTests, freqSource, MeasVin, MeasVout, MeasDB, MeasPhase))

    # Increase the frequency ready for the next test point
    freqSource = round(freqSource * FREQ_MULTIPLIER, 2)
    numTests = numTests + 1

    if freqSource > STOP_FREQ or MeasVout < STOP_VOUT:
        break
    
instScope.close
instSource.close
f.close()