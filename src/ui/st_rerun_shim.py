# Streamlit rerun compatibility shim
import streamlit as st


def rerun() -> None:
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.rerun()

    else:
        raise RuntimeError("No rerun method found in streamlit API")
