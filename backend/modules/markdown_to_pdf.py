"""
Markdown to PDF Converter Module
Converts markdown report to professional PDF using reportlab.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import io
from datetime import datetime
import re


class MarkdownToPDF:
    """Converts markdown text to professional PDF."""
    
    def __init__(self):
        """Initialize converter."""
        pass
    
    def _parse_markdown(self, markdown_text: str) -> list:
        """
        Parse markdown into structured elements.
        
        Args:
            markdown_text: Markdown formatted text
            
        Returns:
            List of (type, content) tuples
        """
        elements = []
        lines = markdown_text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Headings
            if line.startswith('# '):
                elements.append(('h1', line[2:].strip()))
            elif line.startswith('## '):
                elements.append(('h2', line[3:].strip()))
            elif line.startswith('### '):
                elements.append(('h3', line[4:].strip()))
            
            # Lists
            elif line.startswith('- '):
                items = []
                while i < len(lines) and lines[i].startswith('- '):
                    items.append(lines[i][2:].strip())
                    i += 1
                elements.append(('list', items))
                i -= 1  # Back up since loop will increment
            
            # Bold/Italic
            elif line.strip() and not line.startswith('#'):
                # Clean up markdown formatting
                cleaned = line.strip()
                cleaned = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', cleaned)
                cleaned = re.sub(r'\*(.*?)\*', r'<i>\1</i>', cleaned)
                cleaned = re.sub(r'__(.*?)__', r'<b>\1</b>', cleaned)
                cleaned = re.sub(r'_(.*?)_', r'<i>\1</i>', cleaned)
                
                if cleaned:
                    elements.append(('paragraph', cleaned))
            
            i += 1
        
        return elements
    
    def markdown_to_pdf(self, markdown_text: str, filename: str) -> bytes:
        """
        Convert markdown to PDF.
        
        Args:
            markdown_text: Markdown formatted text
            filename: Original filename for report title
            
        Returns:
            PDF bytes
        """
        # Create in-memory PDF
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=0.6 * inch,
            leftMargin=0.6 * inch,
            topMargin=0.6 * inch,
            bottomMargin=0.6 * inch,
        )
        
        # Define styles
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        h2_style = ParagraphStyle(
            'CustomH2',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=10,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        h3_style = ParagraphStyle(
            'CustomH3',
            parent=styles['Heading3'],
            fontSize=11,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=8,
            spaceBefore=8,
            fontName='Helvetica-Bold'
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            leading=13
        )
        
        list_style = ParagraphStyle(
            'CustomList',
            parent=styles['Normal'],
            fontSize=10,
            leftIndent=20,
            spaceAfter=6,
            leading=12
        )
        
        elements = []
        
        # Add header
        clean_filename = filename.replace('.pdf', '')
        elements.append(Paragraph("Insurance Policy Analysis Report", title_style))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(f"<i>{clean_filename}</i>", body_style))
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", body_style))
        elements.append(Spacer(1, 12))
        
        # Parse and add markdown content
        parsed = self._parse_markdown(markdown_text)
        
        for elem_type, content in parsed:
            try:
                if elem_type == 'h1':
                    elements.append(Paragraph(content, title_style))
                    elements.append(Spacer(1, 8))
                
                elif elem_type == 'h2':
                    elements.append(Paragraph(content, h2_style))
                
                elif elem_type == 'h3':
                    elements.append(Paragraph(content, h3_style))
                
                elif elem_type == 'list':
                    for item in content:
                        elements.append(Paragraph(f"• {item}", list_style))
                    elements.append(Spacer(1, 6))
                
                elif elem_type == 'paragraph':
                    elements.append(Paragraph(content, body_style))
                
                # Add page break every ~30 elements to avoid overflow
                if len(elements) > 0 and len(elements) % 30 == 0:
                    elements.append(PageBreak())
            
            except Exception as e:
                print(f"Warning: Could not render element: {str(e)}")
                continue
        
        # Add footer
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(
            "<i>This is a professional analysis generated by an insurance policy analyzer. "
            "For official policy terms, refer to the original policy document.</i>",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8,
                         textColor=colors.grey, alignment=TA_CENTER)
        ))
        
        # Build PDF
        try:
            doc.build(elements)
        except Exception as e:
            print(f"Error building PDF: {str(e)}")
        
        # Get PDF bytes
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
