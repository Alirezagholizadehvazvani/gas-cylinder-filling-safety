"""Run a short demonstration of the safety state machine."""

from .controller import SafetySystem


def main() -> None:
    system = SafetySystem()
    system.power_on()
    system.start()

    for pressure in (20, 60, 90, 110, 119, 120, 124, 125):
        system.sensor.pressure = pressure
        system.update()

    print("Final status:")
    for key, value in system.status().items():
        print(f"  {key}: {value}")

    print("\nEvent log:")
    for line in system.events:
        print(f"  {line}")


if __name__ == "__main__":
    main()
