"""
Professional PDF Report Generator
Generates professional insurance consultant reports with proper table rendering.
Features: word wrapping, proper column widths, no overlapping text, page numbers.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas
from datetime import datetime


class ProfessionalPDFReporter:
    """Generates professional PDF reports with proper table rendering."""
    
    def __init__(self):
        self.page_width, self.page_height = letter
        self.margin = 0.5 * inch
        self.story = []
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='TitlePage',
            fontSize=28,
            textColor=HexColor('#1e293b'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SubtitlePage',
            fontSize=14,
            textColor=HexColor('#475569'),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            fontSize=13,
            textColor=HexColor('#1e293b'),
            spaceAfter=6,
            spaceBefore=8,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CellText',
            fontSize=8,
            textColor=HexColor('#334155'),
            alignment=TA_LEFT,
            leading=9,
            wordWrap='CJK'
        ))
    
    def _truncate_text(self, text: str, max_chars: int = 150) -> str:
        """Truncate long text and keep concise."""
        if not text:
            return ""
        
        text = text.strip()
        # Remove markdown
        text = text.replace('**', '').replace('*', '').replace('_', '')
        
        if len(text) > max_chars:
            return text[:max_chars] + "..."
        return text
    
    def _create_cell_paragraph(self, text: str) -> Paragraph:
        """Create a Paragraph object for table cell with word wrapping."""
        text = self._truncate_text(text, 150)
        return Paragraph(text, self.styles['CellText'])
    
    def _parse_markdown_table(self, markdown_text):
        """Parse markdown table into list of lists with Paragraph objects."""
        lines = markdown_text.strip().split('\n')
        
        table_data = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and separator lines
            if not line or '---' in line:
                continue
            
            # Parse table row (lines with pipes)
            if line.startswith('|') and line.endswith('|'):
                # Extract cells
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                # Convert to Paragraph objects for word wrapping
                cell_paragraphs = [self._create_cell_paragraph(cell) for cell in cells]
                if cell_paragraphs and any(str(p.text).strip() for p in cell_paragraphs):
                    table_data.append(cell_paragraphs)
        
        return table_data if table_data else None
    
    def _deduplicate_table_rows(self, table_data):
        """Remove duplicate rows, keeping first occurrence."""
        if not table_data or len(table_data) <= 1:
            return table_data
        
        header = table_data[0]
        seen_rows = set()
        deduplicated = [header]
        
        for row in table_data[1:]:
            # Create key from text content for deduplication
            row_key = tuple(
                str(cell.text).lower().strip() if hasattr(cell, 'text') else str(cell).lower().strip()
                for cell in row
            )
            if row_key not in seen_rows and any(row_key):
                seen_rows.add(row_key)
                deduplicated.append(row)
        
        return deduplicated
    
    def _create_styled_table(self, table_data, col_widths, header_color, grid_color, row_bg_colors):
        """Create a styled table with proper formatting."""
        if not table_data:
            return None
        
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), header_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff') if header_color != HexColor('#fef08a') else HexColor('#713f12')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, grid_color),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), row_bg_colors),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        return table
    
    def add_title_page(self, policy_name, insurance_company, generated_date):
        """Add professional title page."""
        self.story.append(Spacer(1, 1.5*inch))
        
        title = Paragraph("Insurance Policy Analysis Report", self.styles['TitlePage'])
        self.story.append(title)
        
        self.story.append(Spacer(1, 0.5*inch))
        
        # Extract company name from policy or use generic
        company_display = insurance_company if insurance_company != "Insurance Company" else "Insurance Provider"
        
        # Policy details
        details = [
            f"<b>Policy:</b> {policy_name}",
            f"<b>Insurer:</b> {company_display}",
            f"<b>Generated:</b> {generated_date}"
        ]
        
        for detail in details:
            para = Paragraph(detail, self.styles['SubtitlePage'])
            self.story.append(para)
            self.story.append(Spacer(1, 0.15*inch))
        
        self.story.append(PageBreak())
    
    def add_executive_dashboard(self, dashboard_text):
        """Add executive dashboard with KPI metrics."""
        if not dashboard_text or not dashboard_text.strip():
            return
        
        self.story.append(Paragraph("Executive Dashboard", self.styles['SectionTitle']))
        self.story.append(Spacer(1, 0.1*inch))
        
        # Parse metrics into 2-column table
        lines = [line.strip() for line in dashboard_text.split('\n') if line.strip()]
        
        metrics = []
        for line in lines:
            line = line.lstrip('-•').strip()
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    metric_name = self._create_cell_paragraph(parts[0].strip())
                    rating = self._create_cell_paragraph(parts[1].strip())
                    metrics.append([metric_name, rating])
        
        if metrics:
            dashboard_table = self._create_styled_table(
                table_data=metrics,
                col_widths=[3.0*inch, 2.5*inch],
                header_color=HexColor('#e2e8f0'),
                grid_color=HexColor('#cbd5e1'),
                row_bg_colors=[HexColor('#ffffff'), HexColor('#f8fafc')]
            )
            
            if dashboard_table:
                self.story.append(dashboard_table)
                self.story.append(Spacer(1, 0.2*inch))
    
    def add_snapshot_table(self, snapshot_text):
        """Add policy snapshot table."""
        if not snapshot_text or not snapshot_text.strip():
            return
        
        self.story.append(Paragraph("Policy Snapshot", self.styles['SectionTitle']))
        self.story.append(Spacer(1, 0.08*inch))
        
        table_data = self._parse_markdown_table(snapshot_text)
        table_data = self._deduplicate_table_rows(table_data)
        
        if table_data and len(table_data) > 0:
            snapshot_table = self._create_styled_table(
                table_data=table_data,
                col_widths=[1.8*inch, 3.7*inch],
                header_color=HexColor('#e2e8f0'),
                grid_color=HexColor('#cbd5e1'),
                row_bg_colors=[HexColor('#ffffff'), HexColor('#f8fafc')]
            )
            
            if snapshot_table:
                self.story.append(snapshot_table)
                self.story.append(Spacer(1, 0.12*inch))
    
    def add_coverage_table(self, coverage_text):
        """Add coverage analysis table."""
        if not coverage_text or not coverage_text.strip():
            return
        
        self.story.append(Paragraph("Coverage Analysis", self.styles['SectionTitle']))
        self.story.append(Spacer(1, 0.08*inch))
        
        table_data = self._parse_markdown_table(coverage_text)
        table_data = self._deduplicate_table_rows(table_data)
        
        if table_data and len(table_data) > 0:
            # Dynamic column widths based on content
            num_cols = len(table_data[0]) if table_data else 3
            if num_cols == 3:
                col_widths = [1.3*inch, 1.6*inch, 2.1*inch]
            elif num_cols == 2:
                col_widths = [2.3*inch, 3.2*inch]
            else:
                col_widths = [5.5*inch / num_cols] * num_cols
            
            coverage_table = self._create_styled_table(
                table_data=table_data,
                col_widths=col_widths,
                header_color=HexColor('#e2e8f0'),
                grid_color=HexColor('#cbd5e1'),
                row_bg_colors=[HexColor('#ffffff'), HexColor('#f8fafc')]
            )
            
            if coverage_table:
                self.story.append(coverage_table)
                self.story.append(Spacer(1, 0.12*inch))
    
    def add_financial_caps_table(self, limits_text):
        """Add financial caps table."""
        if not limits_text or not limits_text.strip():
            return
        
        self.story.append(Paragraph("Financial Caps & Sub-Limits", self.styles['SectionTitle']))
        self.story.append(Spacer(1, 0.08*inch))
        
        table_data = self._parse_markdown_table(limits_text)
        table_data = self._deduplicate_table_rows(table_data)
        
        if table_data and len(table_data) > 0:
            num_cols = len(table_data[0]) if table_data else 3
            if num_cols == 3:
                col_widths = [1.3*inch, 1.6*inch, 2.1*inch]
            elif num_cols == 2:
                col_widths = [2.3*inch, 3.2*inch]
            else:
                col_widths = [5.5*inch / num_cols] * num_cols
            
            limits_table = self._create_styled_table(
                table_data=table_data,
                col_widths=col_widths,
                header_color=HexColor('#fee2e2'),
                grid_color=HexColor('#fca5a5'),
                row_bg_colors=[HexColor('#ffffff'), HexColor('#fef2f2')]
            )
            
            if limits_table:
                self.story.append(limits_table)
                self.story.append(Spacer(1, 0.12*inch))
    
    def add_waiting_periods_table(self, waiting_text):
        """Add waiting periods table."""
        if not waiting_text or not waiting_text.strip():
            return
        
        self.story.append(Paragraph("Waiting Periods", self.styles['SectionTitle']))
        self.story.append(Spacer(1, 0.08*inch))
        
        table_data = self._parse_markdown_table(waiting_text)
        table_data = self._deduplicate_table_rows(table_data)
        
        if table_data and len(table_data) > 0:
            num_cols = len(table_data[0]) if table_data else 3
            if num_cols == 3:
                col_widths = [1.6*inch, 1.4*inch, 1.9*inch]
            elif num_cols == 2:
                col_widths = [2.5*inch, 3.0*inch]
            else:
                col_widths = [5.5*inch / num_cols] * num_cols
            
            waiting_table = self._create_styled_table(
                table_data=table_data,
                col_widths=col_widths,
                header_color=HexColor('#fef08a'),
                grid_color=HexColor('#fcd34d'),
                row_bg_colors=[HexColor('#ffffff'), HexColor('#fefce8')]
            )
            
            if waiting_table:
                self.story.append(waiting_table)
                self.story.append(Spacer(1, 0.12*inch))
    
    def add_exclusions_table(self, exclusions_text):
        """Add exclusions table."""
        if not exclusions_text or not exclusions_text.strip():
            return
        
        self.story.append(Paragraph("Exclusions", self.styles['SectionTitle']))
        self.story.append(Spacer(1, 0.08*inch))
        
        table_data = self._parse_markdown_table(exclusions_text)
        table_data = self._deduplicate_table_rows(table_data)
        
        if table_data and len(table_data) > 0:
            num_cols = len(table_data[0]) if table_data else 2
            if num_cols == 2:
                col_widths = [2.1*inch, 3.4*inch]
            else:
                col_widths = [5.5*inch / num_cols] * num_cols
            
            exclusions_table = self._create_styled_table(
                table_data=table_data,
                col_widths=col_widths,
                header_color=HexColor('#fee2e2'),
                grid_color=HexColor('#fca5a5'),
                row_bg_colors=[HexColor('#ffffff'), HexColor('#fef2f2')]
            )
            
            if exclusions_table:
                self.story.append(exclusions_table)
                self.story.append(Spacer(1, 0.12*inch))
    
    def add_claim_restrictions_table(self, restrictions_text):
        """Add claim restrictions table."""
        if not restrictions_text or not restrictions_text.strip():
            return
        
        self.story.append(Paragraph("Claim Restrictions", self.styles['SectionTitle']))
        self.story.append(Spacer(1, 0.08*inch))
        
        table_data = self._parse_markdown_table(restrictions_text)
        table_data = self._deduplicate_table_rows(table_data)
        
        if table_data and len(table_data) > 0:
            num_cols = len(table_data[0]) if table_data else 2
            if num_cols == 2:
                col_widths = [2.1*inch, 3.4*inch]
            else:
                col_widths = [5.5*inch / num_cols] * num_cols
            
            restrictions_table = self._create_styled_table(
                table_data=table_data,
                col_widths=col_widths,
                header_color=HexColor('#e0e7ff'),
                grid_color=HexColor('#a5b4fc'),
                row_bg_colors=[HexColor('#ffffff'), HexColor('#f0f4ff')]
            )
            
            if restrictions_table:
                self.story.append(restrictions_table)
                self.story.append(Spacer(1, 0.12*inch))
    
    def add_key_clauses(self, clauses_text):
        """Add key clauses section."""
        if not clauses_text or not clauses_text.strip():
            return
        
        self.story.append(Paragraph("Key Clauses", self.styles['SectionTitle']))
        self.story.append(Spacer(1, 0.08*inch))
        
        # Parse clauses
        lines = clauses_text.split('\n')
        clause_count = 0
        
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                clause = line.lstrip('-•*').strip()
                if clause and len(clause) > 3 and clause_count < 5:
                    text = self._truncate_text(clause, 200)
                    para = Paragraph(f"• {text}", self.styles['CellText'])
                    self.story.append(para)
                    self.story.append(Spacer(1, 0.05*inch))
                    clause_count += 1
        
        self.story.append(Spacer(1, 0.08*inch))
    
    def add_recommendation(self, rec_text):
        """Add final recommendation section."""
        if not rec_text or not rec_text.strip():
            return
        
        self.story.append(Paragraph("Final Recommendation", self.styles['SectionTitle']))
        self.story.append(Spacer(1, 0.08*inch))
        
        # Parse and display recommendations
        lines = rec_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Clean markdown
            line_clean = line.replace('**', '').replace('_', '')
            
            if line_clean.endswith(':'):
                # Section header
                para = Paragraph(f"<b>{line_clean}</b>", self.styles['CellText'])
                self.story.append(para)
                self.story.append(Spacer(1, 0.03*inch))
            elif line.startswith('-') or line.startswith('•'):
                # Bullet point
                content = line.lstrip('-•').strip()
                text = self._truncate_text(content, 180)
                para = Paragraph(f"• {text}", self.styles['CellText'])
                self.story.append(para)
                self.story.append(Spacer(1, 0.03*inch))
            elif line:
                # Regular text
                text = self._truncate_text(line_clean, 180)
                para = Paragraph(text, self.styles['CellText'])
                self.story.append(para)
                self.story.append(Spacer(1, 0.03*inch))
    
    def generate_pdf(self, filename, policy_name, company_name, analysis_sections):
        """Generate professional PDF with page numbers."""
        
        # Reset story to prevent duplication from previous generations
        self.story = []
        print(f"[PDF DEBUG] Starting PDF generation")
        print(f"[PDF DEBUG] Story reset, length: {len(self.story)}")
        
        def add_page_number(canvas_obj, doc):
            """Callback to add page numbers to each page."""
            canvas_obj.saveState()
            canvas_obj.setFont("Helvetica", 7)
            canvas_obj.setFillColor(HexColor('#94a3b8'))
            page_num = canvas_obj.getPageNumber()
            page_text = f"Page {page_num}"
            canvas_obj.drawRightString(letter[0] - 0.5 * inch, 0.25 * inch, page_text)
            canvas_obj.restoreState()
        
        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=0.75 * inch,
            title="Insurance Policy Analysis Report"
        )
        
        # Build story
        print(f"[PDF DEBUG] Before title page: {len(self.story)} elements")
        self.add_title_page(policy_name, company_name, datetime.now().strftime('%B %d, %Y'))
        print(f"[PDF DEBUG] After title page: {len(self.story)} elements")
        
        if analysis_sections.get('dashboard'):
            self.add_executive_dashboard(analysis_sections['dashboard'])
            print(f"[PDF DEBUG] After dashboard: {len(self.story)} elements")
        
        if analysis_sections.get('snapshot'):
            self.add_snapshot_table(analysis_sections['snapshot'])
            print(f"[PDF DEBUG] After snapshot: {len(self.story)} elements")
        
        if analysis_sections.get('coverage'):
            self.add_coverage_table(analysis_sections['coverage'])
            print(f"[PDF DEBUG] After coverage: {len(self.story)} elements")
        
        if analysis_sections.get('financial_limits'):
            self.add_financial_caps_table(analysis_sections['financial_limits'])
            print(f"[PDF DEBUG] After financial_limits: {len(self.story)} elements")
        
        if analysis_sections.get('waiting_periods'):
            self.add_waiting_periods_table(analysis_sections['waiting_periods'])
            print(f"[PDF DEBUG] After waiting_periods: {len(self.story)} elements")
        
        if analysis_sections.get('exclusions'):
            self.add_exclusions_table(analysis_sections['exclusions'])
            print(f"[PDF DEBUG] After exclusions: {len(self.story)} elements")
        
        if analysis_sections.get('claim_restrictions'):
            self.add_claim_restrictions_table(analysis_sections['claim_restrictions'])
            print(f"[PDF DEBUG] After claim_restrictions: {len(self.story)} elements")
        
        if analysis_sections.get('important_clauses'):
            self.add_key_clauses(analysis_sections['important_clauses'])
            print(f"[PDF DEBUG] After important_clauses: {len(self.story)} elements")
        
        if analysis_sections.get('recommendation'):
            self.add_recommendation(analysis_sections['recommendation'])
            print(f"[PDF DEBUG] After recommendation: {len(self.story)} elements")
        
        # Debug: Log story size before building
        print(f"[PDF] Story elements count: {len(self.story)}")
        print(f"[PDF] Sections included: {list(analysis_sections.keys())}")
        print(f"[PDF DEBUG] About to call doc.build()")
        
        # Build with page numbers callback
        doc.build(self.story, onFirstPage=add_page_number, onLaterPages=add_page_number)
        print(f"[PDF DEBUG] doc.build() completed")
