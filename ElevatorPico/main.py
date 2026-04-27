pico = "Elevator"
# pico = "Scales"
# pico = "Central"
from time import sleep
sleep(3)

if pico == "Elevator":
    from Picos.Elevator.main import main
elif pico == "Scales":
    from Picos.Scales.main import main
elif pico == "Central":
    from Picos.Central.main import main
else:
    print("Invalid pico")
    exit()

try:
    main()
except Exception as e:
    import sys
    sys.print_exception(e)
