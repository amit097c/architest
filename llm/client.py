import requests
import json

URL = 'http://localhost:8000'

def send_prompt(message):
    data = { 'prompt': message }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(URL, data=json.dumps(data), headers=headers)
    if response.status_code == 200:
        return response.json()["message"]
    return None

while True:
    message = input("Client: ")
    if message is None or message.lower() in ['q']:
        break
    response = send_prompt(message)
    print("Server: ", response)