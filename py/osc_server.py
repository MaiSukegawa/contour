from pythonosc.udp_client import SimpleUDPClient

IP = "127.0.0.1"
PORT = 8888

client = SimpleUDPClient(IP, PORT)

def send_motion_data(_motion_data):
    client.send_message("/motion", _motion_data)