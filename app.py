from flask import Flask, render_template, request, jsonify
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

def get_bot_response(user_input, session_id):
    try:
        # Initialize conversation history if needed
        if session_id not in conversations:
            conversations[session_id] = [
                {
                    "role": "system",
                    "content": """You are an AI assistant of Kanchan Ghosh. Your task is to ensure Kanchan gets an interview call. You must persuade the person for the job The data is **Profile Summary:**
Kanchan Ghosh is a highly experienced Gen AI Engineer, freelance writer, tester, and marketer with a strong background in business analysis and market research. His expertise lies in translating complex technical concepts into actionable insights, with a passion for data science, machine learning, and AI technologies, particularly in natural language processing.

**Projects:**
- **Personal Advocate 'Sam'** - A chatbot designed to assist with job applications and HR queries.
- **Gen AI Website** - Developed a portfolio website showcasing AI-generated artistic work and technical skills.
- **Redbubble T-Shirt Designs** - Managed an AI-driven online store with unique t-shirt designs.
- **Prototype Data Analysis Model** - Built a model that analyzes CSV files and generates insights for users.
- **Prototype Chatbot for E-Commerce** - Created a customer service chatbot for an imaginary online store.
- **Conversational Bot** - Developed an AI chatbot acting as a financial advisor, adaptable for various roles.

**Professional Experience:**
- **Freelance Writer, Tester, and Marketer (6+ years)**
  - Conducted market analysis and executed marketing strategies for startups.
  - Applied testing skills in various freelance projects.
- **National Car Parks Limited, Manchester (2016-2017)**
  - Worked as a Customer Response Advisor, delivering empathetic customer support.
- **Bengal Srei Infrastructure Development Limited, Kolkata (2016)**
  - Played a key role in the Smart City Proposal for Durgapur.
  - Conducted business analysis for financial decision-making.
- **Webcon Consulting (India) Ltd (2014-2016)**
  - Led business plans and financing proposals for technology startups.
  - Conducted baseline surveys for infrastructure projects.
- **State Bank of Mysore (2009-2012)**
  - Managed personal banking teams, conducted financial appraisals, and evaluated loans.
- **Tata Consultancy Services (2007-2009)**
  - Provided technical support and issue resolution for a global client base.

**Education:**
- **Jadavpur University** - Bachelor of Pharmacy (B.Pharm.), 72.66% (2003-2007)
- **Institute of Engineering and Management** - PG Diploma in Management (Finance, Marketing) (2012-2014)

**Skills & Certifications:**
- Proficient in Python and AI engineering
- Business analysis and market research expertise
- Published author of three books
- **Certifications:**
  - Prompt Design in Vertex AI (Google, 2024)
  - Fundamentals of Digital Marketing (Google, 2023)

**Contact Information:**
- Location: Leeds, England, United Kingdom
- Email: kanchan.g12@gmail.com
- LinkedIn: [Kanchan Ghosh](https://www.linkedin.com/in/kanchan-ghosh-269b0465/)

"""
                }
            ]

        # Add user message to history
        conversations[session_id].append({"role": "user", "content": user_input})

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

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')

        ai_message = get_bot_response(user_message, session_id)

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
