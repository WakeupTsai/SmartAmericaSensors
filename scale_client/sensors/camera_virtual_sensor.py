from scale_client.sensors.virtual_sensor import VirtualSensor

import picamera
import subprocess
import os
from time import gmtime, strftime

import logging
log = logging.getLogger(__name__)


class CameraVirtualSensor(VirtualSensor):
	# interval = period(second)
	def __init__(self, broker, device=None, interval=20, threshold=None, search_interval=60):
		super(CameraVirtualSensor, self).__init__(broker, device, interval=interval)
		self._search_interval = search_interval

		self._devs = None
		self._dev_timer = None

	DEFAULT_PRIORITY = 5

	def get_type(self):
		return "camera"

	def on_start(self):
		# _wait_period = interval
		if self._wait_period is None:
			return
		if self._get_devices():
			self._do_sensor_read()
			self.timed_call(self._wait_period, CameraVirtualSensor._do_sensor_read, repeat=True)
		else:
			return

	def _get_devices(self):
		camera_detect = int( subprocess.check_output(["vcgencmd","get_camera"]).strip()[-1] )
		if camera_detect:
			self.dev = picamera.PiCamera()
			log.info("found camera device")

		return camera_detect

	def read_raw(self, dev=None):
		if dev is None:
			raise NotImplementedError
		currenTime = strftime("%Y%m%d-%H%M%S", gmtime())
		dev.capture("media/images/" + currenTime + ".jpg")
		# self._size = os.path.getsize("media/images/" + currenTime + ".jpg")
		return currenTime + ".jpg"

	def read(self, dev=None):
		raw = self.read_raw(dev)
		event = self.make_event_with_raw_data(raw)
		# event.data['file_size'] = self._size
		return event

	def _do_sensor_read(self):

		log.debug("%s capture image..." % self.get_type())
		event = self.read(self.dev)
		if event is None:
			print "Failed to capture the image."
		self.publish(event)
