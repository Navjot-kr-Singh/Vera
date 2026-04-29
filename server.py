from flask import Flask, request, jsonify, send_from_directory
from message_engine import MessageEngine
from learning_tracker import LearningTracker
from state_manager import StateManager
import os
from datetime import datetime

app = Flask(__name__, static_folder='static')
engine = MessageEngine()
tracker = LearningTracker()
state = StateManager()

# Indian festival calendar: (month, day) -> festival name
FESTIVAL_CALENDAR = {
    (1, 14): "Makar Sankranti",
    (1, 26): "Republic Day",
    (3, 25): "Holi",
    (3, 30): "Eid al-Fitr",
    (4, 14): "Baisakhi",
    (8, 15): "Independence Day",
    (10, 2):  "Gandhi Jayanti",
    (10, 20): "Diwali",
    (10, 24): "Dussehra",
    (11, 5):  "Bhai Dooj",
    (12, 25): "Christmas",
    (12, 31): "New Year's Eve",
}

def _detect_festival():
    now = datetime.now()
    return FESTIVAL_CALENDAR.get((now.month, now.day))

def _detect_time_of_day():
    hour = datetime.now().hour
    if 6 <= hour < 11:
        return "morning"
    elif 11 <= hour < 15:
        return "lunch time"
    elif 15 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 21:
        return "evening"
    else:
        return "night"

def _detect_day_type():
    return "weekend" if datetime.now().weekday() >= 5 else "weekday"

# --- Judge /v1 API Implementation ---

@app.route('/v1/healthz', methods=['GET'])
def healthz():
    return jsonify({"status": "ok"})

@app.route('/v1/metadata', methods=['GET'])
def metadata():
    return jsonify({
        "team_name": "Antigravity",
        "model": "Hybrid Heuristic Engine v2.0"
    })

@app.route('/v1/context', methods=['POST'])
def push_context():
    data = request.json
    scope = data.get("scope")
    context_id = data.get("context_id")
    payload = data.get("payload")
    state.upsert_context(scope, context_id, payload)
    return jsonify({"accepted": True})

@app.route('/v1/tick', methods=['POST'])
def tick():
    data = request.json
    available_triggers = data.get("available_triggers", [])
    actions = []
    
    for tid in available_triggers:
        trigger_context = state.get_trigger(tid)
        if not trigger_context: continue
        
        scope = trigger_context.get("scope")
        kind = trigger_context.get("kind")
        payload = trigger_context.get("payload", {})
        
        # Resolve Merchant and Category
        mid = payload.get("merchant_id")
        if not mid:
             if state.data["merchants"]:
                 mid = list(state.data["merchants"].keys())[0]
        
        merchant_context = state.get_merchant(mid)
        cat_slug = merchant_context.get("category_slug", "default")
        category_context = state.get_category(cat_slug)
        
        customer_context = None
        if scope == "customer":
            cid = payload.get("customer_id")
            customer_context = state.get_customer(cid)
            
        # Generate using engine
        gen_result = engine.generate(
            category=cat_slug,
            merchant_name=merchant_context.get("identity", {}).get("name", "Your Business"),
            offer="", 
            trigger=kind,
            customer_type=customer_context.get("state", "default") if customer_context else "default",
            full_context={
                "merchant": merchant_context,
                "category": category_context,
                "trigger": trigger_context,
                "customer": customer_context
            }
        )
        
        # Pick the best variation
        best_mode = gen_result["modes"][0]
        
        actions.append({
            "trigger_id": tid,
            "body": best_mode["message"],
            "cta": best_mode.get("cta", "Order now!"),
            "send_as": "vera" if scope == "merchant" else "merchant_on_behalf"
        })
        
    return jsonify({"actions": actions})

@app.route('/v1/reply', methods=['POST'])
def reply():
    data = request.json
    message = data.get("message", "").lower()
    
    # Auto-reply detection
    if any(w in message for w in ["thank you for contacting", "respond shortly", "automated message", "busy right now"]):
         return jsonify({
            "action": "end",
            "body": "Detected automated response. Ending session."
        })

    if any(w in message for w in ["stop", "spam", "useless", "don't", "remove"]):
        return jsonify({
            "action": "end",
            "body": "I apologize for the intrusion. I will stop messaging you immediately."
        })
    
    if any(w in message for w in ["ok", "sure", "lets", "how", "next", "proceed", "yes"]):
        return jsonify({
            "action": "send",
            "body": "Done! I have initialized the campaign. You can proceed to the dashboard to see live performance. Next steps are ready.",
            "cta": "Go to Dashboard"
        })
        
    return jsonify({
        "action": "send",
        "body": "I understand. Many merchants in your area are seeing high engagement with this approach. Would you like to try a small test run?",
        "cta": "Start Test"
    })

# --- Demo UI Routes ---

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/context', methods=['GET'])
def get_context():
    time_of_day = _detect_time_of_day()
    day_type = _detect_day_type()
    festival = _detect_festival()

    if festival:
        suggested_trigger = "festival"
    elif time_of_day == "lunch time":
        suggested_trigger = "lunch time"
    elif day_type == "weekend":
        suggested_trigger = "weekend"
    elif time_of_day in ("evening", "night"):
        suggested_trigger = "payday"
    else:
        suggested_trigger = "default"

    return jsonify({
        "time_of_day": time_of_day,
        "day_type": day_type,
        "festival": festival,
        "suggested_trigger": suggested_trigger,
        "current_time": datetime.now().strftime("%I:%M %p")
    })

@app.route('/api/generate', methods=['POST'])
def generate_message():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    category = data.get('category', '')
    merchant_name = data.get('merchant_name', 'Your Business')
    offer = data.get('offer', 'great deals')
    trigger = data.get('trigger', '')
    customer_context = data.get('customer_context', '')
    tone_style = data.get('tone_style', 'default')

    learning_insight = tracker.get_insight(category, trigger)
    boost_mode_id = learning_insight["boost_mode_id"] if learning_insight else None

    result = engine.generate(
        category, merchant_name, offer, trigger,
        customer_context, tone_style, boost_mode_id
    )

    tracker.record(category, trigger, result.get("modes", []))
    result["learning_insight"] = learning_insight

    return jsonify(result)

if __name__ == '__main__':
    # Use port 8000 as configured in judge_simulator
    print("Starting AI Message Engine server on port 8000...")
    app.run(host='0.0.0.0', port=8000, debug=True)
