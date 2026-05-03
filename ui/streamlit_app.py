import requests
import streamlit as st


import os

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/chat")


st.set_page_config(
    page_title="Bible RAG Chatbot",
    page_icon="📖",
    layout="centered",
)


if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = "default-session"


st.sidebar.title("Session")
st.sidebar.write("Session ID:", st.session_state.session_id)

if st.sidebar.button("Reset Chat"):
    st.session_state.messages = []


st.title("📖 Bible RAG Chatbot")
st.write("Ask Bible-grounded questions about everyday life.")


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


user_question = st.chat_input("Ask a Bible question...")


if user_question:
    st.session_state.messages.append(
        {"role": "user", "content": user_question}
    )

    with st.chat_message("user"):
        st.markdown(user_question)

    with st.chat_message("assistant"):
        with st.spinner("Searching Scripture and preparing an answer..."):
            try:
                response = requests.post(
                    API_URL,
                    json={
                        "question": user_question,
                        "session_id": st.session_state.session_id,
                    },
                    timeout=90,
                )

                response.raise_for_status()

                data = response.json()
                answer = data["answer"]
                sources = data.get("sources", [])

            except requests.exceptions.RequestException as e:
                answer = f"Error connecting to API: {e}"
                sources = []

            st.markdown(answer)

            if sources:
                with st.expander("📚 Sources"):
                    for source in sources:
                        st.write(f"Chunk {source['chunk_id']}")
                        st.write(f"Distance: {source['distance']}")
                        st.write(source["preview"])
                        st.write("---")

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )