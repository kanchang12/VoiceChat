from flask import Flask, render_template, jsonify, request
import openai
from gtts import gTTS
import base64
import os
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

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
    
    # Initial greeting
    initial_message = "Hello! I'm ready to chat. How can I help you today?"
    tts = gTTS(text=initial_message, lang='en')
    audio_filename = f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
    tts.save(audio_filename)
    
    try:
        with open(audio_filename, "rb") as audio_file:
            audio_base64 = base64.b64encode(audio_file.read()).decode()
    finally:
        if os.path.exists(audio_filename):
            os.remove(audio_filename)
    
    return jsonify({
        "text": initial_message,
        "audio": audio_base64,
        "status": "ready"
    })

@app.route('/check_speech', methods=['GET'])
def check_speech():
    session_id = request.args.get('session_id', 'default')
    # Since we're not actually processing speech, just return listening status
    return jsonify({
        "status": "listening"
    })

@app.route('/process_speech', methods=['POST'])
def process_speech():
    try:
        data = request.json
        user_input = data.get('text', '')
        session_id = data.get('session_id', 'default')
        
        # Get AI response
        ai_message = get_bot_response(user_input, session_id)
        
        # Convert to speech
        tts = gTTS(text=ai_message, lang='en')
        audio_filename = f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        tts.save(audio_filename)
        
        try:
            with open(audio_filename, "rb") as audio_file:
                audio_base64 = base64.b64encode(audio_file.read()).decode()
        finally:
            if os.path.exists(audio_filename):
                os.remove(audio_filename)
        
        return jsonify({
            "text": ai_message,
            "audio": audio_base64,
            "status": "response"
        })
    except Exception as e:
        print(f"Error processing speech: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/stop_conversation', methods=['POST'])
def stop_conversation():
    session_id = request.json.get('session_id', 'default')
    if session_id in conversations:
        conversations.pop(session_id)
    return jsonify({"status": "stopped"})

if __name__ == '__main__':
    app.run(debug=True)
