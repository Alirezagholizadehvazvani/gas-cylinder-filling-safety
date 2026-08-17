import unittest

from prototype import SafetySystem, State, EMERGENCY_PRESSURE
from fault_injection import run_all_scenarios


class SafetySystemTests(unittest.TestCase):

    def running_system(self):
        system = SafetySystem()
        system.power_on()
        system.start()
        return system

    def test_startup_reaches_ready(self):
        system = SafetySystem()
        system.power_on()
        self.assertEqual(system.state, State.READY)
        self.assertTrue(system.valve.physically_closed)

    def test_sensor_disconnect_locks(self):
        system = self.running_system()
        system.sensor.connected = False
        system.update()
        self.assertEqual(system.state, State.LOCK)
        self.assertTrue(system.valve.physically_closed)

    def test_sensor_out_of_range_locks(self):
        system = self.running_system()
        system.sensor.pressure = 250
        system.update()
        self.assertEqual(system.state, State.LOCK)
        self.assertTrue(system.valve.physically_closed)

    def test_frozen_sensor_is_detected(self):
        system = self.running_system()
        system.sensor.pressure = 40
        system.update()
        system.sensor.frozen = True
        system.sensor.pressure = 130
        system.update()
        system.update()
        self.assertEqual(system.state, State.LOCK)
        self.assertTrue(system.valve.physically_closed)

    def test_emergency_stop_locks_and_closes(self):
        system = self.running_system()
        system.e_stop = True
        system.update()
        self.assertEqual(system.state, State.LOCK)
        self.assertTrue(system.valve.physically_closed)

    def test_power_failure_locks_and_closes(self):
        system = self.running_system()
        system.power_available = False
        system.update()
        self.assertEqual(system.state, State.LOCK)
        self.assertTrue(system.valve.physically_closed)

    def test_watchdog_failure_locks_and_closes(self):
        system = self.running_system()
        system.watchdog_expired = True
        system.update()
        self.assertEqual(system.state, State.LOCK)
        self.assertTrue(system.valve.physically_closed)

    def test_overpressure_locks_and_closes(self):
        system = self.running_system()
        system.sensor.pressure = EMERGENCY_PRESSURE
        system.update()
        self.assertEqual(system.state, State.LOCK)
        self.assertTrue(system.valve.physically_closed)

    def test_valve_fail_to_close_is_exposed(self):
        system = self.running_system()
        system.valve.fail_to_close = True
        system.e_stop = True
        system.update()
        self.assertEqual(system.state, State.LOCK)
        self.assertFalse(system.valve.physically_closed)
        self.assertIn("Valve failed", "\n".join(system.events))

    def test_valve_feedback_failure_is_exposed(self):
        system = self.running_system()
        system.valve.feedback_failure = True
        system.e_stop = True
        system.update()
        self.assertEqual(system.state, State.LOCK)
        self.assertFalse(system.valve.physically_closed)

    def test_fault_injection_engine_has_nine_scenarios(self):
        results = run_all_scenarios()
        self.assertEqual(len(results), 9)
        self.assertEqual([r.id for r in results], list(range(1, 10)))


if __name__ == "__main__":
    unittest.main()
