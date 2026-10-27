import os
from flask import Flask, render_template
from .extensions import db, login_manager, migrate
from config import config_by_name


def create_app(config_name=None):
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_by_name[config_name])

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)

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