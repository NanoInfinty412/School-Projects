import paho.mqtt.client as mqtt
from gpiozero import CPUTemperature
import time

def on_connect(client, userdata, flags, rc):
    if(rc == 0):
        print("Connection success")
    else:
        print("Connection failed")

if __name__ == "__main__":
    client = mqtt.Client()
    cpu = CPUTemperature()
    client.on_connect = on_connect
    client.connect("broker.emqx.io", 1883, 60)
    # send a message to the raspberry/topic every 1 second, 5 times in a row
    for i in range(5):
        client.publish('raspberry/meta', payload=cpu.temperature, qos=0, retain=False)
        print(f"send {cpu.temperature} to raspberry/temp")
        time.sleep(2)
    client.loop_forever()
