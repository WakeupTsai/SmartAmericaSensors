from scale_client.sensors.analog_virtual_sensor import AnalogVirtualSensor


class GasVirtualSensor(AnalogVirtualSensor):
    def __init__(self, broker, device=None, analog_port=None, threshold=None):
        super(GasVirtualSensor, self).__init__(broker, device=device, analog_port=analog_port)
        self._threshold = threshold

    def get_type(self):
        return "explosive_gas"

    def read(self):
        event = super(GasVirtualSensor, self).read()
        event.data['condition'] = {
                "threshold": {
                "operator": ">",
                "value": self._threshold
                }
            }
        return event

    def policy_check(self, data):
        return float(data.get_raw_data()) > self._threshold