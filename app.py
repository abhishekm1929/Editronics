from flask import Flask, render_template, request, flash, redirect, url_for # type: ignore
from werkzeug.utils import secure_filename
import cv2
import os
import uuid # To generate unique filenames

UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static' # Flask automatically serves files from this folder
ALLOWED_EXTENSIONS = {'png', 'webp', 'jpg', 'jpeg', 'gif'}

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here_change_this_in_production!' # IMPORTANT: Change this!
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['STATIC_FOLDER'] = STATIC_FOLDER # Store for easier access if needed

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def processImage(filename, operation):
    print(f"The operation is {operation} and filename is {filename}")
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        img = cv2.imread(file_path)
        if img is None:
            print(f"Error: Could not read image file: {file_path}")
            return None, "Failed to load image."
    except Exception as e:
        print(f"Error reading image: {e}")
        return None, "Error reading image."

    # Generate a unique filename for the processed image to avoid overwrites
    name, ext = os.path.splitext(filename)
    unique_filename = f"{name}_{uuid.uuid4().hex}{ext}" # Keep original extension or change based on operation

    newFilename_path = os.path.join(app.config['STATIC_FOLDER'], unique_filename)

    # Convert to appropriate extension based on operation for target formats
    if operation == "cwebp":
        newFilename_path = os.path.join(app.config['STATIC_FOLDER'], f"{name}_{uuid.uuid4().hex}.webp")
    elif operation == "cjpg":
        newFilename_path = os.path.join(app.config['STATIC_FOLDER'], f"{name}_{uuid.uuid4().hex}.jpg")
    elif operation == "cpng":
        newFilename_path = os.path.join(app.config['STATIC_FOLDER'], f"{name}_{uuid.uuid4().hex}.png")

    imgProcessed = None
    message = None

    match operation:
        case "cgray":
            imgProcessed = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        case "cwebp":
            imgProcessed = img # No processing, just saving in webp format
        case "cjpg":
            imgProcessed = img # No processing, just saving in jpg format
        case "cpng":
            imgProcessed = img # No processing, just saving in png format
        case _: # Default case for unsupported operations
            message = "Unsupported operation selected."
            print(message)
            return None, message

    if imgProcessed is not None:
        try:
            cv2.imwrite(newFilename_path, imgProcessed)
            # Return filename relative to STATIC_FOLDER for url_for
            return os.path.basename(newFilename_path), None
        except Exception as e:
            message = f"Failed to save processed image: {e}"
            print(message)
            return None, message
    
    return None, "Image processing failed for unknown reason."


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
        
        # Check if an operation was actually selected
        if not operation or operation == "Choose an Operation":
            flash('Please select an image editing operation.', 'danger')
            return redirect(url_for('edit')) # Redirect back to the form

        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(url_for('edit'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'danger')
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
                # Use url_for('static', filename=...) for proper URL generation
                flash(f"Your image has been processed and is available <a href='{url_for('static', filename=processed_filename)}' target='_blank'>here</a>", 'success')
                return redirect(url_for('home')) # Redirect to home or a success page
            else:
                flash(f"Image processing failed: {error_message or 'Unknown error'}", 'danger')
                return redirect(url_for('edit'))
        else:
            flash("Invalid file type. Allowed types are: png, webp, jpg, jpeg, gif", 'danger')
            return redirect(url_for('edit'))
            
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5001)