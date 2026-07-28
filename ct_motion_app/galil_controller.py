import gclib
from config import (
    ENCODER_COUNTS_PER_REVOLUTION,
    HOME_INPUT_POLARITY,
    MICROSTEPPING_RESOLUTION_FACTOR,
    STEPPER_STEPS_PER_REVOLUTION,
)


class Axis:
    VALID_AXES = {"A", "B", "C", "D"}

    def __init__(self, controller: "GalilController", name: str):
        self.controller = controller
        self.name = self._validate_axis(name)

    def _validate_axis(self, axis: str) -> str:
        axis = axis.upper()
        if axis not in self.VALID_AXES:
            raise ValueError(f"Invalid axis '{axis}'. Must be one of {sorted(self.VALID_AXES)}.")
        return axis

    def enable(self) -> None:
        self.controller.command(f"SH{self.name}")

    def disable(self) -> None:
        self.controller.command(f"MO{self.name}")

    def set_profile(
        self,
        speed: int,
        accel: int,
        decel: int,
        motor_type: float | None = None,
    ) -> None:
        self.controller.command(f"SP{self.name}={speed}")
        self.controller.command(f"AC{self.name}={accel}")
        self.controller.command(f"DC{self.name}={decel}")
        if motor_type is not None:
            self.controller.command(f"MT{self.name}={motor_type}")

    def zero_position(self) -> None:
        self.controller.command(f"DP{self.name}=0")

    def zero_encoder(self) -> None:
        self.controller.command(f"DE{self.name}=0")

    def wait_for_motion_complete(self, timeout_ms: int | None = None) -> None:
        previous_timeout = self.controller.g.timeout
        try:
            if timeout_ms is not None:
                self.controller.g.GTimeout(timeout_ms)
            self.controller.g.GMotionComplete(self.name)
        except Exception as exc:
            self.stop()
            self.controller.abort()
            raise TimeoutError(
                f"Axis {self.name} motion did not complete within "
                f"{timeout_ms} ms"
            ) from exc
        finally:
            if timeout_ms is not None:
                self.controller.g.GTimeout(previous_timeout)

    def wait_after_motion(self, timeout_ms: int | None = None) -> None:
        previous_timeout = self.controller.g.timeout
        try:
            if timeout_ms is not None:
                self.controller.g.GTimeout(timeout_ms)
            # Match the DMC-40x0 manual homing example, which waits with AM.
            self.controller.command(f"AM {self.name}")
        except Exception as exc:
            self.stop()
            self.controller.abort()
            raise TimeoutError(
                f"Axis {self.name} did not report after-motion complete "
                f"within {timeout_ms} ms"
            ) from exc
        finally:
            if timeout_ms is not None:
                self.controller.g.GTimeout(previous_timeout)

    def get_encoder_position(self) -> int:
        return int(float(self.controller.command(f"TP{self.name}")))

    def get_step_position(self) -> int:
        return int(float(self.controller.command(f"TD{self.name}")))

    def get_encoder_position_degrees(self) -> float:
        return self.counts_to_degrees(
            self.get_encoder_position() % ENCODER_COUNTS_PER_REVOLUTION,
            ENCODER_COUNTS_PER_REVOLUTION,
        )

    def get_step_position_degrees(self) -> float:
        steps_per_revolution = (
            STEPPER_STEPS_PER_REVOLUTION * MICROSTEPPING_RESOLUTION_FACTOR
        )
        return self.counts_to_degrees(self.get_step_position(), steps_per_revolution)

    def get_position_degrees(self) -> dict[str, float]:
        return {
            "encoder_degrees": self.get_encoder_position_degrees(),
            "step_degrees": self.get_step_position_degrees(),
        }

    @staticmethod
    def counts_to_degrees(counts: int, counts_per_revolution: int) -> float:
        return counts * 360.0 / counts_per_revolution

    def get_motor_type(self) -> float:
        return float(self.controller.command(f"MG _MT{self.name}"))

    def is_stepper(self) -> bool:
        return self.get_motor_type() in {2, -2, 2.5, -2.5}

    def get_forward_limit_state(self) -> int:
        return int(float(self.controller.command(f"MG _LF{self.name}")))

    def get_reverse_limit_state(self) -> int:
        return int(float(self.controller.command(f"MG _LR{self.name}")))

    def get_home_switch_state(self) -> int:
        return int(float(self.controller.command(f"MG _HM{self.name}")))

    def get_stop_code(self) -> int:
        return int(float(self.controller.command(f"MG _SC{self.name}")))

    def get_switch_status(self) -> int:
        return int(float(self.controller.command(f"MG _TS{self.name}")))

    def home_standard(
        self,
        speed: int,
        accel: int,
        decel: int,
        zero_after: bool = True,
        timeout_ms: int | None = None,
    ) -> None:
        # HM is Galil's Standard Home routine. It depends on the home switch
        # and encoder index pulse being wired and configured correctly.
        # CN's second field configures the home input polarity. The DMC-40x0
        # manual homing example uses CN ,-1 for a normally closed switch.
        self.controller.command(f"CN ,{HOME_INPUT_POLARITY}")
        self.set_profile(speed=speed, accel=accel, decel=decel)
        self.controller.command(f"SH {self.name}")
        self.controller.command(f"HM {self.name}")
        self.controller.command(f"BG {self.name}")

        self.controller.command(f"AM {self.name}")
        # self.wait_after_motion(timeout_ms=timeout_ms)

        # if zero_after:
        #     self.zero_position()
        #     self.zero_encoder()

    def home_with_backoff(
        self,
        coarse_speed: int,
        fine_speed: int,
        accel: int,
        decel: int,
        backoff_counts: int,
        zero_after: bool = True,
        timeout_ms: int | None = None,
    ) -> None:
        # First pass finds home quickly. The second pass approaches more
        # slowly after a backoff move so the final home result is repeatable.
        self.home_standard(
            speed=coarse_speed,
            accel=accel,
            decel=decel,
            zero_after=True,
            timeout_ms=timeout_ms,
        )

        # The sign of backoff_counts determines which direction moves away
        # from the home switch. Tune this per mechanism.
        # self.move_relative(backoff_counts, wait=True)

        # self.home_standard(
        #     speed=fine_speed,
        #     accel=accel,
        #     decel=decel,
        #     zero_after=zero_after,
        #     timeout_ms=timeout_ms,
        # )

    def move_relative(self, counts: int, wait: bool = True) -> None:
        self.controller.command(f"PR {self.name}={counts}")
        self.controller.command(f"BG {self.name}")
        if wait:
            self.wait_for_motion_complete()

    def move_absolute(self, counts: int, wait: bool = True) -> None:
        self.controller.command(f"PA {self.name}={counts}")
        self.controller.command(f"BG {self.name}")
        if wait:
            self.wait_for_motion_complete()

    def jog(self, speed: int) -> None:
        self.controller.command(f"JG {self.name}={speed}")
        self.controller.command(f"BG {self.name}")

    def stop(self) -> None:
        self.controller.command(f"ST {self.name}")


class GalilController:
    def __init__(self, address: str):
        self.address = address
        self.g = gclib.py()

    def connect(self) -> None:
        self.g.GOpen(self.address)

    def close(self) -> None:
        try:
            self.g.GClose()
        except Exception:
            pass

    def command(self, cmd: str) -> str:
        try:
            response = self.g.GCommand(cmd)
        except gclib.GclibError as exc:
            try:
                controller_error = self.g.GCommand("TC1")
            except Exception:
                controller_error = "unable to read TC1"
            raise gclib.GclibError(
                f"{exc} while sending '{cmd}'. Controller error: {controller_error}"
            ) from exc
        return response.strip() if isinstance(response, str) else str(response)

    def abort(self) -> None:
        self.command("AB")

    def axis(self, name: str) -> Axis:
        return Axis(self, name)
