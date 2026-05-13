"""
Parses a QGC .plan file and prints each mission item with coordinates.
No drone connection needed. Run: python3 check_mission.py ../../missions/parker_farm2_small.plan
"""
import sys
import json

COMMANDS = {16: "WAYPOINT", 20: "RTL", 22: "TAKEOFF", 178: "DO_CHANGE_SPEED", 206: "DO_SET_CAM_TRIGG_DIST", 530: "DO_GRIPPER"}


def print_item(item, index, bad, prefix=""):
    cmd = item.get("command")
    params = item.get("params", [])
    lat = params[4] if len(params) > 4 else None
    lon = params[5] if len(params) > 5 else None
    alt = params[6] if len(params) > 6 else item.get("Altitude")
    label = COMMANDS.get(cmd, f"cmd={cmd}")

    # Only WAYPOINT (16) must have real coordinates — TAKEOFF 0,0 means "from home", RTL always ignores coords
    has_coords = lat not in (None, 0.0) and lon not in (None, 0.0)
    flag = ""
    if cmd == 16 and not has_coords:
        flag = "  <-- BAD: missing/zero coords"
        bad.append(index)

    print(f"  {prefix}[{index}] {label:<22}  lat={str(lat):>18}  lon={str(lon):>20}  alt={alt}m{flag}")


def check(plan_path: str):
    with open(plan_path) as f:
        raw = json.load(f)

    items = raw.get("mission", {}).get("items", [])
    if not items:
        print("ERROR: no items found under mission.items — check file structure")
        sys.exit(1)

    print(f"\nPlan: {plan_path}")
    print(f"Top-level items: {len(items)}\n")

    bad = []
    for i, item in enumerate(items):
        if item.get("type") == "ComplexItem":
            nested = item.get("TransectStyleComplexItem", {}).get("Items", [])
            print(f"  [{i}] SURVEY (ComplexItem) — {len(nested)} nested waypoints")
            for j, sub in enumerate(nested):
                print_item(sub, j, bad, prefix="  ")
        else:
            print_item(item, i, bad)

    print()
    if bad:
        print(f"WARNING: {len(bad)} WAYPOINT(s) with missing/zero coordinates: indices {bad}")
    else:
        print("All coordinates look good.")

    home = raw.get("mission", {}).get("plannedHomePosition")
    print(f"Home position: {home}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 check_mission.py <path/to/mission.plan>")
        sys.exit(1)
    check(sys.argv[1])
