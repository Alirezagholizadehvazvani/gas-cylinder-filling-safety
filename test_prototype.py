import unittest
from prototype import SafetySystem, State


class SafetyTests(unittest.TestCase):
    def running_system(self):
        s = SafetySystem()
        s.power_on()
        s.start()
        return s

    def test_start_requires_ready(self):
        s = SafetySystem()
        s.start()
        self.assertNotEqual(s.state, State.FILLING)

    def test_120_bar_warning(self):
        s = self.running_system()
        s.sensor.pressure = 120
        s.update()
        self.assertEqual(s.state, State.WARNING)

    def test_125_bar_shutdown(self):
        s = self.running_system()
        s.sensor.pressure = 125
        s.update()
        self.assertEqual(s.state, State.LOCK)
        self.assertFalse(s.valve.open_feedback)

    def test_sensor_disconnect(self):
        s = self.running_system()
        s.sensor.connected = False
        s.update()
        self.assertEqual(s.state, State.LOCK)

    def test_reset_does_not_restart(self):
        s = self.running_system()
        s.sensor.pressure = 125
        s.update()
        s.reset()
        self.assertEqual(s.state, State.READY)
        self.assertFalse(s.valve.open_feedback)

    def test_estop(self):
        s = self.running_system()
        s.e_stop = True
        s.update()
        self.assertEqual(s.state, State.LOCK)

    def test_power_failure(self):
        s = self.running_system()
        s.power_available = False
        s.update()
        self.assertEqual(s.state, State.LOCK)


if __name__ == "__main__":
    unittest.main()
