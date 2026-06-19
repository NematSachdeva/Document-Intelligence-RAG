"""
Report Generator Module
Creates professional PDF reports from insurance policy analysis.
"""

from typing import Dict
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import io
from datetime import datetime


class ReportGenerator:
    """Generates professional PDF reports from insurance policy analysis."""
    
    def __init__(self):
        """Initialize report generator."""
        self.page_width, self.page_height = letter
        
    def generate_policy_report(self, filename: str, analysis_data: Dict, summary_text: str = "") -> bytes:
        """
        Generate a professional PDF report from insurance policy analysis.
        
        Args:
            filename: Original PDF filename (used as report title)
            analysis_data: Dict with 13 insurance policy fields
            summary_text: Optional summary of the policy
            
        Returns:
            bytes: PDF file content
        """
        # Create in-memory PDF
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )
        
        # Container for PDF elements
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=10,
            spaceBefore=12,
            fontName='Helvetica-Bold',
            borderColor=colors.HexColor('#1e40af'),
            borderWidth=2,
            borderPadding=8,
            borderRadius=4
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            leading=14
        )
        
        label_style = ParagraphStyle(
            'Label',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#374151'),
            fontName='Helvetica-Bold',
            spaceAfter=4
        )
        
        # Report Title
        clean_filename = filename.replace('.pdf', '').replace('_', ' ')
        elements.append(Paragraph(f"Insurance Policy Analysis Report", title_style))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(f"<i>{clean_filename}</i>", body_style))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(
            f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            body_style
        ))
        elements.append(Spacer(1, 12))
        
        # Divider line
        from reportlab.platypus import Table as RLTable
        divider_data = [['']]
        divider_table = RLTable(divider_data)
        divider_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, -1), 2, colors.HexColor('#1e40af')),
        ]))
        elements.append(divider_table)
        elements.append(Spacer(1, 12))
        
        # Executive Summary (if provided)
        if summary_text:
            elements.append(Paragraph("Executive Summary", heading_style))
            elements.append(Paragraph(summary_text, body_style))
            elements.append(Spacer(1, 12))
        
        # Policy Details Section
        elements.append(Paragraph("Policy Details", heading_style))
        
        # Create policy information table
        policy_fields = [
            ('Policy Overview', analysis_data.get('policy_overview', 'Not specified')),
            ('Coverage Amount', analysis_data.get('coverage_amount', 'Not specified')),
            ('Premium Amount', analysis_data.get('premium_amount', 'Not specified')),
            ('Policy Duration', analysis_data.get('policy_duration', 'Not specified')),
            ('Covered Items', analysis_data.get('covered_items', 'Not specified')),
            ('Exclusions', analysis_data.get('exclusions', 'Not specified')),
            ('Waiting Periods', analysis_data.get('waiting_periods', 'Not specified')),
            ('Deductibles', analysis_data.get('deductibles', 'Not specified')),
            ('Co-pay Clauses', analysis_data.get('copay_clauses', 'Not specified')),
            ('Renewal Clauses', analysis_data.get('renewal_clauses', 'Not specified')),
            ('Cancellation Clauses', analysis_data.get('cancellation_clauses', 'Not specified')),
            ('Major Risks', analysis_data.get('major_risks', 'Not specified')),
        ]
        
        # Add each field as a section
        for i, (field_name, field_value) in enumerate(policy_fields):
            # Field label
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(f"<b>{field_name}</b>", label_style))
            
            # Field value - truncate very long values
            value_text = str(field_value)
            if len(value_text) > 500:
                value_text = value_text[:497] + "..."
            
            elements.append(Paragraph(value_text, body_style))
            
            # Add page break after every 4-5 fields
            if (i + 1) % 5 == 0 and i < len(policy_fields) - 1:
                elements.append(PageBreak())
        
        # Assessment Section
        elements.append(PageBreak())
        elements.append(Paragraph("Professional Assessment", heading_style))
        assessment = analysis_data.get('overall_assessment', 'Assessment not available')
        elements.append(Paragraph(str(assessment), body_style))
        
        # Footer
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(
            "<i>This report is auto-generated from document analysis. "
            "For official policy information, refer to the original policy document.</i>",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, 
                         textColor=colors.grey, alignment=TA_CENTER)
        ))
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF bytes
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()

