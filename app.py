from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import openai
from gtts import gTTS
import base64
import os
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# OpenAI API Configuration
openai_api_key = os.environ.get("API-KEY")
client = openai.Client(api_key=openai_api_key)

# Store conversation history
conversations = {}

def get_bot_response(user_input, session_id):
    try:
        if session_id not in conversations:
            conversations[session_id] = [
                {
                    "role": "system",
                    "content": "You are an AI assistant. Your goal is to help the user with queries."
                }
            ]
        
        conversations[session_id].append({"role": "user", "content": user_input})
        response = client.chat.completions.create(
            model="gpt-4",
            messages=conversations[session_id],
            max_tokens=150,
            temperature=0.7
        )
        ai_message = response.choices[0].message.content
        conversations[session_id].append({"role": "assistant", "content": ai_message})
        return ai_message
    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        return "Sorry, something went wrong."

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start_conversation', methods=['GET'])
def start_conversation():
    session_id = request.args.get('session_id', 'default')
    
    initial_message = "Hello! I'm ready to chat. Please start speaking."
    tts = gTTS(text=initial_message, lang='en')
    audio_filename = f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
    tts.save(audio_filename)
    
    with open(audio_filename, "rb") as audio_file:
        audio_base64 = base64.b64encode(audio_file.read()).decode()
    os.remove(audio_filename)
    
    return jsonify({
        "text": initial_message,
        "audio": audio_base64
    })

@socketio.on('message')
def handle_message(message):
    session_id = message.get('session_id', 'default')
    user_input = message.get('text', '')
    
    if user_input:
        ai_message = get_bot_response(user_input, session_id)
        tts = gTTS(text=ai_message, lang='en')
        audio_filename = f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        tts.save(audio_filename)
        
        with open(audio_filename, "rb") as audio_file:
            audio_base64 = base64.b64encode(audio_file.read()).decode()
        os.remove(audio_filename)
        
        socketio.emit('response', {
            "text": ai_message,
            "audio": audio_base64
        }, room=request.sid)

if __name__ == '__main__':
    socketio.run(app, debug=True)
