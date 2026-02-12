import asyncio
import os
from dotenv import load_dotenv
from mavsdk import System
from mavsdk.mission import MissionItem, MissionPlan

class Drone:
    def __init__(self):
        load_dotenv()
        self.connection_string = os.getenv("CONNECTION_STRING")
        if not self.connection_string:
            raise ValueError("CONNECTION_STRING not found in .env file")
        self.system = System()

    async def connect(self):
        """Connects to the drone using the connection string from the .env file."""
        print(f"--- Connecting to drone on {self.connection_string} ---")
        await self.system.connect(system_address=self.connection_string)

        async for state in self.system.core.connection_state():
            if state.is_connected:
                print("--> Drone Connected")
                return True
        return False

    async def wait_for_readiness(self):
        """Waits for the drone to be ready (passes health checks)."""
        print("--- Waiting for drone to be ready ---")
        async for health in self.system.telemetry.health():
            if health.is_armable and health.is_global_position_ok:
                print("--> System Ready")
                break

    async def arm(self):
        """Arms the drone."""
        print("--- Arming ---")
        await self.system.action.arm()
        async for is_armed in self.system.telemetry.armed():
            if is_armed:
                print("--> Drone Armed")
                break

    async def takeoff(self, altitude=10.0):
        """Takes off to a specific altitude."""
        print(f"--- Taking off to {altitude}m ---")
        await self.system.action.set_takeoff_altitude(altitude)
        await self.system.action.takeoff()
        async for position in self.system.telemetry.position():
            if position.relative_altitude_m > altitude * 0.95:
                print(f"--> Altitude Reached: {round(position.relative_altitude_m, 1)}m")
                break

    async def upload_mission(self, mission_items):
        """Uploads a mission to the drone."""
        print("--- Uploading mission ---")
        mission_plan = MissionPlan(mission_items)
        await self.system.mission.upload_mission(mission_plan)
        print("--> Mission Uploaded")

    async def start_mission(self):
        """Starts the uploaded mission."""
        print("--- Starting mission ---")
        await self.system.mission.set_current_mission_item(0)
        await asyncio.sleep(1)
        await self.system.mission.start_mission()

    async def monitor_mission_progress(self):
        """Monitors the mission progress and returns when complete."""
        async for progress in self.system.mission.mission_progress():
            print(f"   [Mission] Waypoint {progress.current}/{progress.total}")
            if progress.current == progress.total:
                print("-- Mission Complete")
                break

    async def return_to_launch(self):
        """Commands the drone to return to the launch position."""
        print("--- Returning to Launch ---")
        await self.system.action.return_to_launch()

    async def disarm(self):
        """Disarms the drone."""
        print("--- Disarming ---")
        await self.system.action.disarm()

    async def shutdown(self):
        """Shuts down the connection to the drone."""
        print("--- Shutting down ---")
        # This is not a standard MAVSDK function, but represents disconnecting
        # The 'await self.system.connect()' doesn't have a clean disconnect,
        # the object just gets destroyed.
        pass
