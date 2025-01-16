from flask import Flask, render_template, jsonify
import openai
from openai import OpenAI
from gtts import gTTS
import base64
import os
from datetime import datetime

app = Flask(__name__)

# Configure OpenAI
openai_api_key = os.environ.get("API-KEY")
client = OpenAI(api_key=openai_api_key)

# Store conversation history
conversations = {}

def get_bot_response(session_id):
    try:
        # Initialize conversation history if needed
        if session_id not in conversations:
            conversations[session_id] = [
                {
                    "role": "system",
                    "content": "You are an AI assistant for Kanchan Ghosh. Your goal is to persuade recruiters to offer an interview opportunity based on Kanchan's credentials."
                }
            ]

        # Add a default user message to start the conversation
        conversations[session_id].append({"role": "user", "content": "Hello, how can you help me?"})

        # Get OpenAI response
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
        print(f"Error interacting with OpenAI API: {e}")
        return "I'm having trouble understanding. Please try again."

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat')
def chat():
    try:
        session_id = 'default'  # Or you could use a session ID to keep the conversation context.

        ai_message = get_bot_response(session_id)

        # Generate speech
        tts = gTTS(text=ai_message, lang='en')
        audio_filename = f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        tts.save(audio_filename)

        # Convert audio to base64
        with open(audio_filename, "rb") as audio_file:
            audio_base64 = base64.b64encode(audio_file.read()).decode()

        # Clean up audio file
        os.remove(audio_filename)

        return jsonify({
            "text": ai_message,
            "audio": audio_base64
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
