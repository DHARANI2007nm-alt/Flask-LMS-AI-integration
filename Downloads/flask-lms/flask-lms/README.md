# 🎓 Flask LMS with AI Integration

An AI-powered Learning Management System (LMS) built using Flask that enables students to enroll in courses, watch learning materials, take quizzes, and interact with an AI tutor. Administrators can manage courses, upload resources, and generate quizzes automatically using AI.

---

## 🚀 Live Demo

🌐 https://flask-lms-ai-integration.onrender.com

---

## ✨ Features

### 👨‍🎓 Student
- User Registration & Login
- Browse Available Courses
- Enroll in Courses
- Watch Embedded YouTube Lectures
- Download Course Materials
- Take Multiple Choice Quizzes
- AI Tutor for Learning Assistance
- Track Learning Progress

### 👨‍💼 Admin
- Secure Admin Login
- Add/Edit/Delete Courses
- Upload PDFs
- Add YouTube Learning Videos
- Create Quizzes Manually
- Generate Quiz Questions using AI
- Manage Students

---

## 🤖 AI Features

This project integrates **Groq API** using an OpenAI-compatible interface.

AI Capabilities:
- AI Tutor
- Automatic Quiz Generation
- JSON-based Question Creation
- Fast AI Responses using Llama 3.3 70B

---

## 🛠 Tech Stack

### Backend
- Python
- Flask
- SQLAlchemy

### Frontend
- HTML
- CSS
- Bootstrap
- JavaScript

### Database
- SQLite

### AI
- Groq API
- Llama 3.3 70B Versatile

### Deployment
- Render

### Version Control
- Git
- GitHub

---

## 📂 Project Structure

```
Flask-LMS/
│
├── static/
├── templates/
├── uploads/
├── database/
├── ai.py
├── app.py
├── config.py
├── forms.py
├── models.py
├── routes.py
├── requirements.txt
└── README.md
```

---

## ⚙ Installation

Clone the repository

```bash
git clone https://github.com/DHARANI2007nm-alt/Flask-LMS-AI-integration.git
```

Move into the project

```bash
cd Flask-LMS-AI-integration
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the project

```bash
python app.py
```

---

## 🔑 Environment Variables

Create a `.env` file

```env
SECRET_KEY=your_secret_key

OPENAI_API_KEY=your_groq_api_key

OPENAI_BASE_URL=https://api.groq.com/openai/v1

OPENAI_MODEL=llama-3.3-70b-versatile
```

## 📈 Future Improvements

- Certificate Generation
- Payment Gateway
- Attendance Tracking
- Discussion Forum
- Assignment Submission
- Email Notifications
- AI Course Recommendation

---

## 👩‍💻 Developed By

**Dharani**
**Deva dharshine**

Second Year Computer Science Engineering Student

Panimalar Engineering College

GitHub:
https://github.com/DHARANI2007nm-alt

---

## 📜 License

This project is developed for educational and internship purposes.
