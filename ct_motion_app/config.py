CONTROLLER_ADDRESS = "192.168.42.54"

# DMC-4040 standard uncommitted digital I/O.
#
# The 1-4 axis DMC-4000 controllers, including the DMC-4040, provide
# 8 opto-isolated digital inputs and 8 opto-isolated digital outputs.
# If the controller is fitted with optional extended I/O, increase
# DIGITAL_IO_MAX_BIT after confirming the installed hardware and any
# controller-side I/O configuration.
DIGITAL_IO_MIN_BIT = 1
DIGITAL_IO_MAX_BIT = 8
DIGITAL_OUTPUT_PORT_MIN_VALUE = 0
DIGITAL_OUTPUT_PORT_MAX_VALUE = 255

DEFAULT_SPEED_Z_AXIS = 400
DEFAULT_ACCEL_Z_AXIS = 10000
DEFAULT_DECEL_Z_AXIS = 10000

DEFAULT_SPEED_THETA_AXIS = 400
DEFAULT_ACCEL_THETA_AXIS = 10000
DEFAULT_DECEL_THETA_AXIS = 10000

SMALL_TEST_MOVE = 400

# Conservative homing values. Tune these experimentally on hardware before
# relying on them for production operation.
HOME_SPEED_Z_AXIS = 1000
HOME_FINE_SPEED_Z_AXIS = 200
HOME_ACCEL_Z_AXIS = 20000
HOME_DECEL_Z_AXIS = 20000
HOME_BACKOFF_Z_AXIS = -400
HOME_TIMEOUT_MS_Z_AXIS = 15000

# Theta has a home switch but no physical forward/reverse limit switches.
# HM is still used, but speeds/backoff must be verified carefully in hardware.
HOME_SPEED_THETA_AXIS = 1000
HOME_FINE_SPEED_THETA_AXIS = 200
HOME_ACCEL_THETA_AXIS = 20000
HOME_DECEL_THETA_AXIS = 20000
HOME_BACKOFF_THETA_AXIS = -200
HOME_TIMEOUT_MS_THETA_AXIS = 15000

# Manual homing example uses CN ,-1 for a normally closed home switch.
# Change this to 1 if your home input wiring/polarity is normally open.
HOME_INPUT_POLARITY = -1

# Stepper motors are 400 full steps per revolution. The drives are currently
# configured for quarter stepping, so commanded step counts are scaled by 4.
STEPPER_STEPS_PER_REVOLUTION = 400
MICROSTEPPING_RESOLUTION_FACTOR = 1

ENCODER_COUNTS_PER_REVOLUTION = 8000

#Stepper Motor = 2
MOTOR_TYPE_Z_AXIS = 2 
MOTOR_TYPE_THETA_AXIS = 2
