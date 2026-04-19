"""Student portal — compact professional layout."""
from __future__ import annotations
import sqlite3
from datetime import datetime
import streamlit as st
from database import get_connection
from emotion_infer import predict_emotion_full
from theme import (
    PRIMARY, ACCENT, PRIMARY_MUTED,
    TEXT, TEXT_SEC, TEXT_DIM, TEXT_FAINT,
    CARD, BORDER_S, RADIUS, RADIUS_SM, SHADOW,
    SUCCESS, WARNING, DANGER, DANGER_MUTED, SUCCESS_MUTED,
    CLR_GREEN, CLR_AMBER, CLR_RED,
    page_header, section, stat_row, badge, progress_bar, alert_card,
    card_start, card_end, empty_state,
)

CUR = "LKR"

def render_student_portal(user: dict) -> None:
    t1, t2, t3, t4, t5 = st.tabs(["Check-In", "My Attendance", "My Emotion Logs", "My Risk & Alerts", "Payments"])
    with t1: _check_in(user)
    with t2: _attendance(user)
    with t3: _emotions(user)
    with t4: _risk(user)
    with t5: _fees(user)

def _stu(c: sqlite3.Connection, u: dict):
    return c.execute("SELECT * FROM students WHERE id=?", (u["student_row_id"],)).fetchone()

# ═══════════ CHECK-IN ═══════════
def _check_in(user: dict) -> None:
    with get_connection() as c:
        sess = c.execute("SELECT * FROM class_sessions ORDER BY session_date DESC, session_time DESC").fetchall()
        stu = _stu(c, user)
    if not stu: st.error("Profile not linked."); return
    if not sess:
        empty_state("No sessions scheduled yet.")
        return

    page_header("Facial check-in", "Verify attendance with the camera below")
    def _sess_label(r) -> str:
        mod = (r["module_name"] or r["module_code"] or "Module").strip()
        return f"{mod} — {r['session_name']} ({r['session_date']})"

    opts = {_sess_label(r): r for r in sess}
    ch = st.selectbox("Module", list(opts.keys()), label_visibility="collapsed")
    row = opts[ch]

    left, right = st.columns([1.5, 1], gap="small")
    with left:
        card_start("0.5rem 0.7rem")
        img = st.camera_input("Capture your face", label_visibility="collapsed")
        card_end()
        if img is not None:
            data = img.getvalue()
            er = predict_emotion_full(data)
            _render_checkin_emotion_result(er, stu, row)
    with right:
        card_start("0.5rem 0.7rem")
        st.markdown(
            f"""
<div style="font-size:0.72rem;font-weight:650;color:{TEXT_SEC};text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">Pipeline</div>
<div style="font-size:0.8rem;color:{TEXT_SEC};line-height:1.75;">
  After you capture a frame, <b style="color:{TEXT};">results appear under the camera</b> on the left.<br><br>
  Face detect → crop → 48×48 greyscale → model → confidence
</div>
<div style="border-top:1px solid {BORDER_S};margin-top:12px;padding-top:12px;">
  <div style="font-size:0.72rem;font-weight:650;color:{TEXT_SEC};text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Tips</div>
  <div style="font-size:0.78rem;color:{TEXT_DIM};line-height:1.65;">
    Face the camera straight on, arm’s length, even lighting. In dim rooms you can enable <code style="color:{ACCENT};">SSMS_FACE_CLAHE=1</code>.
  </div>
</div>""",
            unsafe_allow_html=True,
        )
        card_end()


def _render_checkin_emotion_result(er: dict, stu, row) -> None:
    """Show emotion / errors directly under the camera (was below the column row — easy to miss)."""
    if not er["ok"] or er["emotion"] == "no_face":
        st.markdown(
            f'<div style="background:{DANGER_MUTED};border:1px solid rgba(239,68,68,0.28);border-left:3px solid {DANGER};'
            f'border-radius:{RADIUS_SM};padding:0.85rem 1rem;margin:0.45rem 0;box-shadow:{SHADOW};">'
            f'<div style="font-size:0.72rem;font-weight:650;color:{DANGER};text-transform:uppercase;letter-spacing:0.06em;">No face detected</div>'
            f'<div style="font-size:0.88rem;font-weight:600;color:{TEXT};margin-top:4px;">Adjust framing or lighting</div>'
            f'<div style="font-size:0.8rem;color:{TEXT_SEC};margin-top:4px;line-height:1.45;">Ensure your face is visible, centred, and evenly lit.</div></div>',
            unsafe_allow_html=True,
        )
        return

    emotion = er["emotion"]
    conf = float(er["confidence"])
    bbox = er.get("bbox")
    bbox_txt = f"({bbox[0]},{bbox[1]})→({bbox[0]+bbox[2]},{bbox[1]+bbox[3]})" if bbox else "—"
    ei = {"happy": "😊", "sad": "😢", "angry": "😠", "neutral": "😐", "surprise": "😲", "fear": "😨", "disgust": "🤢"}.get(
        emotion, "😐"
    )
    mode = "TensorFlow CNN (4-class)" if er.get("tf_model") else "Fallback heuristic"
    warn = er.get("note") or ""
    prob_rows = ""
    probs = er.get("probs") or {}
    if probs and len(probs) > 1:
        for name in sorted(probs.keys(), key=lambda k: -probs[k])[:4]:
            p = probs[name]
            pct = min(100.0, max(0.0, p * 100.0))
            prob_rows += (
                f'<div style="margin-top:6px;"><span style="color:{TEXT_DIM};font-size:0.72rem;">{name.title()}</span>'
                f'<div style="background:rgba(148,163,184,0.12);border-radius:4px;height:6px;margin-top:3px;">'
                f'<div style="width:{pct:.1f}%;height:6px;background:{PRIMARY};border-radius:4px;opacity:0.9;"></div></div></div>'
            )

    st.success(f"{emotion.title()} — {conf:.0%} confidence ({mode})")
    # Single-line / no indented continuations: Streamlit markdown treats indented lines as code blocks (white box of raw HTML).
    warn_html = (
        f'<div style="font-size:0.72rem;color:{WARNING};margin-top:8px;line-height:1.4;">{warn}</div>' if warn else ""
    )
    prob_html = f'<div style="margin-top:10px;">{prob_rows}</div>' if prob_rows else ""
    card_html = (
        f'<div style="background:{SUCCESS_MUTED};border:1px solid rgba(34,197,94,0.28);border-left:3px solid {SUCCESS};'
        f'border-radius:{RADIUS_SM};padding:0.9rem 1rem;margin:0.45rem 0;box-shadow:{SHADOW};">'
        f'<div style="font-size:0.72rem;font-weight:650;color:{SUCCESS};text-transform:uppercase;letter-spacing:0.06em;">'
        f'Verified · {mode}</div>'
        f'<div style="font-size:1rem;font-weight:700;color:{TEXT};margin-top:6px;">{stu["student_code"]} — {stu["name"]}</div>'
        f'<div style="display:flex;flex-wrap:wrap;gap:10px 14px;margin-top:8px;font-size:0.8rem;color:{TEXT_SEC};">'
        f'<span style="color:{SUCCESS};font-weight:600;">Present</span>'
        f'<span>{ei} <b style="color:{TEXT};">{emotion.title()}</b> ({conf:.0%})</span>'
        f'<span style="color:{TEXT_DIM};">Region {bbox_txt}</span>'
        f"</div>{warn_html}{prob_html}</div>"
    )
    st.markdown(card_html, unsafe_allow_html=True)
    if st.button("Confirm and save attendance", type="primary", key="ck_go", use_container_width=True):
        now = datetime.now().isoformat(timespec="seconds")
        with get_connection() as c:
            c.execute(
                "INSERT INTO attendance_records (student_row_id,session_id,module_code,session_label,check_in_time,status,emotion,emotion_confidence) VALUES (?,?,?,?,?,?,?,?)",
                (stu["id"], row["id"], row["module_code"], row["session_name"], now, "present", emotion, conf),
            )
            c.execute(
                "INSERT INTO emotion_logs (student_row_id,logged_at,context,emotion,confidence) VALUES (?,?,?,?,?)",
                (stu["id"], now, f"{row['module_code']} – {row['session_name']}", emotion, conf),
            )
        st.success("Attendance recorded!")
        st.rerun()

# ═══════════ ATTENDANCE ═══════════
def _attendance(user: dict) -> None:
    page_header("My attendance", "Signed-in sessions and status")
    with get_connection() as c:
        stu = _stu(c, user)
        if not stu: return
        rows = c.execute("SELECT a.*,cs.session_date,cs.module_name FROM attendance_records a LEFT JOIN class_sessions cs ON cs.id=a.session_id WHERE a.student_row_id=? ORDER BY a.check_in_time DESC", (stu["id"],)).fetchall()
    n = len(rows); p = sum(1 for r in rows if r["status"] == "present")
    ab = n - p; rate = f"{p/n*100:.0f}%" if n else "—"
    stat_row([("Rate", rate, "📈"), ("Present", str(p), "✅"), ("Absent", str(ab), "❌"), ("Total", str(n), "📋")])
    if not rows:
        empty_state("No attendance records yet.")
        return
    st.dataframe([{"Date": (r["check_in_time"] or "")[:10], "Module": r["module_code"],
                   "Session": r["session_label"], "Time": (r["check_in_time"] or "")[11:16],
                   "Status": (r["status"] or "").title(), "Emotion": (r["emotion"] or "").title()}
                  for r in rows], use_container_width=True, hide_index=True)

# ═══════════ EMOTION LOGS ═══════════
def _emotions(user: dict) -> None:
    page_header("Emotion logs", "States captured at check-in")
    with get_connection() as c:
        stu = _stu(c, user)
        if not stu: return
        rows = c.execute("SELECT * FROM emotion_logs WHERE student_row_id=? ORDER BY logged_at DESC", (stu["id"],)).fetchall()
    if not rows:
        empty_state("No emotion logs yet.")
        return
    counts: dict[str, int] = {}
    for r in rows:
        e = (r["emotion"] or "neutral").lower(); counts[e] = counts.get(e, 0) + 1
    ico = {"happy": "😊", "sad": "😢", "angry": "😠", "neutral": "😐", "surprise": "😲", "focused": "🎯"}
    parts = " ".join(f'<span style="margin-right:12px;font-size:0.85rem;color:{TEXT_SEC};">'
                     f'{ico.get(e,"😐")} <b style="color:{TEXT};">{cn}</b> {e}</span>'
                     for e, cn in sorted(counts.items(), key=lambda x: -x[1]))
    st.markdown(f'<div style="background:{CARD};border:1px solid {BORDER_S};border-radius:{RADIUS_SM};'
                f'padding:0.55rem 0.9rem;margin-bottom:0.4rem;">{parts}</div>', unsafe_allow_html=True)

    em_colors = {"happy": SUCCESS, "sad": WARNING, "angry": DANGER, "neutral": PRIMARY, "surprise": ACCENT}
    for r in rows:
        em = (r["emotion"] or "neutral").lower(); ei = ico.get(em, "😐")
        lc = em_colors.get(em, PRIMARY)
        cp = f"{(r['confidence'] or 0)*100:.0f}%"
        vr = {"happy": "success", "sad": "warning", "angry": "danger"}.get(em, "info")
        st.markdown(f'<div style="background:{CARD};border:1px solid {BORDER_S};border-left:3px solid {lc};'
                    f'border-radius:{RADIUS_SM};padding:0.55rem 0.9rem;margin-bottom:4px;'
                    f'display:flex;align-items:center;gap:10px;box-shadow:{SHADOW};">'
                    f'<span style="font-size:1.1rem;">{ei}</span>'
                    f'<div style="flex:1;min-width:0;">'
                    f'<div style="font-weight:600;font-size:0.88rem;color:{TEXT};">{em.title()} {badge(cp, vr)}</div>'
                    f'<div style="font-size:0.76rem;color:{TEXT_DIM};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{r["context"] or ""}</div></div>'
                    f'<div style="font-size:0.72rem;color:{TEXT_FAINT};white-space:nowrap;">{r["logged_at"] or ""}</div></div>',
                    unsafe_allow_html=True)

# ═══════════ RISK & ALERTS ═══════════
def _risk(user: dict) -> None:
    page_header("Risk and alerts", "Attendance-linked wellbeing signals")
    with get_connection() as c:
        stu = _stu(c, user)
        if not stu: return
        att = int(stu["attendance_rate"] or 0); rk = stu["risk_level"] or "low"
        sc = max(0, min(100, 100 - att + (30 if rk == "high" else 0)))
    stat_row([("Risk Score", str(sc), "🎯"), ("Level", rk.title(), "⚠️"), ("Attendance", f"{att}%", "📊")])
    st.markdown(progress_bar(att), unsafe_allow_html=True)
    with get_connection() as c:
        alerts = c.execute("SELECT * FROM retention_alerts WHERE student_row_id=? ORDER BY created_at DESC", (stu["id"],)).fetchall()
    if not alerts:
        empty_state("No active alerts — you are on track.")
        return
    section("Active alerts")
    for a in alerts:
        sv = (a["severity"] or "low").lower(); resolved = bool(a.get("resolved", 0))
        st.markdown(alert_card(stu["name"], stu["student_code"], sv, a["message"],
                               a.get("created_at", ""), resolved, a.get("resolution_note", "")), unsafe_allow_html=True)

# ═══════════ FEES ═══════════
def _fees(user: dict) -> None:
    page_header("Payments", "Fees, balance, and history")
    with get_connection() as c:
        stu = _stu(c, user)
        if not stu: st.error("Not linked."); return
        fees = c.execute("SELECT f.*,IFNULL(p.paid,0) AS paid FROM fee_items f LEFT JOIN (SELECT fee_item_id,SUM(amount) AS paid FROM payments GROUP BY fee_item_id) p ON p.fee_item_id=f.id WHERE f.student_row_id=? ORDER BY f.due_date", (stu["id"],)).fetchall()
        pays = c.execute("SELECT p.*,f.description AS fee_desc FROM payments p LEFT JOIN fee_items f ON f.id=p.fee_item_id WHERE p.student_row_id=? ORDER BY p.paid_at DESC", (stu["id"],)).fetchall()
    if not fees:
        empty_state("No fee items assigned.")
        return
    td = sum(float(f["amount"]) for f in fees); tp = sum(float(f["paid"]) for f in fees); bal = td - tp

    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        bal_border = DANGER if bal > 0 else SUCCESS
        bal_bg = DANGER_MUTED if bal > 0 else SUCCESS_MUTED
        st.markdown(
            f'<div style="background:{bal_bg};border:1px solid {BORDER_S};border-left:3px solid {bal_border};'
            f'border-radius:{RADIUS_SM};padding:0.75rem;text-align:center;box-shadow:{SHADOW};">'
            f'<div style="font-size:0.7rem;color:{TEXT_DIM};font-weight:650;text-transform:uppercase;letter-spacing:0.06em;">Balance</div>'
            f'<div style="font-size:1.2rem;font-weight:750;color:{TEXT};margin-top:4px;">{CUR} {bal:,.2f}</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(f'<div style="background:{CARD};border:1px solid {BORDER_S};border-radius:{RADIUS_SM};padding:0.7rem;text-align:center;">'
                    f'<div style="font-size:0.72rem;color:{TEXT_DIM};font-weight:600;">Paid</div>'
                    f'<div style="font-size:1.25rem;font-weight:800;color:{CLR_GREEN};">{CUR} {tp:,.2f}</div></div>',
                    unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div style="background:{CARD};border:1px solid {BORDER_S};border-radius:{RADIUS_SM};padding:0.7rem;text-align:center;">'
                    f'<div style="font-size:0.72rem;color:{TEXT_DIM};font-weight:600;">Total Due</div>'
                    f'<div style="font-size:1.25rem;font-weight:800;color:{CLR_AMBER};">{CUR} {td:,.2f}</div></div>',
                    unsafe_allow_html=True)

    unpaid = [(f["id"], f["description"], float(f["amount"]), float(f["paid"]), f["due_date"]) for f in fees if float(f["amount"]) - float(f["paid"]) > 0]
    if unpaid:
        section("Outstanding")
        for fid, desc, amt, pa, due in unpaid:
            rem = amt - pa
            st.markdown(f'<div style="background:{CARD};border:1px solid {BORDER_S};border-radius:{RADIUS_SM};'
                        f'padding:0.55rem 0.9rem;margin-bottom:4px;display:flex;align-items:center;'
                        f'justify-content:space-between;box-shadow:{SHADOW};">'
                        f'<div><div style="font-weight:600;font-size:0.88rem;color:{TEXT};">{desc}</div>'
                        f'<div style="font-size:0.75rem;color:{TEXT_DIM};">Due: {due}</div></div>'
                        f'<div style="font-weight:800;font-size:1rem;color:{CLR_RED};">{CUR} {rem:,.2f}</div></div>',
                        unsafe_allow_html=True)

    paid_items = [f for f in fees if float(f["amount"]) - float(f["paid"]) <= 0]
    if paid_items:
        section("Paid")
        for f in paid_items:
            st.markdown(f'<div style="background:rgba(16,185,129,0.06);border:1px solid rgba(16,185,129,0.12);'
                        f'border-radius:{RADIUS_SM};padding:0.5rem 0.8rem;margin-bottom:4px;display:flex;'
                        f'justify-content:space-between;align-items:center;">'
                        f'<span style="color:{SUCCESS};font-weight:600;font-size:0.86rem;">{f["description"]}</span>'
                        f'<span style="color:{SUCCESS};font-weight:700;font-size:0.86rem;">{CUR} {float(f["amount"]):,.2f}</span></div>',
                        unsafe_allow_html=True)

    if unpaid:
        section("Make payment")
        card_start("0.7rem 0.9rem")
        options = {f"{d} ({CUR} {a-p:,.2f})": (fid, a-p) for fid, d, a, p, _ in unpaid}
        ch = st.selectbox("Select Fee", list(options.keys()), key="pay_sel"); fid, mx = options[ch]
        amt = st.number_input(f"Amount ({CUR})", min_value=0.01, max_value=mx, value=mx, step=0.01, key="pay_a")
        met = st.selectbox("Method", ["Credit / Debit Card", "Bank Transfer", "Cash Deposit"], key="pay_m")
        if met == "Credit / Debit Card":
            card_num = st.text_input("Card Number", placeholder="4242 4242 4242 4242", key="pay_card", max_chars=19)
            cc1, cc2, cc3 = st.columns(3)
            cc1.text_input("Expiry", placeholder="12/27", key="pay_exp", max_chars=5)
            cc2.text_input("CVV", placeholder="123", key="pay_cvv", type="password", max_chars=4)
            cc3.text_input("Name", placeholder="A. M. Ahamed", key="pay_cname")
            ref_str = f"Card ending {card_num[-4:]}" if len(card_num) >= 4 else "Card"
        elif met == "Bank Transfer":
            st.markdown(f'<div style="background:{PRIMARY_MUTED};border:1px solid rgba(59,130,246,0.22);'
                        f'border-radius:{RADIUS_SM};padding:0.55rem 0.85rem;margin:0.35rem 0;font-size:0.82rem;color:{TEXT_SEC};line-height:1.65;">'
                        f'<b style="color:{TEXT};">Bank:</b> People\'s Bank — Colombo Fort<br>'
                        f'<b style="color:{TEXT};">Acc:</b> 123-456789-001 · SSMS University Fund<br>'
                        f'<b style="color:{TEXT};">Ref:</b> {stu["student_code"]}</div>', unsafe_allow_html=True)
            ref_str = st.text_input("Transfer Reference", key="pay_ref_bt")
        else:
            ref_str = st.text_input("Cash Receipt No.", key="pay_ref_cash")
        if st.button("Process payment", type="primary", key="pay_go", use_container_width=True):
            method_label = met.split(" / ")[0] if "/" in met else met
            with get_connection() as c:
                c.execute("INSERT INTO payments (student_row_id,fee_item_id,amount,method,reference) VALUES (?,?,?,?,?)",
                          (stu["id"], fid, amt, method_label, ref_str or None))
            st.success(f"{CUR} {amt:,.2f} via {method_label} processed!"); st.rerun()
        card_end()

    if pays:
        section("Payment history", f"{len(pays)} transactions")
        st.dataframe([{"Date": (r["paid_at"] or "")[:16], "Fee": r["fee_desc"] or "—",
                       "Amount": f"{CUR} {r['amount']:,.2f}", "Method": r["method"] or "—"}
                      for r in pays], use_container_width=True, hide_index=True)
