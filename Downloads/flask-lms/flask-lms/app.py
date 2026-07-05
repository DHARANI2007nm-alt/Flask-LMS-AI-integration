"""
app.py
------
Application factory + entry point.

Run with:
    python app.py

Creates the SQLite DB (database/lms.db) on first launch and seeds a default
admin account so you can log in immediately:
    email: admin@lms.local
    password: admin123
"""
from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from config import Config
from models import db, User
from routes import (
    main_bp, auth_bp, courses_bp, student_bp, admin_bp, quizzes_bp,
)

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"

csrf = CSRFProtect()


@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # Extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(quizzes_bp)

    # Error handlers
    @app.errorhandler(403)
    def forbidden(_):
        return render_template("errors.html", code=403,
                               message="You don't have permission to view this page."), 403

    @app.errorhandler(404)
    def not_found(_):
        return render_template("errors.html", code=404,
                               message="Page not found."), 404

    @app.errorhandler(500)
    def server_error(_):
        return render_template("errors.html", code=500,
                               message="Something went wrong on our end."), 500

    # DB init + seed default admin
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email=app.config["DEFAULT_ADMIN_EMAIL"]).first():
            admin = User(
                name=app.config["DEFAULT_ADMIN_NAME"],
                email=app.config["DEFAULT_ADMIN_EMAIL"],
                role="admin",
            )
            admin.set_password(app.config["DEFAULT_ADMIN_PASSWORD"])
            db.session.add(admin)
            db.session.commit()
            print(f"[seed] created admin: {admin.email} / "
                  f"{app.config['DEFAULT_ADMIN_PASSWORD']}")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)
