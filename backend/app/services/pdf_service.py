import io
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import Depoimento
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def gerar_pdf_termo_depoimento(db: Session, id_depoimento) -> bytes:
    """
    Fetches the complete testimony data from the database and generates 
    the official SSP-PI PDF document using ReportLab's Platypus engine.
    """
    # 1. Fetch the testimony record along with its database relationships
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

    # 2. Setup memory buffer and document template with strict margins
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
    
    # 3. Initialize and configure custom paragraph styles
    styles = getSampleStyleSheet()
    
    header_style = ParagraphStyle(
        'SSP_Header',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        alignment=1 # Center alignment
    )
    
    title_style = ParagraphStyle(
        'SSP_Title',
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=18,
        alignment=1,
        spaceAfter=15,
        spaceBefore=10
    )
    
    label_bold_style = ParagraphStyle(
        'SSP_Label',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14
    )
    
    body_style = ParagraphStyle(
        'SSP_Body',
        fontName='Helvetica',
        fontSize=11,
        leading=16,
        alignment=4, # Justified alignment
        spaceAfter=12
    )
    
    center_text_style = ParagraphStyle(
        'SSP_CenterSign', 
        fontName='Helvetica', 
        fontSize=10, 
        leading=14,
        alignment=1
    )
    
    italic_center_style = ParagraphStyle(
        'SSP_ItalicSign', 
        fontName='Helvetica-Oblique', 
        fontSize=9, 
        leading=12,
        alignment=1
    )

    # 4. Build the official Header Section
    story.append(Paragraph("ESTADO DO PIAUÍ", header_style))
    story.append(Paragraph("SECRETARIA DE SEGURANÇA PÚBLICA", header_style))
    nome_delegacia = depoimento.inquerito.delegacia.nome_unidade.upper() if depoimento.inquerito and depoimento.inquerito.delegacia else "DELEGACIA DE POLÍCIA CIVIL"
    story.append(Paragraph(nome_delegacia, header_style))
    story.append(Spacer(1, 15))
    
    # 5. Build the Document Title
    tipo_depoente_str = depoimento.tipo_depoente.value.upper() if depoimento.tipo_depoente else "DEPOENTE"
    story.append(Paragraph(f"TERMO DE DEPOIMENTO ({tipo_depoente_str})", title_style))
    
    # 6. Extract metadata info safely
    num_proc = depoimento.inquerito.num_procedimento if depoimento.inquerito else "Não informado"
    data_inst = depoimento.inquerito.data_instauracao.strftime('%d/%m/%Y') if depoimento.inquerito and depoimento.inquerito.data_instauracao else "--/--/----"
    nome_usuario = depoimento.usuario.nome if depoimento.usuario else "Não informado"
    matricula_usuario = depoimento.usuario.matricula if depoimento.usuario else "N/A"
    
    nome_depoente = depoimento.depoente.nome_depoente if depoimento.depoente else "Não informado"
    cpf_depoente = depoimento.depoente.cpf if depoimento.depoente else "Não informado"
    condicao = depoimento.tipo_depoente.value if depoimento.tipo_depoente else "Não especificado"
    
    # 7. Assemble the Case Metadata Table
    meta_data = [
        [Paragraph("Procedimento / IP nº:", label_bold_style), Paragraph(num_proc, styles['Normal'])],
        [Paragraph("Data de Instauração:", label_bold_style), Paragraph(data_inst, styles['Normal'])],
        [Paragraph("Autoridade Responsável:", label_bold_style), Paragraph(f"{nome_usuario} (Matrícula: {matricula_usuario})", styles['Normal'])],
        [Paragraph("Nome do Depoente:", label_bold_style), Paragraph(nome_depoente, styles['Normal'])],
        [Paragraph("CPF:", label_bold_style), Paragraph(cpf_depoente, styles['Normal'])],
        [Paragraph("Condição Jurídica:", label_bold_style), Paragraph(condicao, styles['Normal'])],
    ]
    
    # Set explicit column widths to guarantee structural alignment
    meta_table = Table(meta_data, colWidths=[140, 364])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('LINEBELOW', (0,5), (1,5), 1, colors.gray), # Divider line after metadata
    ]))
    
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # 8. Build the Statement Content Section
    story.append(Paragraph("DEPOIMENTO / DECLARAÇÕES PRESTADAS", label_bold_style))
    story.append(Spacer(1, 8))
    
    # Replace newlines with HTML line breaks to ensure correct text rendering in Paragraph flows
    formatted_text = texto_final.replace('\n', '<br/>')
    story.append(Paragraph(formatted_text, body_style))
    story.append(Spacer(1, 20))
    
    # 9. Build Closing Statement and Signature Fields
    story.append(Paragraph("Nada mais havendo a declarar, foi lavrado o presente termo.", styles['Normal']))
    story.append(Spacer(1, 45))
    
    # Authority Signature Block
    story.append(Paragraph("__________________________________________________", center_text_style))
    story.append(Paragraph(nome_usuario, center_text_style))
    story.append(Paragraph("Autoridade Policial / Escrivão de Polícia", italic_center_style))
    
    story.append(Spacer(1, 40))
    
    # Testifier Signature Block
    story.append(Paragraph("__________________________________________________", center_text_style))
    story.append(Paragraph(nome_depoente, center_text_style))
    story.append(Paragraph(f"Depoente ({condicao})", italic_center_style))
    
    # 10. Compile the document flow and extract content bytes
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    import hashlib
    sha256 = hashlib.sha256(pdf_bytes).hexdigest()
    
    return pdf_bytes, sha256