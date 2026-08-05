from time import sleep

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

MONITOR_PERIOD_SECONDS = 0.25


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


def format_axis_status(axis_name: str, status: dict[str, float]) -> str:
    """
    Format the current encoder and step angles for a given axis.
    """
    return (
        f"{axis_name}: "
        f"encoder={status['encoder_degrees']:8.3f} deg mod360 "
        f"step={status['step_degrees']:10.3f} deg unwrapped"
    )


def main() -> None:
    controller = GalilController(CONTROLLER_ADDRESS)

    z_axis = None
    theta_axis = None

    try:
        controller.connect()
        print("Connected to controller")
        print(f"Microstepping resolution factor: {MICROSTEPPING_RESOLUTION_FACTOR}")
        print(
            "Step counts per revolution: "
            f"{STEPPER_STEPS_PER_REVOLUTION * MICROSTEPPING_RESOLUTION_FACTOR}"
        )
        print(f"Encoder counts per revolution: {ENCODER_COUNTS_PER_REVOLUTION}")
        print(
            "Monitoring angular values every "
            f"{MONITOR_PERIOD_SECONDS:.2f} seconds. Press Ctrl+C to stop."
        )

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

        print()

        #Zero all of the values
        z_axis.zero_encoder()
        z_axis.zero_position()
        theta_axis.zero_encoder()
        theta_axis.zero_position()

        z_axis.jog(DEFAULT_SPEED_Z_AXIS)
        theta_axis.jog(DEFAULT_SPEED_THETA_AXIS)

        while True:
            z_status = get_axis_status(z_axis)
            theta_status = get_axis_status(theta_axis)
            print(
                f"{format_axis_status('Z Axis', z_status)} | "
                f"{format_axis_status('Theta Axis', theta_status)}",
                flush=True,
            )
            sleep(MONITOR_PERIOD_SECONDS)

    except KeyboardInterrupt:
        theta_axis.stop()
        z_axis.stop()
        print("\nStopped live angle monitor")

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
