"""Command-line utility for DMC-4040 digital I/O.

This file is intentionally separate from ``main.py``. The main script sends
motion and homing commands; this utility only sends digital I/O commands so a
developer or technician can check sensors and outputs without moving an axis.
"""

import argparse
from time import sleep

from config import CONTROLLER_ADDRESS, DIGITAL_IO_MAX_BIT, DIGITAL_IO_MIN_BIT
from galil_controller import GalilController


DEFAULT_IO_BITS = range(DIGITAL_IO_MIN_BIT, DIGITAL_IO_MAX_BIT + 1)


def parse_state(value: str) -> bool:
    """Convert human-friendly output states into True/False.

    The CLI accepts several spellings so the operator can type natural command
    names like ``on``/``off`` or direct logic levels like ``1``/``0``.
    """
    normalized = value.strip().lower()
    if normalized in {"1", "on", "true", "high", "set"}:
        return True
    if normalized in {"0", "off", "false", "low", "clear"}:
        return False
    raise argparse.ArgumentTypeError(
        "state must be one of: 1, 0, on, off, high, low, true, false"
    )


def format_bits(values: dict[int, int]) -> str:
    """Format bit readings as compact ``bit=value`` pairs."""
    return " ".join(f"{bit}={state}" for bit, state in values.items())


def read_inputs(controller: GalilController, bits: list[int]) -> dict[int, int]:
    """Read a list of digital inputs one bit at a time with ``@IN[n]``."""
    return {bit: controller.read_digital_input(bit) for bit in bits}


def read_outputs(controller: GalilController, bits: list[int]) -> dict[int, int]:
    """Read a list of digital output latches one bit at a time with ``@OUT[n]``."""
    return {bit: controller.read_digital_output(bit) for bit in bits}


def add_bit_argument(parser: argparse.ArgumentParser, name: str = "bit") -> None:
    """Attach the shared single-bit positional argument to a subcommand."""
    parser.add_argument(
        name,
        type=int,
        help=(
            f"Digital IO bit number. Defaults are configured for DMC-4040 "
            f"standard bits {DIGITAL_IO_MIN_BIT}-{DIGITAL_IO_MAX_BIT}."
        ),
    )


def add_bits_argument(parser: argparse.ArgumentParser) -> None:
    """Attach the shared multi-bit ``--bits`` option to a subcommand."""
    parser.add_argument(
        "--bits",
        type=int,
        nargs="+",
        default=list(DEFAULT_IO_BITS),
        help=(
            f"Digital IO bit numbers to read. Defaults to "
            f"{DIGITAL_IO_MIN_BIT}-{DIGITAL_IO_MAX_BIT}."
        ),
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser and its subcommands.

    Subcommands map directly to the helper methods on ``GalilController``:

    - ``read-input`` sends ``MG @IN[n]``.
    - ``read-output`` sends ``MG @OUT[n]``.
    - ``write-output`` sends ``SBn`` or ``CBn``.
    - ``write-port`` sends ``OP value``.
    - ``status`` and ``poll`` are convenience readbacks across several bits.
    """
    parser = argparse.ArgumentParser(
        description="Read and write Galil controller digital IO."
    )
    parser.add_argument(
        "--address",
        default=CONTROLLER_ADDRESS,
        help=f"Controller address. Defaults to {CONTROLLER_ADDRESS}.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    read_input_parser = subparsers.add_parser("read-input", help="Read one input bit")
    add_bit_argument(read_input_parser)

    read_output_parser = subparsers.add_parser(
        "read-output", help="Read one output bit"
    )
    add_bit_argument(read_output_parser)

    write_output_parser = subparsers.add_parser(
        "write-output", help="Set or clear one output bit"
    )
    add_bit_argument(write_output_parser)
    write_output_parser.add_argument("state", type=parse_state)

    write_port_parser = subparsers.add_parser(
        "write-port", help="Write the 8-bit output port with OP"
    )
    write_port_parser.add_argument(
        "value", type=int, help="Output port value from 0 to 255"
    )

    status_parser = subparsers.add_parser(
        "status", help="Read input and output bit states"
    )
    add_bits_argument(status_parser)

    poll_parser = subparsers.add_parser("poll", help="Continuously read IO states")
    add_bits_argument(poll_parser)
    poll_parser.add_argument(
        "--period",
        type=float,
        default=0.25,
        help="Polling period in seconds. Defaults to 0.25.",
    )

    return parser


def main() -> None:
    """Connect to the DMC-4040, run one IO command, and always close cleanly."""
    args = build_parser().parse_args()
    controller = GalilController(args.address)

    try:
        controller.connect()

        if args.command == "read-input":
            # Passive read of one field input.
            print(controller.read_digital_input(args.bit))
        elif args.command == "read-output":
            # Read the controller's output latch for one output.
            print(controller.read_digital_output(args.bit))
        elif args.command == "write-output":
            # Change exactly one output bit without rewriting the full port.
            controller.set_digital_output(args.bit, args.state)
            print(f"Output {args.bit} set to {int(args.state)}")
        elif args.command == "write-port":
            # Replace all eight standard outputs in one command. Use carefully.
            controller.set_output_port(args.value)
            print(f"Output port set to {args.value}")
        elif args.command == "status":
            # Snapshot both directions so wiring/debug work has one compact view.
            inputs = read_inputs(controller, args.bits)
            outputs = read_outputs(controller, args.bits)
            print(f"IN  {format_bits(inputs)}")
            print(f"OUT {format_bits(outputs)}")
        elif args.command == "poll":
            # Repeat status reads until Ctrl+C. This is useful while toggling
            # switches by hand or watching an output during troubleshooting.
            print("Press Ctrl+C to stop.")
            while True:
                inputs = read_inputs(controller, args.bits)
                outputs = read_outputs(controller, args.bits)
                print(
                    f"IN  {format_bits(inputs)} | OUT {format_bits(outputs)}",
                    flush=True,
                )
                sleep(args.period)

    except KeyboardInterrupt:
        print("\nStopped IO polling")

    finally:
        controller.close()


if __name__ == "__main__":
    main()
