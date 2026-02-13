

# 📚 Notes Sharing Website

A full-stack **Flask-based Notes Sharing Platform** where students can  
upload, browse, search, like, and download study notes with an  
admin dashboard and modern responsive UI.

---

---

## ✨ Features

### 👤 User Features
- Secure **User Registration & Login**
- Upload notes (PDF, DOC, Images)
- Browse notes uploaded by others
- **Search & filter** notes by title and subject
- **Like system** for notes interaction ❤️
- Download study materials
- Personal **My Notes dashboard**
- **Dark mode / Night mode** 🌙
- Fully **mobile-responsive UI** 📱

### 🛠 Admin Features
- Admin login panel
- View all registered users
- View all uploaded notes
- Delete users or notes
- Dashboard statistics (total users & notes)

---

## 🧱 Tech Stack

**Frontend**
- HTML5, CSS3, Bootstrap 5
- Responsive & mobile-friendly design
- Dark mode with JavaScript

**Backend**
- Python Flask
- Flask-SQLAlchemy ORM
- Session-based authentication

**Database**
- SQLite (for demo & deployment)

**Deployment**
- Render (Gunicorn production server)

---

## 📂 Project Structure

notes-sharing-website/
│
├── app.py
├── database.db
├── requirements.txt
├── Procfile
│
├── uploads/
│
├── templates/
│ ├── base.html
│ ├── index.html
│ ├── login.html
│ ├── register.html
│ ├── dashboard.html
│ ├── upload.html
│ ├── notes.html
│ ├── my_notes.html
│ └── admin/
│ ├── dashboard.html
│ ├── users.html
│ └── notes.html
│
└── static/
├── css/style.css
└── js/

