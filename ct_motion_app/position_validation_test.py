import csv
from datetime import datetime
from pathlib import Path
from time import sleep, time

from config import (
    CONTROLLER_ADDRESS,
    DEFAULT_ACCEL_THETA_AXIS,
    DEFAULT_ACCEL_Z_AXIS,
    DEFAULT_DECEL_THETA_AXIS,
    DEFAULT_DECEL_Z_AXIS,
    DEFAULT_SPEED_THETA_AXIS,
    DEFAULT_SPEED_Z_AXIS,
    ENCODER_COUNTS_PER_REVOLUTION,
    MICROSTEPPING_RESOLUTION_FACTOR,
    MOTOR_TYPE_THETA_AXIS,
    MOTOR_TYPE_Z_AXIS,
    STEPPER_STEPS_PER_REVOLUTION,
)
from galil_controller import Axis, GalilController


REVOLUTION_COUNTS = range(1, 6)
TRIALS_PER_REVOLUTION_COUNT = 3
STARTUP_SETTLE_DELAY_SECONDS = 0.5
SETTLE_DELAY_SECONDS = 0.5
ZERO_DELAY_SECONDS = 0.5
RESULTS_DIR = Path("validation_results")


CSV_FIELDS = [
    "sample_index",
    "timestamp",
    "elapsed_seconds",
    "axis_label",
    "axis_name",
    "revolutions",
    "trial",
    "cumulative_commanded_revolutions",
    "encoder_error_degrees_from_zero",
    "encoder_distance_degrees_from_zero",
]


def step_counts_per_revolution() -> int:
    return STEPPER_STEPS_PER_REVOLUTION * MICROSTEPPING_RESOLUTION_FACTOR


def setup_axis(
    axis: Axis,
    speed: int,
    accel: int,
    decel: int,
    motor_type: float,
) -> None:
    axis.set_profile(
        speed=speed,
        accel=accel,
        decel=decel,
        motor_type=motor_type,
    )
    axis.enable()


def zero_axes(axes: list[Axis]) -> None:
    for axis in axes:
        axis.zero_encoder()
        axis.zero_position()
    sleep(ZERO_DELAY_SECONDS)


def move_axes_relative(axes: list[Axis], counts: int) -> None:
    for axis in axes:
        axis.controller.command(f"PR{axis.name}={counts}")

    for axis in axes:
        axis.controller.command(f"BG{axis.name}")

    for axis in axes:
        axis.controller.g.GMotionComplete(axis.name)


def read_axis_row(
    sample_index: int,
    started_at: float,
    axis_label: str,
    axis: Axis,
    revolutions: int,
    trial: int,
    cumulative_commanded_revolutions: int,
) -> dict[str, str | int | float]:
    encoder_counts_raw = axis.get_encoder_position()
    encoder_counts_mod = encoder_counts_raw % ENCODER_COUNTS_PER_REVOLUTION
    encoder_angle = Axis.counts_to_degrees(
        encoder_counts_mod,
        ENCODER_COUNTS_PER_REVOLUTION,
    )
    expected_encoder_angle = (
        cumulative_commanded_revolutions * 360.0
    ) % 360.0
    encoder_error = ((encoder_angle - expected_encoder_angle + 180.0) % 360.0) - 180.0
    encoder_distance = abs(encoder_error)

    return {
        "sample_index": sample_index,
        "timestamp": datetime.now().isoformat(timespec="milliseconds"),
        "elapsed_seconds": round(time() - started_at, 3),
        "axis_label": axis_label,
        "axis_name": axis.name,
        "revolutions": revolutions,
        "trial": trial,
        "cumulative_commanded_revolutions": cumulative_commanded_revolutions,
        "encoder_error_degrees_from_zero": round(encoder_error, 6),
        "encoder_distance_degrees_from_zero": round(encoder_distance, 6),
    }


def plot_results(csv_path: Path, plot_path: Path) -> bool:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return False

    with csv_path.open(newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    if not rows:
        return False

    axes = sorted({row["axis_label"] for row in rows})
    _, plots = plt.subplots(len(axes), 1, sharex=True, figsize=(10, 6))
    if len(axes) == 1:
        plots = [plots]

    for plot, axis_label in zip(plots, axes):
        axis_rows = [row for row in rows if row["axis_label"] == axis_label]
        elapsed = [float(row["elapsed_seconds"]) for row in axis_rows]
        angles = [
            float(row["encoder_distance_degrees_from_zero"])
            for row in axis_rows
        ]
        labels = [
            f"{row['revolutions']} rev T{row['trial']}"
            for row in axis_rows
        ]

        plot.plot(elapsed, angles, marker="o")
        plot.axhline(0, color="gray", linewidth=1, linestyle="--")
        plot.set_ylabel(f"{axis_label}\ndistance deg")
        plot.grid(True, alpha=0.3)

        for x_value, y_value, label in zip(elapsed, angles, labels):
            plot.annotate(
                label,
                (x_value, y_value),
                textcoords="offset points",
                xytext=(0, 6),
                ha="center",
                fontsize=8,
            )

    plots[-1].set_xlabel("Elapsed time (s)")
    plt.suptitle("Encoder distance from zero after integer-revolution moves")
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150)
    plt.close()
    return True


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    run_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = RESULTS_DIR / f"position_validation_{run_stamp}.csv"
    plot_path = RESULTS_DIR / f"position_validation_{run_stamp}.png"

    controller = GalilController(CONTROLLER_ADDRESS)
    z_axis = None
    theta_axis = None

    try:
        controller.connect()
        controller.abort()

        z_axis = controller.axis("A")
        theta_axis = controller.axis("B")
        axes = [z_axis, theta_axis]
        axis_labels = {
            "A": "Z Axis",
            "B": "Theta Axis",
        }

        setup_axis(
            z_axis,
            speed=DEFAULT_SPEED_Z_AXIS,
            accel=DEFAULT_ACCEL_Z_AXIS,
            decel=DEFAULT_DECEL_Z_AXIS,
            motor_type=MOTOR_TYPE_Z_AXIS,
        )
        setup_axis(
            theta_axis,
            speed=DEFAULT_SPEED_THETA_AXIS,
            accel=DEFAULT_ACCEL_THETA_AXIS,
            decel=DEFAULT_DECEL_THETA_AXIS,
            motor_type=MOTOR_TYPE_THETA_AXIS,
        )

        print("Connected to controller")
        print(f"Writing validation data to {csv_path}")
        print(f"Step counts per revolution: {step_counts_per_revolution()}")
        print(f"Encoder counts per revolution: {ENCODER_COUNTS_PER_REVOLUTION}")
        print(
            "Startup settle delay after enabling motors: "
            f"{STARTUP_SETTLE_DELAY_SECONDS:.2f} s"
        )
        print("Zeroing encoder and step counters once before all trials")
        print(f"Settle delay after each trial: {SETTLE_DELAY_SECONDS:.2f} s")

        sleep(STARTUP_SETTLE_DELAY_SECONDS)
        
        started_at = time()
        sample_index = 1
        cumulative_commanded_revolutions = 0

        zero_axes(axes)
        with csv_path.open("w", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
            writer.writeheader()

            for revolutions in REVOLUTION_COUNTS:
                commanded_step_counts = revolutions * step_counts_per_revolution()

                for trial in range(1, TRIALS_PER_REVOLUTION_COUNT + 1):
                    print(
                        f"\nTrial {trial}: {revolutions} revolution(s), "
                        f"{commanded_step_counts} step counts"
                    )

                    move_axes_relative(axes, commanded_step_counts)
                    cumulative_commanded_revolutions += revolutions
                    sleep(SETTLE_DELAY_SECONDS)

                    for axis in axes:
                        row = read_axis_row(
                            sample_index=sample_index,
                            started_at=started_at,
                            axis_label=axis_labels[axis.name],
                            axis=axis,
                            revolutions=revolutions,
                            trial=trial,
                            cumulative_commanded_revolutions=(
                                cumulative_commanded_revolutions
                            ),
                        )
                        writer.writerow(row)
                        csv_file.flush()
                        print(
                            f"{row['axis_label']}: "
                            f"encoder error="
                            f"{row['encoder_error_degrees_from_zero']:.3f} deg, "
                            f"distance from zero="
                            f"{row['encoder_distance_degrees_from_zero']:.3f} deg"
                        )
                        sample_index += 1

        if plot_results(csv_path, plot_path):
            print(f"\nSaved plot to {plot_path}")
        else:
            print("\nCSV saved. Install matplotlib to generate the plot image.")

    finally:
        try:
            controller.abort()
        except Exception:
            pass

        for axis in (z_axis, theta_axis):
            try:
                if axis is not None:
                    axis.disable()
            except Exception:
                pass

        controller.close()
        print("Disconnected")


if __name__ == "__main__":
    main()
