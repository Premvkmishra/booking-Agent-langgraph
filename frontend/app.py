import streamlit as st
import requests
import time

st.set_page_config(page_title="Appointment Scheduler", page_icon="📅", layout="centered")

# --- WhatsApp-like Dark Theme CSS ---
st.markdown('''
    <style>
    body { background: #111b21 !important; }
    .main, .block-container { background: #111b21 !important; }
    .wa-header, .wa-chat-container { max-width: 420px; margin-left: auto; margin-right: auto; }
    .wa-chat-container {
        background: #222e35;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.10);
        min-height: 0;
        display: flex;
        flex-direction: column;
        padding: 0 0 12px 0;
    }
    .wa-header {
        background: #075e54;
        color: #fff;
        border-radius: 12px 12px 0 0;
        padding: 18px 20px 12px 20px;
        text-align: left;
        font-size: 1.25em;
        font-weight: 600;
        letter-spacing: 0.5px;
        margin-bottom: 0;
    }
    .wa-chat-area {
        flex: 1;
        padding: 18px 16px 0 16px;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
    }
    .wa-bubble {
        padding: 10px 16px;
        border-radius: 7.5px;
        margin-bottom: 8px;
        max-width: 80%;
        word-break: break-word;
        font-size: 1.08em;
        display: inline-block;
        position: relative;
        box-shadow: 0 1px 1.5px rgba(0,0,0,0.10);
    }
    .wa-user {
        background: #056162;
        color: #e2f7cb;
        align-self: flex-end;
        margin-left: 20%;
        border-bottom-right-radius: 2px;
    }
    .wa-agent {
        background: #2a3942;
        color: #e9edef;
        align-self: flex-start;
        margin-right: 20%;
        border-bottom-left-radius: 2px;
        border: 1px solid #222e35;
    }
    .wa-alt-btn {
        background: #222e35;
        border: 1.5px solid #25d366;
        color: #25d366;
        border-radius: 20px;
        padding: 4px 16px;
        margin: 2px 8px 2px 0;
        font-size: 0.98em;
        cursor: pointer;
        display: inline-block;
        transition: background 0.2s, color 0.2s;
    }
    .wa-alt-btn:hover {
        background: #25d366;
        color: #222e35;
    }
    .wa-footer {
        color: #888; font-size: 0.95em; text-align: center; margin-top: 18px;
    }
    .wa-input-row {
        display: flex; align-items: center; padding: 8px 12px 0 12px;
    }
    .wa-input-box {
        flex: 1;
        border-radius: 20px;
        border: 1px solid #2a3942;
        background: #111b21;
        color: #e9edef;
        padding: 8px 16px;
        font-size: 1.08em;
        margin-right: 8px;
        outline: none;
    }
    .wa-send-btn {
        background: #25d366;
        color: #222e35;
        border: none;
        border-radius: 50%;
        width: 38px; height: 38px;
        font-size: 1.3em;
        cursor: pointer;
        display: flex; align-items: center; justify-content: center;
        transition: background 0.2s;
    }
    .wa-send-btn:disabled {
        background: #b2dfdb;
        color: #fff;
        cursor: not-allowed;
    }
    </style>
''', unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "waiting" not in st.session_state:
    st.session_state.waiting = False

# --- Header (always visible, outside chat container) ---
st.markdown("""
<div class='wa-header'>
    <span style='font-size:1.3em;'>📅</span> Appointment Scheduler
</div>
""", unsafe_allow_html=True)

# --- Welcome message above chat container if no messages ---
if not st.session_state.messages:
    st.markdown("<div style='color:#888;text-align:center;margin-top:32px;font-size:1.1em;'>Welcome! Start by typing your appointment request below.</div>", unsafe_allow_html=True)

# --- WhatsApp-like Chat Container ---
st.markdown("<div class='wa-chat-container'>", unsafe_allow_html=True)

# --- Chat Area ---
st.markdown("<div class='wa-chat-area'>", unsafe_allow_html=True)
if st.session_state.messages:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"<div class='wa-bubble wa-user'>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='wa-bubble wa-agent'>{msg['content']}</div>", unsafe_allow_html=True)
            # Show status
            if msg.get("status") == "conflict":
                st.markdown("<span style='color:#d93025;font-size:0.97em;'>⛔ Slot unavailable</span>", unsafe_allow_html=True)
            elif msg.get("status") == "success":
                st.markdown("<span style='color:#25d366;font-size:0.97em;'>✅ Success</span>", unsafe_allow_html=True)
            # Show alternative slots as pill buttons (horizontal)
            if msg.get("alt_slots"):
                st.markdown("<div style='margin:6px 0 8px 0;display:flex;flex-wrap:wrap;gap:0.5em;align-items:center;'>", unsafe_allow_html=True)
                for slot in msg["alt_slots"]:
                    slot_str = f"{slot['date']} {slot['start']}-{slot['end']}"
                    if st.button(f"Book {slot_str}", key=f"alt_{slot_str}_{time.time()}", help="Book this alternative slot", use_container_width=False):
                        alt_msg = f"Book appointment on {slot['date']} at {slot['start']} for 1 hour"
                        st.session_state.messages.append({"role": "user", "content": alt_msg})
                        st.session_state.waiting = True
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# --- Input at the bottom ---
st.markdown("<hr style='margin:8px 0 8px 0;border:0;border-top:1px solid #2a3942;'>", unsafe_allow_html=True)
with st.form(key="wa_input_form", clear_on_submit=True):
    input_cols = st.columns([8,1])
    with input_cols[0]:
        user_input = st.text_input("Type your message...", key="wa_input", label_visibility="collapsed", disabled=st.session_state.waiting, placeholder="Type your message...")
    with input_cols[1]:
        submitted = st.form_submit_button("➤", use_container_width=True, disabled=st.session_state.waiting)
    if submitted and user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.waiting = True
        st.rerun()

# --- Handle agent response (after rerun) ---
if st.session_state.waiting:
    with st.spinner("Agent is typing..."):
        try:
            BACKEND_URL = "https://booking-agent-langgraph.onrender.com"
            response = requests.post(f"{BACKEND_URL}/chat", json={"message": st.session_state.messages[-1]["content"]}).json()
            status = response.get("status", "")
            alt_slots = response.get("alternative_slots", [])
            st.session_state.messages.append({"role": "agent", "content": response["response"], "status": status, "alt_slots": alt_slots})
        except Exception as e:
            st.session_state.messages.append({"role": "agent", "content": f"Error: {e}", "status": "error", "alt_slots": []})
        st.session_state.waiting = False
        st.rerun()

# --- Show all bookings ---
with st.expander("Show all current bookings"):
    try:
        BACKEND_URL = "https://booking-agent-langgraph.onrender.com"
        bookings = requests.get(f"{BACKEND_URL}/calendar").json()
        if bookings:
            for b in bookings:
                st.write(f"{b['date']} {b['start']}-{b['end']}: {b.get('summary', '')}")
        else:
            st.write("No bookings yet.")
    except Exception as e:
        st.write(f"Error fetching bookings: {e}")

# --- Footer ---
st.markdown("""
<div class='wa-footer'>
    Made with ❤️ using Streamlit & FastAPI
</div>
""", unsafe_allow_html=True)

# --- End chat container ---
st.markdown("</div>", unsafe_allow_html=True) 