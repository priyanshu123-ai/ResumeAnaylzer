"""
report_service.py — PDF Report Generation
==========================================
Generates downloadable PDF analysis reports using ReportLab.
"""

import io
from datetime import datetime
from typing import Dict, Any, List

from backend.utils.logger import get_logger

logger = get_logger(__name__)


def generate_analysis_report_pdf(
    report_data: Dict[str, Any],
    user_name: str,
    job_title: str
) -> bytes:
    """
    Generate a styled PDF report from analysis results.

    Args:
        report_data: Full analysis report dict.
        user_name: Name of the user.
        job_title: Job position title.

    Returns:
        PDF file as bytes (ready for HTTP response).
    """
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, KeepTogether
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
        )

        # ── Color Palette ─────────────────────────────────────
        PRIMARY = colors.HexColor("#6C63FF")
        SECONDARY = colors.HexColor("#F7F7FE")
        SUCCESS = colors.HexColor("#10B981")
        WARNING = colors.HexColor("#F59E0B")
        DANGER = colors.HexColor("#EF4444")
        DARK = colors.HexColor("#1F2937")
        GRAY = colors.HexColor("#6B7280")

        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "Title", parent=styles["Title"],
            textColor=PRIMARY, fontSize=22, spaceAfter=4,
        )
        subtitle_style = ParagraphStyle(
            "Subtitle", parent=styles["Normal"],
            textColor=GRAY, fontSize=11, spaceAfter=12,
        )
        heading_style = ParagraphStyle(
            "Heading", parent=styles["Heading2"],
            textColor=DARK, fontSize=13, spaceBefore=12, spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "Body", parent=styles["Normal"],
            textColor=DARK, fontSize=10, spaceAfter=4, leading=14,
        )
        score_style = ParagraphStyle(
            "Score", parent=styles["Normal"],
            textColor=PRIMARY, fontSize=28, alignment=TA_CENTER,
        )

        elements = []
        generated_at = datetime.now().strftime("%B %d, %Y at %I:%M %p")

        # ── Header ────────────────────────────────────────────
        elements.append(Paragraph("AI Resume Analyzer", title_style))
        elements.append(Paragraph("Professional Analysis Report", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=2, color=PRIMARY))
        elements.append(Spacer(1, 12))

        # ── Report Metadata ───────────────────────────────────
        meta_data = [
            ["Candidate", user_name],
            ["Job Title", job_title],
            ["Generated", generated_at],
        ]
        meta_table = Table(meta_data, colWidths=[1.5*inch, 5*inch])
        meta_table.setStyle(TableStyle([
            ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 10),
            ("TEXTCOLOR", (0,0), (0,-1), PRIMARY),
            ("TEXTCOLOR", (1,0), (1,-1), DARK),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 16))

        # ── Overall ATS Score ─────────────────────────────────
        ats_total = report_data.get("overall_score", 0)
        score_color = SUCCESS if ats_total >= 70 else (WARNING if ats_total >= 50 else DANGER)
        score_label = "Excellent" if ats_total >= 70 else ("Good" if ats_total >= 50 else "Needs Work")

        elements.append(Paragraph("📊 ATS Score Summary", heading_style))

        score_table_data = [["Overall ATS Score", "Skill Match", "Keyword Match"]]
        ats_detail = report_data.get("ats_score", {})
        score_table_data.append([
            f"{ats_total:.1f}%",
            f"{report_data.get('skill_match_score', 0):.1f}%",
            f"{report_data.get('keyword_match_score', 0):.1f}%",
        ])
        score_table = Table(score_table_data, colWidths=[2.2*inch, 2.2*inch, 2.2*inch])
        score_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), PRIMARY),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 12),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("FONTNAME", (0,1), (-1,-1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0,1), (-1,-1), score_color),
            ("FONTSIZE", (0,1), (-1,-1), 18),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [SECONDARY]),
            ("GRID", (0,0), (-1,-1), 0.5, colors.lightgrey),
            ("TOPPADDING", (0,0), (-1,-1), 8),
            ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ]))
        elements.append(score_table)
        elements.append(Spacer(1, 16))

        # ── Component Scores ──────────────────────────────────
        elements.append(Paragraph("🔍 Score Breakdown", heading_style))
        comp_data = [["Component", "Score", "Status"]]
        components = [
            ("Keyword Match", ats_detail.get("keyword_score", 0)),
            ("Format Score", ats_detail.get("format_score", 0)),
            ("Sections Score", ats_detail.get("section_score", 0)),
            ("Action Verbs", ats_detail.get("action_verb_score", 0)),
            ("Length Score", ats_detail.get("length_score", 0)),
        ]
        for name, score in components:
            status = "[OK] Good" if score >= 70 else ("[WARN] Fair" if score >= 40 else "[ERR] Poor")
            comp_data.append([name, f"{score:.1f}%", status])

        comp_table = Table(comp_data, colWidths=[2.5*inch, 1.5*inch, 2.6*inch])
        comp_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), DARK),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 10),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, SECONDARY]),
            ("GRID", (0,0), (-1,-1), 0.5, colors.lightgrey),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ]))
        elements.append(comp_table)
        elements.append(Spacer(1, 16))

        # ── Keywords ──────────────────────────────────────────
        matched = report_data.get("matched_keywords", [])
        missing = report_data.get("missing_keywords", [])

        if matched:
            elements.append(Paragraph("[OK] Matched Keywords", heading_style))
            elements.append(Paragraph(", ".join(matched[:20]), body_style))
            elements.append(Spacer(1, 8))

        if missing:
            elements.append(Paragraph("[ERR] Missing Keywords (Add These)", heading_style))
            elements.append(Paragraph(", ".join(missing[:15]), body_style))
            elements.append(Spacer(1, 8))

        # ── Suggestions ───────────────────────────────────────
        suggestions = report_data.get("suggestions", [])
        if suggestions:
            elements.append(Paragraph("💡 Improvement Suggestions", heading_style))
            for i, suggestion in enumerate(suggestions[:8], 1):
                elements.append(Paragraph(f"{i}. {suggestion}", body_style))
            elements.append(Spacer(1, 8))

        # ── AI Feedback ───────────────────────────────────────
        gemini_feedback = report_data.get("gemini_feedback", "")
        if gemini_feedback:
            elements.append(Paragraph("🤖 AI Resume Feedback", heading_style))
            # Split into paragraphs for better formatting
            for para in gemini_feedback.split("\n\n")[:4]:
                if para.strip():
                    clean = para.replace("**", "").replace("##", "")
                    elements.append(Paragraph(clean.strip(), body_style))
            elements.append(Spacer(1, 8))

        # ── Footer ────────────────────────────────────────────
        elements.append(HRFlowable(width="100%", thickness=1, color=GRAY))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(
            f"Generated by AI Resume Analyzer | {generated_at} | Confidential",
            ParagraphStyle("Footer", parent=styles["Normal"],
                          textColor=GRAY, fontSize=8, alignment=TA_CENTER)
        ))

        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        logger.info(f"PDF report generated: {len(pdf_bytes)} bytes")
        return pdf_bytes

    except ImportError:
        logger.error("ReportLab not installed. Run: pip install reportlab")
        raise RuntimeError("PDF generation library not available.")
    except Exception as e:
        logger.error(f"PDF generation failed: {e}", exc_info=True)
        raise RuntimeError(f"Could not generate PDF: {e}")
