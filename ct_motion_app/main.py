from galil_controller import GalilController, Axis
from config import (
    CONTROLLER_ADDRESS,
    DEFAULT_SPEED_Z_AXIS,
    DEFAULT_ACCEL_Z_AXIS,
    DEFAULT_DECEL_Z_AXIS,
    DEFAULT_SPEED_THETA_AXIS,
    DEFAULT_ACCEL_THETA_AXIS,
    DEFAULT_DECEL_THETA_AXIS,
    SMALL_TEST_MOVE,
    MOTOR_TYPE_Z_AXIS,
    MOTOR_TYPE_THETA_AXIS,
)


def print_axis_status(axis: Axis, axis_name: str) -> None:
    """
    Print the current encoder and step positions for a given axis.
    """
    encoder_pos = axis.get_encoder_position()
    step_pos = axis.get_step_position()

    print(f"{axis_name} encoder position: {encoder_pos}")
    print(f"{axis_name} step position:    {step_pos}")


def main() -> None:
    controller = GalilController(CONTROLLER_ADDRESS)

    z_axis = None
    theta_axis = None

    z_move = SMALL_TEST_MOVE
    theta_move = SMALL_TEST_MOVE * 4

    try:
        controller.connect()
        print("Connected to controller")

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

        z_axis.zero_position()
        z_axis.zero_encoder()
        theta_axis.zero_position()
        theta_axis.zero_encoder()

        print("\nInitial positions:")
        print_axis_status(z_axis, "Z Axis")
        print_axis_status(theta_axis, "Theta Axis")

        print("\n--- Sequence 1: Z up, Theta forward ---")
        z_axis.move_relative(z_move, wait=True)
        theta_axis.move_relative(theta_move, wait=True)
        print_axis_status(z_axis, "Z Axis")
        print_axis_status(theta_axis, "Theta Axis")

        print("\n--- Sequence 2: Z down, Theta backward ---")
        z_axis.move_relative(-z_move, wait=True)
        theta_axis.move_relative(-theta_move, wait=True)
        print_axis_status(z_axis, "Z Axis")
        print_axis_status(theta_axis, "Theta Axis")

        print("\n--- Sequence 3: Alternating motion pattern ---")
        for i in range(3):
            print(f"\nCycle {i + 1}:")

            print("  Z positive, Theta negative")
            z_axis.move_relative(z_move, wait=True)
            theta_axis.move_relative(-theta_move, wait=True)
            print_axis_status(z_axis, "Z Axis")
            print_axis_status(theta_axis, "Theta Axis")

            print("  Z negative, Theta positive")
            z_axis.move_relative(-z_move, wait=True)
            theta_axis.move_relative(theta_move, wait=True)
            print_axis_status(z_axis, "Z Axis")
            print_axis_status(theta_axis, "Theta Axis")

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