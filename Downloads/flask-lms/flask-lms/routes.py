"""
routes.py
---------
All view functions grouped into blueprints:
  - main       : home, about, contact
  - auth       : register, login, logout, profile
  - courses    : browse, search, detail
  - student    : dashboard, my courses, enroll, materials, download, AI tutor
  - admin      : dashboard, CRUD courses, materials, quizzes, users, results
  - quizzes    : take, submit, result
"""
from functools import wraps
from pathlib import Path
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    send_from_directory, current_app, session, jsonify, abort,
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_

from models import (
    db, User, Course, Enrollment, Material, Quiz, Question, Result,
)
from forms import (
    RegisterForm, LoginForm, ProfileForm, CourseForm, MaterialForm,
    QuizForm, QuestionForm, AIGenerateQuizForm, ContactForm,
)
from ai import tutor_reply, generate_quiz, AIUnavailable


# ---------- Blueprints ----------
main_bp = Blueprint("main", __name__)
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
courses_bp = Blueprint("courses", __name__, url_prefix="/courses")
student_bp = Blueprint("student", __name__, url_prefix="/student")
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
quizzes_bp = Blueprint("quizzes", __name__, url_prefix="/quizzes")


# ---------- Decorators ----------
def admin_required(f):
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            flash("Admins only.", "danger")
            return redirect(url_for("main.home"))
        return f(*args, **kwargs)
    return wrapper


# ============================================================
# MAIN
# ============================================================
@main_bp.route("/")
def home():
    featured = Course.query.order_by(Course.created_at.desc()).limit(6).all()
    return render_template("home/home.html", featured=featured)


@main_bp.route("/about")
def about():
    return render_template("home/about.html")


@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        # In production: send email / persist to DB. Here: flash confirmation.
        flash("Thanks! We received your message.", "success")
        return redirect(url_for("main.contact"))
    return render_template("home/contact.html", form=form)


# ============================================================
# AUTH
# ============================================================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash("Email already registered.", "warning")
            return render_template("authentication/register.html", form=form)
        u = User(name=form.name.data.strip(),
                 email=form.email.data.lower().strip(),
                 role="student")
        u.set_password(form.password.data)
        db.session.add(u)
        db.session.commit()
        login_user(u)
        flash("Welcome! Your account is ready.", "success")
        return redirect(url_for("student.dashboard"))
    return render_template("authentication/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("Logged in.", "success")
            if user.is_admin:
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("student.dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("authentication/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("main.home"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.name = form.name.data.strip()
        current_user.bio = form.bio.data or ""
        if form.password.data:
            current_user.set_password(form.password.data)
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("auth.profile"))
    return render_template("authentication/profile.html", form=form)


# ============================================================
# COURSES (public browse)
# ============================================================
@courses_bp.route("/")
def list_courses():
    q = (request.args.get("q") or "").strip()
    query = Course.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Course.title.ilike(like),
                                 Course.description.ilike(like),
                                 Course.category.ilike(like)))
    items = query.order_by(Course.created_at.desc()).all()
    return render_template("courses/list.html", courses=items, q=q)


@courses_bp.route("/<int:course_id>")
def detail(course_id):
    course = Course.query.get_or_404(course_id)
    enrolled = False
    if current_user.is_authenticated:
        enrolled = Enrollment.query.filter_by(
            user_id=current_user.id, course_id=course.id).first() is not None
    return render_template("courses/detail.html", course=course, enrolled=enrolled)


# ============================================================
# STUDENT
# ============================================================
@student_bp.route("/dashboard")
@login_required
def dashboard():
    enrollments = (Enrollment.query
                   .filter_by(user_id=current_user.id)
                   .order_by(Enrollment.enrolled_at.desc()).all())
    recent_results = (Result.query.filter_by(user_id=current_user.id)
                      .order_by(Result.taken_at.desc()).limit(5).all())
    return render_template("student/dashboard.html",
                           enrollments=enrollments,
                           recent_results=recent_results)


@student_bp.route("/enroll/<int:course_id>", methods=["POST"])
@login_required
def enroll(course_id):
    course = Course.query.get_or_404(course_id)
    exists = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
    if exists:
        flash("You are already enrolled.", "info")
    else:
        db.session.add(Enrollment(user_id=current_user.id, course_id=course.id, progress=0))
        db.session.commit()
        flash(f"Enrolled in “{course.title}”.", "success")
    return redirect(url_for("courses.detail", course_id=course.id))


@student_bp.route("/course/<int:course_id>/materials")
@login_required
def materials(course_id):
    course = Course.query.get_or_404(course_id)
    enr = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
    if not enr and not current_user.is_admin:
        flash("Enroll first to access materials.", "warning")
        return redirect(url_for("courses.detail", course_id=course.id))
    return render_template("student/materials.html", course=course, enrollment=enr)


@student_bp.route("/course/<int:course_id>/progress", methods=["POST"])
@login_required
def set_progress(course_id):
    """Simple manual progress update triggered from a slider on the materials page."""
    enr = Enrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first_or_404()
    try:
        p = max(0, min(100, int(request.form.get("progress", 0))))
    except ValueError:
        p = enr.progress
    enr.progress = p
    db.session.commit()
    flash("Progress updated.", "success")
    return redirect(url_for("student.materials", course_id=course_id))


@student_bp.route("/uploads/<path:filename>")
@login_required
def download(filename):
    # Only enrolled users (or admin) can download; check via material lookup
    mat = Material.query.filter_by(file_name=filename, kind="pdf").first_or_404()
    if not current_user.is_admin:
        enr = Enrollment.query.filter_by(user_id=current_user.id, course_id=mat.course_id).first()
        if not enr:
            abort(403)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


# --- AI Tutor ---
@student_bp.route("/course/<int:course_id>/tutor", methods=["GET"])
@login_required
def tutor(course_id):
    course = Course.query.get_or_404(course_id)
    enr = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
    if not enr and not current_user.is_admin:
        flash("Enroll first to chat with the AI tutor.", "warning")
        return redirect(url_for("courses.detail", course_id=course.id))
    history = session.get(f"tutor_hist_{course.id}", [])
    return render_template("student/ai_tutor.html", course=course, history=history)


@student_bp.route("/course/<int:course_id>/tutor/ask", methods=["POST"])
@login_required
def tutor_ask(course_id):
    course = Course.query.get_or_404(course_id)
    question = (request.form.get("question") or request.json.get("question", "")).strip()
    if not question:
        return jsonify({"error": "Empty question"}), 400

    key = f"tutor_hist_{course.id}"
    history = session.get(key, [])
    try:
        answer = tutor_reply(course.title, course.description, question, history)
    except AIUnavailable as e:
        return jsonify({"error": str(e)}), 503

    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer})
    session[key] = history[-20:]  # cap
    return jsonify({"answer": answer})


@student_bp.route("/course/<int:course_id>/tutor/reset", methods=["POST"])
@login_required
def tutor_reset(course_id):
    session.pop(f"tutor_hist_{course_id}", None)
    flash("Conversation cleared.", "info")
    return redirect(url_for("student.tutor", course_id=course_id))


# ============================================================
# ADMIN
# ============================================================
@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    stats = {
        "users": User.query.count(),
        "students": User.query.filter_by(role="student").count(),
        "courses": Course.query.count(),
        "enrollments": Enrollment.query.count(),
        "quizzes": Quiz.query.count(),
        "results": Result.query.count(),
    }
    latest_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    latest_courses = Course.query.order_by(Course.created_at.desc()).limit(5).all()
    return render_template("admin/dashboard.html",
                           stats=stats,
                           latest_users=latest_users,
                           latest_courses=latest_courses)


# --- Courses CRUD ---
@admin_bp.route("/courses")
@admin_required
def manage_courses():
    items = Course.query.order_by(Course.created_at.desc()).all()
    return render_template("admin/manage_courses.html", courses=items)


@admin_bp.route("/courses/new", methods=["GET", "POST"])
@admin_required
def new_course():
    form = CourseForm()
    if form.validate_on_submit():
        c = Course(title=form.title.data.strip(),
                   category=(form.category.data or "General").strip(),
                   cover_url=form.cover_url.data or "",
                   description=form.description.data or "")
        db.session.add(c)
        db.session.commit()
        flash("Course created.", "success")
        return redirect(url_for("admin.manage_courses"))
    return render_template("courses/form.html", form=form, action="New course")


@admin_bp.route("/courses/<int:course_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    form = CourseForm(obj=course)
    if form.validate_on_submit():
        course.title = form.title.data.strip()
        course.category = (form.category.data or "General").strip()
        course.cover_url = form.cover_url.data or ""
        course.description = form.description.data or ""
        db.session.commit()
        flash("Course updated.", "success")
        return redirect(url_for("admin.manage_courses"))
    return render_template("courses/form.html", form=form, action=f"Edit: {course.title}")


@admin_bp.route("/courses/<int:course_id>/delete", methods=["POST"])
@admin_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash("Course deleted.", "info")
    return redirect(url_for("admin.manage_courses"))


# --- Materials ---
@admin_bp.route("/courses/<int:course_id>/materials", methods=["GET", "POST"])
@admin_required
def manage_materials(course_id):
    course = Course.query.get_or_404(course_id)
    form = MaterialForm()
    if form.validate_on_submit():
        m = Material(course_id=course.id, title=form.title.data.strip(), kind=form.kind.data)
        if form.kind.data == "pdf":
            file = form.pdf_file.data
            if not file:
                flash("Choose a PDF file.", "warning")
                return redirect(request.url)
            fname = secure_filename(f"{course.id}_{file.filename}")
            file.save(Path(current_app.config["UPLOAD_FOLDER"]) / fname)
            m.file_name = fname
        else:
            if not form.youtube_url.data:
                flash("Provide a YouTube URL.", "warning")
                return redirect(request.url)
            m.youtube_url = form.youtube_url.data
        db.session.add(m)
        db.session.commit()
        flash("Material added.", "success")
        return redirect(url_for("admin.manage_materials", course_id=course.id))
    return render_template("admin/materials.html", course=course, form=form)


@admin_bp.route("/materials/<int:material_id>/delete", methods=["POST"])
@admin_required
def delete_material(material_id):
    m = Material.query.get_or_404(material_id)
    cid = m.course_id
    if m.kind == "pdf" and m.file_name:
        try:
            (Path(current_app.config["UPLOAD_FOLDER"]) / m.file_name).unlink(missing_ok=True)
        except OSError:
            pass
    db.session.delete(m)
    db.session.commit()
    flash("Material deleted.", "info")
    return redirect(url_for("admin.manage_materials", course_id=cid))


# --- Users ---
@admin_bp.route("/users")
@admin_required
def manage_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/manage_users.html", users=users)


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash("You cannot delete your own account here.", "warning")
        return redirect(url_for("admin.manage_users"))
    u = User.query.get_or_404(user_id)
    db.session.delete(u)
    db.session.commit()
    flash("User deleted.", "info")
    return redirect(url_for("admin.manage_users"))


# --- Enrollments & Results ---
@admin_bp.route("/enrollments")
@admin_required
def enrollments():
    items = Enrollment.query.order_by(Enrollment.enrolled_at.desc()).all()
    return render_template("admin/enrollments.html", enrollments=items)


@admin_bp.route("/results")
@admin_required
def results():
    items = Result.query.order_by(Result.taken_at.desc()).all()
    return render_template("admin/results.html", results=items)


# --- Quizzes (admin side) ---
@admin_bp.route("/courses/<int:course_id>/quizzes", methods=["GET", "POST"])
@admin_required
def manage_quizzes(course_id):
    course = Course.query.get_or_404(course_id)
    form = QuizForm()
    if form.validate_on_submit():
        q = Quiz(course_id=course.id, title=form.title.data.strip())
        db.session.add(q)
        db.session.commit()
        flash("Quiz created.", "success")
        return redirect(url_for("admin.edit_quiz", quiz_id=q.id))
    return render_template("quizzes/form.html", course=course, form=form)


@admin_bp.route("/quizzes/<int:quiz_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    qform = QuestionForm()
    aiform = AIGenerateQuizForm()
    if qform.submit.data and qform.validate_on_submit():
        db.session.add(Question(
            quiz_id=quiz.id,
            text=qform.text.data.strip(),
            option_a=qform.option_a.data.strip(),
            option_b=qform.option_b.data.strip(),
            option_c=qform.option_c.data.strip(),
            option_d=qform.option_d.data.strip(),
            correct_index=int(qform.correct_index.data),
        ))
        db.session.commit()
        flash("Question added.", "success")
        return redirect(url_for("admin.edit_quiz", quiz_id=quiz.id))
    return render_template("quizzes/edit.html", quiz=quiz, qform=qform, aiform=aiform)


@admin_bp.route("/quizzes/<int:quiz_id>/ai_generate", methods=["POST"])
@admin_required
def ai_generate_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    form = AIGenerateQuizForm()
    if not form.validate_on_submit():
        flash("Invalid AI form input.", "warning")
        return redirect(url_for("admin.edit_quiz", quiz_id=quiz.id))
    try:
        items = generate_quiz(form.topic.data, form.num_questions.data, form.difficulty.data)
    except AIUnavailable as e:
        flash(str(e), "danger")
        return redirect(url_for("admin.edit_quiz", quiz_id=quiz.id))
    for it in items:
        db.session.add(Question(quiz_id=quiz.id, **it))
    db.session.commit()
    flash(f"AI added {len(items)} question(s) to “{quiz.title}”.", "success")
    return redirect(url_for("admin.edit_quiz", quiz_id=quiz.id))


@admin_bp.route("/quizzes/<int:quiz_id>/delete", methods=["POST"])
@admin_required
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    cid = quiz.course_id
    db.session.delete(quiz)
    db.session.commit()
    flash("Quiz deleted.", "info")
    return redirect(url_for("admin.manage_quizzes", course_id=cid))


@admin_bp.route("/questions/<int:qid>/delete", methods=["POST"])
@admin_required
def delete_question(qid):
    q = Question.query.get_or_404(qid)
    quiz_id = q.quiz_id
    db.session.delete(q)
    db.session.commit()
    flash("Question removed.", "info")
    return redirect(url_for("admin.edit_quiz", quiz_id=quiz_id))


# ============================================================
# QUIZZES (student side)
# ============================================================
@quizzes_bp.route("/<int:quiz_id>/take", methods=["GET", "POST"])
@login_required
def take(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    # must be enrolled
    if not current_user.is_admin:
        enrolled = Enrollment.query.filter_by(
            user_id=current_user.id, course_id=quiz.course_id).first()
        if not enrolled:
            flash("Enroll in the course to take this quiz.", "warning")
            return redirect(url_for("courses.detail", course_id=quiz.course_id))

    if not quiz.questions:
        flash("This quiz has no questions yet.", "info")
        return redirect(url_for("courses.detail", course_id=quiz.course_id))

    if request.method == "POST":
        score = 0
        for q in quiz.questions:
            try:
                picked = int(request.form.get(f"q_{q.id}", -1))
            except ValueError:
                picked = -1
            if picked == q.correct_index:
                score += 1
        result = Result(user_id=current_user.id, quiz_id=quiz.id,
                        score=score, total=len(quiz.questions))
        db.session.add(result)
        db.session.commit()
        return redirect(url_for("quizzes.result", result_id=result.id))

    return render_template("quizzes/take.html", quiz=quiz)


@quizzes_bp.route("/result/<int:result_id>")
@login_required
def result(result_id):
    r = Result.query.get_or_404(result_id)
    if r.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    return render_template("quizzes/result.html", r=r)
