from flask import Flask, request, redirect, render_template_string
import json, os, re, random, datetime

app = Flask(__name__)
DATA_FILE = "messages.json"
LOG_FILE = "flagged_messages.txt"
ADMIN_SECRET = "sunflower42"  # Change this!

AVATARS = [
    "🐶 Dog", "🐱 Cat", "🐦 Bird", "🦊 Fox", "🐰 Bunny", "🐢 Turtle",
    "🧙 Wizard", "🤖 Robot", "🦄 Unicorn", "🐸 Frog", "🐻 Bear", "🐨 Koala"
]

AFFIRMATIONS = [
    "You are enough just as you are.",
    "One small step is still progress.",
    "This moment matters, and so do you.",
    "You're not alone — someone cares.",
    "Kindness begins with yourself.",
    "You're doing your best, and that's okay.",
    "Healing is not linear — keep going.",
    "You bring something special to the world."
]

BAD_PHRASES = {
    "kill myself": "talk to someone you trust",
    "end it all": "pause and breathe — you're not alone",
    "hate myself": "struggling is human, and you deserve care",
    "i want to die": "you matter — please talk to someone you trust",
    "die": "take a break — the world needs you",
    "useless": "you have value even if you can't see it now",
    "worthless": "you matter more than you think",
    "go to hell": "take a deep breath and respond kindly",
    "stupid": "silly",
    "idiot": "goofball",
    "dumb": "quirky",
    "crap": "crud",
    "damn": "darn",
    "hell": "heck",
    "shut up": "please be quiet",
    "bastard": "grumpy noodle",
    "freak": "unique soul",
    "fat": "cuddly"
}

TRIGGER_WORDS = list(BAD_PHRASES.keys()) + [
    "kill", "cut", "self-harm", "hang", "jump", "shoot", "stab", "suicide", "burn", "bleed", "hate", "depressed"
]

def censor_message(text):
    for bad, replacement in BAD_PHRASES.items():
        text = re.sub(rf'\b{re.escape(bad)}\b', replacement, text, flags=re.IGNORECASE)
    return text

def is_trigger(text):
    lowered = text.lower()
    return any(word in lowered for word in TRIGGER_WORDS)

def log_to_file(timestamp, avatar, raw):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} | {avatar} | {raw}\n")

def get_affirmation():
    return random.choice(AFFIRMATIONS)

TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>💬 Cozy Support Board</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(to bottom right, #fceabb, #f8b500); margin: 0; padding: 0; }
        .container { max-width: 700px; margin: 40px auto; background: #fffbea; padding: 30px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        h1 { text-align: center; color: #4a3f35; margin-bottom: 20px; }
        form { display: flex; flex-direction: column; gap: 10px; margin-bottom: 30px; }
        textarea, select { padding: 12px; border: 1px solid #ddd; border-radius: 10px; font-size: 1em; background: #fffef5; }
        button { padding: 10px; font-size: 1em; border: none; border-radius: 10px; background-color: #ffb347; color: white; font-weight: bold; cursor: pointer; transition: background 0.2s ease; }
        button:hover { background-color: #ff9933; }
        .post { background: #fff6d6; padding: 15px; border-left: 6px solid #ffd580; margin-bottom: 12px; border-radius: 10px; font-size: 1em; position: relative; }
        .persona { font-weight: bold; color: #6c584c; margin-right: 10px; display: inline-block; }
        .reaction, .report { font-size: 0.9em; cursor: pointer; margin-left: 10px; color: #999; }
        .reaction:hover, .report:hover { color: #333; }
        .affirmation { font-size: 0.85em; font-style: italic; color: #444; margin-top: 5px; }
        .footer { font-size: 0.85em; color: #6e584d; border-top: 1px dashed #d4ba94; padding-top: 15px; margin-top: 40px; }
        .log { white-space: pre-wrap; background: #fff6d6; padding: 10px; border-radius: 10px; }
    </style>
    <script>
        function setupEnterSubmit() {
            const textarea = document.querySelector("textarea");
            textarea.addEventListener("keypress", function(e) {
                if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    this.form.submit();
                }
            });
        }
        function addReaction(el) {
            const count = el.getAttribute("data-count");
            el.setAttribute("data-count", parseInt(count)+1);
            el.innerText = "❤️ " + (parseInt(count)+1);
        }
        window.onload = setupEnterSubmit;
    </script>
</head>
<body>
    <div class="container">
        <h1>💬 Cozy Support Board</h1>
        <form method="POST" action="/post">
            <textarea name="message" placeholder="What's on your mind?" required maxlength="500"></textarea>
            <select name="avatar" required>
                {% for a in avatars %}
                <option value="{{a}}">{{a}}</option>
                {% endfor %}
            </select>
            <button type="submit">Post</button>
        </form>

        {% for msg in messages %}
            <div class="post">
                <span class="persona">{{ msg.persona }}</span>{{ msg.text }}
                <div class="affirmation">🌟 {{ msg.affirmation }}</div>
                <span class="reaction" onclick="addReaction(this)" data-count="0">❤️ 0</span>
                <span class="report" onclick="alert('Post flagged.')">🚩 Report</span>
            </div>
        {% endfor %}

        <div class="footer">
            <strong>✨ Community Guidelines:</strong><br>
            Be kind. Stay anonymous. No bullying, spamming, or sharing private info.<br>
            Self-harm content is translated for safety. You are not alone. 💛<br><br>
            By posting, you agree to the <em>Support Board Terms of Use</em>.
        </div>
    </div>
</body>
</html>
'''

def load_messages():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_messages(messages):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

@app.route("/")
def index():
    messages = load_messages()[::-1]
    return render_template_string(TEMPLATE, messages=messages, avatars=AVATARS)

@app.route("/post", methods=["POST"])
def post():
    text = request.form.get("message", "").strip()
    avatar = request.form.get("avatar", "").strip()
    if not text or avatar not in AVATARS:
        return redirect("/")

    messages = load_messages()
    clean = censor_message(text)
    affirm = get_affirmation()
    messages.append({"text": clean, "persona": avatar, "affirmation": affirm})
    save_messages(messages)

    if is_trigger(text):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_to_file(now, avatar, text)

    return redirect("/")

@app.route(f"/admin-log-{ADMIN_SECRET}")
def admin_log():
    if not os.path.exists(LOG_FILE):
        return "No logs found."
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    return f"<pre class='log'>{content}</pre><br><a href='/clear-log-{ADMIN_SECRET}'>Clear log</a>"

@app.route(f"/clear-log-{ADMIN_SECRET}")
def clear_log():
    open(LOG_FILE, "w", encoding="utf-8").close()
    return "Log cleared."

if __name__ == "__main__":
    app.run(debug=True)

import os
port = int(os.environ.get("PORT", 10000))
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)