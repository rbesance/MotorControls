from galil_controller import Axis, GalilController
from config import (
    CONTROLLER_ADDRESS,
    DEFAULT_ACCEL_THETA_AXIS,
    DEFAULT_ACCEL_Z_AXIS,
    DEFAULT_DECEL_THETA_AXIS,
    DEFAULT_DECEL_Z_AXIS,
    DEFAULT_SPEED_THETA_AXIS,
    DEFAULT_SPEED_Z_AXIS,
    HOME_ACCEL_THETA_AXIS,
    HOME_ACCEL_Z_AXIS,
    HOME_BACKOFF_THETA_AXIS,
    HOME_BACKOFF_Z_AXIS,
    HOME_DECEL_THETA_AXIS,
    HOME_DECEL_Z_AXIS,
    HOME_FINE_SPEED_THETA_AXIS,
    HOME_FINE_SPEED_Z_AXIS,
    HOME_INPUT_POLARITY,
    HOME_SPEED_THETA_AXIS,
    HOME_SPEED_Z_AXIS,
    HOME_TIMEOUT_MS_THETA_AXIS,
    HOME_TIMEOUT_MS_Z_AXIS,
    MOTOR_TYPE_THETA_AXIS,
    MOTOR_TYPE_Z_AXIS,
)


def print_axis_status(axis: Axis, axis_name: str, has_physical_limits: bool) -> None:
    """
    Print useful axis state before and after homing.
    """
    print(f"{axis_name} motor type: {axis.get_motor_type()}")
    print(f"{axis_name} is stepper: {'Yes' if axis.is_stepper() else 'No'}")
    print(f"{axis_name} encoder position: {axis.get_encoder_position()}")
    print(f"{axis_name} step position: {axis.get_step_position()}")
    print(f"{axis_name} home switch state (_HM): {axis.get_home_switch_state()}")
    print(f"{axis_name} stop code (_SC): {axis.get_stop_code()}")
    print(f"{axis_name} switch status (_TS): {axis.get_switch_status()}")

    if not has_physical_limits:
        print(
            f"{axis_name} forward/reverse limit readback: "
            "reported by controller, but physical switches may not be wired"
        )

    print(f"{axis_name} forward limit state: {axis.get_forward_limit_state()}")
    print(f"{axis_name} reverse limit state: {axis.get_reverse_limit_state()}")


def main() -> None:
    controller = GalilController(CONTROLLER_ADDRESS)

    z_axis = None
    theta_axis = None

    try:
        controller.connect()
        print("Connected to controller")
        print(f"Home input polarity configured with CN ,{HOME_INPUT_POLARITY}")

        # Stop any previous motion before configuring or homing.
        controller.abort()

        # z_axis = controller.axis("A")
        theta_axis = controller.axis("B")

        # Configure normal motion profiles before enabling the motors.
        # z_axis.set_profile(
        #     speed=DEFAULT_SPEED_Z_AXIS,
        #     accel=DEFAULT_ACCEL_Z_AXIS,
        #     decel=DEFAULT_DECEL_Z_AXIS,
        #     motor_type=MOTOR_TYPE_Z_AXIS,
        # )
        theta_axis.set_profile(
            speed=DEFAULT_SPEED_THETA_AXIS,
            accel=DEFAULT_ACCEL_THETA_AXIS,
            decel=DEFAULT_DECEL_THETA_AXIS,
            motor_type=MOTOR_TYPE_THETA_AXIS,
        )

        # z_axis.enable()
        theta_axis.enable()

        print("\nBefore homing:")
        # print_axis_status(z_axis, "Z Axis", has_physical_limits=False)
        print()
        print_axis_status(theta_axis, "Theta Axis", has_physical_limits=False)

        # Home Z first. HM uses the home switch and encoder index pulse.
        # The backoff move pulls away from the switch, then the fine HM pass
        # approaches more slowly for better repeatability.
        # print("\nHoming Z Axis with HM...")
        # z_axis.home_standard(
        #     coarse_speed=HOME_SPEED_Z_AXIS,
        #     fine_speed=HOME_FINE_SPEED_Z_AXIS,
        #     accel=HOME_ACCEL_Z_AXIS,
        #     decel=HOME_DECEL_Z_AXIS,
        #     backoff_counts=HOME_BACKOFF_Z_AXIS,
        #     zero_after=True,
        #     timeout_ms=HOME_TIMEOUT_MS_Z_AXIS,
        # )
        # print("Z Axis homing complete")

        # Home Theta with HM as well. Theta has no physical forward/reverse
        # limit switches, so the home switch and index pulse are the critical
        # safety and repeatability references for this axis.
        print("\nHoming Theta Axis with HM...")
        theta_axis.home_with_backoff(
            coarse_speed=HOME_SPEED_THETA_AXIS,
            fine_speed=HOME_FINE_SPEED_THETA_AXIS,
            accel=HOME_ACCEL_THETA_AXIS,
            decel=HOME_DECEL_THETA_AXIS,
            backoff_counts=HOME_BACKOFF_THETA_AXIS,
            zero_after=True,
            timeout_ms=HOME_TIMEOUT_MS_THETA_AXIS,
        )
        print("Theta Axis homing complete")

        print("\nAfter homing:")
        # print_axis_status(z_axis, "Z Axis", has_physical_limits=True)
        # print()
        print_axis_status(theta_axis, "Theta Axis", has_physical_limits=False)

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
