"""SSMS — run: streamlit run app.py"""
from __future__ import annotations
import streamlit as st
from branding import ADMIN_LOGIN_EMAIL, PAGE_TITLE, SYSTEM_NAME_SHORT
from catalog import OTHER_OPTION, all_programme_choices
from database import get_connection, init_db
from seed import SEED_PASSWORD_ADMIN, seed_if_empty
from auth_util import verify_password
from registration import register_new_lecturer, register_new_student
from theme import (
    BG, BG2, CARD, SURFACE, PRIMARY, ACCENT, SKY, SUCCESS,
    TEXT, TEXT_SEC, TEXT_DIM, TEXT_FAINT, BORDER_S, RADIUS, RADIUS_SM, SHADOW, SHADOW_MD,
    inject_theme, card_start, card_end, info_panel,
)
from views_student import render_student_portal
from views_lecturer import render_lecturer_portal
from views_admin import render_admin_portal


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, layout="wide",
                       initial_sidebar_state="collapsed")
    inject_theme()
    if "db_ready" not in st.session_state:
        init_db(); seed_if_empty(); st.session_state.db_ready = True
    if "user" not in st.session_state:
        st.session_state.user = None
    if "auth_portal" not in st.session_state:
        st.session_state.auth_portal = None

    root = st.empty()
    if st.session_state.user is None:
        with root.container():
            _login_page()
        return
    with root.container():
        _render_portal(st.session_state.user)


def _render_portal(u: dict) -> None:
    role = str(u["role"]).replace("_", " ").title()
    name = u.get("display_name", u["email"])
    st.markdown(
        f'<div style="background:{CARD};border:1px solid {BORDER_S};border-radius:{RADIUS};'
        f'border-left:3px solid {PRIMARY};padding:0.65rem 1.2rem;margin-bottom:0.65rem;'
        f'display:flex;align-items:center;justify-content:space-between;box-shadow:{SHADOW};">'
        f'<div><span style="font-size:0.95rem;font-weight:650;color:{TEXT};">{SYSTEM_NAME_SHORT}</span>'
        f'<span style="color:{TEXT_DIM};margin:0 10px;">·</span>'
        f'<span style="font-size:0.82rem;color:{TEXT_SEC};font-weight:500;">{role}</span></div>'
        f'<div style="font-size:0.82rem;color:{TEXT_SEC};">Signed in as <b style="color:{TEXT};">{name}</b></div></div>',
        unsafe_allow_html=True,
    )
    _, cr = st.columns([9, 1])
    with cr:
        if st.button("Sign out", key="hdr_logout"):
            st.session_state.user = None; st.rerun()
    if u["role"] == "student":   render_student_portal(u)
    elif u["role"] == "lecturer": render_lecturer_portal(u)
    else:                         render_admin_portal(u)


def _login_page() -> None:
    p = st.session_state.auth_portal
    if p is None:
        _role_landing(); return
    container = st.container()
    with container:
        _, bc, _ = st.columns([0.3, 1.2, 5.5])
        with bc:
            if st.button("← Back", key="back_roles"):
                st.session_state.auth_portal = None; st.rerun()
        {"admin": _admin_panel, "student": _student_panel, "lecturer": _lecturer_panel}[p]()


def _role_landing() -> None:
    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
section[data-testid="stMain"] .block-container {{
  background-image:
    radial-gradient(ellipse 85% 50% at 50% -15%, rgba(59,130,246,0.14), transparent 50%),
    radial-gradient(ellipse 50% 38% at 100% 5%, rgba(56,189,248,0.08), transparent 42%),
    radial-gradient(ellipse 42% 32% at 0% 10%, rgba(34,197,94,0.05), transparent 40%),
    repeating-linear-gradient(0deg, transparent, transparent 22px, rgba(148,163,184,0.028) 22px, rgba(148,163,184,0.028) 23px) !important;
  background-color: {BG} !important;
  padding-top: 0.35rem !important;
  padding-bottom: 0.65rem !important;
  padding-left: 1rem !important;
  padding-right: 1rem !important;
}}
/* Hero copy: Streamlit wraps markdown; force centered block */
section[data-testid="stMain"] .ssms-landing-hero,
section[data-testid="stMain"] .ssms-landing-hero h1,
section[data-testid="stMain"] .ssms-landing-hero p {{
  text-align: center !important;
}}
section[data-testid="stMain"] .ssms-landing-hero p.ssms-landing-sub {{
  margin-left: auto !important;
  margin-right: auto !important;
}}
.ssms-landing-hero {{
  max-width: 640px;
  margin: 0 auto;
  padding: 0.65rem 0.35rem 0.35rem;
  text-align: center !important;
}}
.ssms-landing-eyebrow {{
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 0.6rem;
  font-weight: 600;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: {TEXT_DIM};
  margin-bottom: 0.45rem;
}}
.ssms-landing-title {{
  font-family: 'DM Serif Display', Georgia, serif;
  font-size: clamp(1.45rem, 2.8vw, 1.95rem);
  font-weight: 400 !important;
  line-height: 1.12;
  color: {TEXT};
  margin: 0;
  letter-spacing: -0.03em;
  text-shadow: 0 1px 36px rgba(59,130,246,0.1);
}}
section[data-testid="stMain"] h1.ssms-landing-title {{
  font-weight: 400 !important;
}}
.ssms-landing-sub {{
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  margin: 0.55rem auto 0;
  max-width: 28rem;
  font-size: 0.84rem;
  line-height: 1.5;
  color: {TEXT_SEC};
  font-weight: 450;
  text-align: center !important;
}}
.ssms-landing-rule {{
  width: 56px;
  height: 2px;
  margin: 0.75rem auto 0;
  border-radius: 2px;
  background: linear-gradient(90deg, transparent, {PRIMARY}, {SKY}, transparent);
  opacity: 0.88;
  animation: ssms-pulse-line 3.2s ease-in-out infinite;
}}
@keyframes ssms-pulse-line {{
  0%, 100% {{ opacity: 0.55; }}
  50% {{ opacity: 1; }}
}}
.ssms-landing-section {{
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  margin: 0.65rem auto 0;
  font-size: 0.62rem;
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: {TEXT_FAINT};
}}
.ssms-role-card-wrap > div:first-child {{
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}}
.ssms-role-card-wrap:hover > div:first-child {{
  transform: translateY(-4px);
  box-shadow: 0 16px 40px rgba(0,0,0,0.42), 0 0 0 1px rgba(59,130,246,0.16) !important;
}}
section[data-testid="stMain"] div[data-testid="column"]:has(div[class*="st-key-pk_a"]),
section[data-testid="stMain"] div[data-testid="column"]:has(div[class*="st-key-pk_l"]),
section[data-testid="stMain"] div[data-testid="column"]:has(div[class*="st-key-pk_s"]) {{
  display: flex;
  flex-direction: column;
  align-items: stretch;
}}
section[data-testid="stMain"] div[class*="st-key-pk_a"],
section[data-testid="stMain"] div[class*="st-key-pk_l"],
section[data-testid="stMain"] div[class*="st-key-pk_s"] {{
  margin-top: 0 !important;
  width: 100% !important;
}}
section[data-testid="stMain"] div[class*="st-key-pk_a"] button,
section[data-testid="stMain"] div[class*="st-key-pk_l"] button,
section[data-testid="stMain"] div[class*="st-key-pk_s"] button {{
  width: 100% !important;
  margin-top: -1px !important;
  min-height: 2.15rem !important;
  border-radius: 0 0 12px 12px !important;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
  font-size: 0.7rem !important;
  font-weight: 650 !important;
  letter-spacing: 0.16em !important;
  text-transform: uppercase !important;
  background: {SURFACE} !important;
  color: {ACCENT} !important;
  border: 1px solid rgba(255,255,255,0.07) !important;
  border-top: 1px solid rgba(255,255,255,0.04) !important;
  box-shadow: 0 10px 28px rgba(0,0,0,0.32) !important;
  transition: background 0.18s, color 0.18s, border-color 0.18s !important;
}}
section[data-testid="stMain"] div[class*="st-key-pk_a"] button:hover,
section[data-testid="stMain"] div[class*="st-key-pk_l"] button:hover,
section[data-testid="stMain"] div[class*="st-key-pk_s"] button:hover {{
  background: rgba(59,130,246,0.12) !important;
  color: {TEXT} !important;
  border-color: rgba(59,130,246,0.32) !important;
}}
</style>
""",
        unsafe_allow_html=True,
    )

    _, land_mid, _ = st.columns([0.1, 0.8, 0.1])
    with land_mid:
        st.markdown(
            f"""
<div class="ssms-landing-hero">
  <div style="width:44px;height:44px;margin:0 auto 0.45rem;border-radius:14px;
    background: linear-gradient(135deg, rgba(59,130,246,0.32) 0%, rgba(15,18,26,0.96) 52%);
    border: 1px solid rgba(148,163,184,0.16);
    box-shadow: {SHADOW_MD}, inset 0 1px 0 rgba(255,255,255,0.06);
    display:flex;align-items:center;justify-content:center;">
    <span style="font-family:'Plus Jakarta Sans',sans-serif;font-size:0.95rem;font-weight:800;
      color:{TEXT};letter-spacing:-0.1em;">SS</span>
  </div>
  <p class="ssms-landing-eyebrow">Retention &amp; engagement suite</p>
  <h1 class="ssms-landing-title">{SYSTEM_NAME_SHORT}</h1>

  
  <div class="ssms-landing-rule" aria-hidden="true"></div>
  <p class="ssms-landing-section">Choose your workspace</p>
</div>""",
            unsafe_allow_html=True,
        )

        def _ico_shield(stroke: str) -> str:
            return (
                f'<svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
                f'<path d="M12 3L4 7v5c0 5 3.5 9 8 10 4.5-1 8-5 8-10V7l-8-4z" stroke="{stroke}" stroke-width="1.35" stroke-linejoin="round"/>'
                f'<path d="M9 12l2 2 4-4" stroke="{stroke}" stroke-width="1.35" stroke-linecap="round" stroke-linejoin="round"/></svg>'
            )

        def _ico_chart(stroke: str) -> str:
            return (
                f'<svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
                f'<path d="M4 19h16M6 16V9M10 16V5M14 16v-7M18 16v-3" stroke="{stroke}" stroke-width="1.35" stroke-linecap="round"/>'
                f'<path d="M3 21h18" stroke="{stroke}" stroke-width="1.35" stroke-opacity="0.35"/></svg>'
            )

        def _ico_user(stroke: str) -> str:
            return (
                f'<svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
                f'<path d="M12 11a4 4 0 100-8 4 4 0 000 8z" stroke="{stroke}" stroke-width="1.35"/>'
                f'<path d="M4 20a8 8 0 0116 0" stroke="{stroke}" stroke-width="1.35" stroke-linecap="round"/></svg>'
            )

        def _role_card_html(title: str, desc: str, svg: str, accent: str) -> str:
            sh = "0 8px 32px rgba(0,0,0,0.34), 0 0 0 1px rgba(255,255,255,0.04)"
            return (
                f'<div class="ssms-role-card-wrap" style="margin:0 auto;max-width:100%;">'
                f'<div style="border-radius:12px 12px 0 0;overflow:hidden;box-shadow:{sh};">'
                f'<div style="min-height:128px;box-sizing:border-box;padding:0.85rem 0.95rem 0.75rem;'
                f'background: linear-gradient(180deg, rgba(36,44,60,0.5) 0%, {CARD} 42%);'
                f'border:1px solid rgba(255,255,255,0.07);border-bottom:none;border-top:2px solid {accent};">'
                f'<div style="margin-bottom:0.5rem;">{svg}</div>'
                f'<div style="font-family:\'Plus Jakarta Sans\',system-ui,sans-serif;font-size:0.92rem;font-weight:700;'
                f'color:{TEXT};letter-spacing:-0.02em;">{title}</div>'
                f'<div style="margin-top:0.38rem;font-size:0.72rem;line-height:1.45;color:{TEXT_DIM};font-weight:450;">{desc}</div>'
                f"</div></div></div>"
            )

        roles = [
            ("Administrator", "Govern users, fees, attendance exports, and system-wide policies.", "pk_a", "admin", PRIMARY, _ico_shield(PRIMARY)),
            ("Lecturer", "Schedule sessions, and act on retention alerts.", "pk_l", "lecturer", SKY, _ico_chart(SKY)),
            ("Student", "Check in with face verification, review attendance, and manage fees.", "pk_s", "student", SUCCESS, _ico_user(SUCCESS)),
        ]

        c1, c2, c3 = st.columns(3, gap="small")
        for col, (title, desc, key, portal, accent, svg) in zip([c1, c2, c3], roles):
            with col:
                st.markdown(_role_card_html(title, desc, svg, accent), unsafe_allow_html=True)
                if st.button(
                    "Open workspace",
                    key=key,
                    help=f"Sign in as {title}",
                    use_container_width=True,
                    type="secondary",
                ):
                    st.session_state.auth_portal = portal
                    st.rerun()


def _auth_hdr(title: str, sub: str, icon: str = "") -> None:
    mark = (
        f'<div style="width:40px;height:40px;border-radius:10px;margin:0 auto 0.5rem;'
        f'background:{BG2};border:1px solid {BORDER_S};display:flex;align-items:center;justify-content:center;'
        f'font-size:0.75rem;font-weight:700;color:{PRIMARY};">{icon}</div>'
        if icon
        else ""
    )
    st.markdown(
        f'<div style="text-align:center;padding:0.45rem 0 0.15rem;">{mark}'
        f'<h3 style="margin:0;font-size:1.02rem;font-weight:650;color:{TEXT}!important;">{title}</h3>'
        f'<p style="margin:4px 0 0;color:{TEXT_DIM};font-size:0.8rem;">{sub}</p></div>',
        unsafe_allow_html=True,
    )


def _admin_panel() -> None:
    _, m, _ = st.columns([1.5, 2, 1.5])
    with m:
        card_start("1rem 1.2rem")
        _auth_hdr("Admin sign in", f"{ADMIN_LOGIN_EMAIL}", "AD")
        st.text_input("Email", value=ADMIN_LOGIN_EMAIL, disabled=True, key="adm_e")
        pw = st.text_input("Password", type="password", key="adm_pw")
        if st.button("Sign in →", type="primary", use_container_width=True, key="adm_go"):
            with get_connection() as c:
                r = c.execute("SELECT u.id,u.email,u.password_hash,u.role,u.student_row_id,s.name AS student_name,u.name AS user_name FROM users u LEFT JOIN students s ON s.id=u.student_row_id WHERE lower(u.email)=lower(?) AND u.role='admin'", (ADMIN_LOGIN_EMAIL,)).fetchone()
            if not r: st.error("No admin account.")
            elif not verify_password(pw, r["password_hash"]): st.error(f"Wrong password. Demo: **`{SEED_PASSWORD_ADMIN}`**")
            else: _set_user(r)
        card_end()

def _student_panel() -> None:
    _, m, _ = st.columns([1.5, 2, 1.5])
    with m:
        card_start("1rem 1.2rem")
        _auth_hdr("Student portal", "Sign in or register", "ST")
        t1, t2 = st.tabs(["Sign in", "Register"])
        with t1:
            _sign_in("student")
        with t2:
            info_panel("Use your institutional email and a password of at least six characters.")
            _reg_student()
        card_end()

def _lecturer_panel() -> None:
    _, m, _ = st.columns([1.5, 2, 1.5])
    with m:
        card_start("1rem 1.2rem")
        _auth_hdr("Lecturer portal", "Sign in or request access", "LC")
        t1, t2 = st.tabs(["Sign in", "Register"])
        with t1:
            _sign_in("lecturer")
        with t2:
            info_panel("Administrator approval is required before you can sign in as a lecturer.")
            _reg_lecturer()
        card_end()

def _sign_in(role: str) -> None:
    e = st.text_input("Email", placeholder="name@university.esu", key=f"in_e_{role}")
    p = st.text_input("Password", type="password", key=f"in_p_{role}")
    if st.button("Sign in →", type="primary", use_container_width=True, key=f"in_g_{role}"):
        with get_connection() as c:
            pend = c.execute("SELECT u.id,u.password_hash FROM users u WHERE lower(u.email)=lower(?) AND u.role='lecturer' AND IFNULL(u.approved,1)=0", (e.strip(),)).fetchone()
        if role == "lecturer" and pend and verify_password(p, pend["password_hash"]):
            st.warning("Awaiting admin approval."); return
        with get_connection() as c:
            r = c.execute("SELECT u.id,u.email,u.password_hash,u.role,u.student_row_id,s.name AS student_name,u.name AS user_name FROM users u LEFT JOIN students s ON s.id=u.student_row_id WHERE lower(u.email)=lower(?) AND u.role=? AND (u.role!='lecturer' OR IFNULL(u.approved,1)=1)", (e.strip(), role)).fetchone()
        if not r or not verify_password(p, r["password_hash"]): st.error("Invalid credentials.")
        else: _set_user(r)

def _set_user(r) -> None:
    d = r["student_name"] or r["user_name"] or r["email"].split("@")[0]
    st.session_state.user = {"id": r["id"], "email": r["email"], "role": r["role"],
                              "student_row_id": r["student_row_id"], "display_name": d}
    st.session_state.auth_portal = None
    st.rerun()

def _reg_student() -> None:
    with st.form("reg_stu"):
        c1, c2 = st.columns(2)
        nm = c1.text_input("Full name", key="rs_n"); sc = c2.text_input("Student ID", key="rs_c")
        em = st.text_input("Email", key="rs_e"); pw = st.text_input("Password (min 6)", type="password", key="rs_p")
        pl = all_programme_choices(); pr = st.selectbox("Programme", pl, key="rs_pr")
        op = ""
        if pr == OTHER_OPTION: op = st.text_input("Specify", key="rs_o")
        yr = st.number_input("Year", 1, 8, 1, key="rs_y")
        sub = st.form_submit_button("Create account", type="primary")
    if sub:
        cf = op.strip() if pr == OTHER_OPTION else pr
        if pr == OTHER_OPTION and not cf: st.error("Enter programme."); return
        ok, msg = register_new_student(name=nm, student_code=sc, email=em, password=pw, course=cf, year=int(yr))
        (st.success if ok else st.error)(msg)

def _reg_lecturer() -> None:
    with st.form("reg_lec"):
        nm = st.text_input("Full name", key="rl_n"); em = st.text_input("Email", key="rl_e")
        pw = st.text_input("Password (min 6)", type="password", key="rl_p")
        sub = st.form_submit_button("Submit request", type="primary")
    if sub:
        ok, msg = register_new_lecturer(name=nm, email=em, password=pw)
        (st.success if ok else st.error)(msg)

main()
