from gpiozero import CPUTemperature

def main():
    cpu = CPUTemperature()
    print(cpu.temperature)
    return 0

if __name__ == "__main__":
    main()
