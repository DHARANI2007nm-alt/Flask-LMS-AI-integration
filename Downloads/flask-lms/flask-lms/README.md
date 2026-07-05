# Flask LMS — Online Course & Learning Management System

A complete, production-quality LMS built with **Python Flask**, **SQLite/SQLAlchemy**,
**Flask-Login**, **Flask-WTF**, and **Bootstrap 5**. Includes two bonus AI features:

- **AI Tutor** — a per-course chatbot that answers student questions in context.
- **AI Quiz Generation** — admins generate multiple-choice quizzes from a topic in one click.

---

## Project Structure

```
flask-lms/
├── app.py                 # App factory + entry point (runs the server)
├── config.py              # Configuration (secret key, DB URI, upload paths, AI keys)
├── models.py              # SQLAlchemy models: User, Course, Enrollment, Material, Quiz, Question, Result
├── forms.py               # Flask-WTF forms with validation
├── routes.py              # All view functions (auth, student, admin, courses, quizzes, AI)
├── ai.py                  # OpenAI-compatible client: AI Tutor + AI quiz generator
├── requirements.txt       # Python dependencies
├── static/
│   ├── css/style.css      # Custom styles on top of Bootstrap 5
│   ├── js/main.js         # Small helpers (AI tutor chat widget, confirm dialogs)
│   └── images/            # Logo, placeholders
├── templates/
│   ├── base.html          # Master layout: navbar + footer + flash messages
│   ├── home/              # Home, About, Contact
│   ├── authentication/    # login, register, profile
│   ├── student/           # dashboard, my_courses, ai_tutor
│   ├── admin/             # dashboard, manage_courses, manage_users, enrollments, results
│   ├── courses/           # list, detail, materials, form (add/edit)
│   └── quizzes/           # take, result, form (add/generate)
├── database/              # SQLite file lives here (auto-created)
└── uploads/               # Uploaded PDFs / materials (auto-created)
```

### File purpose

| File | Purpose |
|---|---|
| `app.py` | Creates the Flask app, initializes extensions (SQLAlchemy, LoginManager, CSRF), registers blueprints, seeds an admin user. |
| `config.py` | Central configuration. Reads env vars for secret key + AI credentials. |
| `models.py` | Database schema and relationships. |
| `forms.py` | WTForms classes for every user input (login, register, course, quiz, question, contact). |
| `routes.py` | HTTP routes grouped by blueprint: `auth`, `student`, `admin`, `courses`, `quizzes`, `ai`. |
| `ai.py` | Thin wrapper around any OpenAI-compatible API for tutoring + quiz generation. |
| `requirements.txt` | Pin of Python packages. |

---

## Database (SQLAlchemy) Relationships

- **User** (1) — (N) **Enrollment** (N) — (1) **Course**  (many-to-many via `Enrollment`, with extra `progress` field)
- **Course** (1) — (N) **Material** (PDF path or YouTube URL)
- **Course** (1) — (N) **Quiz** (1) — (N) **Question**
- **User** (1) — (N) **Result** (N) — (1) **Quiz** (a student's quiz attempt score)

Every model has a primary key `id`. Foreign keys use `ondelete='CASCADE'` so deleting a
course cleans up its materials, quizzes, questions, enrollments, and results.

---

## Roles

- **Student**: register, login, browse/search courses, enroll, view materials, watch YouTube,
  download PDFs, take quizzes, see scores, track progress, chat with AI tutor.
- **Admin**: dashboard with counts, CRUD courses, upload materials, add quizzes manually or
  **generate them with AI**, manage users, view all enrollments and quiz results.

Default admin: **admin@lms.local / admin123** (change on first login).

---

## Setup

```bash
cd flask-lms
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000.

### Enabling AI features (optional but recommended)

Set environment variables before running:

```bash
export OPENAI_API_KEY="sk-..."                       # required for AI
export OPENAI_BASE_URL="https://api.openai.com/v1"   # optional (default)
export OPENAI_MODEL="gpt-4o-mini"                    # optional (default)
```

Works with any OpenAI-compatible provider (OpenAI, Groq, OpenRouter, Together, local
Ollama with `/v1`, Lovable AI Gateway, etc.). Without a key the AI pages show a friendly
"AI not configured" message; the rest of the LMS works normally.

---

## Security

- Passwords hashed with `werkzeug.security` (PBKDF2-SHA256).
- Session cookies signed with `SECRET_KEY`.
- `@login_required` and `@admin_required` decorators guard protected routes.
- WTForms provide server-side validation + CSRF tokens.
- File uploads: extension whitelist, `secure_filename`, size limit.
- Flash messages for user feedback; custom 404 / 500 pages.
