"""
models.py
---------
SQLAlchemy models.

Relationships:
- User  1---N  Enrollment  N---1  Course     (many-to-many with extra `progress`)
- Course 1---N Material                       (PDF file OR YouTube URL)
- Course 1---N Quiz  1---N  Question          (a course can have many quizzes;
                                              each quiz has many MCQ questions)
- User  1---N  Result  N---1  Quiz            (a student's attempt score)
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="student", nullable=False)  # student | admin
    bio = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    enrollments = db.relationship(
        "Enrollment", back_populates="user",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    results = db.relationship(
        "Result", back_populates="user",
        cascade="all, delete-orphan", passive_deletes=True,
    )

    # --- helpers ---
    def set_password(self, raw: str) -> None:
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password_hash, raw)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    category = db.Column(db.String(80), default="General")
    cover_url = db.Column(db.String(500), default="")  # optional image URL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    materials = db.relationship(
        "Material", back_populates="course",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    quizzes = db.relationship(
        "Quiz", back_populates="course",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    enrollments = db.relationship(
        "Enrollment", back_populates="course",
        cascade="all, delete-orphan", passive_deletes=True,
    )


class Enrollment(db.Model):
    """Many-to-many User<->Course, with per-enrollment progress (0-100)."""
    __tablename__ = "enrollments"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    progress = db.Column(db.Integer, default=0)  # 0..100
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "course_id", name="uq_user_course"),)

    user = db.relationship("User", back_populates="enrollments")
    course = db.relationship("Course", back_populates="enrollments")


class Material(db.Model):
    """A learning resource: either a PDF file or an embedded YouTube video."""
    __tablename__ = "materials"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    kind = db.Column(db.String(20), default="pdf")  # pdf | video
    file_name = db.Column(db.String(255), default="")  # if kind=pdf
    youtube_url = db.Column(db.String(500), default="")  # if kind=video
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    course = db.relationship("Course", back_populates="materials")


class Quiz(db.Model):
    __tablename__ = "quizzes"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    course = db.relationship("Course", back_populates="quizzes")
    questions = db.relationship(
        "Question", back_populates="quiz",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    results = db.relationship(
        "Result", back_populates="quiz",
        cascade="all, delete-orphan", passive_deletes=True,
    )


class Question(db.Model):
    """Multiple-choice question with 4 options; `correct_index` in 0..3."""
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(300), nullable=False)
    option_b = db.Column(db.String(300), nullable=False)
    option_c = db.Column(db.String(300), nullable=False)
    option_d = db.Column(db.String(300), nullable=False)
    correct_index = db.Column(db.Integer, nullable=False)  # 0..3

    quiz = db.relationship("Quiz", back_populates="questions")

    @property
    def options(self):
        return [self.option_a, self.option_b, self.option_c, self.option_d]


class Result(db.Model):
    __tablename__ = "results"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    score = db.Column(db.Integer, nullable=False)      # correct answers
    total = db.Column(db.Integer, nullable=False)      # total questions
    taken_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="results")
    quiz = db.relationship("Quiz", back_populates="results")

    @property
    def percent(self) -> int:
        return round((self.score / self.total) * 100) if self.total else 0
