from datetime import datetime
from backend.app import db

class AteliePedido(db.Model):
    __tablename__ = 'atelie_pedidos'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=True)
    nome_cliente = db.Column(db.String(150), nullable=False)
    telefone = db.Column(db.String(20))
    modelo = db.Column(db.String(150))
    descricao = db.Column(db.Text)
    data_entrega = db.Column(db.Date, nullable=True)
    data_prova = db.Column(db.Date, nullable=True)
    costureira = db.Column(db.String(100))
    status = db.Column(db.String(50), default='aguardando_croqui')
    observacoes = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    materiais = db.relationship('AtelieMaterial', backref='pedido', lazy=True, cascade='all, delete-orphan')
    historico = db.relationship('AtelieHistorico', backref='pedido', lazy=True, cascade='all, delete-orphan', order_by='AtelieHistorico.criado_em')
    cliente = db.relationship('Cliente', backref='atelie_pedidos', lazy=True)

    STATUS_LABELS = {
        'aguardando_croqui': 'Aguardando Croqui',
        'croqui_aprovado': 'Croqui Aprovado',
        'compra_material': 'Compra de Material',
        'em_corte': 'Em Corte',
        'em_costura': 'Em Costura',
        'com_bordadeira': 'Com Bordadeira',
        'ajustes_finais': 'Ajustes Finais',
        'pronto': 'Pronto para Entrega',
        'entregue': 'Entregue',
    }

    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self.status, self.status)

    @property
    def dias_para_entrega(self):
        if not self.data_entrega:
            return None
        from datetime import date
        delta = (self.data_entrega - date.today()).days
        return delta

    def __repr__(self):
        return f'<AteliePedido #{self.id} {self.nome_cliente}>'


class AtelieMaterial(db.Model):
    __tablename__ = 'atelie_materiais'

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('atelie_pedidos.id'), nullable=False)
    nome = db.Column(db.String(150), nullable=False)
    quantidade = db.Column(db.String(50))
    unidade = db.Column(db.String(20), default='metros')
    cor = db.Column(db.String(50))
    fornecedor = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pendente')
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    STATUS_LABELS = {
        'pendente': 'Pendente',
        'em_compra': 'Em Compra',
        'no_atelie': 'No Ateliê',
        'usado': 'Usado',
    }

    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self.status, self.status)


class AtelieHistorico(db.Model):
    __tablename__ = 'atelie_historico'

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('atelie_pedidos.id'), nullable=False)
    autor = db.Column(db.String(100))
    mensagem = db.Column(db.Text, nullable=False)
    status_novo = db.Column(db.String(50))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
