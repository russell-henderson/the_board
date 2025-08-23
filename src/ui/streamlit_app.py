# src/ui/streamlit_app.py
from __future__ import annotations

import json
import os
from textwrap import dedent
from typing import Dict, List

import streamlit as st

# -----------------------------------------------------------------------------
# Page config & global CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="the_board",
    page_icon="🎯",
    layout="wide",
)


def inject_base_css() -> None:
    """Base styles for cards and metrics."""
    st.markdown(
        dedent("""
        <style>
          .hero {
            background: linear-gradient(90deg, #6d76e7 0%, #7141B8 100%);
            border-radius: 14px;
            padding: 28px 24px;
            color: white;
            margin: 0.5rem 0 1.5rem 0;
          }
          .metric-card {
            border-radius: 14px;
            padding: 16px 18px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
          }
          .metric-value { font-size: 1.6rem; font-weight: 800; color: #e5e7eb; }
          .metric-label { font-size: 0.9rem; color: #cbd5e1; }
          .status-card {
            border-radius: 12px; padding: 12px 14px; margin: 8px 0;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            color: #e5e7eb;
          }
          .status-green { box-shadow: inset 0 0 0 1px rgba(16,185,129,.25); }
          .status-amber { box-shadow: inset 0 0 0 1px rgba(245,158,11,.25); }
          .status-gray  { box-shadow: inset 0 0 0 1px rgba(148,163,184,.25); }
          .section-title { font-size: 1.25rem; font-weight: 700; color: #e5e7eb; margin: 0.5rem 0; }
        </style>
        """),
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# LED indicator strip (OFF/ON)
# -----------------------------------------------------------------------------
def inject_led_css() -> None:
    """One-time CSS injection for the LED indicators."""
    if st.session_state.get("_led_css_injected"):
        return
    st.markdown(
        dedent("""
        <style>
          .led-wrap { display:flex; gap:2rem; justify-content:center; margin: 0.75rem 0 1.25rem 0; }
          .led-item { text-align:center; }
          .led {
            width: 32px; height: 32px; border-radius: 50%;
            background: #1f2937; /* OFF base */
            box-shadow: inset 0 0 6px rgba(0,0,0,.6);
            transition: background .2s ease, box-shadow .2s ease, transform .12s ease;
            margin: 0 auto .4rem auto;
          }
          .led.on { transform: translateY(-1px); }
          /* ON glow colors */
          .led.ceo.on { background:#7c3aed; box-shadow: 0 0 12px #7c3aed, inset 0 0 6px rgba(0,0,0,.35); }
          .led.cto.on { background:#2563eb; box-shadow: 0 0 12px #2563eb, inset 0 0 6px rgba(0,0,0,.35); }
          .led.coo.on { background:#10b981; box-shadow: 0 0 12px #10b981, inset 0 0 6px rgba(0,0,0,.35); }
          .led.cfo.on { background:#facc15; box-shadow: 0 0 12px #facc15, inset 0 0 6px rgba(0,0,0,.35); }
          .led.cmo.on { background:#ec4899; box-shadow: 0 0 12px #ec4899, inset 0 0 6px rgba(0,0,0,.35); }
          /* OFF tints (darker variants) */
          .led.ceo.off { background:#4c1d95; }
          .led.cto.off { background:#1e3a8a; }
          .led.coo.off { background:#065f46; }
          .led.cfo.off { background:#92400e; }
          .led.cmo.off { background:#831843; }
          .led-label { font-size: .85rem; color: #cbd5e1; }
        </style>
        """),
        unsafe_allow_html=True,
    )
    st.session_state["_led_css_injected"] = True


def render_agent_leds(active: Dict[str, bool]) -> None:
    """Render the 5 indicator LEDs with ON/OFF states."""

    def led(role: str, label: str, on: bool) -> str:
        state = "on" if on else "off"
        return dedent(f"""
        <div class="led-item">
          <div class="led {role} {state}"></div>
          <span class="led-label">{label}</span>
        </div>
        """).strip()

    html = dedent(f"""
    <div class="led-wrap">
      {led("ceo", "CEO", active.get("ceo", False))}
      {led("cto", "CTO", active.get("cto", False))}
      {led("coo", "COO", active.get("coo", False))}
      {led("cfo", "CFO", active.get("cfo", False))}
      {led("cmo", "CMO", active.get("cmo", False))}
    </div>
    """)
    st.markdown(html, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Safe HTML builders
# -----------------------------------------------------------------------------
def metric_card_html(value: str, label: str) -> str:
    return dedent(f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """).strip()


def status_card_html(goal: str, plan_id: str, created: str, status: str) -> str:
    color = "status-gray"
    if status.lower() in {"completed", "success"}:
        color = "status-green"
    elif status.lower() in {"in_progress", "running"}:
        color = "status-amber"
    # Use &bull; to avoid non-ASCII bullet errors in Python source
    return dedent(f"""
    <div class="status-card {color}">
      <strong>{goal}</strong><br/>
      <small>ID: {plan_id} &bull; {created} &bull; {status.title()}</small>
    </div>
    """).strip()


# -----------------------------------------------------------------------------
# Main sections
# -----------------------------------------------------------------------------
def show_dashboard() -> None:
    inject_base_css()
    inject_led_css()

    # Hero
    st.markdown(
        dedent("""
        <div class="hero">
          <div style="font-size:2.1rem; font-weight:800; margin-bottom:6px;">🎯 the_board</div>
          <div style="font-size:1.05rem; font-weight:600;">Multi-Agent Strategic Intelligence Platform</div>
          <div style="opacity:.95; margin-top:4px;">Transform your high-level goals into actionable, multi-faceted strategies</div>
        </div>
        """),
        unsafe_allow_html=True,
    )

    # LED strip (Section A)
    st.markdown(
        '<div class="section-title">Agent Activity</div>', unsafe_allow_html=True
    )

    # Demo toggles so you can test glow behavior now; later wire to WS events
    active = st.session_state.get(
        "agent_leds",
        {"ceo": False, "cto": False, "coo": False, "cfo": False, "cmo": False},
    )
    with st.expander("LED demo toggles", expanded=False):
        c = st.columns(5)
        for i, key in enumerate(["ceo", "cto", "coo", "cfo", "cmo"]):
            active[key] = c[i].toggle(key.upper(), value=active[key])
        st.session_state["agent_leds"] = active
    render_agent_leds(active)

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(metric_card_html("5", "Active Agents"), unsafe_allow_html=True)
    with col2:
        st.markdown(metric_card_html("12", "Plans Created"), unsafe_allow_html=True)
    with col3:
        st.markdown(metric_card_html("89%", "Success Rate"), unsafe_allow_html=True)
    with col4:
        st.markdown(metric_card_html("2.4s", "Avg Response"), unsafe_allow_html=True)

    st.divider()

    # Recent Activity (mock data; replace with API response later)
    st.markdown(
        '<div class="section-title">Recent Activity</div>', unsafe_allow_html=True
    )
    recent: List[Dict[str, str]] = [
        {
            "goal": "Launch SaaS product",
            "id": "plan_001",
            "created": "2 hours ago",
            "status": "completed",
        },
        {
            "goal": "Market expansion strategy",
            "id": "plan_002",
            "created": "4 hours ago",
            "status": "in_progress",
        },
        {
            "goal": "Team restructuring",
            "id": "plan_003",
            "created": "6 hours ago",
            "status": "pending",
        },
    ]
    for p in recent:
        st.markdown(
            status_card_html(p["goal"], p["id"], p["created"], p["status"]),
            unsafe_allow_html=True,
        )


def show_submit_goal() -> None:
    inject_base_css()
    st.markdown(
        '<div class="section-title">Submit Strategic Goal</div>', unsafe_allow_html=True
    )
    goal = st.text_area(
        "Strategic Goal",
        height=120,
        placeholder="Describe your high-level strategic goal…",
    )
    context = st.text_area(
        "Additional Context",
        height=120,
        placeholder="Provide any relevant context, constraints, or background information…",
    )
    category = st.selectbox(
        "Category",
        [
            "General",
            "Market Strategy",
            "Go-To-Market",
            "Operations",
            "Technical",
            "Finance",
        ],
        index=0,
    )

    colA, colB = st.columns([1, 3])
    with colA:
        if st.button("Submit for Analysis", use_container_width=True):
            # NOTE: Wire this to your FastAPI /plan endpoint. The 422 you saw earlier
            # is fixed here by including 'goal_category'.
            payload = {
                "high_level_goal": goal,
                "user_context": context,
                "goal_category": category,
            }
            st.session_state["last_submitted_goal"] = payload
            st.success("Goal queued for analysis (mock). Wire to /plan to activate.")
    with colB:
        st.caption("Payload preview")
        st.code(
            json.dumps(st.session_state.get("last_submitted_goal", {}), indent=2),
            language="json",
        )


def show_direct_chat() -> None:
    """Section B – direct chat to all agents (broadcast style)."""
    inject_base_css()
    st.markdown(
        '<div class="section-title">Direct Chat — All Agents</div>',
        unsafe_allow_html=True,
    )

    import requests

    api_url = os.environ.get("BOARD_API_URL", "http://localhost:8000")

    # Fetch chat log from backend
    try:
        resp = requests.get(f"{api_url}/chat/log?limit=50", timeout=5)
        chat_log = resp.json() if resp.status_code == 200 else []
    except requests.RequestException:
        chat_log = []

    msg = st.text_input("Message", placeholder="Type a message to the board…")
    if st.button("Send"):
        if msg.strip():
            try:
                requests.post(
                    f"{api_url}/chat",
                    json={"sender": "You", "message": msg.strip()},
                    timeout=5,
                )
            except requests.RequestException:
                st.error("Failed to send message to backend.")
            try:
                from src.ui.st_rerun_shim import rerun
            except ImportError:
                pass
            rerun()
        else:
            st.info("Please enter a message.")

    # Render chat log
    for entry in reversed(chat_log):
        st.markdown(f"**{entry['sender']}:** {entry['message']}")


# -----------------------------------------------------------------------------
# Navigation
# -----------------------------------------------------------------------------
PAGES = {
    "Dashboard": show_dashboard,
    "Submit Goal": show_submit_goal,
    "Direct Chat": show_direct_chat,  # <- this is the “B” section you wanted
}


def main() -> None:
    st.sidebar.success("API Connected")  # mock; replace with real health check
    page = st.sidebar.selectbox("Choose a section:", list(PAGES.keys()))
    PAGES[page]()


if __name__ == "__main__":
    main()
