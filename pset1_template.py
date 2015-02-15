# To help you get going, this template has the main structures set up. You need
# to fill in the code according to Assignment 1.

import pyaudio
import numpy as np

import sys
sys.path.append('./common')
from core import *

kSamplingRate = 44100

class Audio:
    def __init__(self):

        self.audio = pyaudio.PyAudio()
        dev_idx = self._find_best_output()
        self.stream = self.audio.open(format = pyaudio.paFloat32,
                                    channels = 1,
                                    frames_per_buffer = 512,
                                    rate = kSamplingRate,
                                    output = True,
                                    input = False,
                                    output_device_index = dev_idx,
                                    stream_callback = self._callback)
        register_terminate_func(self.close)

        self.generators = []
        self.gain = 0.5

    def add_generator(self, gen):
        self.generators.append(gen);

    def set_gain(self, gain) :
        self.gain = gain;

    def get_gain(self) :
        return self.gain;

    def _callback(self, in_data, frame_count, time_info, status):

        data = [gen.generate(frame_count) for gen in self.generators]
        index = 0
        output = np.zeros(frame_count, dtype = np.float32)

        for (arr, continue_flag) in data:
            output = np.add(output, arr)
            if not continue_flag:
                del self.generators[index]
            else:
                index += 1
        output = output * self.gain
        return (output.tostring(), pyaudio.paContinue)

        #if len(data) > 0:
        #    return (data[0][0].tostring(), pyaudio.paContinue)
        #else:
        #    stuff = np.zeros(frame_count, dtype=np.float32)
        #    return (stuff.tostring(), pyaudio.paContinue)

        #if len(self.generators) > 0:
        #    (stuff, flag) = self.generators[0].generate(frame_count)
        #else:
        #    stuff = np.zeros(frame_count, dtype=np.float32)

        #return (stuff.tostring(), pyaudio.paContinue)


    # return the best output index if found. Otherwise, return None
    def _find_best_output(self):
        # for Windows, we want to find the ASIO host API and device
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

        cnt = self.audio.get_device_count()
        for i in range(cnt):
          dev = self.audio.get_device_info_by_index(i)
          if dev['hostApi'] == host_api_idx:
              print 'Found Device', i
              return i

        # did not find desired device.
        return None

    # shut down the audio driver. It is import to do this before python quits.
    # Otherwise, python might hang without fully shutting down.
    # core.register_terminate_func (see __init__ above) will make sure this
    # function gets called automatically before shutdown.
    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()



class NoteGenerator(object):
    def __init__(self, pitch, duration):
        self.counter = 0
        self.frequency = self.pitch_to_frequency(pitch)
        self.duration = duration
        self.num_frames = self.duration_to_num_frames(duration);
        
        #envelope parameters
        self.a = 0.0    #length of attack (s)
        self.n1 = 1.0   #rate of increase of signal
        self.d = self.duration - self.a   #length of decay (s)
        self.n2 = .1   #rate of decrease of signal
        self.env = self.create_envelope()
  
    def pitch_to_frequency(self, pitch):
        return (2 ** ((pitch - 69) / 12)) * 440

    def duration_to_num_frames(self, duration):
        return duration * kSamplingRate

    def generate(self, frame_count):
        frames = np.arange(self.counter, self.counter + frame_count)
        factor = self.frequency * 2.0 * np.pi / kSamplingRate
        output = .1 * np.sin(factor * frames, dtype = np.float32)
        output = self.mul_with_envelope(output, frame_count)

        self.counter += frame_count
        continue_flag = self.counter < self.num_frames
        return (output, continue_flag);

    def create_envelope(self):
    
        # Here we use the envelope defined in figure 9.2 from lecture
        #  (at 48:00 in the video)

        # input is a numpy array that contains the frames we'd like to
        # use the envelope on.

        # if the duration of the note is longer that the duration of 
        # the delay, we make the frames after the duration of the
        # delay 0.
      
        # Here is the full envelope generator from lecture:
        #  if (time < a):
        #       return (time/a)**(1/n1)
        #  else:
        #      return 1 - [(time-a)/d]**(1/n2)

        
        # First, we start with simple envelope with a = 0.
        #  create the array of timesteps
        env = np.divide(np.arange(self.num_frames), kSamplingRate, dtype = np.float32)
        #  generate values for the envelope
        for x in np.nditer(env, op_dtypes = ['float32'], op_flags=['readwrite']):
            x[...]  = 1.0 - (((x - self.a)/self.d) ** (1.0/self.n2))
        return env
    
    def mul_with_envelope(self, input, frame_count):
        # deal with wrap-around
        if (self.counter + frame_count > self.num_frames):
          diff = self.counter + frame_count - self.num_frames
          env = self.env[self.counter:self.counter+diff]
          env = np.append(env, np.zeros(diff, dtype=np.float32)) #set these values to zero to prevent clipping
        
        else: # get the slice of our envelope that we want
          env = self.env[self.counter:self.counter+frame_count]

        # Multiply the envelope and the input signal to get the output.
        return env * input


        


class MainWidget1(BaseWidget) :
    def __init__(self):
        super(MainWidget1, self).__init__()
        self.audio = Audio()


class MainWidget(BaseWidget) :
    def __init__(self):
        super(MainWidget, self).__init__()

        self.audio = Audio()

    def on_key_down(self, keycode, modifiers):
        # Your code here. You can change this whole function as you wish.
        print 'key-down', keycode, modifiers

        if keycode[1] == '1':
          gen = NoteGenerator(72, 1)
          self.audio.add_generator(gen)

        elif keycode[1] == 'up':
         self.audio.set_gain( self.audio.get_gain() * 1.1 )

        elif keycode[1] == 'down':
         self.audio.set_gain( self.audio.get_gain() / 1.1 )

    def on_key_up(self, keycode):
       # Your code here. You can change this whole function as you wish.
       print 'key up', keycode


run(MainWidget)
