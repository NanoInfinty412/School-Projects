import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    if(rc == 0):
        print("Connection success")
    else:
        print("Connection failed")

if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect("broker.emqx.io", 1883, 60)
    client.loop_forever()
