import os
import sys
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import google.generativeai as genai
from dotenv import load_dotenv
import json

# ------------------ APP CONFIG ------------------ #
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, 'templates')
static_dir = os.path.join(base_dir, 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = "your_secret_key"

app.config['UPLOAD_FOLDER'] = os.path.join(static_dir, 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Add "pages" directory for imports
sys.path.append(os.path.join(base_dir, 'pages'))


# ------------------ ROUTES ------------------ #

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# ------------------ CUSTOM MODULES ------------------ #
from pages.face_detector import detect_face_shape
import pages.undertone_detector as undertone_detector
import pages.body_detector as body_detector

body_detector = body_detector.BodyDetector()

# Temporary in-memory user DB
users = {}

# ------------------ AUTH ------------------ #

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if email in users and users[email]['password'] == password:
            session['user'] = users[email]['name']
            flash('Login successful!', 'success')
            return redirect(url_for('home'))

        flash('Invalid email or password.', 'error')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        if email in users:
            flash('Email already registered.', 'error')
            return redirect(url_for('signup'))

        users[email] = {'name': name, 'password': password}
        session['user'] = name

        flash('Account created successfully!', 'success')
        return redirect(url_for('home'))

    return render_template('signup.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


# ------------------ FACE SHAPE DETECTOR ------------------ #
@app.route("/faces")
def faces():
    return render_template("faces.html")


# ------------------ UNDERTONE DETECTOR ------------------ #

@app.route('/undertone.html', methods=['GET', 'POST'])
def undertone():
    if request.method == 'POST':
        file = request.files.get('file')

        if not file or file.filename == "":
            return "No file uploaded", 400

        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        image_url = url_for('static', filename=f"uploads/{filename}")

        undertone_value, best_colors, avoid_colors = undertone_detector.detect_undertone(save_path)

        return render_template(
            'undertone_result.html',
            undertone=undertone_value,
            best_colors=best_colors,
            avoid_colors=avoid_colors,
            image_url=image_url
        )

    return render_template('undertone_upload.html')


# ------------------ BODY SHAPE ANALYZER ------------------ #

@app.route('/start-analysis', methods=['GET', 'POST'])
def start_analysis():
    if request.method == 'POST':
        try:
            bust = float(request.form['bust'])
            waist = float(request.form['waist'])
            hips = float(request.form['hips'])
        except (ValueError, KeyError):
            return "Invalid input. Please enter numeric values.", 400

        result = body_detector.run_analysis(bust, waist, hips)
        return render_template('body_result.html', result=result)

    return render_template('body_input.html')

# ------------------ CHATBOT PAGE ------------------ #

@app.route("/fashion-ai", methods=["GET", "POST"])
def fashion_ai():
    if request.method == "POST":
        file = request.files.get("image")
        shape = request.form.get("shape")
        palette = request.form.get("palette")
        undertone = request.form.get("undertone")

        context = {"image_url": "", "shape": shape, "palette": palette, "undertone": undertone}

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            context["image_url"] = save_path

        recommendations = ask_gemini_for_recommendations(context)

        return render_template("result.html", context=context, recommendations=recommendations)

    return render_template("index.html")


@app.post("/api/chat")
def chat():
    data = request.json
    user_msg = data.get("message", "")

    prompt = f"""
You are ChicBot.

RULES:
- Max 4–5 short lines.
- No markdown.
- No bold.
- No emojis.
- No long paragraphs.
- No questions unless necessary.
- Give a direct fashion suggestion only.

User: {user_msg}
"""

    response = model.generate_content(
        prompt,
        generation_config={
            "max_output_tokens": 60,
            "temperature": 0.4,
            "top_p": 0.8
        }
    )

    reply = response.text.strip()
    return jsonify({"reply": reply})



@app.route("/ai-stylist-chat")
def ai_stylist_chat():
    return render_template("chat.html")

# ------------------ GEMINI AI SETUP ------------------ #

# Load environment variables from .env
load_dotenv()
service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_path

# Set path to your service account JSON key
service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not service_account_path or not os.path.exists(service_account_path):
    raise ValueError("❌ Service account JSON not found! Set GOOGLE_APPLICATION_CREDENTIALS in .env")

# Set environment variable for Google authentication
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_path

# Configure Gemini AI client (no API key needed)
genai.configure()

# Initialize the model
model = genai.GenerativeModel("gemini-1.5-flash")

# --------- AI FASHION STYLIST --------- #
def ask_gemini_for_recommendations(context: dict):
    prompt = f"""
You are ChicBot, an AI Fashion Stylist.

IMPORTANT RULES:
- Do NOT use bullets, markdown, lists, emojis, symbols, or formatting.
- Output MUST be valid JSON only.
- Only give a plain JSON array. No extra text.
- Each description must be short, cute, and maximum 5 lines.

User details:
- Face Shape: {context.get('shape')}
- Color Palette: {context.get('palette')}
- Undertone: {context.get('undertone')}

Generate EXACTLY 3 outfit recommendations.
Descriptions must be brief and feel like a friendly stylist talking in short lines.

Return ONLY a JSON array like:

[
  {
    "look_name": "Soft Girl Brunch",
    "description": "A pastel cami dress with soft curls. Light textures that flatter your tone. Simple jewelry for a fresh vibe. Cute and easy for daytime.",
    "image": "AI generated outfit aesthetic"
  }
]
"""


    # Generate content using Gemini
    response = model.generate_content(prompt)
    raw = response.text.strip().replace("*", "").replace("_", "")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        return [{
            "look_name": "AI Suggestion",
            "description": raw,
            "image": "https://source.unsplash.com/600x800/?fashion,outfit"
        }]


# ------------------ VIEW LOOKS ------------------ #

@app.route('/view_looks')
def view_looks():
    selected_shape = request.args.get("shape")   # ← read shape from URL
    looks_data = {
        "Hourglass": [
            {"name": "Wrap Dress", "desc": "Wrap dresses highlight the waist", "img": "wrap_dress.jpeg",
             "link": "https://www.amazon.in/s?k=wrap+dress+for+women"},
            {"name": "High-Waist Bottoms", "desc": "Fitted tops with high-waist bottoms", "img": "high_waist.jpeg",
             "link": "https://www.amazon.in/s?k=high+waist+jeans+for+women"},
            {"name": "Statement Belt", "desc": "Belts to accentuate curves", "img": "belt.jpeg",
             "link": "https://www.amazon.in/s?k=belts+for+women"},
            {"name": "V-Neck Top", "desc": "V-necklines elongate your neck", "img": "vneck.jpeg",
             "link": "https://www.amazon.in/s?k=v+neck+top+for+women"},
        ],
        "Apple": [
            {"name": "Empire Dress", "desc": "Empire waist balances midsection", "img": "empire_dress.jpeg",
             "link": "https://www.amazon.in/s?k=empire+waist+dress"},
            {"name": "A-line Skirt", "desc": "Works well for apple body shape", "img": "aline_skirt.jpeg",
             "link": "https://www.amazon.in/s?k=a+line+skirt+for+women"},
            {"name": "Flowy Top", "desc": "Flowy tops add balance", "img": "flowy_top.jpeg",
             "link": "https://www.amazon.in/s?k=flowy+tops+for+women"},
            {"name": "Structured Jacket", "desc": "Defines shoulders and adds structure", "img": "structured_jacket.jpeg",
             "link": "https://www.amazon.in/s?k=structured+jacket+for+women"},
        ],
        "Pear": [
            {"name": "A-Line Skirt", "desc": "Enhances waist, reduces hips", "img": "aline_skirt.jpeg",
             "link": "https://www.amazon.in/s?k=a+line+skirts+for+women"},
            {"name": "Off-Shoulder Top", "desc": "Adds balance to your upper body", "img": "off_shoulder.jpeg",
             "link": "https://www.amazon.in/s?k=off+shoulder+top+for+women"},
            {"name": "High-Waist Pants", "desc": "Elongate the legs", "img": "high_waist_pants.jpeg",
             "link": "https://www.amazon.in/s?k=high+waist+pants+for+women"},
            {"name": "Short Jacket", "desc": "Ends above hips for balance", "img": "short_jacket.jpeg",
             "link": "https://www.amazon.in/s?k=short+jacket+for+women"},
        ],
        "Rectangle": [
            {"name": "Peplum Top", "desc": "Adds waist definition", "img": "peplum.jpeg",
             "link": "https://www.amazon.in/s?k=peplum+tops+for+women"},
            {"name": "Waist Belt", "desc": "Defines waistline", "img": "waist_belt.jpeg",
             "link": "https://www.amazon.in/s?k=waist+belts+for+women"},
            {"name": "Ruffled Top", "desc": "Adds volume to upper body", "img": "ruffled.jpeg",
             "link": "https://www.amazon.in/s?k=ruffled+top+for+women"},
            {"name": "Fit-and-Flare Dress", "desc": "Creates curves", "img": "fit_flare.jpeg",
             "link": "https://www.amazon.in/s?k=fit+and+flare+dress+for+women"},
        ],
        "Inverted Triangle": [
            {"name": "V-Neck Blouse", "desc": "Softens broad shoulders", "img": "vneck_blouse.jpeg",
             "link": "https://www.amazon.in/s?k=v+neck+blouse+for+women"},
            {"name": "Light Bottoms", "desc": "Balances top-heavy shape", "img": "light_bottoms.jpeg",
             "link": "https://www.amazon.in/s?k=light+colored+pants+for+women"},
            {"name": "Flowy Skirt", "desc": "Adds volume to lower body", "img": "flowy_skirt.jpeg",
             "link": "https://www.amazon.in/s?k=flowy+skirts+for+women"},
            {"name": "Simple Top", "desc": "Minimal embellishments", "img": "simple_top.jpeg",
             "link": "https://www.amazon.in/s?k=simple+top+for+women"},
        ],
    }

    if selected_shape and selected_shape in looks_data:
        return render_template(
            "view_looks.html", 
            all_looks={selected_shape: looks_data[selected_shape]},
            selected_shape=selected_shape
        )

    # If no shape passed → show everything
    return render_template(
        "view_looks.html",
        all_looks=looks_data,
        selected_shape=None
    )


# ------------------ RUN APP ------------------ #

if __name__ == "__main__":
    import webbrowser
    import threading

    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000")

    threading.Timer(1, open_browser).start()

    app.run(debug=True, use_reloader=False)
