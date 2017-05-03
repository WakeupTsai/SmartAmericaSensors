from scale_client.sensors.virtual_sensor import VirtualSensor

import pyaudio
import wave
import sys
import os
from ctypes import *
import subprocess
from time import gmtime, strftime

import logging
log = logging.getLogger(__name__)

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 512
RECORD_SECONDS = 9
DEVICE = 2

class MicrophoneVirtualSensor(VirtualSensor):
	# interval = period(second)
	def __init__(self, broker, device=None, interval=60, threshold=None, search_interval=60):
		super(MicrophoneVirtualSensor, self).__init__(broker, device, interval=interval)
		self._search_interval = search_interval

		self._devs = None
		self._dev_timer = None

	DEFAULT_PRIORITY = 5


	def get_type(self):
		return "microphone"


	def on_start(self):
		if self._wait_period is None:
			return
		if self._get_devices():
			self._do_sensor_read()
			self.timed_call(self._wait_period, MicrophoneVirtualSensor._do_sensor_read, repeat=True)
		else:
			return

	def _get_devices(self):

		#Hide messages from PortAudio on stdout/stderr
		# devnull = os.open(os.devnull, os.O_WRONLY)
		# old_stderr = os.dup(2)
		# sys.stderr.flush()
		# os.dup2(devnull, 2)
		# os.close(devnull)

		self._devs = pyaudio.PyAudio()
		info = self._devs.get_host_api_info_by_index(0)
		numdevices = info.get('deviceCount')

		if numdevices >= 1 :
			for i in range(0, numdevices):
				#get the correct microphone device id
				#Input Device id  2  -  USB PnP Sound Device: Audio (hw:1,0)
				#Input Device id  5  -  default
				if (self._devs.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
					print "Input Device id ", i, " - ", self._devs.get_device_info_by_host_api_device_index(0, i).get('name')
					self.dev = i
					break
		return numdevices



	def read_raw(self, dev=None):

		if dev is None:
			raise NotImplementedError

		currenTime = strftime("%Y%m%d-%H%M%S", gmtime())


		stream = self._devs.open(format=FORMAT, channels=CHANNELS,
						rate=RATE, input=True,
						frames_per_buffer=CHUNK,
						input_device_index=dev)

		frames = []
		#print "recording ..."
		for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
			try:
				data = stream.read(CHUNK)
				frames.append(data)
			except IOError as ex:
				if ex[1] != pyaudio.paInputOverflowed:
					raise
				data = '\x00' * CHUNK
		#print "finished recording"


		# stop Recording
		stream.stop_stream()

		waveFile = wave.open("media/audios/"+currenTime+".wav", 'wb')
		waveFile.setnchannels(CHANNELS)
		waveFile.setsampwidth(self._devs.get_sample_size(FORMAT))
		waveFile.setframerate(RATE)
		waveFile.writeframes(b''.join(frames))
		waveFile.close()

		stream.close()
		#self._devs.terminate()

		return currenTime + ".wav"

	def read(self, dev=None):
		raw = self.read_raw(dev)
		event = self.make_event_with_raw_data(raw)
		return event

	def _do_sensor_read(self):

		log.debug("%s record audio..." % self.get_type())
		event = self.read(self.dev)
		if event is None:
			print "Failed to record the audio."
		self.publish(event)
