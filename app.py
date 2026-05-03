import os
import requests
from flask import Flask, request, jsonify
from google import genai  # 🔥 NEW GOOGLE SDK

app = Flask(__name__)

# --- 1. THE VAULT ---
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "rishav_monk_mode_123")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "").strip()
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# Initialize New Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY)

# --- 2. THE BRAIN ---
aero_persona = """
You are Aero Bot, the elite AI automation consultant and sales closer for Aero Agency.
Your tone is highly professional, stoic, confident, and direct. 
CRITICAL RULE: Always analyze the user's language and mirror it perfectly.
- If they speak English, reply in English.
- If they speak Hindi, reply in Hindi.
- If they use Hinglish (Hindi written in the English alphabet), you MUST reply in natural, highly professional Hinglish.
Keep your responses concise, highly structured, and focused on business ROI.
"""

# --- 3. HEALTH CHECK ---
@app.route('/', methods=['GET'])
def home():
    return "Aero Bot Server is Running Perfectly! 🚀", 200

# --- 4. THE MASTER TRAFFIC CONTROLLER ---
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # GET: Meta Webhook Verification
    if request.method == 'GET':
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Forbidden", 403

    # POST: Incoming Messages
    if request.method == 'POST':
        data = request.get_json()

        # 🚨 X-RAY VISION: Print everything beautifully in logs
        print("\n" + "="*50)
        print("🚨 RAW PAYLOAD RECEIVED FROM META:")
        print(data)
        print("="*50 + "\n")

       # --- ROUTE A: INSTAGRAM ---
if data.get("object") == "instagram":

    try:

        for entry in data.get("entry", []):

            for change in entry.get("changes", []):

                field = change.get("field")
                value = change.get("value", {})

                print("🔥 INSTAGRAM CHANGE:")
                print(change)

                # =========================
                # COMMENT EVENTS
                # =========================
                if field == "comments":

                    comment_text = value.get("text", "")
                    comment_id = value.get("id")

                    user = value.get("from", {})
                    username = user.get("username")
                    user_id = user.get("id")

                    print(f"💬 COMMENT: {comment_text}")
                    print(f"👤 USERNAME: {username}")

                    TRIGGERS = [
                        "price",
                        "details",
                        "info",
                        "interested",
                        "dm",
                        "send"
                    ]

                    # FILTER COMMENTS
                    if any(
                        word in comment_text.lower()
                        for word in TRIGGERS
                    ):

                        # =========================
                        # PUBLIC COMMENT REPLY
                        # =========================
                        reply_url = f"https://graph.facebook.com/v25.0/{comment_id}/replies"

                        reply_headers = {
                            "Authorization": f"Bearer {IG_ACCESS_TOKEN}"
                        }

                        reply_payload = {
                            "message": "Sent you details in DM 👌"
                        }

                        reply_response = requests.post(
                            reply_url,
                            headers=reply_headers,
                            data=reply_payload
                        )

                        print("✅ COMMENT REPLY SENT")
                        print(reply_response.text)

                        # =========================
                        # SEND DM
                        # =========================
                        dm_url = "https://graph.facebook.com/v25.0/me/messages"

                        dm_headers = {
                            "Authorization": f"Bearer {IG_ACCESS_TOKEN}",
                            "Content-Type": "application/json"
                        }

                        dm_payload = {
                            "recipient": {
                                "id": user_id
                            },
                            "message": {
                                "text": (
                                    "Hey 👋\n\n"
                                    "Thanks for your comment.\n\n"
                                    "Aapko details WhatsApp pe chahiye?"
                                )
                            }
                        }

                        dm_response = requests.post(
                            dm_url,
                            headers=dm_headers,
                            json=dm_payload
                        )

                        print("✅ DM SENT")
                        print(dm_response.text)

                # =========================
                # DM EVENTS
                # =========================
                elif field == "messages":

                    if "message" in value:

                        sender = value.get("from")
                        message_data = value.get("message", {})

                        user_msg = message_data.get("text")

                        print(f"📩 IG DM: {user_msg}")

    except Exception as e:
        print(f"❌ IG Processing Error: {e}")

        # --- ROUTE B: WHATSAPP ---
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
                                
                                print(f"✅ WA MESSAGE EXTRACTED: '{user_msg}' from {from_number}")
                                
                                # Generate AI reply using New SDK
                                response = client.models.generate_content(
                                    model='gemini-2.5-flash',
                                    contents=f"{aero_persona}\nUser: {user_msg}"
                                )
                                bot_reply = response.text
                                print(f"🤖 AI REPLY GENERATED: {bot_reply}")
                                
                                # Send to WhatsApp API
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
                                meta_response = requests.post(url, headers=headers, json=payload)
                                print(f"📤 META API STATUS: {meta_response.status_code} - {meta_response.text}")
            except Exception as e:
                print(f"❌ WA Processing Error: {e}")

        return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 10000))
)
  
    
    