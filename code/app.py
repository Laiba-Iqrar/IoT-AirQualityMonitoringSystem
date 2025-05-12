from flask import Flask, render_template
import requests
import datetime
import os
from dotenv import load_dotenv
from email_alert import send_email_alert

load_dotenv()

app = Flask(__name__)

CHANNEL_ID = os.getenv('THINGSPEAK_CHANNEL_ID')
API_KEY = os.getenv('THINGSPEAK_API_KEY')

last_alert = {'rain': False, 'temp': False}

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M:%S'):
    return value.strftime(format)

def get_latest_data():
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?results=1&api_key={API_KEY}"
    r = requests.get(url)
    feed = r.json()['feeds'][0]

    return {
        'Temperature': float(feed['field1']) if feed['field1'] else None,
        'Humidity': float(feed['field2']) if feed['field2'] else None,
        'CO2': float(feed['field3']) if feed['field3'] else None,
        'Rain': int(feed['field5']) if feed['field5'] else 0,
        'timestamp': datetime.datetime.strptime(feed['created_at'], "%Y-%m-%dT%H:%M:%SZ")
    }

def get_all_data(limit=50):
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?results={limit}&api_key={API_KEY}"
    r = requests.get(url)
    feeds = r.json()['feeds']

    history = []
    for f in feeds:
        history.append({
            'timestamp': datetime.datetime.strptime(f['created_at'], "%Y-%m-%dT%H:%M:%SZ"),
            'fields': {
                'Temperature': float(f['field1']) if f['field1'] else None,
                'Humidity': float(f['field2']) if f['field2'] else None,
                'CO2': float(f['field3']) if f['field3'] else None,
                'Rain': int(f['field5']) if f['field5'] else None
            }
        })
    return history

@app.route('/')
def dashboard():
    latest = get_latest_data()
    history = get_all_data()
    fields = ['Temperature', 'Humidity', 'CO2', 'Rain']

    if latest['Rain'] == 1 and not last_alert['rain']:
        send_email_alert("Rain Detected ☔", f"Rain detected at {latest['timestamp']}.\n\nSensor Value: {latest['Rain']}")
        last_alert['rain'] = True
    elif latest['Rain'] == 0:
        last_alert['rain'] = False

    if latest['Temperature'] and latest['Temperature'] > 31 and not last_alert['temp']:
        send_email_alert("High Temperature Alert 🌡️", f"Temperature is {latest['Temperature']}°C as of {latest['timestamp']}.\nPlease take necessary action.")
        last_alert['temp'] = True
    elif latest['Temperature'] and latest['Temperature'] <= 31:
        last_alert['temp'] = False

    return render_template('dashboard.html',
                           channel_name="MQ-135 Monitor",
                           fields=fields,
                           latest_entry={'fields': latest, 'timestamp': latest['timestamp']},
                           all_data=history)


if __name__ == '__main__':
    app.run(debug=True)
