import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# --- 1. THE VAULT (Server fetches keys dynamically) ---
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "rishav_monk_mode_123")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "").strip()
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# Initialize Google Gemini AI
genai.configure(api_key=GEMINI_API_KEY)

# --- 2. THE BRAIN (System Instructions & Persona) ---
aero_persona = """
You are Aero Bot, the elite AI automation consultant and sales closer for Aero Agency.
Your tone is highly professional, stoic, confident, and direct. 
CRITICAL RULE: Always analyze the user's language and mirror it perfectly.
- If they speak English, reply in English.
- If they speak Hindi, reply in Hindi.
- If they use Hinglish (Hindi written in the English alphabet), you MUST reply in natural, highly professional Hinglish.
Keep your responses concise, highly structured, and focused on business ROI.
"""

# --- 3. THE TRAFFIC CONTROLLER (Webhook logic for IG & WA) ---
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # GET Request: Meta Webhook Verification
    if request.method == 'GET':
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Forbidden", 403

    # POST Request: Processing incoming messages
    if request.method == 'POST':
        data = request.get_json()

        # --- ROUTE A: Handle INSTAGRAM Messages ---
        if data.get("object") == "instagram":
            try:
                for entry in data['entry']:
                    for messaging_event in entry.get('messaging', []):
                        if 'message' in messaging_event and 'text' in messaging_event['message']:
                            user_msg = messaging_event['message']['text']
                            print(f"🔥 IG MESSAGE RECEIVED: {user_msg}")
                            # TODO: Add Gemini AI reply and number extraction logic here
            except Exception as e:
                print(f"IG Error: {e}")

        # --- ROUTE B: Handle WHATSAPP Messages ---
        elif data.get("object") == "whatsapp_business_account":
            try:
                for entry in data['entry']:
                    for change in entry['changes']:
                        value = change['value']
                        if 'messages' in value:
                            message = value['messages'][0]
                            if message['type'] == 'text':
                                phone_number_id = value['metadata']['phone_number_id']
                                from_number = message['from']
                                user_msg = message['text']['body']
                                
                                print(f"✅ WA MESSAGE RECEIVED: {user_msg}")
                                
                                # Generate AI response using Gemini
                                model = genai.GenerativeModel('gemini-2.5-flash')
                                response = model.generate_content(aero_persona + "\nUser: " + user_msg)
                                bot_reply = response.text
                                
                                # Send reply back to WhatsApp via Meta Graph API
                                url = f"https://graph.facebook.com/v25.0/{phone_number_id}/messages"
                                headers = {
                                    "Authorization": f"Bearer {META_ACCESS_TOKEN}",
                                    "Content-Type": "application/json"
                                }
                                payload = {
                                    "messaging_product": "whatsapp",
                                    "to": from_number,
                                    "text": {"body": bot_reply}
                                }
                                requests.post(url, headers=headers, json=payload)
            except Exception as e:
                print(f"WA Error: {e}")

        return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(port=10000, debug=True)
    