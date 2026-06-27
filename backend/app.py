import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__,
                template_folder='../frontend/pages',
                static_folder='../frontend/assets')

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nobre_elegancy_dev_2025')

    database_url = os.environ.get('DATABASE_URL', 'sqlite:///noivas.db')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+pg8000://', 1)
    elif database_url.startswith('postgresql://') and 'pg8000' not in database_url:
        database_url = database_url.replace('postgresql://', 'postgresql+pg8000://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Faça login para continuar.'

    from backend.models.usuario import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    # Blueprints
    from backend.routers.auth import bp as auth_bp
    from backend.routers.contratos import bp as contratos_bp
    from backend.routers.estoque import bp as estoque_bp
    from backend.routers.clientes import bp as clientes_bp
    from backend.routers.agenda import bp as agenda_bp
    from backend.routers.contabilidade import bp as contabilidade_bp
    from backend.routers.dashboard import bp as dashboard_bp
    from backend.routers.consultas import bp as consultas_bp
    from backend.routers.pwa import bp as pwa_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(contratos_bp)
    app.register_blueprint(estoque_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(agenda_bp)
    app.register_blueprint(contabilidade_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(consultas_bp)
    app.register_blueprint(pwa_bp)

    with app.app_context():
        db.create_all()
        _init_admin()

    return app


def _init_admin():
    from backend.models.usuario import Usuario
    from werkzeug.security import generate_password_hash
    admin = Usuario.query.filter_by(email='Isaac').first()
    if not admin:
        admin = Usuario(
            nome='Isaac',
            email='Isaac',
            senha_hash=generate_password_hash('753951'),
            nivel='admin',
            ativo=True
        )
        db.session.add(admin)
        db.session.commit()
