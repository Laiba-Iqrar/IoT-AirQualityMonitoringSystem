# app.py
from flask import Flask, render_template
import requests
from datetime import datetime

app = Flask(__name__)

@app.template_filter('datetimeformat')
def datetimeformat_filter(value, format='%Y-%m-%d %H:%M:%S'):
    try:
        dt = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
        return dt.strftime(format)
    except (ValueError, TypeError):
        return value

THINGSPEAK_CHANNEL_ID = '2917545'
THINGSPEAK_API_KEY = 'RS6ZZWX4LP9DLCL0'
NUM_RESULTS = 100

def fetch_thingspeak_data():
    url = f'https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds.json'
    params = {
        'api_key': THINGSPEAK_API_KEY,
        'results': NUM_RESULTS
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        feeds = data.get('feeds', [])
        channel_info = data.get('channel', {})
        fields = {k: v for k, v in channel_info.items() if k.startswith('field')}

        processed_data = []
        for feed in feeds:
            entry = {
                'timestamp': feed.get('created_at'),
                'fields': {}
            }
            for field_id, field_name in fields.items():
                entry['fields'][field_name] = feed.get(field_id)
            processed_data.append(entry)

        return {
            'channel_info': channel_info,
            'fields': fields.values(),
            'data': processed_data
        }

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

@app.route('/')
def dashboard():
    thingspeak_data = fetch_thingspeak_data()
    if not thingspeak_data:
        return "Error fetching data from ThingSpeak"
    latest_entry = thingspeak_data['data'][-1] if thingspeak_data['data'] else None
    return render_template('dashboard.html',
                           channel_name=thingspeak_data['channel_info'].get('name'),
                           fields=thingspeak_data['fields'],
                           latest_entry=latest_entry,
                           all_data=thingspeak_data['data'])

if __name__ == '__main__':
    app.run(debug=True)
