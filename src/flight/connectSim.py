
drone = System(mavsdk_server_address="localhost", port=50051)
await drone.connect()
 
    print("Waiting for drone...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("--> Link: OK")
            break

