"""Lecturer portal — compact professional layout."""
from __future__ import annotations
import streamlit as st
from analytics_util import emotion_sentiment_chart, module_programme_attendance_chart, weekly_checkin_trend
from catalog import PROGRAMMES
from database import get_connection
from theme import (
    PRIMARY, PRIMARY_D, ACCENT, HEADER_BG,
    TEXT, TEXT_SEC, TEXT_DIM, TEXT_FAINT,
    BG, CARD, CARD_HOVER, SURFACE, BORDER_S, RADIUS, RADIUS_SM,
    SHADOW, SHADOW_MD, SUCCESS, WARNING, DANGER,
    CLR_INDIGO, CLR_GREEN, CLR_AMBER, CLR_RED,
    page_header, section, stat_row, badge, student_card, alert_card,
    progress_bar, card_start, card_end, info_panel, empty_state,
    chart_header, chart_footer,
)

_AV = ["#6366f1", "#ec4899", "#14b8a6", "#f59e0b", "#ef4444", "#8b5cf6", "#0ea5e9"]

def render_lecturer_portal(user: dict) -> None:
    nm = user.get("display_name", user["email"].split("@")[0])
    pc = _cnt_iv(nm, user["email"])
    iv_label = f"Interventions ({pc})" if pc > 0 else "Interventions"
    t1, t2, t3, t4, t5 = st.tabs(["Sessions", "Students", "Analytics", "Alerts", iv_label])
    with t1: _sessions()
    with t2: _students()
    with t3: _analytics()
    with t4: _alerts()
    with t5: _interventions(nm, user["email"])

def _session_mod_badge(mod: str) -> str:
    m = (mod or "").strip()
    if not m:
        return "?"
    w = m.split()
    if len(w) >= 2:
        return (w[0][0] + w[1][0]).upper()[:4]
    return m[:4].upper()


def _cnt_iv(dn: str, em: str) -> int:
    s = em.split("@")[0]
    with get_connection() as c:
        r = c.execute("SELECT COUNT(*) AS c FROM interventions WHERE status!='resolved' AND (lower(assigned_to)=lower(?) OR lower(assigned_to)=lower(?) OR lower(assigned_to)=lower(?))", (dn, em, s)).fetchone()
    return int(r["c"]) if r else 0

# ═══════════ SESSIONS ═══════════
def _sessions() -> None:
    page_header("Attendance Sessions", "Create and manage sessions", "📅")
    info_panel(
        "Sessions are class meetings you schedule. Each student sees them on Check-In and records "
        "attendance against that session; emotion is logged with the same check-in. "
        "Choose one of the five programme modules below (no short codes)."
    )
    with st.expander("Create session", expanded=False):
        mod = st.selectbox("Module", PROGRAMMES, key="ls_mod")
        c3, c4 = st.columns(2)
        st_ = c3.selectbox("Type", ["Lecture", "Lab", "Tutorial"], key="ls_t")
        sn = c4.text_input("Session name", "Week 4 lecture", key="ls_sn")
        c5, c6 = st.columns(2)
        sd = c5.date_input("Date", key="ls_d")
        stm = c6.text_input("Time", "14:00", key="ls_tm")
        if st.button("Create", type="primary", key="ls_go"):
            with get_connection() as c:
                c.execute(
                    "INSERT INTO class_sessions (module_code,module_name,session_type,session_name,session_date,session_time) VALUES (?,?,?,?,?,?)",
                    (mod, mod, st_, sn, str(sd), stm),
                )
            st.success("Session created.")
            st.rerun()

    with get_connection() as c:
        rows = c.execute("SELECT * FROM class_sessions ORDER BY session_date DESC, session_time DESC").fetchall()
    if not rows: empty_state("No sessions.", "📅"); return
    for i, r in enumerate(rows):
        with get_connection() as c:
            pr = c.execute("SELECT COUNT(*) AS c FROM attendance_records WHERE session_id=? AND status='present'", (r["id"],)).fetchone()["c"]
            ab = c.execute("SELECT COUNT(*) AS c FROM attendance_records WHERE session_id=? AND status!='present'", (r["id"],)).fetchone()["c"]
        total = pr + ab; rate = f"{pr/total*100:.0f}%" if total > 0 else "—"
        cl = _AV[i % len(_AV)]
        mod = (r["module_name"] or r["module_code"] or "").strip() or "Module"
        bd = _session_mod_badge(mod)
        st.markdown(f"""
<div style="background:{CARD};border:1px solid {BORDER_S};border-radius:{RADIUS_SM};
            padding:0.6rem 0.9rem;margin-bottom:4px;display:flex;align-items:center;
            justify-content:space-between;box-shadow:{SHADOW};transition:background 0.1s;"
     onmouseover="this.style.background='{CARD_HOVER}'" onmouseout="this.style.background='{CARD}'">
  <div style="display:flex;align-items:center;gap:10px;">
    <div style="width:34px;height:34px;border-radius:50%;background:{cl};
                display:flex;align-items:center;justify-content:center;color:white;
                font-weight:800;font-size:0.65rem;flex-shrink:0;">{bd}</div>
    <div>
      <div style="font-weight:600;font-size:0.9rem;color:{TEXT};">{mod} — {r["session_name"]}</div>
      <div style="font-size:0.78rem;color:{TEXT_DIM};">{r["session_type"] or "Session"}</div>
    </div>
  </div>
  <div style="text-align:right;">
    <div style="font-size:0.78rem;color:{TEXT_DIM};">{r["session_date"]} · {r["session_time"]}</div>
    <div style="margin-top:3px;">{badge(f"{pr} Present","success") if pr>0 else ""} {badge(f"{ab} Absent","danger") if ab>0 else ""}
      <span style="font-size:0.8rem;font-weight:700;color:{TEXT_SEC};margin-left:5px;">{rate}</span></div>
  </div>
</div>""", unsafe_allow_html=True)

# ═══════════ STUDENTS ═══════════
def _students() -> None:
    page_header("Students", "Monitor attendance and engagement", "👥")
    with get_connection() as c:
        rows = c.execute("SELECT * FROM students ORDER BY student_code").fetchall()
    if not rows: empty_state("No students.", "👥"); return
    t = len(rows)
    lr = sum(1 for r in rows if (r["risk_level"] or "low").lower() == "low")
    mr = sum(1 for r in rows if (r["risk_level"] or "").lower() == "medium")
    hr = sum(1 for r in rows if (r["risk_level"] or "").lower() == "high")
    stat_row([("Total", str(t), "👥"), ("Low Risk", str(lr), "✅"), ("Medium", str(mr), "⚠️"), ("High", str(hr), "🔴")])

    q = st.text_input("🔍 Search...", "", key="lec_s", label_visibility="collapsed", placeholder="Search students...")
    filtered = [r for r in rows if q.lower() in (r["name"] or "").lower() or q.lower() in (r["student_code"] or "").lower() or q.lower() in (r["email"] or "").lower()] if q else rows

    for i, r in enumerate(filtered):
        att = int(r["attendance_rate"] or 0)
        rk = (r["risk_level"] or "low").lower()
        rk_b = badge(f"{rk.title()}", rk if rk in ("low", "medium", "high") else "default")
        st.markdown(f"""
<div style="background:{CARD};border:1px solid {BORDER_S};border-radius:{RADIUS_SM};
            padding:0.55rem 0.9rem;margin-bottom:4px;box-shadow:{SHADOW};
            display:grid;grid-template-columns:70px 1.2fr 1fr 85px;gap:10px;align-items:center;">
  <div style="font-size:0.82rem;font-weight:600;color:{TEXT_DIM};">{r["student_code"]}</div>
  <div>
    <div style="font-weight:600;font-size:0.88rem;color:{TEXT};">{r["name"]}</div>
    <div style="font-size:0.72rem;color:{TEXT_FAINT};">{r["email"] or ""}</div>
  </div>
  <div>{progress_bar(att)}</div>
  <div style="text-align:center;">{rk_b}</div>
</div>""", unsafe_allow_html=True)

# ═══════════ ANALYTICS — compact ═══════════
def _analytics() -> None:
    page_header("Analytics", "Attendance and engagement overview", "📊")
    with get_connection() as c:
        t = c.execute("SELECT COUNT(*) AS c FROM students").fetchone()["c"]
        a = c.execute("SELECT AVG(attendance_rate) AS a FROM students").fetchone()["a"] or 0
        ar = c.execute("SELECT COUNT(*) AS c FROM students WHERE risk_level IN ('high','medium')").fetchone()["c"]
        sn = c.execute("SELECT COUNT(*) AS c FROM class_sessions").fetchone()["c"]
    stat_row([("Avg Attendance", f"{float(a):.0f}%", "📈"), ("At Risk", f"{ar}", "⚠️"), ("Modules", str(sn), "📚")])

    chart_header("Programme attendance (avg %)"); st.bar_chart(module_programme_attendance_chart(5), height=150); chart_footer()
    chart_header("Weekly trends"); st.line_chart(weekly_checkin_trend(5), height=140); chart_footer()
    c1, c2 = st.columns(2)
    with c1:
        with get_connection() as c:
            lc = c.execute("SELECT COUNT(*) AS c FROM students WHERE IFNULL(risk_level,'low')='low'").fetchone()["c"]
            mc = c.execute("SELECT COUNT(*) AS c FROM students WHERE risk_level='medium'").fetchone()["c"]
            hc = c.execute("SELECT COUNT(*) AS c FROM students WHERE risk_level='high'").fetchone()["c"]
        chart_header("Risk distribution"); st.bar_chart({"Low": lc, "Medium": mc, "High": hc}, height=130); chart_footer()
    with c2:
        chart_header("Emotion distribution"); st.bar_chart(emotion_sentiment_chart(), height=130); chart_footer()

# ═══════════ ALERTS ═══════════
def _alerts() -> None:
    page_header("Student Alerts", "Monitor and resolve alerts", "🔔")
    info_panel(
        "Alerts are rows in the retention_alerts table: each links to one student with a severity "
        "(e.g. low / medium / high / critical) and a message. In this demo build they are created "
        "from seed data (or could be added by an admin process); the app does not auto-generate them "
        "from attendance. Lecturers review active alerts, add an optional note, and mark them resolved."
    )
    with get_connection() as c:
        active = c.execute("SELECT a.*,s.name,s.student_code FROM retention_alerts a JOIN students s ON s.id=a.student_row_id WHERE a.resolved=0 ORDER BY a.created_at DESC").fetchall()
        resolved = c.execute("SELECT a.*,s.name,s.student_code FROM retention_alerts a JOIN students s ON s.id=a.student_row_id WHERE a.resolved=1 ORDER BY a.created_at DESC").fetchall()
    ac = len(active); hp = sum(1 for r in active if (r["severity"] or "").lower() in ("high", "critical")); rc = len(resolved)
    stat_row([("Active", str(ac), "🔴"), ("High Priority", str(hp), "⚠️"), ("Resolved", str(rc), "✅")])

    if active:
        section("Active", "", "⚠️")
        for r in active:
            st.markdown(alert_card(r["name"], r["student_code"], r["severity"] or "low", r["message"], r.get("created_at", "")), unsafe_allow_html=True)
        card_start("0.5rem 0.7rem")
        c1, c2 = st.columns([2, 1])
        ids = [r["id"] for r in active]
        pk = c1.selectbox("Alert", ids, format_func=lambda i: f"#{i}", key="la_pk")
        nt = c2.text_input("Note", placeholder="Contacted student", key="la_nt")
        if st.button("Resolve →", type="primary", key="la_go"):
            with get_connection() as c: c.execute("UPDATE retention_alerts SET resolved=1, resolution_note=? WHERE id=?", (nt or "Resolved", pk))
            st.success("Resolved."); st.rerun()
        card_end()
    else:
        empty_state("No active alerts.", "🎉")

    if resolved:
        section("Resolved", "", "✅")
        for r in resolved:
            st.markdown(alert_card(r["name"], r["student_code"], r["severity"] or "low", r["message"], r.get("created_at", ""), True, r.get("resolution_note", "")), unsafe_allow_html=True)

# ═══════════ INTERVENTIONS ═══════════
def _interventions(dn: str, email: str) -> None:
    page_header("My Interventions", "Assigned to you", "📋")
    s = email.split("@")[0]
    with get_connection() as c:
        rows = c.execute("SELECT * FROM interventions WHERE lower(assigned_to)=lower(?) OR lower(assigned_to)=lower(?) OR lower(assigned_to)=lower(?) ORDER BY CASE WHEN status='resolved' THEN 1 ELSE 0 END, created_at DESC", (dn, email, s)).fetchall()
    if not rows: empty_state("No interventions assigned.", "✅"); return
    oc = sum(1 for r in rows if r["status"] != "resolved"); rc = sum(1 for r in rows if r["status"] == "resolved")
    stat_row([("Open", str(oc), "🔔"), ("Resolved", str(rc), "✅")], cols=2)
    for r in rows:
        res = r["status"] == "resolved"; sev = (r["severity"] or "low").lower()
        sv = {"critical": "critical", "high": "high", "medium": "medium"}.get(sev, "low")
        lc = {"critical": "#991b1b", "high": DANGER, "medium": WARNING}.get(sev, SUCCESS)
        st.markdown(f"""
<div style="background:{CARD};border:1px solid {BORDER_S};border-left:3px solid {lc};
            border-radius:{RADIUS_SM};padding:0.65rem 0.9rem;margin-bottom:5px;box-shadow:{SHADOW};">
  <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
    <span style="font-weight:700;font-size:0.9rem;color:{TEXT};">{r["student_code"]}</span>
    {badge(sev.title(), sv)} {badge(r["type"], "info")}
    {badge(r["status"].replace("_"," ").title(), "resolved" if res else "open")}
  </div>
  <div style="font-size:0.84rem;color:{TEXT_SEC};margin-bottom:3px;">{r["description"]}</div>
  {"<div style='font-size:0.8rem;color:"+TEXT_DIM+";'>Action: "+(r["action_taken"] or "—")+"</div>" if r.get("action_taken") else ""}
  <div style="font-size:0.8rem;color:{TEXT_DIM};">Assigned: {r["assigned_to"] or "—"}</div>
  <div style="font-size:0.7rem;color:{TEXT_FAINT};margin-top:3px;">{r["created_at"] or ""}</div>
</div>""", unsafe_allow_html=True)
        if not res:
            na = st.text_area("Action taken", value=r["action_taken"] or "", key=f"iv_a_{r['id']}", height=55)
            b1, b2 = st.columns(2)
            with b1:
                if st.button("Save", key=f"iv_s_{r['id']}"):
                    with get_connection() as c: c.execute("UPDATE interventions SET action_taken=? WHERE id=?", (na, r["id"]))
                    st.success("Saved."); st.rerun()
            with b2:
                if st.button("Resolve", key=f"iv_r_{r['id']}", type="primary"):
                    with get_connection() as c: c.execute("UPDATE interventions SET status='resolved', action_taken=? WHERE id=?", (na or r["action_taken"] or "Resolved", r["id"]))
                    st.success("Resolved."); st.rerun()
