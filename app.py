import os
from flask import (
    Flask, render_template, redirect, url_for,
    request, flash, session, send_from_directory
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ---------------- CONFIG ----------------
app.config['SECRET_KEY'] = 'aum_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "png", "jpg", "jpeg"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db = SQLAlchemy(app)


# ---------------- DATABASE MODELS ----------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    note_id = db.Column(db.Integer, db.ForeignKey("note.id"), nullable=False)

    # prevent duplicate likes
    __table_args__ = (db.UniqueConstraint("user_id", "note_id", name="unique_like"),)


# ---------------- CREATE DATABASE ----------------
with app.app_context():
    db.create_all()
   

    # Create default admin if not exists
    admin = User.query.filter_by(email="admin@notes.com").first()
    if not admin:
        admin_user = User(
            username="admin",
            email="admin@notes.com",
            password=generate_password_hash("admin123"),
            is_admin=True,
        )
        db.session.add(admin_user)
        db.session.commit()



# ---------------- HELPER FUNCTION ----------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------- ROUTES ----------------

# Home
@app.route("/")
def home():
    recent_notes = Note.query.order_by(Note.id.desc()).limit(6).all()
    return render_template("index.html", notes=recent_notes)



# -------- REGISTER --------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        existing_user = User.query.filter(
            (User.email == email) | (User.username == username)
        ).first()

        if existing_user:
            flash("User already exists!", "danger")
            return redirect(url_for("register"))

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# -------- LOGIN --------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.username
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("login.html")


# -------- DASHBOARD --------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html", username=session["username"])


# -------- LOGOUT --------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("home"))


# -------- UPLOAD NOTE --------
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        subject = request.form["subject"]
        file = request.files["file"]

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            # Ensure unique filename
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            counter = 1
            while os.path.exists(filepath):
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{counter}{ext}"
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                counter += 1

            file.save(filepath)

            new_note = Note(
                title=title,
                subject=subject,
                filename=filename,
                user_id=session["user_id"],
            )
            db.session.add(new_note)
            db.session.commit()

            flash("Note uploaded successfully!", "success")
            return redirect(url_for("notes"))

        flash("Invalid file type!", "danger")

    return render_template("upload.html")


# -------- VIEW ALL NOTES --------
@app.route("/notes")
def notes():
    if "user_id" not in session:
        return redirect(url_for("login"))

    search_query = request.args.get("search", "")
    subject_filter = request.args.get("subject", "")

    query = Note.query

    if search_query:
        query = query.filter(Note.title.ilike(f"%{search_query}%"))

    if subject_filter:
        query = query.filter(Note.subject.ilike(f"%{subject_filter}%"))

    all_notes = query.order_by(Note.id.desc()).all()

    # subject dropdown
    subjects = db.session.query(Note.subject).distinct().all()
    subjects = [s[0] for s in subjects]

    # like counts
    like_counts = {
        note.id: Like.query.filter_by(note_id=note.id).count()
        for note in all_notes
    }

    return render_template(
        "notes.html",
        notes=all_notes,
        subjects=subjects,
        search_query=search_query,
        subject_filter=subject_filter,
        like_counts=like_counts,
    )



# -------- MY NOTES --------
@app.route("/my-notes")
def my_notes():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_notes = Note.query.filter_by(user_id=session["user_id"]).order_by(Note.id.desc()).all()
    return render_template("my_notes.html", notes=user_notes)


# -------- DOWNLOAD NOTE --------
@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


@app.route("/admin")
def admin_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    if not user.is_admin:
        flash("Access denied!", "danger")
        return redirect(url_for("dashboard"))

    total_users = User.query.count()
    total_notes = Note.query.count()

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_notes=total_notes,
    )

@app.route("/admin/users")
def admin_users():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    if not user.is_admin:
        return redirect(url_for("dashboard"))

    users = User.query.all()
    return render_template("admin/users.html", users=users)


@app.route("/admin/delete-user/<int:user_id>")
def delete_user(user_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    admin = User.query.get(session["user_id"])
    if not admin.is_admin:
        return redirect(url_for("dashboard"))

    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted successfully.", "success")

    return redirect(url_for("admin_users"))


@app.route("/admin/notes")
def admin_notes():
    if "user_id" not in session:
        return redirect(url_for("login"))

    admin = User.query.get(session["user_id"])
    if not admin.is_admin:
        return redirect(url_for("dashboard"))

    notes = Note.query.all()
    return render_template("admin/notes.html", notes=notes)


@app.route("/admin/delete-note/<int:note_id>")
def delete_note(note_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    admin = User.query.get(session["user_id"])
    if not admin.is_admin:
        return redirect(url_for("dashboard"))

    note = Note.query.get(note_id)

    if note:
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], note.filename)
        if os.path.exists(filepath):
            os.remove(filepath)

        db.session.delete(note)
        db.session.commit()
        flash("Note deleted successfully.", "success")

    return redirect(url_for("admin_notes"))


@app.route("/like/<int:note_id>")
def like_note(note_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    existing_like = Like.query.filter_by(
        user_id=session["user_id"],
        note_id=note_id
    ).first()

    if not existing_like:
        new_like = Like(user_id=session["user_id"], note_id=note_id)
        db.session.add(new_like)
        db.session.commit()

    return redirect(url_for("notes"))



# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

