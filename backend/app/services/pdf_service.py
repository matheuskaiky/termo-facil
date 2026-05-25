import io
import html
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import Depoimento
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


_AI_DISCLAIMER_BASE = (
    "Documento gerado com assistência de Inteligência Artificial e revisado por autoridade policial"
)

_FONT = 'Helvetica-Oblique'
_FONT_SIZE = 7.5
# Reserve ~55pt on the right for the page-number stamp
_FOOTER_MAX_WIDTH = 504 - 55


def _build_footer_drawer(nome_usuario: str, matricula_usuario: str):
    """
    Returns a canvas callback that stamps the AI/authority disclaimer and page number.

    Single line when the full text fits; two lines otherwise:
      Line 1 – generic RN-02 disclaimer
      Line 2 – "Autoridade: <nome> (Mat. <matrícula>)"
    """
    single_line = (
        f"Documento gerado com assistência de Inteligência Artificial e "
        f"revisado por {nome_usuario} (Mat. {matricula_usuario})"
    )
    authority_line = f"Autoridade responsável: {nome_usuario} (Mat. {matricula_usuario})"

    def _draw(canvas, doc):
        canvas.saveState()
        page_width, _ = doc.pagesize
        cx = page_width / 2
        right_edge = page_width - 54

        canvas.setFillColorRGB(0.45, 0.45, 0.45)
        canvas.setFont(_FONT, _FONT_SIZE)

        text_width = canvas.stringWidth(single_line, _FONT, _FONT_SIZE)
        if text_width <= _FOOTER_MAX_WIDTH:
            canvas.drawCentredString(cx, 22, single_line)
        else:
            # Two-line footer: generic disclaimer above, authority name below
            canvas.drawCentredString(cx, 29, _AI_DISCLAIMER_BASE)
            canvas.drawCentredString(cx, 19, authority_line)

        canvas.setFont('Helvetica', _FONT_SIZE)
        canvas.drawRightString(right_edge, 22, f"Página {canvas.getPageNumber()}")
        canvas.restoreState()

    return _draw


def gerar_pdf_termo_depoimento(db: Session, id_depoimento) -> bytes:
    depoimento = db.query(Depoimento).filter(Depoimento.id_depoimento == id_depoimento).first()
    if not depoimento:
        raise HTTPException(status_code=404, detail="Depoimento não encontrado.")

    termos_finais = depoimento.termos_finais
    if not termos_finais:
        raise HTTPException(status_code=404, detail="Termos de transcrição e síntese da IA não encontrados para este depoimento.")

    # Prioritize human-edited text over raw AI synthesis
    texto_final = termos_finais.txt_editado_humano or termos_finais.txt_original_ia
    if not texto_final:
        raise HTTPException(status_code=400, detail="Não há texto de depoimento disponível para gerar o documento.")

    # Resolve model names for traceability metadata
    job = termos_finais.job
    nome_asr = job.modelo_asr.nome_modelo if job and job.modelo_asr else "Não informado"
    nome_llm = job.modelo_llm.nome_modelo if job and job.modelo_llm else "Não informado"
    segmentos = termos_finais.segmentos_asr or []
    txt_literal = termos_finais.txt_literal_asr or ""
    data_geracao = datetime.now().strftime('%d/%m/%Y às %H:%M')

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    story = []

    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        'SSP_Header', fontName='Helvetica-Bold', fontSize=10, leading=14, alignment=1
    )
    title_style = ParagraphStyle(
        'SSP_Title', fontName='Helvetica-Bold', fontSize=13, leading=18,
        alignment=1, spaceAfter=6, spaceBefore=10
    )
    annex_title_style = ParagraphStyle(
        'SSP_AnnexTitle', fontName='Helvetica-Bold', fontSize=12, leading=16,
        alignment=1, spaceAfter=6
    )
    label_bold_style = ParagraphStyle(
        'SSP_Label', fontName='Helvetica-Bold', fontSize=10, leading=14
    )
    body_style = ParagraphStyle(
        'SSP_Body', fontName='Helvetica', fontSize=11, leading=16,
        alignment=4, spaceAfter=12
    )
    center_text_style = ParagraphStyle(
        'SSP_CenterSign', fontName='Helvetica', fontSize=10, leading=14, alignment=1
    )
    italic_center_style = ParagraphStyle(
        'SSP_ItalicSign', fontName='Helvetica-Oblique', fontSize=9, leading=12, alignment=1
    )
    small_italic_style = ParagraphStyle(
        'SSP_SmallItalic', fontName='Helvetica-Oblique', fontSize=8, leading=11,
        textColor=colors.HexColor('#555555')
    )
    segment_style = ParagraphStyle(
        'SSP_Segment', fontName='Helvetica', fontSize=9.5, leading=14, spaceAfter=4
    )

    # ─── PARTE 1: TERMO OFICIAL ───────────────────────────────────────────────

    story.append(Paragraph("ESTADO DO PIAUÍ", header_style))
    story.append(Paragraph("SECRETARIA DE SEGURANÇA PÚBLICA", header_style))
    nome_delegacia = (
        depoimento.inquerito.delegacia.nome_unidade.upper()
        if depoimento.inquerito and depoimento.inquerito.delegacia
        else "DELEGACIA DE POLÍCIA CIVIL"
    )
    story.append(Paragraph(nome_delegacia, header_style))
    story.append(Spacer(1, 12))

    tipo_depoente_str = depoimento.tipo_depoente.value.upper() if depoimento.tipo_depoente else "DEPOENTE"
    story.append(Paragraph(f"TERMO DE DEPOIMENTO ({tipo_depoente_str})", title_style))
    story.append(Paragraph("Parte 1 de 2 — Termo Oficial", italic_center_style))
    story.append(Spacer(1, 10))

    num_proc = depoimento.inquerito.num_procedimento if depoimento.inquerito else "Não informado"
    data_inst = (
        depoimento.inquerito.data_instauracao.strftime('%d/%m/%Y')
        if depoimento.inquerito and depoimento.inquerito.data_instauracao
        else "--/--/----"
    )
    nome_usuario = depoimento.usuario.nome if depoimento.usuario else "Não informado"
    matricula_usuario = depoimento.usuario.matricula if depoimento.usuario else "N/A"
    nome_depoente = depoimento.depoente.nome_depoente if depoimento.depoente else "Não informado"
    cpf_depoente = depoimento.depoente.cpf if depoimento.depoente else "Não informado"
    condicao = depoimento.tipo_depoente.value if depoimento.tipo_depoente else "Não especificado"

    meta_data = [
        [Paragraph("Procedimento / IP nº:", label_bold_style), Paragraph(num_proc, styles['Normal'])],
        [Paragraph("Data de Instauração:", label_bold_style), Paragraph(data_inst, styles['Normal'])],
        [Paragraph("Autoridade Responsável:", label_bold_style), Paragraph(f"{nome_usuario} (Matrícula: {matricula_usuario})", styles['Normal'])],
        [Paragraph("Nome do Depoente:", label_bold_style), Paragraph(nome_depoente, styles['Normal'])],
        [Paragraph("CPF:", label_bold_style), Paragraph(cpf_depoente, styles['Normal'])],
        [Paragraph("Condição Jurídica:", label_bold_style), Paragraph(condicao, styles['Normal'])],
        [Paragraph("Modelos IA (ASR / LLM):", label_bold_style), Paragraph(f"{nome_asr} / {nome_llm}", styles['Normal'])],
        [Paragraph("Documento gerado em:", label_bold_style), Paragraph(data_geracao, styles['Normal'])],
    ]

    meta_table = Table(meta_data, colWidths=[160, 344])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('LINEBELOW', (0, 7), (1, 7), 1, colors.gray),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))

    story.append(Paragraph("DEPOIMENTO / DECLARAÇÕES PRESTADAS", label_bold_style))
    story.append(Spacer(1, 8))
    formatted_text = texto_final.replace('\n', '<br/>')
    story.append(Paragraph(formatted_text, body_style))
    story.append(Spacer(1, 20))

    story.append(Paragraph("Nada mais havendo a declarar, foi lavrado o presente termo.", styles['Normal']))
    story.append(Spacer(1, 45))

    story.append(Paragraph("__________________________________________________", center_text_style))
    story.append(Paragraph(nome_usuario, center_text_style))
    story.append(Paragraph("Autoridade Policial / Escrivão de Polícia", italic_center_style))
    story.append(Spacer(1, 40))

    story.append(Paragraph("__________________________________________________", center_text_style))
    story.append(Paragraph(nome_depoente, center_text_style))
    story.append(Paragraph(f"Depoente ({condicao})", italic_center_style))

    # ─── PARTE 2: ANEXO — TRANSCRIÇÃO LITERAL COM TIMESTAMPS ─────────────────

    story.append(PageBreak())

    story.append(Paragraph("ESTADO DO PIAUÍ", header_style))
    story.append(Paragraph("SECRETARIA DE SEGURANÇA PÚBLICA", header_style))
    story.append(Paragraph(nome_delegacia, header_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("ANEXO I — TRANSCRIÇÃO LITERAL COM MARCAÇÃO DE TEMPO", annex_title_style))
    story.append(Paragraph("Parte 2 de 2 — Transcrição ASR (Gerada Automaticamente)", italic_center_style))
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        f"Modelo ASR: <b>{html.escape(nome_asr)}</b> &nbsp;·&nbsp; "
        f"Modelo LLM: <b>{html.escape(nome_llm)}</b> &nbsp;·&nbsp; "
        f"Gerado em: {data_geracao}",
        small_italic_style,
    ))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.gray))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "<i>Este anexo reproduz integralmente a transcrição automática do áudio do depoimento, "
        "incluindo eventuais erros de reconhecimento de fala. "
        "O texto oficial é o constante na Parte 1 deste documento.</i>",
        small_italic_style,
    ))
    story.append(Spacer(1, 14))

    if segmentos:
        for seg in segmentos:
            start = seg.get('start', 0)
            speaker = html.escape(seg.get('speaker', ''))
            text = html.escape(seg.get('text', '').strip())
            m = int(start // 60)
            s = int(start % 60)
            timestamp = f"{m:02d}:{s:02d}"
            story.append(Paragraph(
                f"<b>[{timestamp}]</b> <b>{speaker}:</b> {text}",
                segment_style,
            ))
    elif txt_literal:
        formatted_literal = txt_literal.replace('\n', '<br/>')
        story.append(Paragraph(formatted_literal, body_style))
    else:
        story.append(Paragraph("<i>Transcrição literal não disponível.</i>", small_italic_style))

    # Build PDF — footer with RN-02 disclaimer + authority name stamped on every page
    footer = _build_footer_drawer(nome_usuario, matricula_usuario)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    import hashlib
    sha256 = hashlib.sha256(pdf_bytes).hexdigest()

    return pdf_bytes, sha256
