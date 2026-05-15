"""
charts.py — Plotly Chart Components
=====================================
Reusable, styled chart functions for the dashboard:
  - ATS gauge chart
  - Skill radar chart
  - Keyword bar chart
  - Score breakdown donut chart
  - Historical score line chart
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Optional

# ── Shared theme ─────────────────────────────────────────────────────────────
DARK_THEME = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"family": "Inter, sans-serif", "color": "#94A3B8"},
}

PRIMARY = "#6C63FF"
SUCCESS = "#10B981"
WARNING = "#F59E0B"
DANGER  = "#EF4444"
LIGHT_PURPLE = "#A78BFA"


def _score_color(score: float) -> str:
    """Return color based on score value."""
    if score >= 70: return SUCCESS
    if score >= 50: return WARNING
    return DANGER


# ═══════════════════════════════════════════════════════════════════════════════
# ATS Score Gauge
# ═══════════════════════════════════════════════════════════════════════════════

def ats_gauge_chart(score: float, title: str = "ATS Score") -> go.Figure:
    """
    Create a circular gauge chart for the ATS score.

    Args:
        score: Score value (0-100).
        title: Chart title.

    Returns:
        Plotly Figure object.
    """
    color = _score_color(score)
    label = "Excellent" if score >= 70 else ("Good" if score >= 50 else "Needs Work")

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        delta={"reference": 70, "increasing": {"color": SUCCESS}, "decreasing": {"color": DANGER}},
        number={"suffix": "%", "font": {"size": 40, "family": "Outfit", "color": color}},
        title={"text": f"<b>{title}</b><br><span style='font-size:14px;color:#94A3B8'>{label}</span>",
               "font": {"size": 16}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#2D2D4E",
                     "tickfont": {"size": 11}},
            "bar": {"color": color, "thickness": 0.25},
            "bgcolor": "#1A1A2E",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 50],  "color": "rgba(239,68,68,0.12)"},
                {"range": [50, 70], "color": "rgba(245,158,11,0.12)"},
                {"range": [70, 100],"color": "rgba(16,185,129,0.12)"},
            ],
            "threshold": {
                "line": {"color": color, "width": 3},
                "thickness": 0.8,
                "value": score,
            },
        }
    ))
    fig.update_layout(
        **DARK_THEME,
        height=280,
        margin={"l": 30, "r": 30, "t": 60, "b": 20},
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# Score Breakdown Bar Chart
# ═══════════════════════════════════════════════════════════════════════════════

def score_breakdown_chart(ats_detail: Dict) -> go.Figure:
    """
    Horizontal bar chart showing the 5 ATS score components.

    Args:
        ats_detail: Dict with keyword_score, format_score, etc.
    """
    components = [
        ("Keyword Match", ats_detail.get("keyword_score", 0)),
        ("Format Quality", ats_detail.get("format_score", 0)),
        ("Resume Sections", ats_detail.get("section_score", 0)),
        ("Action Verbs", ats_detail.get("action_verb_score", 0)),
        ("Length Score", ats_detail.get("length_score", 0)),
    ]

    labels = [c[0] for c in components]
    values = [c[1] for c in components]
    colors = [_score_color(v) for v in values]

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker={"color": colors, "opacity": 0.85,
                "line": {"color": "rgba(255,255,255,0.1)", "width": 1}},
        text=[f"{v:.0f}%" for v in values],
        textposition="outside",
        textfont={"color": "#E2E8F0", "size": 12},
        hovertemplate="<b>%{y}</b><br>Score: %{x:.1f}%<extra></extra>",
    ))

    fig.update_layout(
        **DARK_THEME,
        title={"text": "Score Breakdown", "font": {"size": 15, "color": "#E2E8F0"}},
        xaxis={"range": [0, 115], "showgrid": True,
               "gridcolor": "rgba(45,45,78,0.5)", "ticksuffix": "%"},
        yaxis={"tickfont": {"size": 12, "color": "#94A3B8"}},
        height=260,
        bargap=0.35,
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# Keyword Match Donut Chart
# ═══════════════════════════════════════════════════════════════════════════════

def keyword_donut_chart(matched: List[str], missing: List[str]) -> go.Figure:
    """
    Donut chart comparing matched vs missing keywords.
    """
    n_matched = len(matched)
    n_missing = len(missing)
    total = n_matched + n_missing or 1

    fig = go.Figure(go.Pie(
        labels=["Matched Keywords", "Missing Keywords"],
        values=[n_matched, n_missing],
        hole=0.65,
        marker={"colors": [SUCCESS, DANGER],
                "line": {"color": "#0F0F1A", "width": 3}},
        textfont={"size": 12, "color": "white"},
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
    ))

    pct = round(n_matched / total * 100)
    fig.add_annotation(
        text=f"<b style='font-size:22px;color:#E2E8F0'>{pct}%</b><br>"
             f"<span style='font-size:11px;color:#94A3B8'>Match Rate</span>",
        x=0.5, y=0.5, showarrow=False,
        font={"size": 14}, xref="paper", yref="paper",
    )
    fig.update_layout(
        **DARK_THEME,
        title={"text": "Keyword Analysis", "font": {"size": 15, "color": "#E2E8F0"}},
        height=280,
        legend={"font": {"color": "#94A3B8"}, "orientation": "h", "y": -0.1},
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# Skill Radar Chart
# ═══════════════════════════════════════════════════════════════════════════════

def skill_radar_chart(ats_detail: Dict) -> go.Figure:
    """
    Spider/radar chart for the 5 ATS score dimensions.
    """
    categories = ["Keywords", "Format", "Sections", "Action Verbs", "Length"]
    values = [
        ats_detail.get("keyword_score", 0),
        ats_detail.get("format_score", 0),
        ats_detail.get("section_score", 0),
        ats_detail.get("action_verb_score", 0),
        ats_detail.get("length_score", 0),
    ]
    # Close the radar polygon
    values_closed = values + [values[0]]
    categories_closed = categories + [categories[0]]

    fig = go.Figure(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(108,99,255,0.18)",
        line={"color": PRIMARY, "width": 2},
        marker={"size": 6, "color": PRIMARY},
        hovertemplate="<b>%{theta}</b>: %{r:.0f}%<extra></extra>",
    ))

    fig.update_layout(
        polar={
            "radialaxis": {
                "range": [0, 100],
                "tickfont": {"size": 10, "color": "#64748B"},
                "gridcolor": "#2D2D4E",
                "linecolor": "#2D2D4E",
                "ticksuffix": "%",
            },
            "angularaxis": {
                "tickfont": {"size": 11, "color": "#94A3B8"},
                "gridcolor": "#2D2D4E",
                "linecolor": "#2D2D4E",
            },
            "bgcolor": "rgba(0,0,0,0)",
        },
        title={"text": "ATS Radar", "font": {"size": 15, "color": "#E2E8F0"}},
        height=300,
        **DARK_THEME,
        margin={"l": 60, "r": 60, "t": 50, "b": 30},
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# Historical Score Line Chart
# ═══════════════════════════════════════════════════════════════════════════════

def historical_scores_chart(reports: List[Dict]) -> go.Figure:
    """
    Line chart showing ATS score trend across multiple reports.

    Args:
        reports: List of report dicts with 'created_at' and 'ats_score'.
    """
    if not reports:
        fig = go.Figure()
        fig.add_annotation(text="No analysis history yet", x=0.5, y=0.5,
                          showarrow=False, font={"color": "#94A3B8", "size": 14},
                          xref="paper", yref="paper")
        fig.update_layout(height=200, **DARK_THEME, margin={"l": 20, "r": 20, "t": 40, "b": 20})
        return fig

    dates = [r.get("created_at", "")[:10] for r in reports]
    scores = [r.get("ats_score", 0) for r in reports]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=scores,
        mode="lines+markers",
        line={"color": PRIMARY, "width": 2.5, "shape": "spline"},
        marker={"size": 8, "color": scores, "colorscale": [[0, DANGER], [0.5, WARNING], [1, SUCCESS]],
                "line": {"color": "#0F0F1A", "width": 2}},
        fill="tozeroy",
        fillcolor="rgba(108,99,255,0.08)",
        hovertemplate="<b>%{x}</b><br>ATS Score: %{y:.1f}%<extra></extra>",
        name="ATS Score",
    ))

    fig.add_hline(y=70, line_dash="dash", line_color=SUCCESS,
                  annotation_text="Target (70%)", annotation_font_color=SUCCESS)

    fig.update_layout(
        **DARK_THEME,
        title={"text": "Score History", "font": {"size": 15, "color": "#E2E8F0"}},
        xaxis={"showgrid": True, "gridcolor": "rgba(45,45,78,0.5)"},
        yaxis={"range": [0, 105], "showgrid": True, "gridcolor": "rgba(45,45,78,0.5)",
               "ticksuffix": "%"},
        height=220,
        showlegend=False,
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# Admin Analytics Charts
# ═══════════════════════════════════════════════════════════════════════════════

def admin_bar_chart(data: Dict[str, int], title: str) -> go.Figure:
    """Simple bar chart for admin analytics."""
    fig = go.Figure(go.Bar(
        x=list(data.keys()),
        y=list(data.values()),
        marker={"color": PRIMARY, "opacity": 0.85,
                "line": {"color": LIGHT_PURPLE, "width": 1}},
        hovertemplate="<b>%{x}</b><br>%{y}<extra></extra>",
    ))
    fig.update_layout(
        **DARK_THEME,
        title={"text": title, "font": {"size": 15, "color": "#E2E8F0"}},
        xaxis={"tickfont": {"color": "#94A3B8"}},
        yaxis={"showgrid": True, "gridcolor": "rgba(45,45,78,0.5)"},
        height=250,
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
    )
    return fig
