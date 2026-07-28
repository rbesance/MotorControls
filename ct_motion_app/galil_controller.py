"""Galil DMC-4040 controller interface.

The rest of the application should prefer these small Python methods over raw
Galil command strings. Keeping command strings here makes hardware behavior
easier to audit and gives future developers one place to add logging, safety
checks, or controller-specific workarounds.
"""

import gclib
from config import (
    DIGITAL_IO_MAX_BIT,
    DIGITAL_IO_MIN_BIT,
    DIGITAL_OUTPUT_PORT_MAX_VALUE,
    DIGITAL_OUTPUT_PORT_MIN_VALUE,
    ENCODER_COUNTS_PER_REVOLUTION,
    HOME_INPUT_POLARITY,
    MICROSTEPPING_RESOLUTION_FACTOR,
    STEPPER_STEPS_PER_REVOLUTION,
)


class Axis:
    """Motion-focused helper for one Galil axis.

    The application code uses this wrapper instead of sending raw Galil
    commands everywhere. Each method maps to one small controller operation
    such as enabling an axis, reading position, or starting a move.
    """

    VALID_AXES = {"A", "B", "C", "D"}

    def __init__(self, controller: "GalilController", name: str):
        self.controller = controller
        self.name = self._validate_axis(name)

    def _validate_axis(self, axis: str) -> str:
        """Normalize and validate a Galil axis name."""
        axis = axis.upper()
        if axis not in self.VALID_AXES:
            raise ValueError(f"Invalid axis '{axis}'. Must be one of {sorted(self.VALID_AXES)}.")
        return axis

    def enable(self) -> None:
        """Enable this axis with Galil ``SH`` (servo here)."""
        self.controller.command(f"SH{self.name}")

    def disable(self) -> None:
        """Disable this axis with Galil ``MO`` (motor off)."""
        self.controller.command(f"MO{self.name}")

    def set_profile(
        self,
        speed: int,
        accel: int,
        decel: int,
        motor_type: float | None = None,
    ) -> None:
        """Configure speed, acceleration, deceleration, and optional motor type.

        Galil commands used:

        - ``SP`` sets commanded speed.
        - ``AC`` sets acceleration.
        - ``DC`` sets deceleration.
        - ``MT`` sets motor type when provided.
        """
        self.controller.command(f"SP{self.name}={speed}")
        self.controller.command(f"AC{self.name}={accel}")
        self.controller.command(f"DC{self.name}={decel}")
        if motor_type is not None:
            self.controller.command(f"MT{self.name}={motor_type}")

    def zero_position(self) -> None:
        """Zero the commanded motor position with Galil ``DP``."""
        self.controller.command(f"DP{self.name}=0")

    def zero_encoder(self) -> None:
        """Zero the encoder position with Galil ``DE``."""
        self.controller.command(f"DE{self.name}=0")

    def wait_for_motion_complete(self, timeout_ms: int | None = None) -> None:
        """Wait for profiled motion to complete using gclib ``GMotionComplete``."""
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
        """Wait for Galil after-motion complete using ``AM``."""
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
        """Read encoder position with Galil ``TP``."""
        return int(float(self.controller.command(f"TP{self.name}")))

    def get_step_position(self) -> int:
        """Read commanded step/planner position with Galil ``TD``."""
        return int(float(self.controller.command(f"TD{self.name}")))

    def get_encoder_position_degrees(self) -> float:
        """Read encoder position and convert wrapped counts to degrees."""
        return self.counts_to_degrees(
            self.get_encoder_position() % ENCODER_COUNTS_PER_REVOLUTION,
            ENCODER_COUNTS_PER_REVOLUTION,
        )

    def get_step_position_degrees(self) -> float:
        """Read step position and convert counts to degrees."""
        steps_per_revolution = (
            STEPPER_STEPS_PER_REVOLUTION * MICROSTEPPING_RESOLUTION_FACTOR
        )
        return self.counts_to_degrees(self.get_step_position(), steps_per_revolution)

    def get_position_degrees(self) -> dict[str, float]:
        """Return both encoder-derived and step-derived position in degrees."""
        return {
            "encoder_degrees": self.get_encoder_position_degrees(),
            "step_degrees": self.get_step_position_degrees(),
        }

    @staticmethod
    def counts_to_degrees(counts: int, counts_per_revolution: int) -> float:
        """Convert controller counts to mechanical degrees."""
        return counts * 360.0 / counts_per_revolution

    def get_motor_type(self) -> float:
        """Read the configured motor type operand ``_MT``."""
        return float(self.controller.command(f"MG _MT{self.name}"))

    def is_stepper(self) -> bool:
        """Return True when Galil ``MT`` is one of the stepper motor modes."""
        return self.get_motor_type() in {2, -2, 2.5, -2.5}

    def get_forward_limit_state(self) -> int:
        """Read the forward limit operand ``_LF`` for this axis."""
        return int(float(self.controller.command(f"MG _LF{self.name}")))

    def get_reverse_limit_state(self) -> int:
        """Read the reverse limit operand ``_LR`` for this axis."""
        return int(float(self.controller.command(f"MG _LR{self.name}")))

    def get_home_switch_state(self) -> int:
        """Read the home switch operand ``_HM`` for this axis."""
        return int(float(self.controller.command(f"MG _HM{self.name}")))

    def get_stop_code(self) -> int:
        """Read the Galil stop code operand ``_SC`` for this axis."""
        return int(float(self.controller.command(f"MG _SC{self.name}")))

    def get_switch_status(self) -> int:
        """Read Galil switch/status operand ``_TS`` for this axis."""
        return int(float(self.controller.command(f"MG _TS{self.name}")))

    def home_standard(
        self,
        speed: int,
        accel: int,
        decel: int,
        zero_after: bool = True,
        timeout_ms: int | None = None,
    ) -> None:
        """Run Galil standard homing with ``CN``, ``HM``, ``BG``, and ``AM``.

        ``CN`` configures home-input polarity. ``HM`` arms the controller's
        built-in home routine. ``BG`` starts motion. ``AM`` waits until the
        controller reports after-motion complete.
        """
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
        """Home this axis using the project's two-pass homing entry point.

        The backoff/fine pass is currently commented out while hardware
        behavior is being tuned. The public method remains so callers do not
        need to change once the second pass is re-enabled.
        """
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
        """Move relative counts using Galil ``PR`` and ``BG``."""
        self.controller.command(f"PR {self.name}={counts}")
        self.controller.command(f"BG {self.name}")
        if wait:
            self.wait_for_motion_complete()

    def move_absolute(self, counts: int, wait: bool = True) -> None:
        """Move to an absolute count position using Galil ``PA`` and ``BG``."""
        self.controller.command(f"PA {self.name}={counts}")
        self.controller.command(f"BG {self.name}")
        if wait:
            self.wait_for_motion_complete()

    def jog(self, speed: int) -> None:
        """Start continuous jog motion using Galil ``JG`` and ``BG``."""
        self.controller.command(f"JG {self.name}={speed}")
        self.controller.command(f"BG {self.name}")

    def stop(self) -> None:
        """Stop this axis using Galil ``ST``."""
        self.controller.command(f"ST {self.name}")


class GalilController:
    """Thin DMC-4040 connection and command wrapper.

    The DMC accepts terse ASCII commands, for example ``TPA`` or ``SB1``.
    This class keeps the low-level gclib object in one place, adds consistent
    error reporting with ``TC1``, and exposes readable methods for the motion
    and digital-I/O commands used by this project.
    """

    MIN_IO_BIT = DIGITAL_IO_MIN_BIT
    MAX_IO_BIT = DIGITAL_IO_MAX_BIT
    MIN_OUTPUT_PORT_VALUE = DIGITAL_OUTPUT_PORT_MIN_VALUE
    MAX_OUTPUT_PORT_VALUE = DIGITAL_OUTPUT_PORT_MAX_VALUE

    def __init__(self, address: str):
        """Create a controller wrapper for a Galil GOpen address."""
        self.address = address
        self.g = gclib.py()

    def connect(self) -> None:
        """Open the TCP/UDP connection to the controller."""
        self.g.GOpen(self.address)

    def close(self) -> None:
        """Close the controller connection, ignoring close-time cleanup errors."""
        try:
            self.g.GClose()
        except Exception:
            pass

    def command(self, cmd: str) -> str:
        """Send one raw Galil command and return the stripped response.

        Use this when a command does not yet have a typed helper method.
        If gclib raises an error, the wrapper asks the controller for ``TC1``
        so the exception includes the Galil-side error code/message.
        """
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
        """Abort motion/program execution with Galil ``AB``."""
        self.command("AB")

    def axis(self, name: str) -> Axis:
        """Return an ``Axis`` helper for axis A, B, C, or D."""
        return Axis(self, name)

    def _validate_io_bit(self, bit: int) -> int:
        """Validate a DMC-4040 standard digital I/O bit number.

        Standard DMC-4040 units expose uncommitted digital I/O bits 1-8.
        Optional extended I/O can expose additional banks; if your hardware
        includes those banks, update the limits in ``config.py`` first.
        """
        if not self.MIN_IO_BIT <= bit <= self.MAX_IO_BIT:
            raise ValueError(
                f"Invalid IO bit {bit}. Must be between "
                f"{self.MIN_IO_BIT} and {self.MAX_IO_BIT}."
            )
        return bit

    def _validate_output_port_value(self, value: int) -> int:
        """Validate a whole-port output value for Galil ``OP``.

        ``OP`` writes the standard 8-output port as a byte. Bit 0 of the byte
        maps to output 1, bit 1 maps to output 2, and so on through output 8.
        """
        if not self.MIN_OUTPUT_PORT_VALUE <= value <= self.MAX_OUTPUT_PORT_VALUE:
            raise ValueError(
                f"Invalid output port value {value}. Must be between "
                f"{self.MIN_OUTPUT_PORT_VALUE} and {self.MAX_OUTPUT_PORT_VALUE}."
            )
        return value

    def read_digital_input(self, bit: int) -> int:
        """Read one digital input using ``MG @IN[n]``.

        Returns ``1`` when the controller reports the input high/active and
        ``0`` when it reports low/inactive. This is a passive read and does
        not affect motion or output state.
        """
        bit = self._validate_io_bit(bit)
        return int(float(self.command(f"MG @IN[{bit}]")))

    def read_digital_output(self, bit: int) -> int:
        """Read one digital output latch using ``MG @OUT[n]``.

        This reports the controller's commanded output state. It is useful
        for confirming what the DMC thinks it is driving, but it does not
        prove field wiring voltage/current at the terminal.
        """
        bit = self._validate_io_bit(bit)
        return int(float(self.command(f"MG @OUT[{bit}]")))

    def set_digital_output(self, bit: int, state: bool) -> None:
        """Set or clear one digital output using Galil ``SB``/``CB``.

        ``SBn`` sets output bit ``n`` high/on. ``CBn`` clears output bit
        ``n`` low/off. Only call this for outputs that are safe to energize.
        """
        bit = self._validate_io_bit(bit)
        self.command(f"SB{bit}" if state else f"CB{bit}")

    def set_output_port(self, value: int) -> None:
        """Write all eight standard digital outputs at once using ``OP``.

        ``value`` is interpreted as an 8-bit mask:

        - ``OP 0`` clears outputs 1-8.
        - ``OP 1`` sets output 1 only.
        - ``OP 6`` sets outputs 2 and 3.
        - ``OP 255`` sets outputs 1-8.

        This replaces the full output-port state, so prefer
        ``set_digital_output`` when changing only one bit.
        """
        value = self._validate_output_port_value(value)
        self.command(f"OP {value}")
