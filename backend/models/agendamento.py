from datetime import datetime
from backend.app import db

class Agendamento(db.Model):
    __tablename__ = 'agendamentos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    telefone = db.Column(db.String(20))
    data_visita = db.Column(db.Date, nullable=False)
    data_evento = db.Column(db.Date, nullable=True)
    observacoes = db.Column(db.Text)
    status = db.Column(db.String(20), default='agendado')
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Agendamento #{self.id} {self.nome}>'
