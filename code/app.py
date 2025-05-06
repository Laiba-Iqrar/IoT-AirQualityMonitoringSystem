import os
import requests
from flask import Flask, render_template
import datetime
from email_alert import send_email_alert

app = Flask(__name__)

# Replace with your actual channel ID and API key
THINGSPEAK_CHANNEL_ID = '2917545'
THINGSPEAK_API_KEY = 'RS6ZZWX4LP9DLCL0'

def get_latest_data():
    url = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds.json?api_key={THINGSPEAK_API_KEY}&results=1"
    response = requests.get(url)
    if response.status_code == 200:
        feed = response.json()['feeds'][0]
        return {
            'Temperature': float(feed['field1']) if feed['field1'] else None,
            'Humidity': float(feed['field2']) if feed['field2'] else None,
            'CO2': float(feed['field3']) if feed['field3'] else None,
            'Rain': int(feed['field5']) if feed['field5'] else 0,
            'timestamp': datetime.datetime.strptime(feed['created_at'], "%Y-%m-%dT%H:%M:%SZ")
        }
    else:
        raise Exception("Error fetching data from ThingSpeak")

last_alert = {'rain': False, 'temp': False}

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M:%S'):
    return value.strftime(format)

@app.route('/')
def dashboard():
    latest = get_latest_data()
    fields = ['Temperature', 'Humidity', 'CO2', 'Rain']

    if latest['Rain'] == 1 and not last_alert['rain']:
        send_email_alert("Rain Detected", "Rain has been detected by the sensor. Stay safe!")
        last_alert['rain'] = True
    elif latest['Rain'] == 0:
        last_alert['rain'] = False

    if latest['Temperature'] > 31 and not last_alert['temp']:
        send_email_alert("High Temperature Alert", f"The temperature is now {latest['Temperature']}°C.")
        last_alert['temp'] = True
    elif latest['Temperature'] <= 31:
        last_alert['temp'] = False

    all_data = [{
        'timestamp': latest['timestamp'] - datetime.timedelta(minutes=i),
        'fields': {
            'Temperature': latest['Temperature'],
            'Humidity': latest['Humidity'],
            'CO2': latest['CO2'],
            'Rain': latest['Rain']
        }
    } for i in range(10)]

    return render_template(
        'dashboard.html',
        channel_name="MQ-135 Monitor",
        fields=fields,
        latest_entry={'fields': latest, 'timestamp': latest['timestamp']},
        all_data=all_data[::-1]
    )

if __name__ == '__main__':
    app.run(debug=True)
