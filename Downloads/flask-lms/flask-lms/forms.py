"""
forms.py
--------
Flask-WTF forms. Every user input passes through a form for validation and CSRF.
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, PasswordField, TextAreaField, SelectField,
    IntegerField, SubmitField, RadioField,
)
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, Optional, NumberRange, URL,
)


class RegisterForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Length(2, 120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(6, 128)])
    confirm = PasswordField("Confirm password",
                            validators=[DataRequired(), EqualTo("password", "Passwords must match")])
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")


class ProfileForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Length(2, 120)])
    bio = TextAreaField("Bio", validators=[Optional(), Length(max=1000)])
    password = PasswordField("New password (leave blank to keep current)",
                             validators=[Optional(), Length(6, 128)])
    submit = SubmitField("Save changes")


class CourseForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(2, 200)])
    category = StringField("Category", validators=[Optional(), Length(max=80)])
    cover_url = StringField("Cover image URL", validators=[Optional(), URL(), Length(max=500)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=5000)])
    submit = SubmitField("Save course")


class MaterialForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(2, 200)])
    kind = SelectField("Type", choices=[("pdf", "PDF file"), ("video", "YouTube video")],
                       validators=[DataRequired()])
    pdf_file = FileField("PDF file", validators=[Optional(), FileAllowed(["pdf"], "PDFs only")])
    youtube_url = StringField("YouTube URL", validators=[Optional(), URL(), Length(max=500)])
    submit = SubmitField("Upload material")


class QuizForm(FlaskForm):
    title = StringField("Quiz title", validators=[DataRequired(), Length(2, 200)])
    submit = SubmitField("Create quiz")


class QuestionForm(FlaskForm):
    text = TextAreaField("Question", validators=[DataRequired(), Length(3, 1000)])
    option_a = StringField("Option A", validators=[DataRequired(), Length(1, 300)])
    option_b = StringField("Option B", validators=[DataRequired(), Length(1, 300)])
    option_c = StringField("Option C", validators=[DataRequired(), Length(1, 300)])
    option_d = StringField("Option D", validators=[DataRequired(), Length(1, 300)])
    correct_index = SelectField(
        "Correct answer",
        choices=[("0", "A"), ("1", "B"), ("2", "C"), ("3", "D")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Add question")


class AIGenerateQuizForm(FlaskForm):
    topic = StringField("Topic / prompt", validators=[DataRequired(), Length(3, 300)])
    num_questions = IntegerField("Number of questions",
                                 validators=[DataRequired(), NumberRange(min=1, max=15)], default=5)
    difficulty = SelectField("Difficulty",
                             choices=[("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")],
                             default="medium")
    submit = SubmitField("Generate with AI")


class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(2, 120)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    message = TextAreaField("Message", validators=[DataRequired(), Length(5, 2000)])
    submit = SubmitField("Send")


class SearchForm(FlaskForm):
    q = StringField("Search", validators=[Optional(), Length(max=120)])
    submit = SubmitField("Search")
