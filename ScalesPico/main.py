# pico = "Elevator"
pico = "Scales"
# pico = "Central"

if pico == "Elevator":
    from Picos.Elevator.main import main
elif pico == "Scales":
    from Picos.Scales.main import main
elif pico == "Central":
    from Picos.Central.main import main
else:
    print("Invalid pico")
    exit()

main()