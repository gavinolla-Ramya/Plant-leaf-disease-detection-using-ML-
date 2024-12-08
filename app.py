from __future__ import division, print_function
import os
import numpy as np
from flask import Flask, redirect, url_for, request, render_template
from werkzeug.utils import secure_filename
from keras.models import load_model
from keras_preprocessing.image import load_img, img_to_array
import sqlite3

# Define Flask app
app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load model and classes
MODEL_PATH = 'models/model_xception.h5'
CLASSES = {0: "Bacteria", 1: "Fungi", 2: "Nematodes", 3: "Normal", 4: "Virus"}
MODEL = load_model(MODEL_PATH)

# Utility function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Predict function
def model_predict(image_path, model):
    image = load_img(image_path, target_size=(224, 224))
    image = img_to_array(image) / 255.0
    image = np.expand_dims(image, axis=0)
    prediction = np.argmax(model.predict(image))
    return CLASSES.get(prediction, "Unknown"), "result.html"

# Routes
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/signup')
def signup():
    name = request.args.get('username', '')
    contact_no = request.args.get('CN', '')
    email = request.args.get('email', '')
    password = request.args.get('psw', '')

    with sqlite3.connect('signup.db') as con:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO `accounts` (`name`, `contact`, `email`, `password`) VALUES (?, ?, ?, ?)",
            (name, contact_no, email, password),
        )
    return render_template("login.html")

@app.route('/signin', methods=['POST'])
def signin():
    email = request.args.get('uname', '')
    password = request.args.get('psw', '')

    with sqlite3.connect('signup.db') as con:
        cur = con.cursor()
        cur.execute("SELECT `email`, `password` FROM `accounts` WHERE `email` = ? AND `password` = ?", (email, password))
        user = cur.fetchone()

    if user:
        return redirect(url_for('index'))
    else:
        return render_template("login.html")

@app.route('/register')
def register():
    return render_template("register.html")

@app.route('/index')
def index():
    return render_template("index.html")

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/predict2', methods=['POST'])
def predict2():
    if 'file' not in request.files:
        return "No file part", 400

    file = request.files['file']

    if file.filename == '' or not allowed_file(file.filename):
        return "Invalid file type. Only PNG, JPG, and JPEG are allowed.", 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    pred_class, output_page = model_predict(file_path, MODEL)

    # Fetch remedies from the database
    with sqlite3.connect('remedies.db') as con:
        cur = con.cursor()
        query_label = 'viruses' if pred_class == 'Virus' else pred_class
        cur.execute("SELECT `label` FROM `data2` WHERE `message` = ?", (query_label,))
        remedies = cur.fetchall()

    # Fallback for 'Normal'
    remedies =[r[0] for r in remedies]  if remedies else ['Normal Leaf']

    return render_template(output_page, pred_output=pred_class, remedies=remedies, img_src=file_path)

# Run the app
if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure upload folder exists
    app.run(debug=True)
