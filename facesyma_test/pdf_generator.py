"""
Facesyma Test Module — PDF Report Generator
============================================
Generate branded PDF reports with test results and charts.

Uses:
- reportlab for PDF generation
- PIL for charts and branding
- Google Cloud Storage for storage

Report includes:
- Test summary (type, date, language)
- Domain scores with visual progress bars
- AI interpretation
- Chart visualization
- Recommendations
"""

from io import BytesIO
from datetime import datetime
from typing import Dict, Optional
import logging

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from PIL import Image as PILImage, ImageDraw
import io

log = logging.getLogger(__name__)

# ── Test Type Metadata ─────────────────────────────────────────────────────
TEST_METADATA = {
    "personality": {
        "name": "Big Five Personality Test",
        "description": "Assess your personality traits across 5 dimensions",
        "domains": {
            "openness": "Openness to Experience",
            "conscientiousness": "Conscientiousness",
            "extraversion": "Extraversion",
            "agreeableness": "Agreeableness",
            "neuroticism": "Neuroticism (Emotional Stability)"
        }
    },
    "career": {
        "name": "Career Aptitude Test",
        "description": "Discover your career inclinations and strengths",
        "domains": {
            "analytical": "Analytical",
            "creative": "Creative",
            "social": "Social",
            "entrepreneurial": "Entrepreneurial",
            "managerial": "Managerial",
            "technical": "Technical"
        }
    },
    "hr": {
        "name": "HR / Work Style Test",
        "description": "Understand your workplace preferences and interpersonal style",
        "domains": {
            "leadership": "Leadership",
            "team_fit": "Team Fit",
            "communication": "Communication",
            "stress_tolerance": "Stress Tolerance",
            "motivation": "Motivation"
        }
    },
    "skills": {
        "name": "Skills Assessment Test",
        "description": "Evaluate your core competencies and abilities",
        "domains": {
            "problem_solving": "Problem Solving",
            "empathy": "Empathy",
            "organization": "Organization",
            "learning_speed": "Learning Speed",
            "decision_making": "Decision Making"
        }
    },
    "vocation": {
        "name": "Holland RIASEC Vocational Test",
        "description": "Find your ideal career path based on vocational interests",
        "domains": {
            "realistic": "Realistic (R)",
            "investigative": "Investigative (I)",
            "artistic": "Artistic (A)",
            "social": "Social (S)",
            "enterprising": "Enterprising (E)",
            "conventional": "Conventional (C)"
        }
    },
    "relationship": {
        "name": "Relationship & Emotional Intelligence Test",
        "description": "Assess attachment styles, love languages, and emotional awareness",
        "domains": {
            "attachment_style": "Attachment Style",
            "love_language": "Love Language",
            "relationship_values": "Relationship Values",
            "emotional_intelligence": "Emotional Intelligence"
        }
    }
}

def get_score_level(score: float) -> tuple:
    """Determine score level and recommendation"""
    if score < 40:
        return ("Low", "Develop this area through practice and learning")
    elif score < 70:
        return ("Moderate", "This is an average strength area")
    else:
        return ("High", "This is a significant strength - leverage it!")

def create_progress_bar_image(score: float, width: int = 200, height: int = 20) -> PILImage.Image:
    """Create a progress bar image for the score"""
    img = PILImage.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # Background
    draw.rectangle([0, 0, width - 1, height - 1], outline='black', width=1)

    # Fill based on score
    fill_width = int((score / 100) * (width - 2))

    # Color: Red (0-40) → Yellow (40-70) → Green (70-100)
    if score < 40:
        color = (255, 100, 100)  # Red
    elif score < 70:
        color = (255, 200, 100)  # Yellow
    else:
        color = (100, 200, 100)  # Green

    if fill_width > 0:
        draw.rectangle([1, 1, fill_width, height - 2], fill=color)

    # Score text
    draw.text((width // 2 - 10, height // 2 - 5), f"{score:.0f}%", fill='black')

    return img

class PDFReportGenerator:
    """Generate professional PDF reports for test results"""

    def __init__(self, test_type: str, lang: str = "en"):
        self.test_type = test_type
        self.lang = lang
        self.metadata = TEST_METADATA.get(test_type, {})
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2ca02c'),
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))

    def generate_pdf(
        self,
        result_id: str,
        domain_scores: Dict[str, float],
        ai_interpretation: str,
        user_id: Optional[int] = None
    ) -> BytesIO:
        """Generate PDF report and return as BytesIO"""

        # Create PDF buffer
        pdf_buffer = BytesIO()

        # Create PDF document
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        # Build story (content)
        story = self._build_story(result_id, domain_scores, ai_interpretation, user_id)

        # Build PDF
        doc.build(story)
        pdf_buffer.seek(0)
        return pdf_buffer

    def _build_story(
        self,
        result_id: str,
        domain_scores: Dict[str, float],
        ai_interpretation: str,
        user_id: Optional[int]
    ) -> list:
        """Build PDF content story"""
        story = []

        # Header with Facesyma branding
        story.append(Paragraph("FACESYMA", self.styles['CustomTitle']))
        story.append(Paragraph(
            f"<b>{self.metadata.get('name', 'Test Result')}</b>",
            self.styles['CustomHeading']
        ))
        story.append(Spacer(1, 0.2 * inch))

        # Test Info
        info_data = [
            ["Test Type:", self.metadata.get('name', 'Unknown')],
            ["Date:", datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ["Language:", self.lang.upper()],
            ["Result ID:", result_id[:8] + "..."],
        ]
        if user_id:
            info_data.append(["User ID:", str(user_id)])

        info_table = Table(info_data, colWidths=[2 * inch, 4 * inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3 * inch))

        # Domain Scores
        story.append(Paragraph("Test Results", self.styles['Heading2']))
        story.append(Spacer(1, 0.15 * inch))

        scores_data = [["Domain", "Score", "Level", "Assessment"]]
        for domain, score in sorted(domain_scores.items()):
            domain_name = self.metadata.get('domains', {}).get(domain, domain)
            level, assessment = get_score_level(score)
            scores_data.append([
                domain_name,
                f"{score:.1f}%",
                level,
                assessment
            ])

        scores_table = Table(scores_data, colWidths=[2 * inch, 1 * inch, 1 * inch, 2.5 * inch])
        scores_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
        ]))
        story.append(scores_table)
        story.append(Spacer(1, 0.3 * inch))

        # AI Interpretation
        story.append(Paragraph("AI Interpretation", self.styles['Heading2']))
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(
            ai_interpretation,
            self.styles['BodyText']
        ))
        story.append(Spacer(1, 0.3 * inch))

        # Recommendations
        story.append(Paragraph("Recommendations", self.styles['Heading2']))
        story.append(Spacer(1, 0.1 * inch))

        recommendations = self._get_recommendations(domain_scores)
        for i, rec in enumerate(recommendations, 1):
            story.append(Paragraph(
                f"<b>{i}.</b> {rec}",
                self.styles['BodyText']
            ))
            story.append(Spacer(1, 0.1 * inch))

        # Footer
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph(
            f"<i>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
            self.styles['Normal']
        ))

        return story

    def _get_recommendations(self, domain_scores: Dict[str, float]) -> list:
        """Generate recommendations based on scores"""
        recommendations = []

        # Find top and bottom domains
        sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)

        if sorted_domains:
            top_domain, top_score = sorted_domains[0]
            domain_name = self.metadata.get('domains', {}).get(top_domain, top_domain)
            recommendations.append(
                f"Leverage your strength in <b>{domain_name}</b> ({top_score:.0f}%) "
                f"in your personal and professional development."
            )

        if len(sorted_domains) > 1:
            bottom_domain, bottom_score = sorted_domains[-1]
            domain_name = self.metadata.get('domains', {}).get(bottom_domain, bottom_domain)
            recommendations.append(
                f"Focus on developing <b>{domain_name}</b> ({bottom_score:.0f}%) "
                f"through targeted practice and learning."
            )

        recommendations.append(
            "Consider consulting with a career coach or counselor to discuss "
            "how these results align with your goals and aspirations."
        )

        recommendations.append(
            "Retake this assessment in 6-12 months to track your personal growth "
            "and development over time."
        )

        return recommendations


def test_pdf_generation():
    """Quick test of PDF generation"""
    print("\n" + "=" * 70)
    print("TESTING PDF GENERATION")
    print("=" * 70)

    generator = PDFReportGenerator(test_type="personality", lang="en")

    sample_scores = {
        "openness": 75.0,
        "conscientiousness": 65.0,
        "extraversion": 80.0,
        "agreeableness": 70.0,
        "neuroticism": 40.0
    }

    sample_interpretation = (
        "Based on your personality profile, you demonstrate high levels of openness "
        "and extraversion, suggesting you are outgoing and receptive to new experiences. "
        "Your moderate conscientiousness indicates a balance between structure and flexibility. "
        "With a low neuroticism score, you show good emotional stability and resilience."
    )

    pdf_buffer = generator.generate_pdf(
        result_id="test-123456",
        domain_scores=sample_scores,
        ai_interpretation=sample_interpretation,
        user_id=12345
    )

    print(f"✓ PDF generated successfully")
    print(f"✓ PDF size: {len(pdf_buffer.getvalue()) / 1024:.1f} KB")
    print(f"✓ Test completed!\n")

    return pdf_buffer


if __name__ == "__main__":
    test_pdf_generation()
