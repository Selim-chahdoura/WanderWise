import sys
from pathlib import Path

import streamlit as st

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.rag.rag import answer_question


st.title("WanderWise")
st.write("Your AI travel assistant")


# Keep the latest answer in Streamlit session
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
            st.session_state.answer = answer_question(question)
            st.session_state.question = question
            st.session_state.feedback = None


# Display answer
if st.session_state.answer:
    st.write("### Answer")
    st.write(st.session_state.answer)

    st.write("Was this answer helpful?")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("👍"):
            st.session_state.feedback = 1

    with col2:
        if st.button("👎"):
            st.session_state.feedback = -1

    if st.session_state.feedback == 1:
        st.success("Thanks for your feedback!")

    elif st.session_state.feedback == -1:
        st.info("Thanks for your feedback!")