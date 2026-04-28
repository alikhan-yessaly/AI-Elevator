#!/bin/bash
# Device serial IDs (permanent, port-independent)
CENTRAL="id:e6642815e3630e24"
ELEVATOR="id:e6642815e35c6f24"
SCALES="id:e6642815e3718927"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Resolve the actual /dev/cu.* port for a given serial ID
find_port() {
  local RAW_ID="${1#id:}"   # strip "id:" prefix if present
  mpremote devs 2>/dev/null | grep "$RAW_ID" | awk '{print $1}'
}

deploy() {
  local ID=$1
  local DIR=$2

  local PORT
  PORT=$(find_port "$ID")
  if [ -z "$PORT" ]; then
    echo "==> ERROR: device $ID not found — is it plugged in?"
    return 1
  fi

  echo "==> Deploying $DIR on $PORT..."
  echo "    Interrupting running code..."
  python3 "$SCRIPT_DIR/pico_wake.py" "$PORT" 5 || true
  sleep 0.5
  echo "    Copying files..."
  mpremote connect $ID fs cp -r "$SCRIPT_DIR/$DIR/." :/
}

case "$1" in
  central)  deploy $CENTRAL  CentralPico ;;
  elevator) deploy $ELEVATOR ElevatorPico ;;
  scales)   deploy $SCALES   ScalesPico ;;
  all)
    deploy $CENTRAL  CentralPico
    deploy $ELEVATOR ElevatorPico
    deploy $SCALES   ScalesPico
    ;;
  *)
    echo "Usage: ./deploy.sh [central|elevator|scales|all]"
    echo ""
    echo "Connected devices:"
    mpremote devs 2>/dev/null || echo "  (mpremote not found)"
    ;;
esac
