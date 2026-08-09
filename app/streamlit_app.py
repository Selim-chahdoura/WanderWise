import sys
from pathlib import Path

import streamlit as st

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.rag.rag import answer_question_with_trace
from src.monitoring.interactions import (
    ensure_interactions_table,
    save_interaction,
    update_feedback,
)

st.title("WanderWise")
st.write("Your AI travel assistant")


if "monitoring_initialized" not in st.session_state:
    ensure_interactions_table()
    st.session_state.monitoring_initialized = True

if "interaction_id" not in st.session_state:
    st.session_state.interaction_id = None

if "answer" not in st.session_state:
    st.session_state.answer = None

if "question" not in st.session_state:
    st.session_state.question = None

if "feedback" not in st.session_state:
    st.session_state.feedback = None


question = st.text_input(
    "Ask a travel question",
    placeholder="What are the best things to do in Marrakech?",
)


if st.button("Ask"):
    if question:
        with st.spinner("Searching for the best answer..."):
            result = answer_question_with_trace(question)
            st.session_state.answer = result["answer"]
            st.session_state.question = question
            st.session_state.feedback = None

            st.session_state.interaction_id = save_interaction(
                question,
                result,
            )


# Display answer
if st.session_state.answer:
    st.write("### Answer")
    st.write(st.session_state.answer)

    st.write("Was this answer helpful?")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("👍"):
            update_feedback(
                st.session_state.interaction_id,
                1,
            )
            st.session_state.feedback = 1

    with col2:
        if st.button("👎"):
            update_feedback(
                st.session_state.interaction_id,
                -1,
            )
            st.session_state.feedback = -1
        
