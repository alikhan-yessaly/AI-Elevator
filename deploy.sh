#!/bin/bash
# Device serial IDs (permanent, port-independent)
CENTRAL="id:e6642815e3630e24"
ELEVATOR="id:e6642815e35c6f24"
SCALES="id:e6642815e3718927"

deploy() {
  local ID=$1
  local DIR=$2
  echo "==> Deploying $DIR..."
  # Single session: reset then immediately copy before main.py restarts wireless
  mpremote connect $ID reset + fs cp -r $DIR/. :/
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
    echo "Devices:"
    echo "  central   $CENTRAL"
    echo "  elevator  $ELEVATOR"
    echo "  scales    $SCALES"
    ;;
esac
