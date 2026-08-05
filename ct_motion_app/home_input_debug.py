from time import sleep

from config import CONTROLLER_ADDRESS, HOME_INPUT_POLARITY
from galil_controller import Axis, GalilController


POLL_PERIOD_SECONDS = 0.25


def format_axis_inputs(axis: Axis, axis_name: str) -> str:
    return (
        f"{axis_name}: "
        f"_HM={axis.get_home_switch_state()} "
        f"_LF={axis.get_forward_limit_state()} "
        f"_LR={axis.get_reverse_limit_state()} "
        f"_TS={axis.get_switch_status()} "
        f"_SC={axis.get_stop_code()}"
    )


def main() -> None:
    controller = GalilController(CONTROLLER_ADDRESS)

    try:
        controller.connect()
        print("Connected to controller")
        print(f"Configuring home input polarity with CN ,{HOME_INPUT_POLARITY}")
        print("No motion commands will be sent.")
        print(
            "Encoder index is a short pulse, not a steady switch state; "
            "this script prints home/limit/status operands only."
        )
        print("Press Ctrl+C to stop.\n")

        controller.command(f"CN ,{HOME_INPUT_POLARITY}")
 
        z_axis = controller.axis("A")
        theta_axis = controller.axis("B")

        while True:
            print(
                f"{format_axis_inputs(z_axis, 'Z Axis')} | "
                f"{format_axis_inputs(theta_axis, 'Theta Axis')}",
                flush=True,
            )
            sleep(POLL_PERIOD_SECONDS)

    except KeyboardInterrupt:
        print("\nStopped home input debug")

    finally:
        controller.close()
        print("Disconnected")


if __name__ == "__main__":
    main()
