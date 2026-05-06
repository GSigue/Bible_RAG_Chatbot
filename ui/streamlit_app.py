import datetime
import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000/chat"
# For production later, use:
# API_URL = "https://bible-rag-chatbot-anjl.onrender.com/chat"

PAYPAL_URL = "https://www.paypal.com/donate/?hosted_button_id=W2EF8WER9XN8A"


st.set_page_config(
    page_title="Bible Guidance",
    page_icon="📖",
    layout="centered",
)


st.markdown(
    """
    <style>
    header {display: none !important;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}

    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stHeader"] {
        display: none !important;
    }

    .stApp {
        background: #ffffff;
    }

    .block-container {
        padding-top: 0.35rem;
        padding-left: 0.8rem;
        padding-right: 0.8rem;
        max-width: 740px;
    }

    .hero {
        text-align: center;
        padding: 4px 4px 6px 4px;
        margin-bottom: 6px;
    }

    .brand-title {
        color: #1f3c88;
        font-size: 30px;
        font-weight: 800;
        margin: 0;
        line-height: 1.15;
    }

    .brand-subtitle {
        color: #555;
        font-size: 14px;
        margin-top: 6px;
        line-height: 1.4;
    }

    .daily-box {
        background: #fff7e6;
        border: 1px solid #f0dfbd;
        border-radius: 14px;
        padding: 14px;
        margin-bottom: 16px;
    }

    .prompt-title {
        color: #1f3c88;
        font-weight: 700;
        margin-top: 8px;
        margin-bottom: 8px;
        font-size: 15px;
    }

    .donation-box {
        text-align: center;
        background: #fffaf0;
        border: 1px solid #eee4d4;
        border-radius: 14px;
        padding: 14px;
        font-size: 14px;
        margin-top: 20px;
    }

    .footer-note {
        text-align: center;
        color: #777;
        font-size: 12px;
        margin-top: 18px;
        line-height: 1.45;
    }

    button[kind="secondary"] {
        border-radius: 999px !important;
    }

    @media (max-width: 600px) {
        .block-container {
            padding-left: 0.65rem;
            padding-right: 0.65rem;
            padding-top: 0.15rem;
        }

        .brand-title {
            font-size: 26px;
        }

        .brand-subtitle {
            font-size: 13px;
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


def call_api(question: str) -> dict:
    response = requests.post(
        API_URL,
        json={
            "question": question,
            "session_id": st.session_state.session_id,
        },
        timeout=90,
    )
    response.raise_for_status()
    return response.json()


def render_answer(question: str) -> None:
    st.session_state.messages.append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Finding guidance for you..."):
            try:
                data = call_api(question)
                answer = data["answer"]
                sources = data.get("sources", [])

            except requests.exceptions.RequestException:
                answer = (
                    "I’m sorry, something went wrong while connecting to Bible Guidance. "
                    "Please try again in a moment."
                )
                sources = []

            st.markdown(answer)

            if st.button("⭐ Save this", key=f"save_{len(st.session_state.messages)}"):
                st.success("Saved feature coming soon.")

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
            Get Bible-based guidance for anxiety, fear, relationships, and life decisions.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <div class="trust-line">
        Grounded in Scripture • Private • No judgment
    </div>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
Feeling overwhelmed, anxious, or lost?

You're not alone — ask anything and receive Scripture-based guidance.
"""
)

chat_input = st.chat_input("What are you going through?")


today = datetime.date.today().strftime("%B %d")

st.markdown('<div class="daily-box">', unsafe_allow_html=True)

with st.expander(f"🌅 Daily Encouragement ({today})"):
    st.markdown("✨ A short word for today:")

    if st.button("Get today's encouragement", use_container_width=True):
        with st.spinner("Finding encouragement for you..."):
            daily_prompt = "Give me a short encouraging Bible verse and explanation for today."

            try:
                data = call_api(daily_prompt)
                st.markdown(data["answer"])
            except requests.exceptions.RequestException:
                st.warning("Unable to load today's encouragement. Please try again later.")

st.markdown('</div>', unsafe_allow_html=True)


st.markdown('<div class="prompt-title">Start here:</div>', unsafe_allow_html=True)

button_question = None

col1, col2 = st.columns(2)

with col1:
    if st.button("I feel anxious", use_container_width=True):
        button_question = "I feel anxious about my life. What does the Bible say?"

with col2:
    if st.button("I feel afraid", use_container_width=True):
        button_question = "I am afraid. What does the Bible say about fear?"

col3, col4 = st.columns(2)

with col3:
    if st.button("I feel lost", use_container_width=True):
        button_question = "I feel lost in life. What guidance does the Bible give?"

with col4:
    if st.button("I’m struggling to forgive", use_container_width=True):
        button_question = "I am struggling to forgive someone who hurt me. What does the Bible say?"


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


user_question = button_question or chat_input

if user_question:
    print("User question:", user_question)
    render_answer(user_question)


if st.session_state.messages:
    st.markdown("Would you like:")

    col1, col2, col3 = st.columns(3)

    followup_question = None

    with col1:
        if st.button("🙏 A prayer", use_container_width=True):
            followup_question = "Give me a short prayer for this situation."

    with col2:
        if st.button("📖 More verses", use_container_width=True):
            followup_question = "Give me more Bible verses about this situation."

    with col3:
        if st.button("➡️ Next step", use_container_width=True):
            followup_question = "What is one practical step I should take?"

    if followup_question:
        print("Follow-up question:", followup_question)
        render_answer(followup_question)


st.markdown("---")

st.markdown(
    f'❤️ <a href="{PAYPAL_URL}" target="_blank">Support this ministry</a>',
    unsafe_allow_html=True
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


st.markdown(
    """
---
🙏 Come back anytime you need guidance or encouragement.
"""
)