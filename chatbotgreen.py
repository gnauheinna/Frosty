import streamlit as st

# Define the CSS styles
css = """
<style>
    /* Header */
    .header {
        background-color: #197A56;
        padding: 10px;
        display: flex;
        align-items: center;
    }
    .header-logo {
        width: 50px;
        margin-right: 10px;
    }
    .header-title {
        font-family: 'Henderson Sans Bold', sans-serif;
        color: #FFFFFF;
        font-size: 24px;
    }

    /* Chat Window */
    .chat-window {
        background: linear-gradient(0deg, rgba(25,122,86,1) 0%, rgba(34,193,195,1) 100%);
        padding: 20px;
        border-radius: 10px;
        max-height: 400px;
        overflow-y: auto;
    }
    .chat-bubble {
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        max-width: 60%;
    }
    .user-bubble {
        background-color: #000000;
        color: #FFFFFF;
        margin-left: auto;
    }
    .bot-bubble {
        background-color: #197A56;
        color: #FFFFFF;
    }

    /* Input Field */
    .input-field {
        border: 1px solid #197A56;
        padding: 10px;
        border-radius: 5px;
        width: calc(100% - 22px);  /* Adjust the width to account for padding */
    }
    .input-field:hover {
        border-color: #0e3e1b;
    }

    /* Sidebar/Menu */
    .sidebar {
        background-color: #323232;
        padding: 20px;
    }
    .menu-item {
        color: #197A56;
        padding: 10px;
    }
    .menu-item:hover {
        color: #0e3e1b;
    }
    .menu-item-active {
        background-color: #323232;
        color: #197A56;
    }

    /* Buttons */
    .button-primary {
        background-color: #197A56;
        color: #FFFFFF;
        border: none;
        padding: 10px;
        border-radius: 5px;
        cursor: pointer;
    }
    .button-primary:hover {
        background-color: #0e3e1b;
    }
    .button-primary:active {
        background-color: #323232;
    }
    .button-secondary {
        border: 1px solid #197A56;
        color: #197A56;
        padding: 10px;
        border-radius: 5px;
        cursor: pointer;
    }
    .button-secondary:hover {
        border-color: #0e3e1b;
        color: #0e3e1b;
    }
    .button-secondary:active {
        background-color: #323232;
        color: #FFFFFF;
    }

    /* Disabled State */
    .disabled {
        color: #B1b1b1;
    }
</style>
"""

# Inject the CSS styles
st.markdown(css, unsafe_allow_html=True)

# HTML for the header
st.markdown("""
<div class="header">
    <img src="/Users/anniehuang/Desktop/llm-chatbot/BCGLogo.png" class="header-logo">
    <h1 class="header-title">Frosty</h1>
</div>
""", unsafe_allow_html=True)

# HTML for the chat window
st.markdown("""
<div class="chat-window" id="chat-window">
    <div class="chat-bubble user-bubble">Hi</div>
    <div class="chat-bubble bot-bubble">Hello! How can I assist you today?</div>
</div>
""", unsafe_allow_html=True)

# Input field
user_input = st.text_input("Your message", "", key="input", placeholder="Type your message here...", help="Enter your message and press Enter.", max_chars=200)

# Add user's message to chat window
if user_input:
    st.markdown(f'<div class="chat-bubble user-bubble">{user_input}</div>', unsafe_allow_html=True)
    # Optionally, you can add bot response dynamically here
