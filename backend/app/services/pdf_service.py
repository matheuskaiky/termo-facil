import hashlib
import html
import io
from datetime import datetime

from sqlalchemy.orm import Session
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from app.models import Depoimento
from app.core.exceptions import DepoimentoNotFoundError, TermosNotFoundError, TextoAusenteError


_AI_DISCLAIMER_BASE = (
    "Documento gerado com assistência de Inteligência Artificial e revisado por autoridade policial"
)
_FONT = 'Helvetica-Oblique'
_FONT_SIZE = 7.5
_FOOTER_MAX_WIDTH = 504 - 55


def _build_footer_drawer(nome_usuario: str, matricula_usuario: str):
    """Returns a canvas callback that stamps the AI/authority disclaimer and page number."""
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
        if canvas.stringWidth(single_line, _FONT, _FONT_SIZE) <= _FOOTER_MAX_WIDTH:
            canvas.drawCentredString(cx, 22, single_line)
        else:
            canvas.drawCentredString(cx, 29, _AI_DISCLAIMER_BASE)
            canvas.drawCentredString(cx, 19, authority_line)
        canvas.setFont('Helvetica', _FONT_SIZE)
        canvas.drawRightString(right_edge, 22, f"Página {canvas.getPageNumber()}")
        canvas.restoreState()

    return _draw


def _build_styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "base": base,
        "header": ParagraphStyle('SSP_Header', fontName='Helvetica-Bold', fontSize=10, leading=14, alignment=1),
        "title": ParagraphStyle('SSP_Title', fontName='Helvetica-Bold', fontSize=13, leading=18, alignment=1, spaceAfter=6, spaceBefore=10),
        "annex_title": ParagraphStyle('SSP_AnnexTitle', fontName='Helvetica-Bold', fontSize=12, leading=16, alignment=1, spaceAfter=6),
        "label_bold": ParagraphStyle('SSP_Label', fontName='Helvetica-Bold', fontSize=10, leading=14),
        "body": ParagraphStyle('SSP_Body', fontName='Helvetica', fontSize=11, leading=16, alignment=4, spaceAfter=12),
        "center_text": ParagraphStyle('SSP_CenterSign', fontName='Helvetica', fontSize=10, leading=14, alignment=1),
        "italic_center": ParagraphStyle('SSP_ItalicSign', fontName='Helvetica-Oblique', fontSize=9, leading=12, alignment=1),
        "small_italic": ParagraphStyle('SSP_SmallItalic', fontName='Helvetica-Oblique', fontSize=8, leading=11, textColor=colors.HexColor('#555555')),
        "segment": ParagraphStyle('SSP_Segment', fontName='Helvetica', fontSize=9.5, leading=14, spaceAfter=4),
    }


def _resolve_metadata(depoimento: Depoimento, termos_finais) -> dict:
    """Extracts all display values from ORM objects into a plain dict."""
    job = termos_finais.job
    return {
        "nome_usuario": depoimento.usuario.nome if depoimento.usuario else "Não informado",
        "matricula_usuario": depoimento.usuario.matricula if depoimento.usuario else "N/A",
        "nome_depoente": depoimento.depoente.nome_depoente if depoimento.depoente else "Não informado",
        "cpf_depoente": depoimento.depoente.cpf if depoimento.depoente else "Não informado",
        "condicao": depoimento.tipo_depoente.value if depoimento.tipo_depoente else "Não especificado",
        "tipo_depoente_str": depoimento.tipo_depoente.value.upper() if depoimento.tipo_depoente else "DEPOENTE",
        "nome_delegacia": (
            depoimento.inquerito.delegacia.nome_unidade.upper()
            if depoimento.inquerito and depoimento.inquerito.delegacia
            else "DELEGACIA DE POLÍCIA CIVIL"
        ),
        "num_proc": depoimento.inquerito.num_procedimento if depoimento.inquerito else "Não informado",
        "data_inst": (
            depoimento.inquerito.data_instauracao.strftime('%d/%m/%Y')
            if depoimento.inquerito and depoimento.inquerito.data_instauracao
            else "--/--/----"
        ),
        "nome_asr": job.modelo_asr.nome_modelo if job and job.modelo_asr else "Não informado",
        "nome_llm": job.modelo_llm.nome_modelo if job and job.modelo_llm else "Não informado",
        "data_geracao": datetime.now().strftime('%d/%m/%Y às %H:%M'),
        "segmentos": termos_finais.segmentos_asr or [],
        "txt_literal": termos_finais.txt_literal_asr or "",
    }


def _build_part1_content(meta: dict, texto_final: str, styles: dict) -> list:
    """Builds flowables for Part 1 — official testimony term."""
    s = styles
    story = [
        Paragraph("ESTADO DO PIAUÍ", s["header"]),
        Paragraph("SECRETARIA DE SEGURANÇA PÚBLICA", s["header"]),
        Paragraph(meta["nome_delegacia"], s["header"]),
        Spacer(1, 12),
        Paragraph(f"TERMO DE DEPOIMENTO ({meta['tipo_depoente_str']})", s["title"]),
        Paragraph("Parte 1 de 2 — Termo Oficial", s["italic_center"]),
        Spacer(1, 10),
    ]

    meta_rows = [
        [Paragraph("Procedimento / IP nº:", s["label_bold"]), Paragraph(meta["num_proc"], s["base"]['Normal'])],
        [Paragraph("Data de Instauração:", s["label_bold"]), Paragraph(meta["data_inst"], s["base"]['Normal'])],
        [Paragraph("Autoridade Responsável:", s["label_bold"]), Paragraph(f"{meta['nome_usuario']} (Matrícula: {meta['matricula_usuario']})", s["base"]['Normal'])],
        [Paragraph("Nome do Depoente:", s["label_bold"]), Paragraph(meta["nome_depoente"], s["base"]['Normal'])],
        [Paragraph("CPF:", s["label_bold"]), Paragraph(meta["cpf_depoente"], s["base"]['Normal'])],
        [Paragraph("Condição Jurídica:", s["label_bold"]), Paragraph(meta["condicao"], s["base"]['Normal'])],
        [Paragraph("Modelos IA (ASR / LLM):", s["label_bold"]), Paragraph(f"{meta['nome_asr']} / {meta['nome_llm']}", s["base"]['Normal'])],
        [Paragraph("Documento gerado em:", s["label_bold"]), Paragraph(meta["data_geracao"], s["base"]['Normal'])],
    ]
    meta_table = Table(meta_rows, colWidths=[160, 344])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('LINEBELOW', (0, 7), (1, 7), 1, colors.gray),
    ]))
    story += [
        meta_table,
        Spacer(1, 15),
        Paragraph("DEPOIMENTO / DECLARAÇÕES PRESTADAS", s["label_bold"]),
        Spacer(1, 8),
        Paragraph(texto_final.replace('\n', '<br/>'), s["body"]),
        Spacer(1, 20),
        Paragraph("Nada mais havendo a declarar, foi lavrado o presente termo.", s["base"]['Normal']),
        Spacer(1, 45),
        Paragraph("__________________________________________________", s["center_text"]),
        Paragraph(meta["nome_usuario"], s["center_text"]),
        Paragraph("Autoridade Policial / Escrivão de Polícia", s["italic_center"]),
        Spacer(1, 40),
        Paragraph("__________________________________________________", s["center_text"]),
        Paragraph(meta["nome_depoente"], s["center_text"]),
        Paragraph(f"Depoente ({meta['condicao']})", s["italic_center"]),
    ]
    return story


def _build_part2_transcript(meta: dict, styles: dict) -> list:
    """Builds flowables for Part 2 — raw ASR transcript annex."""
    s = styles
    story = [
        PageBreak(),
        Paragraph("ESTADO DO PIAUÍ", s["header"]),
        Paragraph("SECRETARIA DE SEGURANÇA PÚBLICA", s["header"]),
        Paragraph(meta["nome_delegacia"], s["header"]),
        Spacer(1, 12),
        Paragraph("ANEXO I — TRANSCRIÇÃO LITERAL COM MARCAÇÃO DE TEMPO", s["annex_title"]),
        Paragraph("Parte 2 de 2 — Transcrição ASR (Gerada Automaticamente)", s["italic_center"]),
        Spacer(1, 5),
        Paragraph(
            f"Modelo ASR: <b>{html.escape(meta['nome_asr'])}</b> &nbsp;·&nbsp; "
            f"Modelo LLM: <b>{html.escape(meta['nome_llm'])}</b> &nbsp;·&nbsp; "
            f"Gerado em: {meta['data_geracao']}",
            s["small_italic"],
        ),
        Spacer(1, 8),
        HRFlowable(width="100%", thickness=0.5, color=colors.gray),
        Spacer(1, 10),
        Paragraph(
            "<i>Este anexo reproduz integralmente a transcrição automática do áudio do depoimento, "
            "incluindo eventuais erros de reconhecimento de fala. "
            "O texto oficial é o constante na Parte 1 deste documento.</i>",
            s["small_italic"],
        ),
        Spacer(1, 14),
    ]

    if meta["segmentos"]:
        for seg in meta["segmentos"]:
            start = seg.get('start', 0)
            m, sec = int(start // 60), int(start % 60)
            story.append(Paragraph(
                f"<b>[{m:02d}:{sec:02d}]</b> <b>{html.escape(seg.get('speaker', ''))}:</b> "
                f"{html.escape(seg.get('text', '').strip())}",
                s["segment"],
            ))
    elif meta["txt_literal"]:
        story.append(Paragraph(meta["txt_literal"].replace('\n', '<br/>'), s["body"]))
    else:
        story.append(Paragraph("<i>Transcrição literal não disponível.</i>", s["small_italic"]))

    return story


def gerar_pdf_termo_depoimento(db: Session, id_depoimento) -> tuple[bytes, str]:
    """
    Orchestrates PDF generation for a testimony term.
    Raises DepoimentoNotFoundError, TermosNotFoundError, or TextoAusenteError on invalid state.
    """
    depoimento = db.query(Depoimento).filter(Depoimento.id_depoimento == id_depoimento).first()
    if not depoimento:
        raise DepoimentoNotFoundError(f"Depoimento {id_depoimento} não encontrado.")

    termos_finais = depoimento.termos_finais
    if not termos_finais:
        raise TermosNotFoundError("Termos de transcrição e síntese da IA não encontrados para este depoimento.")

    texto_final = termos_finais.txt_editado_humano or termos_finais.txt_original_ia
    if not texto_final:
        raise TextoAusenteError("Não há texto de depoimento disponível para gerar o documento.")

    meta = _resolve_metadata(depoimento, termos_finais)
    styles = _build_styles()

    story = _build_part1_content(meta, texto_final, styles)
    story += _build_part2_transcript(meta, styles)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    footer = _build_footer_drawer(meta["nome_usuario"], meta["matricula_usuario"])
    doc.build(story, onFirstPage=footer, onLaterPages=footer)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes, hashlib.sha256(pdf_bytes).hexdigest()
