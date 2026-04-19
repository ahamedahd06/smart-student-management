"""SSMS design system — refined enterprise-style dark UI (Streamlit)."""
from __future__ import annotations

import streamlit as st

# ── Core palette (zinc / slate base, single blue accent) ─────────────────
BG = "#0c0e12"
BG2 = "#12151c"
SURFACE = "#161a22"
CARD = "#1a1f2a"
CARD_HOVER = "#222831"
ELEVATED = "#1e2430"

# Brand — restrained blue (not loud purple gradient)
PRIMARY = "#3b82f6"
PRIMARY_MUTED = "rgba(59,130,246,0.14)"
PRIMARY_D = "#2563eb"
ACCENT = "#60a5fa"
HEADER_BG = SURFACE  # flat; accent via border / underline in components
HEADER_LINE = PRIMARY

TEAL = "#14b8a6"
PINK = "#ec4899"
ORANGE = "#f59e0b"
SKY = "#38bdf8"
LIME = "#84cc16"

SUCCESS = "#22c55e"
SUCCESS_D = "#16a34a"
SUCCESS_MUTED = "rgba(34,197,94,0.12)"
WARNING = "#eab308"
WARNING_D = "#ca8a04"
DANGER = "#ef4444"
DANGER_D = "#dc2626"
DANGER_MUTED = "rgba(239,68,68,0.12)"

TEXT = "#f1f5f9"
TEXT_SEC = "#94a3b8"
TEXT_DIM = "#64748b"
TEXT_FAINT = "#475569"

BORDER = "rgba(148,163,184,0.06)"
BORDER_S = "rgba(148,163,184,0.1)"
RADIUS = "12px"
RADIUS_SM = "10px"
SHADOW = "0 1px 2px rgba(0,0,0,0.45), 0 4px 12px rgba(0,0,0,0.25)"
SHADOW_MD = "0 4px 20px rgba(0,0,0,0.35)"

CLR_INDIGO = ACCENT
CLR_GREEN = SUCCESS
CLR_AMBER = WARNING
CLR_RED = "#f87171"
CLR_SKY = SKY
CLR_PURPLE = "#a78bfa"
_NUM_COLORS = [ACCENT, CLR_GREEN, WARNING, CLR_RED, SKY, CLR_PURPLE]


def header_bar(title: str, subtitle: str, right_html: str = "") -> None:
    rh = f'<div style="text-align:right;">{right_html}</div>' if right_html else ""
    st.markdown(
        f'<div style="background:{CARD};border:1px solid {BORDER_S};border-radius:{RADIUS};'
        f'border-left:3px solid {PRIMARY};padding:0.75rem 1.25rem;margin-bottom:0.65rem;'
        f'display:flex;align-items:center;justify-content:space-between;box-shadow:{SHADOW};">'
        f'<div><div style="font-size:1.02rem;font-weight:650;color:{TEXT};letter-spacing:-0.02em;">{title}</div>'
        f'<div style="font-size:0.8rem;color:{TEXT_DIM};margin-top:3px;">{subtitle}</div></div>{rh}</div>',
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = "", icon: str = "") -> None:
    ic = f'<span style="margin-right:10px;opacity:0.85;font-size:1rem;">{icon}</span>' if icon else ""
    sub = (
        f'<span style="color:{TEXT_DIM};font-size:0.8rem;font-weight:450;margin-left:10px;">{subtitle}</span>'
        if subtitle
        else ""
    )
    st.markdown(
        f'<div style="padding:0.35rem 0 0.55rem;border-bottom:1px solid {BORDER_S};margin-bottom:0.45rem;">{ic}'
        f'<span style="font-size:1.05rem;font-weight:650;color:{TEXT};letter-spacing:-0.02em;">{title}</span>{sub}</div>',
        unsafe_allow_html=True,
    )


def section(title: str, subtitle: str = "", icon: str = "") -> None:
    ic = f'<span style="margin-right:8px;opacity:0.75;">{icon}</span>' if icon else ""
    sub = f'<span style="color:{TEXT_FAINT};font-size:0.76rem;margin-left:8px;font-weight:450;">{subtitle}</span>' if subtitle else ""
    st.markdown(
        f'<div style="padding:0.2rem 0;margin:0.45rem 0 0.25rem;">{ic}'
        f'<span style="font-size:0.88rem;font-weight:600;color:{TEXT_SEC};letter-spacing:0.02em;">{title}</span>{sub}</div>',
        unsafe_allow_html=True,
    )


def stat_card(label: str, value: str, icon: str = "", idx: int = 0, delta: str = "") -> str:
    accent = _NUM_COLORS[idx % len(_NUM_COLORS)]
    dh = f'<div style="font-size:0.68rem;color:{SUCCESS};margin-top:3px;font-weight:500;">{delta}</div>' if delta else ""
    ic = (
        f'<span style="font-size:1rem;line-height:1;margin-right:8px;opacity:0.88;">{icon}</span>' if icon else ""
    )
    return (
        f'<div style="background:{CARD};border:1px solid {BORDER_S};border-radius:{RADIUS_SM};'
        f'padding:0.75rem 1rem;box-shadow:{SHADOW};">'
        f'<div style="font-size:0.68rem;color:{TEXT_DIM};font-weight:600;text-transform:uppercase;'
        f'letter-spacing:0.06em;margin-bottom:6px;">{label}</div>'
        f'<div style="display:flex;align-items:center;min-height:1.35rem;">{ic}'
        f'<div style="font-size:1.25rem;font-weight:700;color:{accent};line-height:1.1;">{value}</div></div>{dh}</div>'
    )


def stat_row(items: list[tuple], cols: int = 0) -> None:
    n = cols or len(items)
    columns = st.columns(n, gap="small")
    for i, (col, item) in enumerate(zip(columns, items)):
        lbl, val = item[0], item[1]
        ico = item[2] if len(item) > 2 else ""
        delta = item[3] if len(item) > 3 else ""
        with col:
            st.markdown(stat_card(lbl, val, ico, i, delta), unsafe_allow_html=True)


def badge(label: str, variant: str = "default") -> str:
    palette = {
        "success": (TEXT, SUCCESS_MUTED, SUCCESS),
        "warning": (TEXT, "rgba(234,179,8,0.15)", WARNING),
        "danger": (TEXT, DANGER_MUTED, DANGER),
        "info": (TEXT, PRIMARY_MUTED, PRIMARY),
        "default": (TEXT_DIM, "rgba(51,65,85,0.5)", BORDER_S),
        "active": (TEXT, SUCCESS_MUTED, SUCCESS),
        "inactive": (TEXT_DIM, "rgba(51,65,85,0.45)", BORDER_S),
        "low": (TEXT, SUCCESS_MUTED, SUCCESS),
        "medium": (TEXT, "rgba(234,179,8,0.15)", WARNING),
        "high": (TEXT, DANGER_MUTED, DANGER),
        "critical": (TEXT, "rgba(153,27,27,0.35)", "#f87171"),
        "resolved": (TEXT, SUCCESS_MUTED, SUCCESS),
        "open": (TEXT, "rgba(217,119,6,0.2)", WARNING),
        "in_progress": (TEXT, PRIMARY_MUTED, PRIMARY_D),
    }
    fg, bg, border = palette.get(variant, palette["default"])
    bd = border if isinstance(border, str) and border.startswith("rgba") else BORDER_S
    return (
        f'<span style="display:inline-block;padding:3px 11px;border-radius:6px;'
        f'font-size:0.7rem;font-weight:600;color:{fg};background:{bg};border:1px solid {bd};'
        f'white-space:nowrap;">{label}</span>'
    )


_AV_CLR = [PRIMARY, TEAL, SKY, ORANGE, DANGER, CLR_PURPLE, ACCENT]


def student_card(
    name: str,
    subtitle: str,
    status: str = "Active",
    right_text: str = "",
    right_sub: str = "",
    idx: int = 0,
) -> str:
    cl = _AV_CLR[idx % len(_AV_CLR)]
    ini = name[0].upper() if name else "?"
    sv = "active" if status.lower() == "active" else "inactive" if status.lower() == "inactive" else "default"
    sb = badge(status, sv)
    rh = ""
    if right_text:
        rh = (
            f'<div style="text-align:right;">'
            f'<div style="font-weight:600;font-size:0.88rem;color:{TEXT};">{right_text}</div>'
            f'<div style="font-size:0.72rem;color:{TEXT_DIM};">{right_sub}</div></div>'
        )
    return (
        f'<div style="background:{CARD};border:1px solid {BORDER_S};border-radius:{RADIUS_SM};'
        f'padding:0.65rem 1rem;margin-bottom:6px;display:flex;align-items:center;'
        f'justify-content:space-between;transition:background 0.15s, border-color 0.15s;box-shadow:{SHADOW};"'
        f' onmouseover="this.style.background=\'{CARD_HOVER}\'" onmouseout="this.style.background=\'{CARD}\'">'
        f'<div style="display:flex;align-items:center;gap:12px;">'
        f'<div style="width:34px;height:34px;border-radius:10px;background:{cl}22;border:1px solid {cl}44;'
        f'display:flex;align-items:center;justify-content:center;'
        f'color:{cl};font-weight:700;font-size:0.8rem;flex-shrink:0;">{ini}</div>'
        f'<div><div style="font-weight:600;font-size:0.87rem;color:{TEXT};">{name}</div>'
        f'<div style="font-size:0.74rem;color:{TEXT_DIM};">{subtitle}</div></div>'
        f'<div style="margin-left:8px;">{sb}</div></div>{rh}</div>'
    )


def progress_bar(pct: float, color: str = "") -> str:
    if not color:
        color = SUCCESS if pct >= 80 else WARNING if pct >= 60 else DANGER
    track = "#252b36"
    return (
        f'<div style="display:flex;align-items:center;gap:10px;">'
        f'<div style="flex:1;height:7px;background:{track};border-radius:999px;overflow:hidden;border:1px solid {BORDER_S};">'
        f'<div style="width:{min(pct,100):.0f}%;height:100%;background:{color};border-radius:999px;"></div></div>'
        f'<span style="font-size:0.76rem;font-weight:650;color:{TEXT_SEC};min-width:38px;">{pct:.0f}%</span></div>'
    )


def card_start(padding: str = "0.85rem 1.05rem") -> None:
    st.markdown(
        f'<div style="background:{CARD};border:1px solid {BORDER_S};border-radius:{RADIUS_SM};'
        f'padding:{padding};box-shadow:{SHADOW};margin-bottom:0.45rem;">',
        unsafe_allow_html=True,
    )


def card_end() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def info_panel(text: str, icon: str = "") -> None:
    ic = f'<span style="font-size:0.85rem;opacity:0.7;margin-right:8px;">{icon}</span>' if icon else ""
    st.markdown(
        f'<div style="background:{PRIMARY_MUTED};border:1px solid rgba(59,130,246,0.22);'
        f'border-radius:{RADIUS_SM};padding:0.6rem 0.95rem;margin-bottom:0.45rem;display:flex;align-items:flex-start;gap:6px;">'
        f'{ic}<span style="font-size:0.8rem;color:{TEXT_SEC};line-height:1.45;">{text}</span></div>',
        unsafe_allow_html=True,
    )


def empty_state(msg: str, icon: str = "") -> None:
    ic = f'<div style="font-size:1.25rem;opacity:0.25;margin-bottom:0.35rem;">{icon}</div>' if icon else ""
    st.markdown(
        f'<div style="text-align:center;padding:2rem 1rem;background:{SURFACE};'
        f'border:1px dashed {BORDER_S};border-radius:{RADIUS_SM};">'
        f'{ic}'
        f'<p style="font-size:0.86rem;color:{TEXT_DIM};margin:0;font-weight:450;">{msg}</p></div>',
        unsafe_allow_html=True,
    )


def chart_header(title: str, subtitle: str = "") -> None:
    sub = f'<span style="color:{TEXT_FAINT};font-size:0.74rem;margin-left:8px;font-weight:450;">{subtitle}</span>' if subtitle else ""
    st.markdown(
        f'<div style="background:{CARD};border:1px solid {BORDER_S};'
        f'border-radius:{RADIUS_SM} {RADIUS_SM} 0 0;padding:0.55rem 0.95rem;'
        f'box-shadow:{SHADOW};margin-top:0.35rem;">'
        f'<span style="font-size:0.84rem;font-weight:600;color:{TEXT};">{title}</span>{sub}</div>',
        unsafe_allow_html=True,
    )


def chart_footer() -> None:
    st.markdown(
        f'<div style="height:2px;background:{BORDER_S};margin:0;border:1px solid {BORDER_S};border-top:none;'
        f'border-radius:0 0 {RADIUS_SM} {RADIUS_SM};box-shadow:{SHADOW};margin-bottom:0.5rem;"></div>',
        unsafe_allow_html=True,
    )


def alert_card(
    name: str,
    code: str,
    severity: str,
    message: str,
    date: str = "",
    resolved: bool = False,
    note: str = "",
) -> str:
    sv = severity.lower()
    vr = {"critical": "critical", "high": "high", "medium": "medium", "low": "low"}.get(sv, "default")
    lc = {"critical": DANGER_D, "high": DANGER, "medium": WARNING, "low": SUCCESS}.get(sv, PRIMARY)
    status_label = "Resolved" if resolved else severity.title()
    status_badge = badge(status_label, "resolved" if resolved else vr)
    note_html = ""
    if note:
        note_html = (
            f'<div style="background:{SUCCESS_MUTED};border:1px solid rgba(34,197,94,0.25);'
            f'border-radius:8px;padding:0.45rem 0.65rem;margin-top:8px;">'
            f'<div style="font-size:0.65rem;font-weight:650;color:{SUCCESS};text-transform:uppercase;letter-spacing:0.05em;">Resolution</div>'
            f'<div style="font-size:0.78rem;color:{TEXT_SEC};margin-top:2px;">{note}</div></div>'
        )
    return (
        f'<div style="background:{CARD};border:1px solid {BORDER_S};border-left:3px solid {lc};'
        f'border-radius:{RADIUS_SM};padding:0.7rem 1rem;margin-bottom:6px;box-shadow:{SHADOW};">'
        f'<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:4px;">'
        f'<span style="font-weight:650;font-size:0.86rem;color:{TEXT};">{name}</span>'
        f'<span style="font-size:0.72rem;color:{TEXT_DIM};background:{BG2};padding:2px 8px;border-radius:6px;">{code}</span>'
        f"{status_badge}</div>"
        f'<div style="font-size:0.8rem;color:{TEXT_SEC};line-height:1.4;">{message}</div>'
        f"{note_html}"
        f'<div style="font-size:0.68rem;color:{TEXT_FAINT};margin-top:6px;">{date}</div></div>'
    )


# ══════════════════════════════════════════════════════════════════════════
# Global CSS
# ══════════════════════════════════════════════════════════════════════════
_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

section[data-testid="stSidebar"],
div[data-testid="collapsedControl"] {{ display:none!important; }}
header[data-testid="stHeader"] {{ background:transparent!important; height:0!important; }}

html, body, [data-testid="stAppViewContainer"], .stApp {{
  background: {BG} !important;
  font-family: 'Plus Jakarta Sans', 'Segoe UI', system-ui, sans-serif !important;
  color: {TEXT_SEC} !important;
}}

/* Default text in main column (paragraphs, captions) stays readable */
section[data-testid="stMain"] .stMarkdown, section[data-testid="stMain"] .stMarkdown p {{
  color: {TEXT_SEC} !important;
}}

.main .block-container {{
  max-width: 1180px;
  padding: 0.75rem 1.75rem 3rem;
  margin: 0 auto;
}}

h1, h2, h3, h4 {{ color: {TEXT} !important; font-weight: 650 !important; letter-spacing: -0.02em !important; }}

/* Tabs */
div[data-testid="stTabs"] {{
  background: {SURFACE};
  border: 1px solid {BORDER_S};
  border-radius: {RADIUS_SM};
  padding: 5px 6px;
  box-shadow: {SHADOW};
  margin-bottom: 0.65rem;
}}
div[data-testid="stTabs"] [role="tablist"] {{
  gap: 4px;
  border-bottom: none !important;
}}
div[data-testid="stTabs"] button[data-baseweb="tab"] {{
  font-weight: 600;
  font-size: 0.8rem;
  padding: 0.45rem 0.95rem;
  border-radius: 8px !important;
  border: none !important;
  color: {TEXT_DIM};
  transition: color 0.15s, background 0.15s;
  background: transparent !important;
}}
div[data-testid="stTabs"] button[data-baseweb="tab"]:hover {{
  color: {TEXT} !important;
  background: rgba(255,255,255,0.04) !important;
}}
div[data-testid="stTabs"] button[aria-selected="true"] {{
  color: {TEXT} !important;
  background: {CARD} !important;
  box-shadow: 0 0 0 1px {BORDER_S}, 0 1px 3px rgba(0,0,0,0.2);
}}

/* Buttons */
div[data-testid="stButton"] button,
div[data-testid="stFormSubmitButton"] button,
div[data-testid="stDownloadButton"] button {{
  border-radius: 9px !important;
  font-weight: 600 !important;
  font-size: 0.84rem !important;
  padding: 0.48rem 1.05rem !important;
  transition: background 0.15s, border-color 0.15s, transform 0.12s !important;
  border: 1px solid {BORDER_S} !important;
  background: {CARD} !important;
  color: {TEXT} !important;
}}
div[data-testid="stButton"] button:hover,
div[data-testid="stFormSubmitButton"] button:hover {{
  background: {CARD_HOVER} !important;
  border-color: rgba(148,163,184,0.18) !important;
}}
div[data-testid="stButton"] button[kind="primary"],
div[data-testid="stButton"] button[data-testid="stBaseButton-primary"],
div[data-testid="stFormSubmitButton"] button[kind="primary"],
div[data-testid="stFormSubmitButton"] button[data-testid="stBaseButton-primary"] {{
  background: {PRIMARY} !important;
  color: #fff !important;
  border: 1px solid {PRIMARY_D} !important;
  box-shadow: 0 1px 2px rgba(0,0,0,0.2);
}}
div[data-testid="stButton"] button[kind="primary"]:hover {{
  background: {PRIMARY_D} !important;
}}

/* ── Form widgets: force dark surfaces + light text (Base Web often ships light chrome) ── */
div[data-testid="stWidgetLabel"] label,
div[data-testid="stWidgetLabel"] p,
label[data-testid="stWidgetLabel"] {{
  color: {TEXT_SEC} !important;
  font-size: 0.8rem !important;
  font-weight: 500 !important;
}}

div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stDateInput"] input {{
  border-radius: 9px !important;
  border: 1px solid {BORDER_S} !important;
  padding: 0.52rem 0.85rem !important;
  font-size: 0.86rem !important;
  background: {BG2} !important;
  background-color: {BG2} !important;
  color: {TEXT} !important;
  -webkit-text-fill-color: {TEXT} !important;
  caret-color: {TEXT} !important;
}}
div[data-testid="stTextInput"] input::placeholder,
div[data-testid="stNumberInput"] input::placeholder,
div[data-testid="stTextArea"] textarea::placeholder,
div[data-testid="stDateInput"] input::placeholder,
div[data-testid="stSelectbox"] input::placeholder,
div[data-testid="stMultiSelect"] input::placeholder {{
  color: #cbd5e1 !important;
  opacity: 1 !important;
  -webkit-text-fill-color: #cbd5e1 !important;
}}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stNumberInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus,
div[data-testid="stDateInput"] input:focus {{
  border-color: {PRIMARY} !important;
  box-shadow: 0 0 0 2px {PRIMARY_MUTED} !important;
  color: {TEXT} !important;
  -webkit-text-fill-color: {TEXT} !important;
}}

/* Select / multiselect: control surface + value text */
div[data-testid="stSelectbox"] > div > div,
div[data-testid="stMultiSelect"] > div > div {{
  border-radius: 9px !important;
  border: 1px solid {BORDER_S} !important;
  background: {BG2} !important;
  background-color: {BG2} !important;
}}
div[data-testid="stSelectbox"] [data-baseweb="select"] > div,
div[data-testid="stMultiSelect"] [data-baseweb="select"] > div {{
  background: {BG2} !important;
  background-color: {BG2} !important;
}}
div[data-testid="stSelectbox"] [role="combobox"],
div[data-testid="stMultiSelect"] [role="combobox"] {{
  background: {BG2} !important;
  background-color: {BG2} !important;
  color: {TEXT} !important;
  -webkit-text-fill-color: {TEXT} !important;
}}
div[data-testid="stSelectbox"] span,
div[data-testid="stSelectbox"] p,
div[data-testid="stMultiSelect"] span,
div[data-testid="stMultiSelect"] p {{
  color: {TEXT} !important;
  -webkit-text-fill-color: {TEXT} !important;
}}
div[data-testid="stSelectbox"] [data-baseweb="select"] span,
div[data-testid="stMultiSelect"] [data-baseweb="select"] span {{
  color: {TEXT} !important;
  -webkit-text-fill-color: {TEXT} !important;
}}
div[data-testid="stSelectbox"] input,
div[data-testid="stMultiSelect"] input {{
  background: {BG2} !important;
  color: {TEXT} !important;
  -webkit-text-fill-color: {TEXT} !important;
}}

/* Select / multiselect: force readable label (react-select / Base Web often sets dark grey inline) */
div[data-testid="stSelectbox"] [data-baseweb="select"],
div[data-testid="stMultiSelect"] [data-baseweb="select"] {{
  color: {TEXT} !important;
}}
div[data-testid="stSelectbox"] [data-baseweb="select"] *:not(svg):not(path):not(circle):not(rect):not(line):not(polyline):not(polygon),
div[data-testid="stMultiSelect"] [data-baseweb="select"] *:not(svg):not(path):not(circle):not(rect):not(line):not(polyline):not(polygon) {{
  color: #e2e8f0 !important;
  -webkit-text-fill-color: #e2e8f0 !important;
  opacity: 1 !important;
}}
div[data-testid="stSelectbox"] [data-baseweb="select"] [class*="placeholder"],
div[data-testid="stMultiSelect"] [data-baseweb="select"] [class*="placeholder"],
div[data-testid="stSelectbox"] [data-baseweb="select"] [class*="Placeholder"],
div[data-testid="stMultiSelect"] [data-baseweb="select"] [class*="Placeholder"] {{
  color: #cbd5e1 !important;
  -webkit-text-fill-color: #cbd5e1 !important;
  opacity: 1 !important;
}}
div[data-testid="stSelectbox"] [data-baseweb="select"] [class*="singleValue"],
div[data-testid="stMultiSelect"] [data-baseweb="select"] [class*="singleValue"],
div[data-testid="stSelectbox"] [data-baseweb="select"] [class*="SingleValue"],
div[data-testid="stMultiSelect"] [data-baseweb="select"] [class*="SingleValue"] {{
  color: {TEXT} !important;
  -webkit-text-fill-color: {TEXT} !important;
}}

/* Dropdown menus (often portaled under body) */
div[data-baseweb="popover"] ul,
div[data-baseweb="popover"] li,
ul[role="listbox"],
li[role="option"] {{
  background-color: {CARD} !important;
  color: {TEXT} !important;
}}
li[role="option"]:hover {{
  background-color: {CARD_HOVER} !important;
}}

/* Time input if used */
div[data-testid="stTimeInput"] input {{
  background: {BG2} !important;
  color: {TEXT} !important;
  -webkit-text-fill-color: {TEXT} !important;
  border: 1px solid {BORDER_S} !important;
  border-radius: 9px !important;
}}

/* Native date picker text on WebKit */
div[data-testid="stDateInput"] input::-webkit-datetime-edit-text,
div[data-testid="stDateInput"] input::-webkit-datetime-edit-month-field,
div[data-testid="stDateInput"] input::-webkit-datetime-edit-day-field,
div[data-testid="stDateInput"] input::-webkit-datetime-edit-year-field {{
  color: {TEXT} !important;
}}

div[data-testid="stDataFrame"] {{
  border: 1px solid {BORDER_S};
  border-radius: {RADIUS_SM};
  overflow: hidden;
  box-shadow: {SHADOW};
}}

details[data-testid="stExpander"] {{
  border: 1px solid {BORDER_S} !important;
  border-radius: {RADIUS_SM} !important;
  background: {CARD} !important;
  box-shadow: {SHADOW};
  margin-bottom: 0.4rem;
}}
details[data-testid="stExpander"] summary {{
  font-weight: 600;
  font-size: 0.84rem;
  padding: 0.55rem 0.95rem;
  color: {TEXT} !important;
}}

div[data-testid="stVegaLiteChart"] {{
  max-height: 260px !important;
  overflow: hidden;
  opacity: 0.95;
}}

div[data-testid="stAlert"] {{ border-radius: 9px !important; font-size: 0.84rem !important; }}

div[data-testid="stCameraInput"] video {{
  max-height: 300px !important;
  width: 100% !important;
  object-fit: cover;
  border-radius: {RADIUS_SM};
  border: 1px solid {BORDER_S};
}}

hr {{ border-color: {BORDER_S} !important; opacity: 0.35; }}

div[data-testid="stMetric"] {{
  background: {CARD};
  border: 1px solid {BORDER_S};
  border-radius: {RADIUS_SM};
  padding: 0.5rem 0.75rem;
}}
</style>
"""


def inject_theme() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
