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
        self.assertIn("CLOSED confirmation timeout", "\n".join(system.events))
        self.assertIn("SAFE STATE NOT VERIFIED", "\n".join(system.events))

    def test_valve_feedback_failure_is_exposed(self):
        system = self.running_system()
        system.valve.feedback_failure = True
        system.e_stop = True
        system.update()
        self.assertEqual(system.state, State.LOCK)
        self.assertFalse(system.valve.physically_closed)
        self.assertIn("SAFE STATE NOT VERIFIED", "\n".join(system.events))

    def test_reset_rejects_pressure_still_above_warning(self):
        system = self.running_system()
        system.sensor.pressure = 125
        system.update()
        system.reset()
        self.assertEqual(system.state, State.LOCK)

    def test_reset_accepts_pressure_back_in_range(self):
        system = self.running_system()
        system.sensor.pressure = 125
        system.update()
        system.sensor.pressure = 60
        system.reset()
        self.assertEqual(system.state, State.READY)
        system.start()
        self.assertEqual(system.state, State.FILLING)

    def test_holding_estop_does_not_repeat_log_entries(self):
        system = self.running_system()
        system.e_stop = True
        for _ in range(4):
            system.update()
        activations = [e for e in system.events if "Emergency stop activated" in e]
        self.assertEqual(len(activations), 1)

    def test_overpressure_log_has_no_duplicate_locked_line(self):
        system = self.running_system()
        system.sensor.pressure = EMERGENCY_PRESSURE
        system.update()
        locked_lines = [e for e in system.events if e.strip().endswith("System LOCKED")]
        self.assertEqual(len(locked_lines), 0)

    def test_valve_mismatch_during_filling_is_detected(self):
        system = self.running_system()
        system.valve.open_feedback = False
        system.valve.closed_feedback = True
        system.sensor.pressure = 50
        system.update()
        self.assertEqual(system.state, State.LOCK)
        self.assertIn("command/feedback mismatch", "\n".join(system.events))

    def test_fault_injection_engine_has_nine_scenarios(self):
        results = run_all_scenarios()
        self.assertEqual(len(results), 9)
        self.assertEqual([r.id for r in results], list(range(1, 10)))


if __name__ == "__main__":
    unittest.main()
