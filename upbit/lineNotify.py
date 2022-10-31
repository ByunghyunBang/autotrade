import requests
import os

def line_notify(message):
    try:
        TARGET_URL = 'https://notify-api.line.me/api/notify'
        TOKEN = os.getenv('LINE_TOKEN')
        headers={'Authorization': 'Bearer ' + TOKEN}
        data={'message': message}

        response = requests.post(TARGET_URL, headers=headers, data=data)

    except Exception as ex:
        print(ex)
