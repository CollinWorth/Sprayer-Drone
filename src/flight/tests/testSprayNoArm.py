"""
Spray test WITHOUT arming — uses pymavlink to send MAV_CMD_ACTUATOR_TEST (command 310)
directly to PX4 over serial/UDP.

NOTE: As of our testing, PX4 returns ACCEPTED but servo6_raw may stay at 1000
indoors without a full power state. QGC's actuator test slider is the only
confirmed working path. Use testSpray.py (pyautogui) for demos. This file
preserves everything we learned for outdoor/bench debugging.

Wiring facts:
  - MAIN6 configured as "Peripheral via Actuator Set 1" in QGC Actuators
  - servo6_raw = 1000 (off), 1900 (on), 32768 (invalid/cached)
  - MAVLink command 310 = MAV_CMD_ACTUATOR_TEST (NOT 519)
  - Output function 82 = MAV_ACTUATOR_OUTPUT_FUNCTION_OFFBOARD_ACTUATOR_SET1
  - source_component = 190 matches QGC GCS identity
  - MAVLink 2 required (PX4 ignores MAVLink 1 actuator commands)
  - Stream at ~10 Hz while active (param7 = timeout in seconds per message)
"""

import glob
import sys
import time
import threading

try:
    from pymavlink import mavutil
except ImportError:
    print("Install pymavlink: pip install pymavlink pyserial")
    sys.exit(1)

BAUD_RATES = [115200, 57600]
SPRAY_DURATION = 2.0
ACTUATOR_FUNCTION = 82   # MAV_ACTUATOR_OUTPUT_FUNCTION_OFFBOARD_ACTUATOR_SET1
COMMAND_ACTUATOR_TEST = 310
GCS_COMPONENT = 190      # matches QGC source_component


def find_port():
    ports = (
        glob.glob("/dev/tty.usbmodem*")
        + glob.glob("/dev/tty.usbserial*")
        + glob.glob("/dev/ttyACM*")
        + glob.glob("/dev/ttyUSB*")
    )
    return ports


def connect(port, baud):
    conn = mavutil.mavlink_connection(
        port,
        baud=baud,
        source_system=255,
        source_component=GCS_COMPONENT,
    )
    conn.mav.srcVersion = 2  # force MAVLink 2
    print(f"Waiting for heartbeat on {port} @ {baud}...")
    msg = conn.wait_heartbeat(timeout=6)
    if msg is None:
        return None
    print(f"--> Connected (sysid={conn.target_system} compid={conn.target_component})")
    return conn


def send_heartbeat_loop(conn, stop_event):
    while not stop_event.is_set():
        conn.mav.heartbeat_send(
            mavutil.mavlink.MAV_TYPE_GCS,
            mavutil.mavlink.MAV_AUTOPILOT_INVALID,
            0, 0, 0,
        )
        time.sleep(1)


def send_autopilot_version_request(conn):
    conn.mav.command_long_send(
        conn.target_system,
        conn.target_component,
        mavutil.mavlink.MAV_CMD_REQUEST_AUTOPILOT_CAPABILITIES,
        0, 1, 0, 0, 0, 0, 0, 0,
    )
    time.sleep(0.3)


def send_actuator_test(conn, value, timeout_s=0.5):
    """
    param1 = value (-1..1, where 1.0 = full on)
    param2 = timeout (seconds; PX4 resets output after this elapses)
    param5 = output function (82 = Offboard Actuator Set 1)
    """
    conn.mav.command_long_send(
        conn.target_system,
        conn.target_component,
        COMMAND_ACTUATOR_TEST,
        0,           # confirmation
        value,       # param1: normalized value
        timeout_s,   # param2: timeout
        0, 0,
        float(ACTUATOR_FUNCTION),  # param5: output function
        0, 0,
    )


def read_servo6(conn, timeout=0.2):
    deadline = time.time() + timeout
    while time.time() < deadline:
        msg = conn.recv_match(type="SERVO_OUTPUT_RAW", blocking=False)
        if msg:
            return msg.servo6_raw
        time.sleep(0.01)
    return None


def spray(conn, duration=SPRAY_DURATION):
    print(f"SPRAY ON (function {ACTUATOR_FUNCTION}, {duration}s)...")
    end = time.time() + duration
    while time.time() < end:
        send_actuator_test(conn, value=1.0, timeout_s=0.5)
        raw = read_servo6(conn, timeout=0.1)
        if raw is not None:
            print(f"  servo6_raw={raw}")
        time.sleep(0.08)

    print("SPRAY OFF")
    send_actuator_test(conn, value=-1.0, timeout_s=0.1)


def main():
    ports = find_port()
    if not ports:
        print("No serial ports found — trying UDP fallback udpin://0.0.0.0:14540")
        ports_to_try = [("udpin://0.0.0.0:14540", None)]
    else:
        print(f"Ports found: {ports}")
        ports_to_try = [(p, b) for p in ports for b in BAUD_RATES]

    conn = None
    for item in ports_to_try:
        port, baud = item
        try:
            if baud:
                conn = connect(port, baud)
            else:
                conn = mavutil.mavlink_connection(port, source_component=GCS_COMPONENT)
                conn.mav.srcVersion = 2
                print(f"Waiting for heartbeat on {port}...")
                msg = conn.wait_heartbeat(timeout=8)
                if msg:
                    print(f"--> Connected via UDP")
                else:
                    conn = None
        except Exception as e:
            print(f"  Error on {port}: {e}")
            conn = None

        if conn:
            break

    if not conn:
        print("FAILED: Could not connect. Is QGC closed? Is the FC powered?")
        sys.exit(1)

    stop_hb = threading.Event()
    hb_thread = threading.Thread(target=send_heartbeat_loop, args=(conn, stop_hb), daemon=True)
    hb_thread.start()

    send_autopilot_version_request(conn)

    print("\nPress SPACE to spray, Q to quit.")
    try:
        import tty, termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        tty.setraw(fd)
        try:
            while True:
                ch = sys.stdin.read(1)
                if ch == " ":
                    spray(conn)
                elif ch in ("q", "Q", "\x03"):
                    break
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    except Exception:
        # Fallback for environments without tty
        while True:
            input("Press Enter to spray (Ctrl+C to quit): ")
            spray(conn)

    stop_hb.set()
    print("Done.")


if __name__ == "__main__":
    main()
