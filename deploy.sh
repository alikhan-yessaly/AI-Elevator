#!/bin/bash
# Device serial IDs (permanent, port-independent)
CENTRAL="id:e6642815e3630e24"
ELEVATOR="id:e6642815e35c6f24"
SCALES="id:e6642815e3718927"

# Serial ports (fixed by USB hub position)
CENTRAL_PORT="/dev/cu.usbmodem1112201"
ELEVATOR_PORT="/dev/cu.usbmodem11201"
SCALES_PORT="/dev/cu.usbmodem11401"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

deploy() {
  local ID=$1
  local PORT=$2
  local DIR=$3
  echo "==> Deploying $DIR..."
  # Reset via serial (bypasses mpremote's raw-REPL requirement)
  python3 "$SCRIPT_DIR/pico_reset.py" "$PORT" || true
  # Wait for USB re-enumeration + boot.py delay window
  sleep 3
  # Copy during the boot.py idle window (before BLE starts)
  mpremote connect $ID fs cp -r $DIR/. :/
}

case "$1" in
  central)  deploy $CENTRAL  $CENTRAL_PORT  CentralPico ;;
  elevator) deploy $ELEVATOR $ELEVATOR_PORT ElevatorPico ;;
  scales)   deploy $SCALES   $SCALES_PORT   ScalesPico ;;
  all)
    deploy $CENTRAL  $CENTRAL_PORT  CentralPico
    deploy $ELEVATOR $ELEVATOR_PORT ElevatorPico
    deploy $SCALES   $SCALES_PORT   ScalesPico
    ;;
  *)
    echo "Usage: ./deploy.sh [central|elevator|scales|all]"
    echo ""
    echo "Devices:"
    echo "  central   $CENTRAL"
    echo "  elevator  $ELEVATOR"
    echo "  scales    $SCALES"
    ;;
esac
