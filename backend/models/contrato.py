from datetime import datetime, date
from backend.app import db

class Contrato(db.Model):
    __tablename__ = 'contratos'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data_retirada = db.Column(db.Date, nullable=False)
    data_devolucao = db.Column(db.Date, nullable=False)
    data_prova = db.Column(db.Date, nullable=True)
    data_devolucao_real = db.Column(db.Date, nullable=True)
    valor_total = db.Column(db.Float, default=0.0)
    valor_sinal = db.Column(db.Float, default=0.0)
    valor_pago = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='ativo')
    observacoes = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    itens = db.relationship('ContratoItem', backref='contrato', lazy=True, cascade='all, delete-orphan')
    pagamentos = db.relationship('Pagamento', backref='contrato', lazy=True, cascade='all, delete-orphan')
    usuario = db.relationship('Usuario', backref='contratos', lazy=True)

    @property
    def saldo_restante(self):
        return max(0.0, self.valor_total - self.valor_pago)

    def atualizar_status(self):
        if
