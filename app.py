from flask import Flask, render_template, request, send_file, redirect, url_for
import pandas as pd
import os
import shutil
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def clear_folders():
    """Delete all files in upload and output folders."""
    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file part"
        
        file = request.files["file"]
        if file.filename == "":
            return "No file selected"
        
        clear_folders()

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        data = pd.read_csv(filepath)

        notes_lower = data['Notes'].str.lower()

        home_loan_keywords = [
            'campaign: home loan campaign',
            'adset: home loan campaign ad set',
            'ad: home loan campaign ad'
        ]

        home_loan_mask = notes_lower.apply(lambda note: any(k in note for k in home_loan_keywords))
        home_loan_data = data[home_loan_mask]

        yes_mask = home_loan_data['Notes'].str.lower().str.contains('home loan : yes')
        yes_rows = home_loan_data[yes_mask]
        no_rows = home_loan_data[~yes_mask]

        final_home_loan_data = pd.concat([yes_rows, no_rows], ignore_index=True)
        not_home_loan_data = data[~home_loan_mask]

        # Save outputs
        home_loan_path = os.path.join(OUTPUT_FOLDER, "file_home_loans.csv")
        not_home_loan_path = os.path.join(OUTPUT_FOLDER, "file1.csv")

        final_home_loan_data.to_csv(home_loan_path, index=False)
        not_home_loan_data.to_csv(not_home_loan_path, index=False)

        return redirect(url_for("download_page"))

    return render_template("upload.html")


@app.route("/downloads")
def download_page():
    return render_template("downloads.html")


@app.route("/download/<filename>")
def download_file(filename):
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    return send_file(filepath, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
