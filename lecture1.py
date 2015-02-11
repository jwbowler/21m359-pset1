
# lecture1.py - basic sine synthesis


# Start with the most basic function: Hello World!
def main1():
   print 'Hello World!'

# set up pyAudio for streaming. import pyaudio module, create the audio interface and
# create an output stream with the basic parameters:
# channel = 1
# sample rate = 44100
# audio format is 32-bit floating point

import pyaudio

# the callback function gets called on a different thread. In order for the
# main thread not to exit, just sleep forever.

import time

def main2():
   audio = pyaudio.PyAudio()
   stream = audio.open(format = pyaudio.paFloat32,
                        channels = 1,
                        rate = 44100,
                        frames_per_buffer = 1024,
                        output_device_index = None,
                        output = True,
                        input = False,
                        stream_callback = my_callback)

   while 1:
      time.sleep(1.0)




# now, let's make some noise. Literally. In the callback, we need to return
# the number of samples requested. So for starters, let's just return some
# random values, which should sound like white-noise or static. import random
# for that.

# In order to return the values to the pyAudio in the proper format, we need
# to make sure all the values are in a packed array of 32-bit floats. 

# start with just random, then adjust range and add gain attenuation.

import random
import numpy as np

def my_callback(in_data, frame_count, time_info, status) :
   print frame_count
   values = []
   for a in range(frame_count):
      val = random.random() * 2.0 - 1.0
      val *= 0.1
      values.append( val )

   output = np.array(values, dtype=np.float32)
   return (output.tostring(), pyaudio.paContinue)


# let's make a tone out of a pure sine wave. So for that we need the sin
# function. import math sin(a) is very high frequency. Let's chop down the
# frequency by 10. ok. more in normal hearing range, but it should clicky. Why
# is that?

from math import sin

def my_sin_callback(in_data, frame_count, time_info, status) :
   print frame_count
   values = []
   for a in range(frame_count):
      val = sin(float(a * .1))   
      val *= 0.5
      values.append( val )

   output = np.array(values, dtype=np.float32)
   return (output.tostring(), pyaudio.paContinue)


# right, so we need a global sense of the frame so that the sin function gets
# a contiuous and smooth input value. Instead of using the range value which
# always starts at 0, let's use the global frame value

frame = 0
def my_smooth_sin_callback(in_data, frame_count, time_info, status) :
   global frame
   print frame_count
   values = []
   for a in range(frame_count):
      val = sin(float(frame * .1))
      val *= 0.5
      values.append( val )
      frame += 1

   output = np.array(values, dtype=np.float32)
   return (output.tostring(), pyaudio.paContinue)



# effeciency is pretty important and the current audio loop is very
# ineffecient. Luckily, we have  an awesome python lib called numpy that can
# do math / linear algebra / arrays / matricies very fast. import numpy as np
# and use np.arange() with np.sin.

def my_fast_callback(in_data, frame_count, time_info, status) :
   global frame
   print frame_count

   frames = np.arange(frame, frame + frame_count)
   output = .5 * np.sin( frames * .1, dtype = np.float32)
   frame += frame_count

   return (output.tostring(), pyaudio.paContinue)


def test_speed():
   import timeit
   print timeit.timeit("my_smooth_sin_callback(None, 1024, None, None)", 
      setup='from __main__ import my_smooth_sin_callback', number=1000)

   print timeit.timeit("my_fast_callback(None, 1024, None, None)", 
      setup='from __main__ import my_fast_callback', number=1000)

# last for this, let's get a real pitch, because we now still have some non-
# explicit value for the frequency of the sine wave. For this, we introduce
# kSamplingRate since we need it twice, so let's not hard-code it. and we need
# the pitch. Use 440 for concert A.

# in addition, we can also specify the buffer size (ie frame_count). Shorter
# buffers mean a more responsive  audio system.


kSamplingRate = 44100
freq = 440

def my_freq_callback(in_data, frame_count, time_info, status) :
   global frame, freq
   print frame_count

   frames = np.arange(frame, frame + frame_count)
   factor = (2.0 * np.pi) * freq / kSamplingRate 
   output = .5 * np.sin( factor * frames, dtype = np.float32)
   frame += frame_count

   return (output.tostring(), pyaudio.paContinue)


# for adding noise:
# import numpy.random as nprand
   # noise = 0.2 * nprand.random(frame_count)
   # output += noise



# at this point, let's break things up into different files to start creating
# some abstraction / interface layers. We'll make audio.py and introduce the
# kivy framework:

import sys
sys.path.append('./common')
from core import *
from audio_lec import *

class MainWidget(BaseWidget) :
   def __init__(self):
      super(MainWidget, self).__init__()
      
      self.audio = Audio()

   def on_key_down(self, keycode, modifiers):
      print 'key-down', keycode, modifiers
      if keycode[1] == '0':
         self.audio.set_frequency(0)

      elif keycode[1] == '1':
         self.audio.set_frequency(440)

      elif keycode[1] == '2':
         self.audio.set_frequency(660)
      
      elif keycode[1] == 'up':
         self.audio.set_gain( self.audio.get_gain() * 1.1 )

      elif keycode[1] == 'down':
         self.audio.set_gain( self.audio.get_gain() / 1.1 )

      elif keycode[1] == 'z':
         a = b

#main1()
#main2()
run(MainWidget)
