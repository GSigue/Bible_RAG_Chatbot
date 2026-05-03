import os
import requests
import streamlit as st


API_URL = os.getenv(
    "API_URL",
    "https://bible-rag-chatbot-anjl.onrender.com/chat",
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
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}

    .stApp {
        background: linear-gradient(180deg, #f8f6f2 0%, #ffffff 100%);
    }

    .block-container {
        padding-top: 1.25rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 780px;
    }

    .hero {
        background: #ffffff;
        border: 1px solid #eee4d4;
        border-radius: 24px;
        padding: 28px 22px;
        box-shadow: 0 10px 28px rgba(31, 60, 136, 0.08);
        margin-bottom: 22px;
        text-align: center;
    }

    .brand-title {
        color: #1f3c88;
        font-size: 42px;
        font-weight: 850;
        margin: 0;
        line-height: 1.15;
    }

    .brand-subtitle {
        color: #555;
        font-size: 17px;
        margin-top: 12px;
        line-height: 1.55;
    }

    .verse-card {
        background: #fffaf0;
        border-left: 5px solid #c9a227;
        padding: 16px 18px;
        border-radius: 16px;
        color: #333;
        font-size: 15.5px;
        line-height: 1.55;
        margin-bottom: 16px;
    }

    .safe-card {
        background: #eef3ff;
        border: 1px solid #dce6ff;
        border-radius: 16px;
        padding: 16px 18px;
        color: #333;
        font-size: 15.5px;
        line-height: 1.55;
        margin-bottom: 18px;
    }

    .prompt-title {
        color: #1f3c88;
        font-weight: 700;
        margin-top: 10px;
        margin-bottom: 8px;
    }

    .question-chip {
        background: #ffffff;
        border: 1px solid #e6dfd2;
        border-radius: 999px;
        padding: 10px 14px;
        margin: 5px 0;
        font-size: 14px;
        color: #333;
        box-shadow: 0 3px 10px rgba(0,0,0,0.03);
    }

    .donation-box {
        text-align: center;
        background: #fffaf0;
        border: 1px solid #eee4d4;
        border-radius: 18px;
        padding: 16px;
        font-size: 15px;
        margin-top: 28px;
    }

    .footer-note {
        text-align: center;
        color: #777;
        font-size: 13px;
        margin-top: 24px;
        line-height: 1.5;
    }

    div[data-testid="stChatMessage"] {
        border-radius: 18px;
        padding: 6px;
    }

    @media (max-width: 600px) {
        .block-container {
            padding-left: 0.8rem;
            padding-right: 0.8rem;
            padding-top: 0.8rem;
        }

        .hero {
            padding: 22px 16px;
            border-radius: 20px;
        }

        .brand-title {
            font-size: 31px;
        }

        .brand-subtitle {
            font-size: 15px;
        }

        .verse-card,
        .safe-card {
            font-size: 14.5px;
            padding: 14px 15px;
        }

        section[data-testid="stSidebar"] {
            display: none;
        }
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
    st.write("Scripture-centered encouragement for everyday life.")

    st.divider()

    st.markdown("### ❤️ Support this ministry")
    st.write("Help make Scripture-based encouragement available to more people.")
    st.markdown(f"[Support with PayPal]({PAYPAL_URL})")

    st.divider()

    st.markdown("### 📧 Stay encouraged")
    st.caption("Email reflections are coming soon.")

    st.divider()

    if st.button("Reset conversation"):
        st.session_state.messages = []
        st.rerun()


st.markdown(
    """
    <div class="hero">
        <h1 class="brand-title">📖 Bible Guidance</h1>
        <p class="brand-subtitle">
            Find comfort, wisdom, and direction from Scripture for everyday life.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <div class="verse-card">
        <strong>✨ Verse for Reflection</strong><br><br>
        “The Lord is close to the brokenhearted and saves those who are crushed in spirit.”
    </div>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <div class="safe-card">
        You’re welcome to share what’s on your heart — whether you’re seeking comfort,
        clarity, wisdom, or encouragement. This space helps you reflect through Scripture.
    </div>
    """,
    unsafe_allow_html=True,
)


st.markdown('<div class="prompt-title">You can ask things like:</div>', unsafe_allow_html=True)

sample_questions = [
    "What does the Bible say about anxiety?",
    "How should I deal with fear?",
    "What should I pray when I feel overwhelmed?",
    "How can I forgive someone who hurt me?",
]

cols = st.columns(2)
for i, question in enumerate(sample_questions):
    with cols[i % 2]:
        st.markdown(f'<div class="question-chip">{question}</div>', unsafe_allow_html=True)


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

            except requests.exceptions.RequestException:
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
    f"""
    <div class="donation-box">
        ❤️ If Bible Guidance encouraged you,
        <a href="{PAYPAL_URL}" target="_blank">support this ministry here</a>.
    </div>
    """,
    unsafe_allow_html=True,
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