from flask import Flask, render_template, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
import cv2
import os
import uuid

UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'
ALLOWED_EXTENSIONS = {'png', 'webp', 'jpg', 'jpeg', 'gif'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here_change_this_in_production!'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['STATIC_FOLDER'] = STATIC_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def processImage(filename, operation):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        img = cv2.imread(file_path)
        if img is None:
            return None, "Failed to load image."
    except Exception as e:
        return None, f"Error reading image: {e}"

    name, ext = os.path.splitext(filename)
    unique_filename = f"{name}_{uuid.uuid4().hex}{ext}"
    newFilename_path = os.path.join(app.config['STATIC_FOLDER'], unique_filename)

    if operation == "cwebp":
        newFilename_path = os.path.join(app.config['STATIC_FOLDER'], f"{name}_{uuid.uuid4().hex}.webp")
    elif operation == "cjpg":
        newFilename_path = os.path.join(app.config['STATIC_FOLDER'], f"{name}_{uuid.uuid4().hex}.jpg")
    elif operation == "cpng":
        newFilename_path = os.path.join(app.config['STATIC_FOLDER'], f"{name}_{uuid.uuid4().hex}.png")

    imgProcessed = None
    if operation == "cgray":
        imgProcessed = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    elif operation in {"cwebp", "cjpg", "cpng"}:
        imgProcessed = img
    else:
        return None, "Unsupported operation selected."

    try:
        cv2.imwrite(newFilename_path, imgProcessed)
        return os.path.basename(newFilename_path), None
    except Exception as e:
        return None, f"Failed to save processed image: {e}"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/edit", methods=["GET", "POST"])
def edit():
    if request.method == "POST":
        operation = request.form.get("operation")
        if not operation or operation == "Choose an Operation":
            flash('Please select an image editing operation.', 'danger')
            return redirect(url_for('edit'))

        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(url_for('edit'))

        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(url_for('edit'))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                file.save(file_path)
            except Exception as e:
                flash(f"Error saving file: {e}", 'danger')
                return redirect(url_for('edit'))

            processed_filename, error_message = processImage(filename, operation)
            if processed_filename:
                flash(f"Your image has been processed and is available <a href='{url_for('static', filename=processed_filename)}' target='_blank'>here</a>", 'success')
                return redirect(url_for('home'))
            else:
                flash(f"Image processing failed: {error_message or 'Unknown error'}", 'danger')
                return redirect(url_for('edit'))
        else:
            flash("Invalid file type. Allowed types are: png, webp, jpg, jpeg, gif", 'danger')
            return redirect(url_for('edit'))
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5001)
