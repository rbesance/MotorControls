import gclib


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

    def get_encoder_position(self) -> int:
        return int(float(self.controller.command(f"TP{self.name}")))

    def get_step_position(self) -> int:
        return int(float(self.controller.command(f"TD{self.name}")))

    def get_motor_type(self) -> float:
        return float(self.controller.command(f"MG _MT{self.name}"))

    def is_stepper(self) -> bool:
        return self.get_motor_type() in {2, -2, 2.5, -2.5}

    def move_relative(self, counts: int, wait: bool = True) -> None:
        self.controller.command(f"PR{self.name}={counts}")
        self.controller.command(f"BG{self.name}")
        if wait:
            self.controller.g.GMotionComplete(self.name)

    def move_absolute(self, counts: int, wait: bool = True) -> None:
        self.controller.command(f"PA{self.name}={counts}")
        self.controller.command(f"BG{self.name}")
        if wait:
            self.controller.g.GMotionComplete(self.name)

    def jog(self, speed: int) -> None:
        self.controller.command(f"JG{self.name}={speed}")
        self.controller.command(f"BG{self.name}")

    def stop(self) -> None:
        self.controller.command(f"ST{self.name}")


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
        response = self.g.GCommand(cmd)
        return response.strip() if isinstance(response, str) else str(response)

    def abort(self) -> None:
        self.command("AB")

    def axis(self, name: str) -> Axis:
        return Axis(self, name)