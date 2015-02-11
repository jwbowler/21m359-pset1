# audio.py
# Basic Audio Lecture


# Let's move some code into its own module and create a class to encapsulate
# its behavior.
# The audio playback code we created should go in a class and that class
# should go in a python module (ie, a different file) global variables become
# class members (starting with self...). We have a very simple public API __init__ ,
# set_frequency, set_gain, and get_gain

import pyaudio
import numpy as np
import core
import traceback

kSamplingRate = 44100

class Audio:
   def __init__(self):
      self.audio = pyaudio.PyAudio()

      # Find the output device to use. This is most important on Windows machines
      # where we want to find a specific audio driver
      dev_idx = self._find_best_output()

      self.stream = self.audio.open(format = pyaudio.paFloat32,
                                    channels = 1,
                                    frames_per_buffer = 512,
                                    rate = kSamplingRate,
                                    output = True,
                                    input = False,
                                    output_device_index = dev_idx,
                                    stream_callback = self._callback)
      self.frame = 0
      self.frequency = 0
      self.gain = .5

      # this is important so that we close the audio stream even if the program
      # crashes. See core module.
      core.register_terminate_func(self.close)


   def close(self) :
      self.stream.stop_stream()
      self.stream.close()
      self.audio.terminate()

   def set_frequency(self, frequency) :
      print 'set_frequency', frequency
      self.frequency = frequency      

   def set_gain(self, gain) :
      self.gain = np.clip(gain, 0, 1)
      print self.gain

   def get_gain(self) :
      return self.gain

   # return the best output index if found. Otherwise, return None
   def _find_best_output(self):
      # for Windows, we want to find the ASIO host API
      # Look through the list of host APIs until we find the one we are looking for
      cnt = self.audio.get_host_api_count()
      for i in range(cnt):
         api = self.audio.get_host_api_info_by_index(i)
         if api['type'] == pyaudio.paASIO:
            host_api_idx = i
            print 'Found ASIO', host_api_idx
            break
      else:
         # did not find desired API. Bail out
         return None

      # now, find the device associated with the API we just found:
      cnt = self.audio.get_device_count()
      for i in range(cnt):
         dev = self.audio.get_device_info_by_index(i)
         if dev['hostApi'] == host_api_idx:
            print 'Found Device', i
            return i

      # did not find desired device. Sorry. Return None.
      return None

   # this callback gets called on a separate thread. Every time 
   # some audio data is needed by the audio driver, this function gets
   # called. It's job is to supply audio data as a return value.
   def _callback(self, in_data, frame_count, time_info, status) :
      try:
         frames = np.arange(self.frame, self.frame + frame_count)
         factor = self.frequency * 2.0 * np.pi / kSamplingRate 
         output = self.gain * np.sin( factor * frames, dtype = 'float32')
         self.frame += frame_count
         return (output.tostring(), pyaudio.paContinue)
      
      except:
         print 'WHOOOPS. Exception on Audio Thread'
         traceback.print_exc()
         return ('', pyaudio.paAbort)


