#!/bin/bash

for plan in ../../../missions/*.plan; do
    python3 check_mission.py "$plan"
done
