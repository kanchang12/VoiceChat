from flask import Flask, render_template, jsonify, request
import openai
from gtts import gTTS
import base64
import os
from datetime import datetime
import speech_recognition as sr
from time import time
import threading

app = Flask(__name__)

# OpenAI API Configuration
openai_api_key = os.environ.get("API-KEY")
client = openai.Client(api_key=openai_api_key)

# Store conversation history
conversations = {}
listening_threads = {}
SILENCE_THRESHOLD = 1.5  # 1.5 seconds of silence before processing

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

def listen_for_speech(session_id):
    recognizer = sr.Recognizer()
    last_speech_time = time()
    
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        
        while session_id in listening_threads:
            try:
                audio = recognizer.listen(source, timeout=1, phrase_time_limit=None)
                text = recognizer.recognize_google(audio)
                if text.strip():
                    last_speech_time = time()
                    return text
                
                # Check if silence threshold is exceeded
                if time() - last_speech_time > SILENCE_THRESHOLD:
                    return None
                
            except sr.WaitTimeoutError:
                if time() - last_speech_time > SILENCE_THRESHOLD:
                    return None
            except Exception as e:
                print(f"Error in speech recognition: {e}")
                return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start_conversation', methods=['GET'])
def start_conversation():
    session_id = request.args.get('session_id', 'default')
    
    # Clear any existing listening thread
    if session_id in listening_threads:
        listening_threads.pop(session_id)
    
    # Start new listening thread
    listening_threads[session_id] = threading.Thread(
        target=listen_for_speech,
        args=(session_id,)
    )
    listening_threads[session_id].start()
    
    # Initial greeting
    initial_message = "Hello! I'm ready to chat. Please start speaking."
    tts = gTTS(text=initial_message, lang='en')
    audio_filename = f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
    tts.save(audio_filename)
    
    with open(audio_filename, "rb") as audio_file:
        audio_base64 = base64.b64encode(audio_file.read()).decode()
    os.remove(audio_filename)
    
    return jsonify({
        "text": initial_message,
        "audio": audio_base64,
        "status": "listening"
    })

@app.route('/check_speech', methods=['GET'])
def check_speech():
    session_id = request.args.get('session_id', 'default')
    
    if session_id not in listening_threads or not listening_threads[session_id].is_alive():
        return jsonify({"status": "error", "message": "No active listening session"})
    
    speech_text = listen_for_speech(session_id)
    
    if speech_text:
        # Got user input, process it
        ai_message = get_bot_response(speech_text, session_id)
        tts = gTTS(text=ai_message, lang='en')
        audio_filename = f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        tts.save(audio_filename)
        
        with open(audio_filename, "rb") as audio_file:
            audio_base64 = base64.b64encode(audio_file.read()).decode()
        os.remove(audio_filename)
        
        return jsonify({
            "status": "response",
            "user_text": speech_text,
            "bot_text": ai_message,
            "audio": audio_base64
        })
    
    return jsonify({"status": "listening"})

@app.route('/stop_conversation', methods=['POST'])
def stop_conversation():
    session_id = request.json.get('session_id', 'default')
    if session_id in listening_threads:
        listening_threads.pop(session_id)
    return jsonify({"status": "stopped"})

if __name__ == '__main__':
    app.run(debug=True)
