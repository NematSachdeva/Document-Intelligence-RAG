"""
Report Generator Module
Creates professional PDF reports from comprehensive insurance policy analysis.
"""

from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import io
from datetime import datetime


class ReportGenerator:
    """Generates professional PDF reports from comprehensive insurance policy analysis."""
    
    def __init__(self):
        """Initialize report generator."""
        self.page_width, self.page_height = letter
        
    def generate_policy_report(self, filename: str, analysis_data: Dict, summary_text: str = "") -> bytes:
        """
        Generate a professional PDF report from comprehensive insurance policy analysis.
        
        Args:
            filename: Original PDF filename (used as report title)
            analysis_data: Dict with comprehensive analysis sections
            summary_text: Optional summary of the policy
            
        Returns:
            bytes: PDF file content
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
        
        # Container for PDF elements
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=8,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        section_style = ParagraphStyle(
            'SectionHead',
            parent=styles['Heading2'],
            fontSize=13,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=10,
            spaceBefore=12,
            fontName='Helvetica-Bold',
            borderColor=colors.HexColor('#1e40af'),
            borderWidth=1.5,
            borderPadding=6
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            leading=13
        )
        
        # Title
        clean_filename = filename.replace('.pdf', '')
        elements.append(Paragraph("Insurance Policy Analysis Report", title_style))
        elements.append(Spacer(1, 3))
        elements.append(Paragraph(f"<i>{clean_filename}</i>", body_style))
        elements.append(Spacer(1, 2))
        elements.append(Paragraph(
            f"Generated: {datetime.now().strftime('%B %d, %Y')}",
            ParagraphStyle('Sub', parent=styles['Normal'], fontSize=9, textColor=colors.grey)
        ))
        elements.append(Spacer(1, 12))
        
        # POLICY SNAPSHOT
        if "policy_snapshot" in analysis_data:
            elements.append(Paragraph("POLICY SNAPSHOT", section_style))
            snapshot = analysis_data["policy_snapshot"]
            snapshot_data = [
                ["Policy Name", snapshot.get("policy_name", "N/A")],
                ["Insurance Company", snapshot.get("insurance_company", "N/A")],
                ["Policy Type", snapshot.get("policy_type", "N/A")],
                ["Policy Number/UIN", snapshot.get("policy_number_uin", "N/A")],
                ["Coverage Type", snapshot.get("coverage_type", "N/A")],
                ["Policy Duration", snapshot.get("policy_duration", "N/A")],
                ["Sum Insured", snapshot.get("sum_insured", "N/A")],
                ["Premium Amount", snapshot.get("premium_amount", "N/A")],
            ]
            
            snapshot_table = Table(snapshot_data, colWidths=[2*inch, 4.4*inch])
            snapshot_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0f2fe')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(snapshot_table)
            elements.append(Spacer(1, 12))
        
        # EXECUTIVE SUMMARY
        if "executive_summary" in analysis_data:
            elements.append(Paragraph("EXECUTIVE SUMMARY", section_style))
            elements.append(Paragraph(str(analysis_data["executive_summary"]), body_style))
            elements.append(Spacer(1, 12))
        
        # WHAT IS COVERED
        if "what_is_covered" in analysis_data and analysis_data["what_is_covered"]:
            elements.append(Paragraph("WHAT IS COVERED", section_style))
            coverages = analysis_data["what_is_covered"]
            if isinstance(coverages, list):
                for coverage in coverages:
                    if isinstance(coverage, dict):
                        coverage_text = f"<b>{coverage.get('coverage_name', 'Coverage')}</b><br/>"
                        coverage_text += f"{coverage.get('what_covered', 'N/A')}<br/>"
                        if coverage.get('important_limits'):
                            coverage_text += f"<i>Limits: {coverage.get('important_limits')}</i><br/>"
                        if coverage.get('page'):
                            coverage_text += f"<font size=8 color=grey>Page {coverage.get('page')}</font>"
                        elements.append(Paragraph(coverage_text, body_style))
                        elements.append(Spacer(1, 6))
            elements.append(Spacer(1, 12))
        
        # Check if we need a page break
        if len(elements) > 15:
            elements.append(PageBreak())
        
        # SPECIAL BENEFITS
        if "special_benefits" in analysis_data and analysis_data["special_benefits"]:
            elements.append(Paragraph("SPECIAL BENEFITS", section_style))
            for benefit in analysis_data["special_benefits"]:
                benefit_text = f"<b>{benefit.get('benefit_name', 'Benefit')}</b><br/>"
                benefit_text += f"{benefit.get('explanation', 'N/A')}"
                if benefit.get('page'):
                    benefit_text += f"<br/><font size=8 color=grey>Page {benefit.get('page')}</font>"
                elements.append(Paragraph(benefit_text, body_style))
                elements.append(Spacer(1, 6))
            elements.append(Spacer(1, 12))
        
        # WAITING PERIODS
        if "waiting_periods" in analysis_data and analysis_data["waiting_periods"]:
            elements.append(Paragraph("WAITING PERIODS", section_style))
            wp_list = analysis_data["waiting_periods"]
            if isinstance(wp_list, list) and len(wp_list) > 0:
                wp_data = [["Period Type", "Duration", "Impact on You", "Page"]]
                for wp in wp_list:
                    if isinstance(wp, dict):
                        wp_data.append([
                            wp.get("period_type", "N/A"),
                            wp.get("duration", "N/A"),
                            wp.get("impact", "N/A"),
                            wp.get("page", "N/A")
                        ])
                
                if len(wp_data) > 1:  # Only create table if there's data
                    wp_table = Table(wp_data, colWidths=[1.5*inch, 1.2*inch, 2.1*inch, 0.6*inch])
                    wp_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ]))
                    elements.append(wp_table)
                    elements.append(Spacer(1, 12))
        
        # Check page break
        if len(elements) > 30:
            elements.append(PageBreak())
        
        # EXCLUSIONS AND RISKS
        if "exclusions_and_risks" in analysis_data and analysis_data["exclusions_and_risks"]:
            elements.append(Paragraph("EXCLUSIONS AND CLAIM RISKS ⚠️", section_style))
            exc_list = analysis_data["exclusions_and_risks"]
            if isinstance(exc_list, list):
                for exclusion in exc_list:
                    if isinstance(exclusion, dict):
                        risk_level = exclusion.get("risk_level", "Medium").upper()
                        color = "#dc2626" if risk_level == "HIGH" else "#f59e0b" if risk_level == "MEDIUM" else "#10b981"
                        
                        exc_text = f"<b style='color:{color}'>● {exclusion.get('exclusion', 'Exclusion')}</b><br/>"
                        exc_text += f"Impact: {exclusion.get('impact', 'N/A')}<br/>"
                        exc_text += f"<font size=8 color=grey>Risk: {risk_level} | Page {exclusion.get('page', 'N/A')}</font>"
                        elements.append(Paragraph(exc_text, body_style))
                        elements.append(Spacer(1, 8))
            elements.append(Spacer(1, 12))
        
        # CO-PAYS, SUB-LIMITS AND RESTRICTIONS
        if "copay_sublimits_restrictions" in analysis_data and analysis_data["copay_sublimits_restrictions"]:
            elements.append(Paragraph("CO-PAYS, SUB-LIMITS & RESTRICTIONS", section_style))
            res_list = analysis_data["copay_sublimits_restrictions"]
            if isinstance(res_list, list):
                for restriction in res_list:
                    if isinstance(restriction, dict):
                        res_text = f"<b>{restriction.get('restriction_type', 'Restriction')}</b><br/>"
                        res_text += f"{restriction.get('details', 'N/A')}<br/>"
                        res_text += f"Impact on Claims: {restriction.get('impact_on_claims', 'N/A')}"
                        elements.append(Paragraph(res_text, body_style))
                        elements.append(Spacer(1, 8))
            elements.append(Spacer(1, 12))
        
        # Check page break
        if len(elements) > 45:
            elements.append(PageBreak())
        
        # IMPORTANT CLAUSES
        if "important_clauses" in analysis_data:
            elements.append(Paragraph("IMPORTANT CLAUSES", section_style))
            clauses = analysis_data["important_clauses"]
            for clause_name, clause_value in clauses.items():
                if clause_value and clause_value != "Not Found in Document":
                    clause_text = f"<b>{clause_name.replace('_', ' ').title()}</b><br/>"
                    clause_text += f"{str(clause_value)[:200]}{'...' if len(str(clause_value)) > 200 else ''}"
                    elements.append(Paragraph(clause_text, body_style))
                    elements.append(Spacer(1, 6))
            elements.append(Spacer(1, 12))
        
        # CUSTOMER RED FLAGS
        if "customer_red_flags" in analysis_data and analysis_data["customer_red_flags"]:
            elements.append(Paragraph("CUSTOMER RED FLAGS 🚨", section_style))
            flags_list = analysis_data["customer_red_flags"]
            if isinstance(flags_list, list):
                for flag in flags_list:
                    if isinstance(flag, dict):
                        severity = flag.get("severity", "Medium").upper()
                        color = "#dc2626" if severity == "HIGH" else "#f59e0b" if severity == "MEDIUM" else "#10b981"
                        
                        flag_text = f"<font color='{color}'><b>● {flag.get('flag', 'Flag')}</b></font><br/>"
                        flag_text += f"Severity: {severity}<br/>{flag.get('explanation', 'N/A')}"
                        elements.append(Paragraph(flag_text, body_style))
                        elements.append(Spacer(1, 6))
            elements.append(Spacer(1, 12))
        
        # Check page break
        if len(elements) > 55:
            elements.append(PageBreak())
        
        # POLICY RATINGS
        if "policy_ratings" in analysis_data:
            elements.append(Paragraph("POLICY RATINGS", section_style))
            ratings = analysis_data["policy_ratings"]
            
            ratings_data = [
                ["Coverage Strength", ratings.get("coverage_strength", "N/A")],
                ["Claim Friendliness", ratings.get("claim_friendliness", "N/A")],
                ["Waiting Periods", ratings.get("waiting_periods", "N/A")],
                ["Flexibility", ratings.get("flexibility", "N/A")],
                ["Transparency", ratings.get("transparency", "N/A")],
                ["OVERALL RATING", f"<b>{ratings.get('overall_rating', 'N/A')}</b>"],
            ]
            
            ratings_table = Table(ratings_data, colWidths=[2.5*inch, 3.9*inch])
            ratings_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0f2fe')),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#1e40af')),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(ratings_table)
            elements.append(Spacer(1, 8))
            elements.append(Paragraph(f"<i>{ratings.get('rating_explanation', '')}</i>", body_style))
            elements.append(Spacer(1, 12))
        
        # FINAL RECOMMENDATION
        if "final_recommendation" in analysis_data:
            elements.append(PageBreak())
            elements.append(Paragraph("FINAL RECOMMENDATION", section_style))
            rec = analysis_data["final_recommendation"]
            
            elements.append(Paragraph(f"<b>Who Should Buy This Policy</b>", body_style))
            elements.append(Paragraph(rec.get("who_should_buy", "N/A"), body_style))
            elements.append(Spacer(1, 8))
            
            elements.append(Paragraph(f"<b>Who Should Avoid This Policy</b>", body_style))
            elements.append(Paragraph(rec.get("who_should_avoid", "N/A"), body_style))
            elements.append(Spacer(1, 8))
            
            elements.append(Paragraph(f"<b>Main Strengths</b>", body_style))
            elements.append(Paragraph(rec.get("main_strengths", "N/A"), body_style))
            elements.append(Spacer(1, 8))
            
            elements.append(Paragraph(f"<b>Main Weaknesses</b>", body_style))
            elements.append(Paragraph(rec.get("main_weaknesses", "N/A"), body_style))
            elements.append(Spacer(1, 12))
            
            elements.append(Paragraph(f"<b>Key Takeaway</b>", body_style))
            elements.append(Paragraph(rec.get("key_takeaway", "N/A"), body_style))
        
        # Footer
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(
            "<i>This is a professional analysis generated by an insurance policy analyzer. "
            "For official policy terms, refer to the original policy document.</i>",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, 
                         textColor=colors.grey, alignment=TA_CENTER)
        ))
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF bytes
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()

