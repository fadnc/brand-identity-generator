from typing import Dict, Any
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import json
import zipfile
import os
from datetime import datetime
import requests
from io import BytesIO


class ExportService:
    """
    Service for exporting brand packages in various formats.
    """
    
    def __init__(self):
        self.export_dir = os.getenv('UPLOAD_FOLDER', 'app/static/exports')
        os.makedirs(self.export_dir, exist_ok=True)
    
    def export_to_pdf(
        self,
        project,
        include_guidelines: bool = True
    ) -> str:
        """
        Export brand package to PDF with professional formatting.
        """
        
        filename = f"brand_identity_{project.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.export_dir, filename)
        
        # Create PDF
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Cover page
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph(f"Brand Identity Package", title_style))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(project.business_name, styles['Title']))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y')}",
            styles['Normal']
        ))
        story.append(PageBreak())
        
        # Table of Contents
        story.append(Paragraph("Table of Contents", title_style))
        toc_items = [
            "1. Brand Strategy",
            "2. Visual Identity",
            "3. Brand Copy & Messaging",
            "4. Brand Guidelines" if include_guidelines else None,
            "5. Color Palette",
            "6. Typography"
        ]
        for item in toc_items:
            if item:
                story.append(Paragraph(item, styles['Normal']))
                story.append(Spacer(1, 6))
        story.append(PageBreak())
        
        # Brand Strategy
        story.append(Paragraph("Brand Strategy", title_style))
        strategy = project.strategy or {}
        
        if strategy.get('positioning'):
            story.append(Paragraph("Brand Positioning", heading_style))
            pos = strategy['positioning']
            story.append(Paragraph(
                f"<b>Positioning Statement:</b> {pos.get('positioning_statement', 'N/A')}",
                styles['Normal']
            ))
            story.append(Spacer(1, 12))
            
            story.append(Paragraph(
                f"<b>Value Proposition:</b> {pos.get('value_proposition', 'N/A')}",
                styles['Normal']
            ))
            story.append(Spacer(1, 12))
        
        # Brand Values
        if project.brand_values:
            story.append(Paragraph("Brand Values", heading_style))
            for value in project.brand_values:
                story.append(Paragraph(f"• {value}", styles['Normal']))
            story.append(Spacer(1, 12))
        
        story.append(PageBreak())
        
        # Visual Identity
        story.append(Paragraph("Visual Identity", title_style))
        visual = project.visual_identity or {}
        
        # Logo
        if visual.get('logo', {}).get('image_url'):
            story.append(Paragraph("Logo", heading_style))
            try:
                logo_url = visual['logo']['image_url']
                response = requests.get(logo_url)
                img = Image(BytesIO(response.content), width=4*inch, height=4*inch)
                story.append(img)
                story.append(Spacer(1, 12))
            except Exception as e:
                story.append(Paragraph(f"Logo: {logo_url}", styles['Normal']))
        
        story.append(PageBreak())
        
        # Brand Copy
        story.append(Paragraph("Brand Copy & Messaging", title_style))
        brand_copy = project.brand_copy or {}
        
        # Taglines
        if brand_copy.get('taglines'):
            story.append(Paragraph("Taglines", heading_style))
            for i, tagline_data in enumerate(brand_copy['taglines'][:5], 1):
                tagline = tagline_data.get('tagline', '')
                story.append(Paragraph(f"{i}. {tagline}", styles['Normal']))
                story.append(Spacer(1, 6))
            story.append(Spacer(1, 12))
        
        # Brand Story
        if brand_copy.get('brand_story', {}).get('medium'):
            story.append(Paragraph("Brand Story", heading_style))
            story.append(Paragraph(
                brand_copy['brand_story']['medium'],
                styles['Normal']
            ))
            story.append(Spacer(1, 12))
        
        story.append(PageBreak())
        
        # Color Palette
        if visual.get('color_palette'):
            story.append(Paragraph("Color Palette", title_style))
            colors_data = visual['color_palette']
            
            if colors_data.get('primary_colors'):
                story.append(Paragraph("Primary Colors", heading_style))
                for color in colors_data['primary_colors']:
                    hex_color = color.get('hex', '#000000')
                    usage = color.get('usage', 'N/A')
                    story.append(Paragraph(
                        f"• {hex_color} - {usage}",
                        styles['Normal']
                    ))
                story.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(story)
        
        return filepath
    
    def export_to_zip(
        self,
        project,
        include_assets: bool = True,
        include_guidelines: bool = True
    ) -> str:
        """
        Export complete brand package as ZIP file.
        """
        
        filename = f"brand_package_{project.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        filepath = os.path.join(self.export_dir, filename)
        
        with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add JSON data
            json_data = {
                'business_name': project.business_name,
                'industry': project.industry,
                'strategy': project.strategy,
                'visual_identity': project.visual_identity,
                'brand_copy': project.brand_copy,
                'consistency_score': project.consistency_score
            }
            
            zipf.writestr(
                'brand_data.json',
                json.dumps(json_data, indent=2)
            )
            
            # Add PDF if guidelines requested
            if include_guidelines:
                pdf_path = self.export_to_pdf(project, include_guidelines=True)
                zipf.write(pdf_path, 'Brand_Guidelines.pdf')
                os.remove(pdf_path)  # Clean up temp PDF
            
            # Add README
            readme = f"""
Brand Identity Package for {project.business_name}
Generated on {datetime.now().strftime('%B %d, %Y')}

Contents:
- brand_data.json: Complete brand data in JSON format
- Brand_Guidelines.pdf: Comprehensive brand guidelines document
- assets/: Logo and other visual assets

Consistency Score: {project.consistency_score}/1.0

For questions or support, please contact your brand strategist.
"""
            zipf.writestr('README.txt', readme)
        
        return filepath
    
    def export_to_json(self, project) -> str:
        """
        Export brand data as JSON file.
        """
        
        filename = f"brand_data_{project.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.export_dir, filename)
        
        data = {
            'project_id': project.id,
            'business_name': project.business_name,
            'industry': project.industry,
            'target_audience': project.target_audience,
            'brand_values': project.brand_values,
            'strategy': project.strategy,
            'visual_identity': project.visual_identity,
            'brand_copy': project.brand_copy,
            'consistency_score': project.consistency_score,
            'status': project.status,
            'created_at': project.created_at.isoformat(),
            'completed_at': project.completed_at.isoformat() if project.completed_at else None
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filepath