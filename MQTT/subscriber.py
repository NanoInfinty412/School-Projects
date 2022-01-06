# subscriber.py
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("raspberry/meta")

# will be triggered when receiving messages
def on_message(client, userdata, msg):
    print(f"{msg.topic} {msg.payload}")
    
if __name__ == "__main__":
	client = mqtt.Client()
	client.on_connect = on_connect
	client.on_message = on_message
	# Raspberry Pi is powered off, or the network is interrupted abnormally, it will send the will message to other clients
	client.will_set('raspberry/status', b'{"status": "Off"}')
	client.connect("broker.emqx.io", 1883, 60)
	client.loop_forever()