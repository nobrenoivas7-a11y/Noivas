from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import cm

ROSE_GOLD = colors.HexColor('#B76E79')
ROSE_LIGHT = colors.HexColor('#F5E6E8')
ROSE_MID = colors.HexColor('#E8C5C9')
BRANCO = colors.white
CINZA_ESCURO = colors.HexColor('#3D3D3D')
CINZA_CLARO = colors.HexColor('#F9F4F5')
PRETO = colors.black

W, H = A4

def gerar_pdf_contrato(contrato):
    buf = BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)
    _draw_page(c, contrato)
    c.save()
    return buf.getvalue()

def _draw_page(c, contrato):
    y = H

    # ── CABEÇALHO ──────────────────────────────────────────
    c.setFillColor(ROSE_GOLD)
    c.rect(0, H - 3*cm, W, 3*cm, fill=1, stroke=0)

    c.setFillColor(BRANCO)
    c.setFont('Helvetica-Bold', 20)
    c.drawCentredString(W/2, H - 1.2*cm, 'NOBRE ELEGANCY')
    c.setFont('Helvetica', 8.5)
    c.drawCentredString(W/2, H - 1.75*cm, 'ALUGUEL DE TRAJES FINOS LTDA  —  CNPJ: 12.592.893/0001-90')
    c.drawCentredString(W/2, H - 2.15*cm, 'R. Alberto Magno, 203 — Bom Futuro, Fortaleza/CE  |  Tel: (85) 99109-0408')
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(W/2, H - 2.75*cm, 'INSTRUMENTO PARTICULAR DE CONTRATO DE LOCAÇÃO')

    y = H - 3.5*cm

    # ── SEÇÃO: PARTES ──────────────────────────────────────
    y = _secao(c, y, 'PARTES')
    dados_partes = [
        ('Contratada:', 'Nobre Elegancy Aluguel de Trajes Finos Ltda'),
        ('Contratante:', contrato.cliente.nome),
        ('CPF:', contrato.cliente.cpf or 'Não informado'),
        ('Telefone:', contrato.cliente.telefone or 'Não informado'),
        ('Endereço:', contrato.cliente.endereco or 'Não informado'),
    ]
    for label, valor in dados_partes:
        y = _linha(c, y, label, valor)

    y -= 0.3*cm

    # ── SEÇÃO: DADOS DO EVENTO ─────────────────────────────
    y = _secao(c, y, 'OBJETO DO CONTRATO')
    obs = contrato.observacoes or ''
    tipo_evento = _extrair_obs(obs, 'Tipo do evento:')
    if contrato.primeiro_aluguel:
        pecas_str = 'Vestido sob medida (Primeiro Aluguel — confeccionado conforme croqui aprovado)'
    else:
        pecas_str = ', '.join([f'{i.peca.codigo} — {i.peca.modelo} ({i.peca.cor}, T{i.peca.tamanho})' for i in contrato.itens]) or 'Não informado'
    dados_evento = [
        ('Tipo do Evento:', tipo_evento or 'Não informado'),
        ('Item(ns) Locado(s):', pecas_str),
        ('Data de Retirada:', contrato.data_retirada.strftime('%d/%m/%Y')),
        ('Data de Devolução:', contrato.data_devolucao.strftime('%d/%m/%Y')),
        ('Contrato Nº:', f'#{contrato.id:04d}'),
    ]
    for label, valor in dados_evento:
        y = _linha(c, y, label, valor)

    y -= 0.3*cm

    # ── SEÇÃO: MEDIDAS ─────────────────────────────────────
    campos_medida = ['Busto', 'Cintura', 'Quadril', 'Barra/Comprimento', 'Alça', 'Manga', 'Obs. Medidas']
    medidas_existentes = [(campo, _extrair_obs(obs, f'{campo}:')) for campo in campos_medida]
    medidas_existentes = [(c_, v) for c_, v in medidas_existentes if v]
    if medidas_existentes:
        y = _secao(c, y, 'MEDIDAS DA NOIVA')
        for campo, val in medidas_existentes:
            y = _linha(c, y, f'{campo}:', val)
        y -= 0.3*cm

    # ── SEÇÃO: VALORES ─────────────────────────────────────
    y = _secao(c, y, 'DO PREÇO E DAS CONDIÇÕES DE PAGAMENTO')
    pagamentos = contrato.pagamentos
    forma = pagamentos[0].forma.replace('_', ' ').title() if pagamentos else 'Não informado'
    dados_valores = [
        ('Valor Total:', f'R$ {contrato.valor_total:.2f}'.replace('.', ',')),
        ('Valor Pago:', f'R$ {contrato.valor_pago:.2f}'.replace('.', ',')),
        ('Saldo Restante:', f'R$ {contrato.saldo_restante:.2f}'.replace('.', ',')),
        ('Forma de Pagamento:', forma),
    ]
    for label, valor in dados_valores:
        y = _linha(c, y, label, valor)

    y -= 0.5*cm

    # ── CLÁUSULAS ──────────────────────────────────────────
    clausulas = [
        "CLÁUSULA 1 – DO OBJETO: O presente contrato tem como objeto a locação por prazo certo e determinado dos produtos, devidamente descritos no Quadro Resumo, de propriedade da LOCADORA, e escolhidos pela LOCATÁRIA, de acordo com a disponibilidade.",
        "CLÁUSULA 2 – DO PRAZO: 2.1 O prazo de cada locação é de 03 (três) dias, compreendendo o dia de entrega e devolução dos produtos, salvo casos pré-estabelecidos no fechamento do contrato e devidamente indicados no Quadro Resumo. 2.2 As datas de entrega e devolução dos produtos estão definidas no Quadro Resumo, e devem ser cumpridas entre as partes. 2.3 Caso os produtos locados não sejam devolvidos na data prevista pela LOCATÁRIA, serão cobrados de forma proporcional os valores indicados na Cláusula 3.",
        "CLÁUSULA 3 – DO PAGAMENTO: 3.1 O valor de entrada referente à reserva do vestido deverá ser pago no ato da confirmação, garantindo o fechamento do contrato e a reserva do produto. 3.2 O valor remanescente deverá ser pago pela LOCATÁRIA até a data da retirada.",
        "CLÁUSULA 4 – DAS RESPONSABILIDADES DA LOCADORA: 4.1 A LOCADORA compromete-se a entregar os produtos locados à LOCATÁRIA limpos, em adequado estado de conservação e prontos para utilização na data solicitada. 4.2 Caso seja constatada alguma avaria no momento da retirada, a LOCADORA se compromete a efetuar prontamente o reparo e, se não for possível fazê-lo, a substituição ou troca do produto, independente do seu preço de locação, conforme disponibilidade no acervo. 4.3 Em caso de eventual impossibilidade da entrega dos produtos locados, os valores pagos serão integralmente restituídos à LOCATÁRIA. 4.4 A LOCADORA entregará as peças diretamente à LOCATÁRIA ou a quem esta indicar, mediante indicação expressa por qualquer meio de comunicação. Nesta situação, a LOCADORA isenta-se de responsabilidade caso a LOCATÁRIA não realize a prova final dos produtos locados.",
        "CLÁUSULA 5 – DAS RESPONSABILIDADES DA LOCATÁRIA: 5.1 A LOCATÁRIA, no ato da retirada dos produtos, declara que os recebeu em adequado estado de conservação, prontos para uso, com os devidos ajustes realizados. 5.2 Após o recebimento dos produtos, a LOCATÁRIA assume o compromisso e a responsabilidade pela guarda, cuidado e utilização com zelo dos produtos locados, responsabilizando-se por eventual perda, destruição, manchas e/ou quaisquer danos que ocorram, sendo expressamente proibido à LOCATÁRIA lavar ou ajustar os produtos locados. 5.3 Em caso de perda ou dano irreparável dos produtos locados, a LOCATÁRIA se compromete a pagar, a título de indenização, o valor de 50% (cinquenta por cento) do valor do aluguel integral do referido produto, no ato da devolução dos produtos. 5.4 A LOCATÁRIA se compromete a devolver todos os produtos locados, além de seus acessórios, capas, embalagens e cabides, na data indicada no ato da contratação. Em caso de perda ou dano das capas, será cobrada multa de R$ 100,00 (cem reais); R$ 40,00 (quarenta reais) para embalagens de acessórios; e R$ 10,00 (dez reais) para cabides.",
        "CLÁUSULA 6 – DO CANCELAMENTO: 6.1 Em caso de cancelamento, por quaisquer motivos, este deverá ser comunicado expressamente pela LOCATÁRIA até a data de início da locação. 6.2 A LOCATÁRIA receberá um voucher com crédito de 100% do valor até então pago, para utilização em uma nova locação no prazo de até 12 (doze) meses da data de sua emissão. 6.3 Caso a solicitação de cancelamento da locação seja realizada pela LOCATÁRIA após os ajustes e/ou consertos realizados, o custo destes serviços será descontado do valor do voucher.",
        "CLÁUSULA 7 – PROVAS E AJUSTES: 7.1 As provas acontecem em horário comercial (segunda a quinta-feira, das 9h às 17h), sendo os horários definidos entre cliente e equipe de prova de acordo com suas disponibilidades. Provas solicitadas fora do horário comercial terão taxa de R$ 120,00. 7.2 Em caso de desistência da LOCATÁRIA por não satisfação dos ajustes realizados, caberá à LOCADORA a disponibilização de outras peças de seu acervo para utilização da mesma. Se, após todas as tratativas para resolução por parte da LOCADORA, a LOCATÁRIA ainda assim optar pela desistência do serviço, a LOCADORA ficará isenta de qualquer responsabilidade financeira decorrente.",
        "CLÁUSULA 8 – DA TROCA: 8.1 A troca dos produtos locados poderá ser realizada em até 15 (quinze) dias corridos antes do início da locação, mediante prévia autorização da LOCADORA, de acordo com sua disponibilidade e viabilidade de ajustes. 8.2 Caso a LOCATÁRIA já tenha realizado os ajustes da locação, deverá efetuar o pagamento à LOCADORA dos mesmos, mediante breve orçamento elaborado pela equipe técnica da LOCADORA, para garantir a troca dos produtos.",
        "CLÁUSULA 9 – TROCA DE MODELO DO TRAJE: 9.1 A CONTRATANTE poderá solicitar a troca do modelo do traje locado, desde que a solicitação seja feita antes do início das provas e esteja sujeita à disponibilidade do acervo da CONTRATADA. 9.2 Havendo disponibilidade, a troca poderá ser realizada mediante assinatura de aditivo contratual. Caso o novo modelo escolhido possua valor superior ao originalmente contratado, a CONTRATANTE deverá efetuar o pagamento integral da diferença de valor antes da confirmação da troca. Se o novo modelo possuir valor inferior, não haverá devolução, abatimento ou crédito da diferença já paga. 9.3 A troca somente será considerada efetivada após a confirmação da disponibilidade do novo traje e da quitação dos valores eventualmente devidos.",
        "CLÁUSULA 10 – DAS DISPOSIÇÕES GERAIS: 10.1 Todas as cobranças decorrentes do presente contrato estão sujeitas a protesto e inclusão do nome do devedor nos cadastros dos órgãos de proteção ao crédito, sendo que os custos decorrentes de cobrança, incluindo, sem limitação, honorários advocatícios, serão de responsabilidade do devedor. 10.2 As partes elegem o Foro da Comarca de Fortaleza/CE como competente para dirimir quaisquer dúvidas oriundas do presente contrato, com exclusão de qualquer outro, por mais privilegiado que possa ser.",
        "Declaro que tenho conhecimento das cláusulas contratuais que tratam da conservação dos produtos, bem como de todas as demais cláusulas previstas nas Condições Gerais do Contrato.",
    ]

    if y < 7*cm:
        c.showPage()
        y = H - 1.5*cm

    y = _secao(c, y, 'CONDIÇÕES GERAIS DO CONTRATO')
    c.setFont('Helvetica', 7.5)
    c.setFillColor(CINZA_ESCURO)
    for cl in clausulas:
        if y < 5*cm:
            c.showPage()
            y = H - 1.5*cm
            c.setFont('Helvetica', 7.5)
            c.setFillColor(CINZA_ESCURO)
        lines = _wrap(c, cl, W - 3*cm, 'Helvetica', 7.5)
        for line in lines:
            if y < 2*cm:
                c.showPage()
                y = H - 1.5*cm
                c.setFont('Helvetica', 7.5)
                c.setFillColor(CINZA_ESCURO)
            c.drawString(1.5*cm, y, line)
            y -= 0.38*cm
        y -= 0.15*cm

    y -= 0.5*cm

    # ── ASSINATURAS ────────────────────────────────────────
    if y < 4*cm:
        c.showPage()
        y = H - 1.5*cm

    c.setStrokeColor(ROSE_MID)
    c.line(1.5*cm, y, 9*cm, y)
    c.line(11*cm, y, W - 1.5*cm, y)
    c.setFont('Helvetica', 9)
    c.setFillColor(CINZA_ESCURO)
    c.drawCentredString(5.25*cm, y - 0.4*cm, 'Contratante')
    c.drawCentredString(16*cm, y - 0.4*cm, 'Contratada')
    c.drawCentredString(5.25*cm, y - 0.75*cm, contrato.cliente.nome)
    c.drawCentredString(16*cm, y - 0.75*cm, 'Nobre Elegancy Noivas')
    if contrato.cliente.cpf:
        c.setFont('Helvetica', 8)
        c.drawCentredString(5.25*cm, y - 1.1*cm, f'CPF: {contrato.cliente.cpf}')
    c.drawCentredString(16*cm, y - 1.1*cm, 'CNPJ: 12.592.893/0001-90')

    # ── RODAPÉ ─────────────────────────────────────────────
    c.setFillColor(ROSE_LIGHT)
    c.rect(0, 0, W, 1.2*cm, fill=1, stroke=0)
    c.setFillColor(ROSE_GOLD)
    c.setFont('Helvetica', 8)
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    c.drawString(1.5*cm, 0.45*cm, f'Gerado em: {agora}')
    c.drawCentredString(W/2, 0.45*cm, 'Nobre Elegancy — Fortaleza/CE')
    c.drawRightString(W - 1.5*cm, 0.45*cm, f'Contrato #{contrato.id:04d}')


def _secao(c, y, titulo):
    c.setFillColor(ROSE_LIGHT)
    c.rect(1*cm, y - 0.65*cm, W - 2*cm, 0.65*cm, fill=1, stroke=0)
    c.setFillColor(ROSE_GOLD)
    c.rect(1*cm, y - 0.65*cm, 0.25*cm, 0.65*cm, fill=1, stroke=0)
    c.setFont('Helvetica-Bold', 10)
    c.setFillColor(ROSE_GOLD)
    c.drawString(1.5*cm, y - 0.45*cm, titulo)
    return y - 0.85*cm


def _linha(c, y, label, valor):
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(ROSE_GOLD)
    c.drawString(1.5*cm, y, label)
    c.setFont('Helvetica', 9)
    c.setFillColor(CINZA_ESCURO)
    c.drawString(6*cm, y, str(valor))
    return y - 0.5*cm


def _extrair_obs(obs, campo):
    for linha in obs.split('\n'):
        if linha.strip().startswith(campo):
            return linha.split(':', 1)[1].strip() if ':' in linha else ''
    return ''


def _wrap(c, text, max_width, font, size):
    words = text.split()
    lines = []
    current = ''
    for word in words:
        test = f'{current} {word}'.strip()
        if c.stringWidth(test, font, size) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines
