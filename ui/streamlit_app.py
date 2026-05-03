import os
import requests
import streamlit as st


import os

API_URL = os.getenv(
    "API_URL",
    "https://bible-rag-chatbot-anjl.onrender.com/chat"
)

PAYPAL_URL = "https://www.paypal.com/donate/?hosted_button_id=W2EF8WER9XN8A"


st.set_page_config(
    page_title="Bible Guidance",
    page_icon="📖",
    layout="centered",
)


st.markdown(
    """
    <style>
    .main {
        background-color: #f8f6f2;
    }

    .block-container {
        padding-top: 2rem;
        max-width: 850px;
    }

    .brand-title {
        text-align: center;
        color: #1f3c88;
        font-size: 44px;
        font-weight: 800;
        margin-bottom: 0;
    }

    .brand-subtitle {
        text-align: center;
        color: #555;
        font-size: 18px;
        margin-top: 8px;
        margin-bottom: 24px;
    }

    .reflection-box {
        background-color: #fffaf0;
        border-left: 5px solid #c9a227;
        padding: 16px 20px;
        border-radius: 10px;
        margin-bottom: 24px;
        color: #333;
        font-size: 16px;
    }

    .safe-space {
        background-color: #eef3ff;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 24px;
        color: #333;
    }

    .footer-note {
        text-align: center;
        color: #777;
        font-size: 13px;
        margin-top: 32px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = "default-session"


with st.sidebar:
    st.markdown("## 📖 Bible Guidance")
    st.write("A Scripture-centered companion for everyday questions.")

    st.divider()

    st.markdown("### ❤️ Support this ministry")
    st.write(
        "If this encourages you, consider supporting the work so others can benefit too."
    )
    st.markdown(f"[Donate with PayPal]({PAYPAL_URL})")

    st.divider()

    st.markdown("### 📧 Stay encouraged")
    email = st.text_input("Receive future Scripture reflections")

    if st.button("Join community"):
        if email and "@" in email:
            st.success("Thank you for joining 🙏")
        else:
            st.warning("Please enter a valid email.")

    st.divider()

    if st.button("Reset conversation"):
        st.session_state.messages = []
        st.rerun()


st.markdown(
    """
    <h1 class="brand-title">📖 Bible Guidance</h1>
    <p class="brand-subtitle">
    Find comfort, wisdom, and direction from Scripture for everyday life.
    </p>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <div class="reflection-box">
        <strong>✨ Verse for Reflection</strong><br><br>
        “The Lord is close to the brokenhearted and saves those who are crushed in spirit.”
    </div>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <div class="safe-space">
        You’re welcome to ask anything — whether you're seeking comfort, clarity,
        wisdom, or encouragement. This space is here to help you reflect through Scripture.
    </div>
    """,
    unsafe_allow_html=True,
)


sample_questions = [
    "What does the Bible say about anxiety?",
    "How should I deal with fear?",
    "What should I pray when I feel overwhelmed?",
    "How can I forgive someone who hurt me?",
]

st.markdown("#### You can ask things like:")

cols = st.columns(2)
for i, question in enumerate(sample_questions):
    with cols[i % 2]:
        st.caption(f"• {question}")


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


user_question = st.chat_input("Share what's on your heart...")


if user_question:
    st.session_state.messages.append(
        {"role": "user", "content": user_question}
    )

    with st.chat_message("user"):
        st.markdown(user_question)

    with st.chat_message("assistant"):
        with st.spinner("Searching Scripture and preparing guidance..."):
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
                answer = (
                    "I’m sorry, something went wrong while connecting to Bible Guidance. "
                    "Please try again in a moment."
                )
                sources = []

            st.markdown(answer)

            if sources:
                with st.expander("📚 Scripture passages used"):
                    for source in sources:
                        st.markdown(f"**Passage chunk {source['chunk_id']}**")
                        st.caption(f"Similarity distance: {source['distance']}")
                        st.write(source["preview"])
                        st.divider()

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )


st.markdown(
    """
    <p class="footer-note">
    Bible Guidance offers Scripture-based reflection and encouragement.
    It is not a substitute for pastoral care, counseling, or emergency support.
    </p>
    """,
    unsafe_allow_html=True,
)