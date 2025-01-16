from flask import Flask, render_template, jsonify, request
import openai
from gtts import gTTS
import base64
import os
from datetime import datetime

app = Flask(__name__)

# OpenAI API Configuration
openai_api_key = os.environ.get("API-KEY")  # Ensure your API key is set in the environment variables
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

        # Get response from OpenAI
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
    session_id = "default"
    
    # First message from the assistant
    initial_message = "Hello! How can I assist you today?"

    # Generate speech from the initial message
    tts = gTTS(text=initial_message, lang='en')
    audio_filename = f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
    tts.save(audio_filename)

    # Convert audio to base64
    with open(audio_filename, "rb") as audio_file:
        audio_base64 = base64.b64encode(audio_file.read()).decode()

    # Clean up audio file after sending
    os.remove(audio_filename)

    return jsonify({
        "text": initial_message,
        "audio": audio_base64
    })

@app.route('/continue_conversation', methods=['POST'])
def continue_conversation():
    try:
        data = request.json
        user_input = data.get('message', '')
        session_id = data.get('session_id', 'default')

        ai_message = get_bot_response(user_input, session_id)

        # Generate speech from the AI's response
        tts = gTTS(text=ai_message, lang='en')
        audio_filename = f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        tts.save(audio_filename)

        # Convert audio to base64
        with open(audio_filename, "rb") as audio_file:
            audio_base64 = base64.b64encode(audio_file.read()).decode()

        # Clean up the audio file
        os.remove(audio_filename)

        return jsonify({
            "text": ai_message,
            "audio": audio_base64
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
