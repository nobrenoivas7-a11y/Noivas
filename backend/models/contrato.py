from datetime import datetime, date
from backend.app import db

class Contrato(db.Model):
    __tablename__ = 'contratos'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data_retirada = db.Column(db.Date, nullable=False)
    data_devolucao = db.Column(db.Date, nullable=False)
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
        if self.status == 'ativo' and self.data_devolucao < date.today():
            self.status = 'atrasado'

    def __repr__(self):
        return f'<Contrato #{self.id:04d}>'


class ContratoItem(db.Model):
    __tablename__ = 'contrato_itens'

    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(db.Integer, db.ForeignKey('contratos.id'), nullable=False)
    peca_id = db.Column(db.Integer, db.ForeignKey('pecas.id'), nullable=False)
    preco_cobrado = db.Column(db.Float, default=0.0)


class Pagamento(db.Model):
    __tablename__ = 'pagamentos'

    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(db.Integer, db.ForeignKey('contratos.id'), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(20), default='sinal')
    forma = db.Column(db.String(20), default='pix')
    observacao = db.Column(db.String(200))
    data = db.Column(db.DateTime, default=datetime.utcnow)


class Despesa(db.Model):
    __tablename__ = 'despesas'

    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    categoria = db.Column(db.String(50))
    data = db.Column(db.Date, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
