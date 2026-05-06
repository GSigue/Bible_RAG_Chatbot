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
        padding: 8px 6px 10px 6px;
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

    .trust-line {
        text-align: center;
        color: #777;
        font-size: 12.5px;
        margin-bottom: 14px;
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


chat_input = st.chat_input("What are you going through?")

user_question = button_question or chat_input


def call_api(question: str):
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


if user_question:
    print("User question:", user_question)

    st.session_state.messages.append(
        {"role": "user", "content": user_question}
    )

    with st.chat_message("user"):
        st.markdown(user_question)

    with st.chat_message("assistant"):
        with st.spinner("Finding guidance for you..."):
            try:
                data = call_api(user_question)
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

        st.session_state.messages.append(
            {"role": "user", "content": followup_question}
        )

        with st.chat_message("user"):
            st.markdown(followup_question)

        with st.chat_message("assistant"):
            with st.spinner("Finding guidance for you..."):
                try:
                    data = call_api(followup_question)
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
        ❤️ If Bible Guidance helped you,
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