
from flask import Flask, render_template, request, redirect
import fitz
import re
import sqlite3

app = Flask(__name__)
DATABASE = "careermatch.db"


def init_db():
    connection = sqlite3.connect(DATABASE)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            job_role TEXT NOT NULL,
            applied_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Applied'
        )
    """)

    connection.commit()
    connection.close()


init_db()
# Skills our application can recognise
SKILLS = [
    "python",
    "java",
    "sql",
    "html",
    "css",
    "javascript",
    "flask",
    "django",
    "machine learning",
    "data analysis",
    "pandas",
    "numpy",
    "power bi",
    "excel",
    "mysql",
    "git",
    "github",
    "communication",
    "problem solving",
    "data visualization",
    "statistics",
    "scikit-learn",
    "react",
    "node.js",
    "rest api"
]


def extract_resume_text(file):
    """Extract text from an uploaded PDF resume."""
    document = fitz.open(stream=file.read(), filetype="pdf")

    text = ""

    for page in document:
        text += page.get_text()

    document.close()

    return text


def find_skills(text):
    """Find recognised skills in a piece of text."""
    text = text.lower()
    found_skills = []

    for skill in SKILLS:
        pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"

        if re.search(pattern, text):
            found_skills.append(skill)

    return found_skills


@app.route("/")
def home():
    return render_template("index.html")
@app.route("/tracker")
def tracker():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    applications = connection.execute(
        "SELECT * FROM applications ORDER BY id DESC"
    ).fetchall()

    connection.close()

    return render_template(
        "tracker.html",
        applications=applications
    )
@app.route("/tracker/add", methods=["POST"])
def add_application():
    company = request.form.get("company", "").strip()
    job_role = request.form.get("job_role", "").strip()
    applied_date = request.form.get("applied_date", "").strip()
    status = request.form.get("status", "Applied").strip()

    if company and job_role and applied_date:
        connection = sqlite3.connect(DATABASE)
        connection.execute(
            """INSERT INTO applications
            (company, job_role, applied_date, status)
            VALUES (?, ?, ?, ?)""",
            (company, job_role, applied_date, status)
        )
        connection.commit()
        connection.close()

    return redirect("/tracker")

@app.route("/analyze", methods=["POST"])
def analyze():
    resume_file = request.files.get("resume")
    job_description = request.form.get("job_description", "")

    if not resume_file or not resume_file.filename:
        return "Please upload your resume.", 400

    if not resume_file.filename.lower().endswith(".pdf"):
        return "Please upload a PDF file.", 400

    if not job_description.strip():
        return "Please enter a job description.", 400

    try:
        resume_text = extract_resume_text(resume_file)
    except Exception:
        return "We could not read this PDF. Please try another PDF.", 400

    if not resume_text.strip():
        return (
            "No readable text was found. Please use a text-based PDF resume.",
            400
        )

    resume_skills = find_skills(resume_text)
    job_skills = find_skills(job_description)

    matched_skills = [
        skill for skill in job_skills if skill in resume_skills
    ]

    missing_skills = [
        skill for skill in job_skills if skill not in resume_skills
    ]

    if job_skills:
        match_percentage = round(
            len(matched_skills) / len(job_skills) * 100
        )
    else:
        match_percentage = 0

    return render_template(
        "result.html",
        match_percentage=match_percentage,
        resume_skills=resume_skills,
        job_skills=job_skills,
        matched_skills=matched_skills,
        missing_skills=missing_skills
    )

@app.route("/tracker/delete/<int:application_id>", methods=["POST"])
def delete_application(application_id):
    connection = sqlite3.connect(DATABASE)
    connection.execute(
        "DELETE FROM applications WHERE id = ?",
        (application_id,)
    )
    connection.commit()
    connection.close()

    return redirect("/tracker")
@app.route("/tracker/update/<int:application_id>", methods=["POST"])
def update_application(application_id):
    status = request.form.get("status", "Applied")

    allowed_statuses = ["Applied", "Interview", "Selected", "Rejected"]

    if status in allowed_statuses:
        connection = sqlite3.connect(DATABASE)
        connection.execute(
            "UPDATE applications SET status = ? WHERE id = ?",
            (status, application_id)
        )
        connection.commit()
        connection.close()

    return redirect("/tracker")
if __name__ == "__main__":
    app.run(debug=True)
