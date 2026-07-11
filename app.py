import os
import requests
from flask import Flask, jsonify
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)

# 1. SECRET_KEY अब Render के Environment Variable से आएगी
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_fallback_key')

socketio = SocketIO(app, cors_allowed_origins="*", ping_interval=20, ping_timeout=60)

# 2. External Ping Route (UptimeRobot के लिए)
# UptimeRobot में आपको URL डालना है: https://your-app.onrender.com/ping
@app.route('/ping')
def ping():
    return jsonify({"status": "Alive", "message": "Server is active"}), 200

# 3. Self-Ping फंक्शन (Render को स्लीप होने से रोकने के लिए)
def self_ping():
    # Render Variable से आपका ऐप URL लेगा
    app_url = os.environ.get('APP_URL') 
    if app_url:
        while True:
            try:
                requests.get(f"{app_url}/ping")
                print("Self-ping successful!")
            except Exception as e:
                print("Self-ping failed:", e)
            
            # हर 10 मिनट (600 सेकंड) में पिंग करेगा
            socketio.sleep(600)

@socketio.on('connect')
def test_connect():
    print('Client connected')

@socketio.on('join_tracking_room')
def on_join(data):
    room = data['target_id'] 
    join_room(room)
    emit('start_transmitting', {'message': 'Tracker is watching'}, to=room)

@socketio.on('send_location')
def handle_location(data):
    room = data['my_id'] 
    emit('receive_location', data, to=room)

@socketio.on('stop_tracking')
def on_stop(data):
    room = data['target_id']
    emit('stop_transmitting', {'message': 'Tracker left'}, to=room)

if __name__ == '__main__':
    # सर्वर स्टार्ट होते ही Self-Ping लूप चालू हो जाएगा
    socketio.start_background_task(self_ping)
    
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port)

