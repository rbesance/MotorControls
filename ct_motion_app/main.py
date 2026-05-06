from galil_controller import GalilController, Axis
from config import (
    CONTROLLER_ADDRESS,
    DEFAULT_SPEED_Z_AXIS,
    DEFAULT_ACCEL_Z_AXIS,
    DEFAULT_DECEL_Z_AXIS,
    DEFAULT_SPEED_THETA_AXIS,
    DEFAULT_ACCEL_THETA_AXIS,
    DEFAULT_DECEL_THETA_AXIS,
    MOTOR_TYPE_Z_AXIS,
    MOTOR_TYPE_THETA_AXIS,
    MICROSTEPPING_RESOLUTION_FACTOR,
    ENCODER_COUNTS_PER_REVOLUTION,
    STEPPER_STEPS_PER_REVOLUTION,
)

TEST_REVOLUTIONS = 10


def get_axis_status(axis: Axis) -> dict[str, float]:
    """
    Read the current encoder and step positions and convert them to degrees.
    """
    encoder_pos = axis.get_encoder_position()
    step_pos = axis.get_step_position()
    step_counts_per_revolution = (
        STEPPER_STEPS_PER_REVOLUTION * MICROSTEPPING_RESOLUTION_FACTOR
    )
    encoder_degrees = Axis.counts_to_degrees(
        encoder_pos % ENCODER_COUNTS_PER_REVOLUTION,
        ENCODER_COUNTS_PER_REVOLUTION,
    )
    step_degrees = Axis.counts_to_degrees(step_pos, step_counts_per_revolution)

    return {
        "encoder_counts": encoder_pos,
        "step_counts": step_pos,
        "encoder_degrees": encoder_degrees,
        "step_degrees": step_degrees,
    }


def print_axis_status(axis_name: str, status: dict[str, float]) -> None:
    """
    Print the current encoder and step positions for a given axis.
    """
    print(f"{axis_name} encoder counts:  {status['encoder_counts']:.0f}")
    print(f"{axis_name} step counts:     {status['step_counts']:.0f}")
    print(f"{axis_name} encoder angle:   {status['encoder_degrees']:.3f} deg modulo 360")
    print(f"{axis_name} step angle:      {status['step_degrees']:.3f} deg unwrapped")


def print_axis_delta(
    axis_name: str,
    before: dict[str, float],
    after: dict[str, float],
) -> None:
    """
    Print the change in encoder and step positions for a given axis.
    """
    encoder_count_delta = (
        after["encoder_counts"] - before["encoder_counts"]
    ) % ENCODER_COUNTS_PER_REVOLUTION
    step_count_delta = after["step_counts"] - before["step_counts"]
    encoder_angle_delta = Axis.counts_to_degrees(
        encoder_count_delta,
        ENCODER_COUNTS_PER_REVOLUTION,
    )
    step_angle_delta = after["step_degrees"] - before["step_degrees"]

    print(f"{axis_name} encoder count delta: {encoder_count_delta:.0f} modulo 8000")
    print(f"{axis_name} step count delta:    {step_count_delta:.0f}")
    print(f"{axis_name} encoder angle delta: {encoder_angle_delta:.3f} deg modulo 360")
    print(f"{axis_name} step angle delta:    {step_angle_delta:.3f} deg unwrapped")


def main() -> None:
    controller = GalilController(CONTROLLER_ADDRESS)

    z_axis = None
    theta_axis = None

    step_counts_per_revolution = (
        STEPPER_STEPS_PER_REVOLUTION * MICROSTEPPING_RESOLUTION_FACTOR
    )
    test_move_counts = TEST_REVOLUTIONS * step_counts_per_revolution

    try:
        controller.connect()
        print("Connected to controller")
        print(f"Microstepping resolution factor: {MICROSTEPPING_RESOLUTION_FACTOR}")
        print(f"Step counts per revolution: {step_counts_per_revolution}")
        print(f"Encoder counts per revolution: {ENCODER_COUNTS_PER_REVOLUTION}")
        print(f"Test move: {TEST_REVOLUTIONS} revolutions ({test_move_counts} counts)")
        print(
            "Expected step angle change: "
            f"{TEST_REVOLUTIONS * 360.0:.3f} deg unwrapped"
        )
        print("Expected encoder angle change: 0.000 deg modulo 360")

        controller.abort()

        z_axis = controller.axis("A")
        theta_axis = controller.axis("B")

        z_axis.enable()
        z_axis.set_profile(
            speed=DEFAULT_SPEED_Z_AXIS,
            accel=DEFAULT_ACCEL_Z_AXIS,
            decel=DEFAULT_DECEL_Z_AXIS,
            motor_type=MOTOR_TYPE_Z_AXIS,
        )

        theta_axis.enable()
        theta_axis.set_profile(
            speed=DEFAULT_SPEED_THETA_AXIS,
            accel=DEFAULT_ACCEL_THETA_AXIS,
            decel=DEFAULT_DECEL_THETA_AXIS,
            motor_type=MOTOR_TYPE_THETA_AXIS,
        )

        print("Z Axis motor type:", z_axis.get_motor_type())
        print("Is Z Axis stepper:", "Yes" if z_axis.is_stepper() else "No")

        print("Theta Axis motor type:", theta_axis.get_motor_type())
        print("Is Theta Axis stepper:", "Yes" if theta_axis.is_stepper() else "No")

        print("\nInitial positions:")
        z_start = get_axis_status(z_axis)
        theta_start = get_axis_status(theta_axis)
        print_axis_status("Z Axis", z_start)
        print_axis_status("Theta Axis", theta_start)

        print(f"\n--- Test bench: move {TEST_REVOLUTIONS} revolutions ---")
        z_axis.move_relative(test_move_counts, wait=True)
        theta_axis.move_relative(test_move_counts, wait=True)

        print("\nFinal positions:")
        z_end = get_axis_status(z_axis)
        theta_end = get_axis_status(theta_axis)
        print_axis_status("Z Axis", z_end)
        print_axis_status("Theta Axis", theta_end)

        print("\nMeasured change:")
        print_axis_delta("Z Axis", z_start, z_end)
        print_axis_delta("Theta Axis", theta_start, theta_end)

    finally:
        try:
            controller.abort()
        except Exception:
            pass

        try:
            if z_axis is not None:
                z_axis.disable()
        except Exception:
            pass

        try:
            if theta_axis is not None:
                theta_axis.disable()
        except Exception:
            pass

        controller.close()
        print("Disconnected")


if __name__ == "__main__":
    main()
