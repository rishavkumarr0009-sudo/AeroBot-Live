from flask import Flask, request, jsonify
import google.generativeai as genai
import requests
import os


app = Flask(__name__)

# --- Meta Configuration ---
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "rishav_monk_mode_123")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "").strip()

# --- AI Configuration ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
genai.configure(api_key=GEMINI_API_KEY)

# Define the Bot's Identity and Strict Rules (The System Prompt)
aero_persona = """
You are Aero Bot, the elite AI automation consultant and sales closer for Aero Agency.
Your tone is highly professional, stoic, confident, and direct. 
CRITICAL RULE: Always reply in the exact language the user speaks. If they speak English, reply in English. If they speak Hindi, reply in Hindi. If they use Hinglish (Hindi written in English alphabet), you must reply in natural, professional Hinglish.
Keep your responses concise and highly structured.
"""

# Initialize the 2.5 Flash model WITH the new persona injected
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction=aero_persona
)


# Outbound Messaging Engine
def send_whatsapp_message(recipient_number, message_text, phone_number_id):
    url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_number,
        "type": "text",
        "text": {"body": message_text}
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print(f"📤 SUCCESS: Message sent back to WhatsApp!")
        else:
            print(f"❌ ERROR: Failed to send. Meta responded with: {response.text}")
    except Exception as e:
        print(f"❌ CRITICAL ERROR during outbound request: {e}")

# 1. Meta verification route
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook Verified successfully!")
        return challenge, 200
    else:
        return "Verification failed", 403

# 2. Webhook endpoint to receive incoming WhatsApp messages
@app.route('/webhook', methods=['POST'])
def receive_message():
    data = request.json

    try:
        if 'object' in data and data['object'] == 'whatsapp_business_account':
            entry = data['entry'][0]
            changes = entry['changes'][0]
            value = changes['value']

            if 'messages' in value:
                message = value['messages'][0]
                
                if message['type'] == 'text':
                    sender_number = message['from']
                    message_text = message['text']['body']
                    # Dynamically extracting your test bot's phone number ID
                    phone_number_id = value['metadata']['phone_number_id']

                    print("\n" + "="*40)
                    print(f"📩 NEW MESSAGE RECEIVED!")
                    print(f"📱 From: {sender_number}")
                    print(f"💬 User says: {message_text}")
                    print("-" * 40)
                    print("🤖 Generating AI Response...")
                    
                    # AI Processing
                    response = model.generate_content(message_text)
                    bot_reply = response.text

                    print(f"🧠 AI Reply: \n{bot_reply}")
                    print("-" * 40)
                    print("🚀 Routing reply back to Meta API...")
                    
                    # Triggering the outbound message
                    send_whatsapp_message(sender_number, bot_reply, phone_number_id)
                    
                    print("="*40 + "\n")

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"Error parsing the webhook payload: {e}")
        return jsonify({"status": "error"}), 500

if __name__ == "__main__":
    print("🚀 Server is running on port 5000...")
    app.run(port=5000) 
    