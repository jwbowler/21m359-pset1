# To help you get going, this template has the main structures set up. You need
# to fill in the code according to Assignment 1.

from __future__ import division
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

        # generate sound data for all the generators
        data = [gen.generate(frame_count) for gen in self.generators]
        
        output = np.zeros(frame_count, dtype = np.float32)
        index = 0 # index through the data to figure out which generator to remove
        for (arr, continue_flag) in data:
          output = np.add(output, arr)
          if not continue_flag:
            del self.generators[index]
          else:
            index += 1
        output = output * self.gain 

        return (output.tostring(), pyaudio.paContinue)

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
    def __init__(self, pitch, duration, gain, wave_type = None):
        self.counter = 0 #keep track of how much of our note we have generated
        self.frequency = self.pitch_to_frequency(pitch) 
        self.duration = duration
        self.num_frames = self.duration_to_num_frames(duration);
        
        self.gain = gain
        #wave freq parameters
        #square wave: odd harmonics
        if (wave_type == "square"):
            sq_coeff = [1., 1./3, 1./5, 1./7, 1./9, 1./11, 1./13, 1./15]
            sq_freqs = [1., 3., 5., 7., 9., 11., 13., 1./15] #numbers are relative to the fundemental freq.
            self.waveform = zip(sq_coeff, sq_freqs)
            self.gain = self.gain * 0.5 #to compenstate for loudness relative to other waveforms

        #triangle wave: odd harmonics, but subtract every other one.
        #I used less frequencies here because they drop off quickly.
        elif (wave_type == "triangle"):
            tri_coeff = [1., -1./9, 1./25, -1./49, 1./81, -1./121]
            tri_freqs = [1., 3., 5., 7., 9., 11.]
            self.waveform = zip(tri_coeff, tri_freqs)
            self.gain = self.gain * .9 #to compenstate for loudness relative to other waveforms

        #sawtooth wave: all harmonics1
        elif (wave_type == "sawtooth"):
            saw_coeff = [1., 1./2, 1./3, 1./4, 1./5, 1./6, 1./7, 1./8, 1./9, 1./10, 1./11]
            saw_freqs = [1., 2., 3., 4., 5., 6., 7., 8., 9., 10., 11.]
            self.waveform = zip(saw_coeff, saw_freqs)
            self.gain = self.gain * 0.2 #to compenstate for loudness relative to other waveforms
        
        else:
            sine_coeff = [1.]
            sine_freqs = [1.]
            self.waveform = zip(sine_coeff, sine_freqs)

        #envelope parameters
        self.a = 0.0    #length of attack (s)
        self.n1 = 1.0   #rate of increase of signal
        self.d = self.duration - self.a   #length of decay (s)
        self.n2 = .2   #rate of decrease of signal
        self.env = self.create_envelope()
  
    #converts MIDI to frequency
    def pitch_to_frequency(self, pitch):
        return (2. ** ((pitch - 69) / 12)) * 440

    #converts duration in seconds to frames (samples)
    def duration_to_num_frames(self, duration):
        return duration * kSamplingRate

    #generates frame_count amount of the note we want
    def generate(self, frame_count):
        frames = np.arange(self.counter, self.counter + frame_count)
        output = np.zeros(frame_count, dtype=np.float32)
        for freq in self.waveform: # add all harmonics for our waveform
            output += freq[0] * self.gain * np.sin(frames * freq[1] * self.frequency * 2.0 * np.pi / kSamplingRate)
        output = self.mul_with_envelope(output, frame_count) #multiplying signal with envelope to get a decay

        self.counter += frame_count #update counter
        continue_flag = self.counter < self.num_frames #we know if we're done if we've gone through all the frames
        return (output, continue_flag);

    def create_envelope(self):
    
        # Here we use the envelope defined in figure 9.2 from lecture
        #  (at 48:00 in the video)

        # input is a numpy array that contains the frames we'd like to
        # use the envelope on.

        # Here is the full envelope generator from lecture:
        #  if (time < a):
        #       return (time/a)**(1/n1)
        #  else:
        #      return 1 - [(time-a)/d]**(1/n2)

        
        # First, we start with simple envelope with a = 0.
        #  create the array of timesteps
        env = np.divide(np.arange(self.num_frames), kSamplingRate, dtype = np.float32)
        #  generate values for the envelope
        env = 1.0 - (((env - self.a)/self.d) ** (1.0/self.n2))

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
        self.key = 60
        self.timbres = ["sine", "square", "triangle", "sawtooth"]
        self.timbre_i = 0 

    def on_key_down(self, keycode, modifiers):
        # Your code here. You can change this whole function as you wish.
        print 'key-down', keycode, modifiers

        ##### FOUR CHORD SONG! #####
        #I chord
        if keycode[1] == '1':
          gen = NoteGenerator(self.key, 1, 1., self.timbres[self.timbre_i])
          self.audio.add_generator(gen)
          gen1 = NoteGenerator(self.key + 4, 1, 1., self.timbres[self.timbre_i])
          self.audio.add_generator(gen1)
          gen2 = NoteGenerator(self.key + 7, 1, 1., self.timbres[self.timbre_i])
          self.audio.add_generator(gen2)
        #V chord
        elif keycode[1] == '2':
          gen = NoteGenerator(self.key + 7, 1, 1., self.timbres[self.timbre_i])
          self.audio.add_generator(gen)
          gen1 = NoteGenerator(self.key + 11, 1, 1., self.timbres[self.timbre_i])
          self.audio.add_generator(gen1)
          gen2 = NoteGenerator(self.key + 14, 1, 1., self.timbres[self.timbre_i])
          self.audio.add_generator(gen2)
        #vi chord
        elif keycode[1] == '3':
          gen = NoteGenerator(self.key + 9, 1, 1., self.timbres[self.timbre_i])
          self.audio.add_generator(gen)
          gen1 = NoteGenerator(self.key + 12, 1, 1., self.timbres[self.timbre_i])
          self.audio.add_generator(gen1)
          gen2 = NoteGenerator(self.key + 16, 1, 1., self.timbres[self.timbre_i])
          self.audio.add_generator(gen2)
        #IV chord
        elif keycode[1] == '4':
          gen = NoteGenerator(self.key + 5, 1, 1., self.timbres[self.timbre_i])
          self.audio.add_generator(gen)
          gen1 = NoteGenerator(self.key + 9, 1, 1., self.timbres[self.timbre_i])
          self.audio.add_generator(gen1)
          gen2 = NoteGenerator(self.key + 12, 1, 1., self.timbres[self.timbre_i])
          self.audio.add_generator(gen2)
        elif keycode[1] == '4':
          gen = NoteGenerator(72, 1, 1.)
          self.audio.add_generator(gen)


        #### RIGHT HAND PENTATONIC MELODY ####
        elif keycode[1] == 't':
          gen = NoteGenerator(self.key + 12, 1, 1., self.timbres[self.timbre_i])
          self.audio.add_generator(gen)
        elif keycode[1] == 'y':
          gen = NoteGenerator(self.key + 14, 1, 1., self.timbres[self.timbre_i])
          self.audio.add_generator(gen)
        elif keycode[1] == 'u':
          gen = NoteGenerator(self.key + 16, 1, 1., self.timbres[self.timbre_i])
          self.audio.add_generator(gen)
        elif keycode[1] == 'i':
          gen = NoteGenerator(self.key + 19, 1, 1., self.timbres[self.timbre_i])
          self.audio.add_generator(gen)
        elif keycode[1] == 'o':
          gen = NoteGenerator(self.key + 21, 1, 1., self.timbres[self.timbre_i])
          self.audio.add_generator(gen)
        elif keycode[1] == 'p':
          gen = NoteGenerator(self.key + 24, 1, 1., self.timbres[self.timbre_i])
          self.audio.add_generator(gen)
        
        #### SET VOLUME ####
        elif keycode[1] == 'up':
          self.audio.set_gain( self.audio.get_gain() * 1.1 )
        elif keycode[1] == 'down':
          self.audio.set_gain( self.audio.get_gain() / 1.1 )

        #### SET KEY ####
        elif keycode[1] == 'right':
          self.key += 1
        elif keycode[1] == 'left':
          self.key -= 1

        #### SET TIMBRE  ####
        elif keycode[1] == 'spacebar':
          self.timbre_i = (self.timbre_i + 1) % len(self.timbres)
          print self.timbres[self.timbre_i]
    def on_key_up(self, keycode):
       # Your code here. You can change this whole function as you wish.
       #print 'key up', keycode
        pass

run(MainWidget)
