"""Streamlit client for the_board's local FastAPI service."""
from __future__ import annotations

import json
import os
from typing import Any, Optional

import requests
import streamlit as st

API_BASE_URL = os.getenv("THE_BOARD_API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="the_board", page_icon="◉", layout="wide")


def api_request(method: str, path: str, **kwargs: Any) -> Optional[requests.Response]:
    try:
        return requests.request(method, f"{API_BASE_URL}{path}", timeout=10, **kwargs)
    except requests.RequestException:
        return None


def fetch_plan(plan_id: str) -> Optional[dict[str, Any]]:
    response = api_request("GET", f"/state/plans/{plan_id}")
    return response.json() if response and response.ok else None


def render_plan(plan: dict[str, Any]) -> None:
    summary = plan["summary"]
    st.subheader(f"Plan {plan['plan']['plan_id']}")
    st.caption(f"Status: {plan['plan']['status']} · {summary['completed_tasks']}/{summary['total_tasks']} tasks complete")
    for task in plan["tasks"]:
        state = task["state"].replace("_", " ").title()
        st.write(f"**{task['agent']}** — {state}")
        st.caption(task["description"])
    result = api_request("GET", f"/plan/{plan['plan']['plan_id']}/result")
    if result and result.ok:
        data = result.json()["plan_data"]
        st.divider()
        st.subheader("Executive plan")
        st.markdown(data["synthesized_strategy"])
        st.caption(f"Confidence: {data['confidence_score']:.0%} · Contributors: {', '.join(data['contributing_agents'])}")
        if data["identified_risks"]:
            st.warning("Risks: " + "; ".join(data["identified_risks"]))
        st.download_button("Download JSON", json.dumps(data, indent=2), "strategic-plan.json", "application/json")


def main() -> None:
    st.title("the_board")
    st.caption("Local strategic planning with an executive board of specialist agents.")
    health = api_request("GET", "/health")
    if not health or not health.ok:
        st.error("The API is unavailable. Start it with `poetry run dev`.")
        return
    with st.form("goal"):
        goal = st.text_area("Strategic goal", placeholder="Launch a new service for a defined customer segment.")
        context = st.text_area("Context (optional)", placeholder="Budget, timeline, constraints, and relevant background.")
        submitted = st.form_submit_button("Create plan")
    if submitted:
        response = api_request("POST", "/plan", json={"high_level_goal": goal, "user_context": context or None})
        if not response or response.status_code != 202:
            st.error("The plan could not be created. Provide a goal with at least three characters.")
        else:
            st.session_state.plan_id = response.json()["plan_id"]
            st.success("Plan created. Refresh to follow progress.")
    plan_id = st.text_input("Plan ID", st.session_state.get("plan_id", ""))
    if plan_id:
        plan = fetch_plan(plan_id)
        if plan:
            render_plan(plan)
        else:
            st.warning("Plan not found.")


if __name__ == "__main__":
    main()
