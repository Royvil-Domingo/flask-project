import os
from flask import Flask, render_template, flash, redirect, url_for
from flask_login import current_user
from flask_wtf.csrf import CSRFError
from .extensions import db, login_manager, migrate, csrf
from config import config_by_name


def create_app(config_name=None):
    # Defaults to production so a deployment that forgets FLASK_ENV never
    # runs with DEBUG on. Local development sets FLASK_ENV=development in .env.
    config_name = config_name or os.environ.get('FLASK_ENV', 'production')

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_by_name[config_name])
    app.config.setdefault('WTF_CSRF_TIME_LIMIT', None)  # token lasts as long as the session

    if config_name == 'production' and app.config['SECRET_KEY'] == 'change-this-secret-key':
        raise RuntimeError(
            'SECRET_KEY is not set. Add it to your .env file (local) or to the '
            'environment variables of your hosting platform.'
        )

    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        # Read-only filesystem (e.g. Vercel's serverless functions). Safe to
        # ignore here: the instance folder is only needed for the local
        # SQLite fallback; a Postgres DATABASE_URL never touches it.
        pass

    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    csrf.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'error'

    from .models import User, Equipment, Borrower, Borrowing

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes.auth import auth as auth_bp
    from .routes.main import main as main_bp
    from .routes.equipment import equipment as equipment_bp
    from .routes.borrowers import borrowers as borrowers_bp
    from .routes.borrowings import borrowings as borrowings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(equipment_bp)
    app.register_blueprint(borrowers_bp)
    app.register_blueprint(borrowings_bp)

    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app


def register_error_handlers(app):
    @app.errorhandler(CSRFError)
    def csrf_error(e):
        flash('Your session expired or the form was invalid. Please try again.', category='error')
        return redirect(url_for('main.dashboard') if current_user.is_authenticated else url_for('auth.login'))

    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template('errors/500.html'), 500