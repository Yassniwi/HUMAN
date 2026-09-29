import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

from chatbot_config import MODEL_NAME, SYSTEM_PROMPT

load_dotenv()

app = Flask(__name__)

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


def build_contents(history, message):
    """Convert chat history and the new message into Gemini contents."""
    contents = []
    for item in history:
        role = "user" if item.get("role") == "user" else "model"
        text = str(item.get("text", "")).strip()
        if text:
            contents.append(
                types.Content(role=role, parts=[types.Part.from_text(text=text)])
            )
    contents.append(
        types.Content(role="user", parts=[types.Part.from_text(text=message)])
    )
    return contents


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    if client is None:
        return jsonify({"error": "GEMINI_API_KEY is missing in the .env file."}), 500

    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Please enter a message."}), 400

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=build_contents(history, message),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.4,
            ),
        )
        return jsonify({"reply": response.text})
    except Exception as error:
        return jsonify({"error": f"Something went wrong: {error}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
