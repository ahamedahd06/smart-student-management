"""Admin portal — compact professional layout with tight analytics."""
from __future__ import annotations
import streamlit as st
from analytics_util import emotion_sentiment_chart, module_programme_attendance_chart, weekly_checkin_trend
from auth_util import hash_password
from catalog import OTHER_OPTION, all_programme_choices
from database import get_connection
from registration import approve_lecturer, list_pending_lecturers, reject_lecturer
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

CUR = "LKR"
_AV = ["#6366f1", "#ec4899", "#14b8a6", "#f59e0b", "#ef4444", "#8b5cf6", "#0ea5e9"]

def render_admin_portal(user: dict) -> None:
    t1, t2, t3, t4, t5, t6 = st.tabs(["Students", "Lecturers", "Attendance", "Analytics", "Alerts & Interventions", "Fees"])
    with t1: _students()
    with t2: _lecturers()
    with t3: _attendance()
    with t4: _analytics()
    with t5: _interventions()
    with t6: _fees()

# ═══════════ STUDENTS ═══════════
def _students() -> None:
    page_header("Student Management", "CRUD operations on student records", "👥")
    with st.expander("➕ Add Student", expanded=False):
        c1, c2 = st.columns(2); code = c1.text_input("Student ID *", key="ns_c"); name = c2.text_input("Full Name *", key="ns_n")
        c3, c4 = st.columns(2); email = c3.text_input("Email *", key="ns_e")
        pl = all_programme_choices(); prog = c4.selectbox("Course *", pl, key="ns_p")
        op = ""
        if prog == OTHER_OPTION: op = st.text_input("Specify course", key="ns_o")
        cv = op.strip() if prog == OTHER_OPTION else prog
        c5, c6 = st.columns(2); yr = c5.number_input("Year *", 1, 8, 1, key="ns_y"); stat = c6.selectbox("Status *", ["active", "inactive"], key="ns_s")
        cl = st.checkbox("Create login", value=True); ipw = ""
        if cl: ipw = st.text_input("Password (min 6)", type="password", key="ns_pw")
        if st.button("Create Student", type="primary", key="ns_go"):
            if not (code and name and email): st.error("Fill required fields."); return
            if prog == OTHER_OPTION and not cv: st.error("Specify course."); return
            if cl and len(ipw) < 6: st.error("Min 6 chars."); return
            with get_connection() as c:
                c.execute("INSERT INTO students (student_code,name,email,course,year,status) VALUES (?,?,?,?,?,?)", (code.upper(), name, email.lower(), cv, int(yr), stat))
                if cl:
                    sid = c.execute("SELECT id FROM students WHERE student_code=?", (code.upper(),)).fetchone()["id"]
                    c.execute("INSERT INTO users (email,password_hash,role,student_row_id,approved,name) VALUES (?,?,?,?,1,?)", (email.lower(), hash_password(ipw), "student", sid, name))
            st.success("Student created."); st.rerun()

    with get_connection() as c:
        rows = c.execute("SELECT * FROM students ORDER BY student_code").fetchall()
    if not rows: empty_state("No students.", "👥"); return
    t = len(rows); ac = sum(1 for r in rows if (r["status"] or "active").lower() == "active"); ia = t - ac
    stat_row([("Total", str(t), "👥"), ("Active", str(ac), "✅"), ("Inactive", str(ia), "⏸")])

    q = st.text_input("🔍 Search...", key="as", label_visibility="collapsed", placeholder="Search students...")
    filtered = [r for r in rows if q.lower() in (r["name"] or "").lower() or q.lower() in (r["student_code"] or "").lower() or q.lower() in (r["email"] or "").lower()] if q else rows

    for i, r in enumerate(filtered):
        att = int(r["attendance_rate"] or 0)
        rk = (r["risk_level"] or "low").lower()
        rk_b = badge(f"{rk.title()}", rk if rk in ("low", "medium", "high") else "default")
        status_b = badge((r["status"] or "active").title(), "active" if (r["status"] or "").lower() == "active" else "inactive")
        st.markdown(f"""
<div style="background:{CARD};border:1px solid {BORDER_S};border-radius:{RADIUS_SM};
            padding:0.55rem 0.9rem;margin-bottom:4px;box-shadow:{SHADOW};
            display:grid;grid-template-columns:65px 1.2fr 0.8fr 95px 70px 70px;gap:8px;align-items:center;font-size:0.84rem;">
  <div style="font-weight:600;color:{TEXT_DIM};">{r["student_code"]}</div>
  <div>
    <div style="font-weight:600;color:{TEXT};">{r["name"]}</div>
    <div style="font-size:0.72rem;color:{TEXT_FAINT};">{r["email"] or ""}</div>
  </div>
  <div style="font-size:0.8rem;color:{TEXT_SEC};">{r["course"] or ""} · Yr {r["year"] or "—"}</div>
  <div>{progress_bar(att)}</div>
  <div style="text-align:center;">{status_b}</div>
  <div style="text-align:center;">{rk_b}</div>
</div>""", unsafe_allow_html=True)

# ═══════════ LECTURERS ═══════════
def _lecturers() -> None:
    page_header("Lecturer Approvals", "Manage registration requests", "📋")
    with get_connection() as c: pend = list_pending_lecturers(c)
    if not pend: empty_state("No pending approvals.", "✅"); return
    info_panel(f"<b>{len(pend)}</b> lecturers awaiting approval.", "⏳")
    for i, r in enumerate(pend):
        cl = _AV[i % len(_AV)]; ini = "".join(w[0].upper() for w in (r["name"] or "?").split()[:2])
        st.markdown(f"""
<div style="background:{CARD};border:1px solid {BORDER_S};border-radius:{RADIUS_SM};
            padding:0.6rem 0.9rem;margin-bottom:4px;display:flex;align-items:center;gap:10px;box-shadow:{SHADOW};">
  <div style="width:34px;height:34px;border-radius:50%;background:{cl};display:flex;align-items:center;
              justify-content:center;color:white;font-weight:700;font-size:0.75rem;">{ini}</div>
  <div style="flex:1;">
    <div style="font-weight:600;font-size:0.9rem;color:{TEXT};">{r["name"] or "?"}</div>
    <div style="font-size:0.76rem;color:{TEXT_DIM};">{r["email"]}</div>
  </div>
</div>""", unsafe_allow_html=True)
        b1, b2, _ = st.columns([1, 1, 4])
        with b1:
            if st.button("✓ Approve", key=f"ap_{r['id']}", type="primary"): approve_lecturer(int(r["id"])); st.success("Approved."); st.rerun()
        with b2:
            if st.button("✗ Reject", key=f"rj_{r['id']}"): reject_lecturer(int(r["id"])); st.info("Rejected."); st.rerun()

# ═══════════ ATTENDANCE ═══════════
def _attendance() -> None:
    page_header("Attendance Records", "View and export data", "📊")
    c1, c2 = st.columns([3, 1])
    mod = c1.text_input("🔍 Filter...", "", key="att_q", label_visibility="collapsed", placeholder="Filter by module...")
    rows: list = []
    with c2:
        with get_connection() as c:
            rows = c.execute("SELECT a.*,s.name,s.student_code FROM attendance_records a JOIN students s ON s.id=a.student_row_id WHERE a.module_code LIKE ? ORDER BY a.check_in_time DESC", (f"%{mod.strip() or '%'}%",)).fetchall()
        if rows:
            st.download_button("📥 Export", data=_csv(rows), file_name="attendance.csv", mime="text/csv")
    if not rows: empty_state("No attendance records.", "📋"); return
    t = len(rows); p = sum(1 for r in rows if (r["status"] or "").lower() == "present")
    ab = sum(1 for r in rows if (r["status"] or "").lower() == "absent"); la = t - p - ab
    stat_row([("Rate", f"{p/t*100:.0f}%" if t else "—", "📈"), ("Present", str(p), "✅"), ("Absent", str(ab), "❌"), ("Late", str(la), "⏰")])
    st.dataframe([{"Date": (r["check_in_time"] or "")[:10], "Student": f"{r['student_code']} — {r['name']}",
                   "Module": r["module_code"], "Session": r["session_label"],
                   "Time": (r["check_in_time"] or "")[11:16], "Status": (r["status"] or "").title(),
                   "Emotion": (r["emotion"] or "").title()}
                  for r in rows], use_container_width=True, hide_index=True)

def _csv(rows) -> str:
    if not rows: return ""
    k = rows[0].keys(); lines = [",".join(k)]
    for r in rows: lines.append(",".join(str(r[x]) for x in k))
    return "\n".join(lines)

# ═══════════ ANALYTICS — compact grid ═══════════
def _analytics() -> None:
    page_header("System Analytics", "Comprehensive overview", "📊")
    with get_connection() as c:
        t = c.execute("SELECT COUNT(*) AS c FROM students").fetchone()["c"]
        a = c.execute("SELECT AVG(attendance_rate) AS a FROM students").fetchone()["a"] or 0
        hr = c.execute("SELECT COUNT(*) AS c FROM students WHERE risk_level='high'").fetchone()["c"]
        ts = c.execute("SELECT COUNT(*) AS c FROM class_sessions").fetchone()["c"]
    stat_row([("Students", str(t), "👥"), ("Avg Attendance", f"{float(a):.0f}%", "📈"), ("At Risk", str(hr), "⚠️"), ("Modules", str(ts), "📚")])

    c1, c2 = st.columns(2)
    with c1:
        chart_header("Programme attendance (avg %)")
        st.bar_chart(module_programme_attendance_chart(5), height=140)
        chart_footer()
    with c2:
        chart_header("Weekly trends")
        st.line_chart(weekly_checkin_trend(5), height=140)
        chart_footer()

    c3, c4 = st.columns(2)
    with c3:
        chart_header("Risk Distribution")
        with get_connection() as c:
            lc = c.execute("SELECT COUNT(*) AS c FROM students WHERE IFNULL(risk_level,'low')='low'").fetchone()["c"]
            mc = c.execute("SELECT COUNT(*) AS c FROM students WHERE risk_level='medium'").fetchone()["c"]
            hc = c.execute("SELECT COUNT(*) AS c FROM students WHERE risk_level='high'").fetchone()["c"]
        st.bar_chart({"Low": lc, "Medium": mc, "High": hc}, height=120)
        chart_footer()
    with c4:
        chart_header("Emotion distribution")
        st.bar_chart(emotion_sentiment_chart(), height=120)
        chart_footer()

# ═══════════ INTERVENTIONS ═══════════
def _interventions() -> None:
    page_header("Alerts & Interventions", "Manage student support", "🔔")
    with st.expander("➕ Create Intervention", expanded=False):
        c1, c2 = st.columns(2)
        sid = c1.text_input("Student ID *", key="iv_s", placeholder="e.g. S001")
        typ = c2.selectbox("Type *", ["Attendance", "Emotional", "Academic", "Other"], key="iv_t")
        c3, c4 = st.columns(2)
        sev = c3.selectbox("Severity *", ["low", "medium", "high", "critical"], key="iv_sv")
        who = c4.text_input("Assigned To *", key="iv_w", placeholder="e.g. Dr. Sarah Johnson")
        desc = st.text_area("Description *", key="iv_d", placeholder="Describe the issue...", height=60)
        act = st.text_area("Action Taken *", key="iv_a", placeholder="Intervention taken...", height=60)
        if st.button("Create", type="primary", key="iv_go"):
            with get_connection() as c: c.execute("INSERT INTO interventions (student_code,type,severity,description,action_taken,assigned_to,status) VALUES (?,?,?,?,?,?,?)", (sid.upper(), typ, sev, desc, act, who, "in_progress"))
            st.success("Created."); st.rerun()

    with get_connection() as c: rows = c.execute("SELECT * FROM interventions ORDER BY created_at DESC").fetchall()
    if not rows: empty_state("No interventions.", "📝"); return
    oc = sum(1 for r in rows if r["status"] != "resolved")
    cr = sum(1 for r in rows if (r["severity"] or "").lower() == "critical")
    rc = sum(1 for r in rows if r["status"] == "resolved")
    stat_row([("Open", str(oc), "🔔"), ("Critical", str(cr), "🔴"), ("Resolved", str(rc), "✅")])

    for r in rows:
        res = r["status"] == "resolved"; sev = (r["severity"] or "low").lower()
        sv = {"critical": "critical", "high": "high", "medium": "medium"}.get(sev, "low")
        lc = {"critical": "#991b1b", "high": DANGER, "medium": WARNING}.get(sev, SUCCESS)
        outcome = ""
        if res and r.get("action_taken"):
            outcome = (f'<div style="background:rgba(16,185,129,0.06);border:1px solid rgba(16,185,129,0.12);'
                       f'border-radius:6px;padding:0.4rem 0.6rem;margin-top:4px;">'
                       f'<div style="font-size:0.7rem;font-weight:700;color:{SUCCESS};">Outcome:</div>'
                       f'<div style="font-size:0.8rem;color:{TEXT_SEC};">{r["action_taken"]}</div></div>')
        st.markdown(f"""
<div style="background:{CARD};border:1px solid {BORDER_S};border-left:3px solid {lc};
            border-radius:{RADIUS_SM};padding:0.65rem 0.9rem;margin-bottom:5px;box-shadow:{SHADOW};">
  <div style="display:flex;align-items:center;gap:6px;margin-bottom:3px;">
    <span style="font-weight:700;font-size:0.9rem;color:{TEXT};">{r["student_code"]}</span>
    {badge(sev.title(), sv)} {badge(r["type"], "info")}
    {badge(r["status"].replace("_"," ").title(), "resolved" if res else "open")}
  </div>
  <div style="font-size:0.84rem;color:{TEXT_SEC};">{r["description"][:200]}</div>
  {"<div style='font-size:0.8rem;color:"+TEXT_DIM+";margin-top:3px;'>Action: "+(r["action_taken"] or "—")+"</div>" if not res and r.get("action_taken") else ""}
  <div style="font-size:0.8rem;color:{TEXT_DIM};margin-top:2px;">Assigned: {r["assigned_to"] or "—"}</div>
  {outcome}
  <div style="font-size:0.7rem;color:{TEXT_FAINT};margin-top:3px;">{r["created_at"] or ""}</div>
</div>""", unsafe_allow_html=True)

# ═══════════ FEES ═══════════
def _fees() -> None:
    page_header("Fee Management", "Student fees and payments", "💰")
    ca, cb = st.columns(2)
    with ca:
        with st.expander("➕ Add to student", expanded=False):
            with get_connection() as c: stu = c.execute("SELECT id,student_code,name FROM students ORDER BY student_code").fetchall()
            if not stu: st.info("No students."); return
            opts = {f"{s['student_code']} — {s['name']}": s["id"] for s in stu}
            pk = st.selectbox("Student", list(opts.keys()), key="f_s"); sid = opts[pk]
            desc = st.text_input("Description", placeholder="e.g. Tuition Fee", key="f_d")
            amt = st.number_input(f"Amount ({CUR})", min_value=0.01, step=0.01, value=100.00, key="f_a")
            due = st.date_input("Due date", key="f_du")
            if st.button("Add Fee →", type="primary", key="f_go"):
                if not desc: st.error("Required."); return
                with get_connection() as c: c.execute("INSERT INTO fee_items (student_row_id,description,amount,due_date) VALUES (?,?,?,?)", (sid, desc, amt, str(due)))
                st.success(f"{CUR} {amt:,.2f} added."); st.rerun()
    with cb:
        with st.expander("➕ Add to ALL students", expanded=False):
            da = st.text_input("Description", placeholder="e.g. Library Fee", key="fa_d")
            aa = st.number_input(f"Amount ({CUR})", min_value=0.01, step=0.01, value=75.00, key="fa_a")
            dd = st.date_input("Due date", key="fa_du")
            if st.button("Add to All →", type="primary", key="fa_go"):
                if not da: st.error("Required."); return
                with get_connection() as c:
                    al = c.execute("SELECT id FROM students").fetchall()
                    for s in al: c.execute("INSERT INTO fee_items (student_row_id,description,amount,due_date) VALUES (?,?,?,?)", (s["id"], da, aa, str(dd)))
                st.success(f"Added to {len(al)} students."); st.rerun()

    with get_connection() as c:
        rows = c.execute("SELECT s.student_code,s.name,IFNULL(SUM(f.amount),0) AS tf,IFNULL(SUM(p.paid),0) AS tp FROM students s LEFT JOIN fee_items f ON f.student_row_id=s.id LEFT JOIN (SELECT fee_item_id,SUM(amount) AS paid FROM payments GROUP BY fee_item_id) p ON p.fee_item_id=f.id GROUP BY s.id ORDER BY s.student_code").fetchall()
    if not rows: empty_state("No fee data.", "💰"); return
    tf = sum(float(r["tf"]) for r in rows); tp = sum(float(r["tp"]) for r in rows); tb = tf - tp
    stat_row([("Total Fees", f"{CUR} {tf:,.0f}", "💰"), ("Collected", f"{CUR} {tp:,.0f}", "✅"), ("Outstanding", f"{CUR} {tb:,.0f}", "⏳")])
    for i, r in enumerate(rows):
        bal = float(r["tf"]) - float(r["tp"]); paid = bal <= 0
        rv = f"{CUR} {bal:,.2f}" if not paid else "Fully Paid"
        st.markdown(student_card(r["name"], f'{r["student_code"]} · Total: {CUR} {float(r["tf"]):,.2f}',
                                  "Active" if paid else "Inactive", rv, "Outstanding" if not paid else "", i),
                    unsafe_allow_html=True)
