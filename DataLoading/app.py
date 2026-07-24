import streamlit as st
from FinalAgentBoot import FinalAgentBoot


# -------------------- Page Config --------------------
st.set_page_config(
    page_title="AI Customer Support",
    page_icon="🤖",
    layout="wide"
)

# -------------------- Session State --------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------- Sidebar --------------------
with st.sidebar:

    st.title("⚙️ Settings")

    st.divider()

    # New Chat
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    # Clear Chat
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    # Model Selection
    model = st.selectbox(
        "🤖 Select Model",
        [
            "Gemma",
            "Llama",
            "Qwen"
        ]
    )

    # Temperature
    temperature = st.slider(
        "🌡️ Temperature",
        0.0,
        1.0,
        0.7,
        0.1
    )

    st.divider()

    # Theme
    theme = st.radio(
        "🎨 Theme",
        [
            "Light",
            "Dark"
        ]
    )

    st.divider()

    # Chat Statistics
    total_messages = len(st.session_state.messages)

    user_messages = len(
        [m for m in st.session_state.messages if m["role"] == "user"]
    )

    ai_messages = len(
        [m for m in st.session_state.messages if m["role"] == "assistant"]
    )

    st.subheader("📊 Statistics")

    st.metric("Total Messages", total_messages)
    st.metric("User Messages", user_messages)
    st.metric("AI Messages", ai_messages)

    st.divider()

    st.info(
        """
        **AI Customer Support**

        Saurabh Upadhyay  Build a Amazon Style Chat Boot \
        For AI Customer Support.🚚
       
        
        
        Powered by:
        - LangChain
        - Streamlit
        - SQLite
        - RAG
        - GENAI
        """
    )

# -------------------- Main Page --------------------
st.title("🤖 AI Customer Support Assistant")

st.caption("i am a AI boot build by saurabh upadhyay" \
" Ask anything about your orders, returns, refunds, or products.")

# -------------------- Display Chat --------------------
for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -------------------- Chat Input --------------------
prompt = st.chat_input("Type your message...")

if prompt:

    # User Message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    # AI Response
    if "agent" not in st.session_state:
     st.session_state.agent = FinalAgentBoot()



    with st.spinner("Thinking..."):
        answer = st.session_state.agent.customer_support_agent(prompt)

    

    with st.chat_message("assistant"):
        st.markdown(answer)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )