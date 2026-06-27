from flask_login import UserMixin
from datetime import datetime
from backend.app import db

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    nivel = db.Column(db.String(20), default='funcionaria')
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_admin(self):
        return self.nivel == 'admin'

    def __repr__(self):
        return f'<Usuario {self.nome}>'
