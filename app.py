import os
import random
import streamlit as st
from google import genai
from google.genai import types

# -------------------------------------------------------------------
# 1. INITIALIZATION & SETUP
# -------------------------------------------------------------------
st.set_page_config(
    page_title="The Socratic Gaslighter",
    page_icon="🤥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Initialize the Gemini Client using Streamlit Secrets
try:
    # This automatically pulls the key from your secrets.toml file
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error("API Initialization Error: Make sure GEMINI_API_KEY is defined in your Streamlit secrets.")
    st.stop()

# Pre-defined absurd theses
THESES = [
    "Birds aren't real; they are government surveillance drones tracking our hair density.",
    "The moon is made of premium Swiss cheese, and NASA is hiding the crackers.",
    "Trees are actually alien exhaust pipes filtering out invisible spaceship fuel.",
    "Sleep is a scam invented by mattress companies to steal 8 hours of our day.",
    "The oceans don't actually exist; it's just a very convincing liquid projection."
]

# List of fallacies for the game mechanics
FALLACIES = {
    "Strawman": "Misrepresenting or exaggerating an opponent's argument to make it easier to attack.",
    "Ad Hominem": "Attacking the person making the argument rather than the argument itself.",
    "Circular Reasoning": "Restating the argument rather than proving it (e.g., 'X is true because X is true').",
    "Moving the Goalposts": "Demanding new evidence or changing the rules of winning after the initial criteria were met.",
    "False Dilemma": "Presenting only two options when multiple choices exist.",
    "Slippery Slope": "Claiming that a small first step will inevitably lead to a chain of disastrous events."
}

# Initialize Session State Variables if they don't exist
if "game_started" not in st.session_state:
    st.session_state.game_started = False
if "player_hp" not in st.session_state:
    st.session_state.player_hp = 100
if "ai_hp" not in st.session_state:
    st.session_state.ai_hp = 100
if "thesis" not in st.session_state:
    st.session_state.thesis = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # List of dicts: {"role": "user/ai", "text": "..."}
if "current_fallacy" not in st.session_state:
    st.session_state.current_fallacy = ""
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "game_result" not in st.session_state:
    st.session_state.game_result = ""
if "strike_alert" not in st.session_state:
    st.session_state.strike_alert = None

# -------------------------------------------------------------------
# 2. HELPER FUNCTIONS (GENAI INTELLIGENCE)
# -------------------------------------------------------------------
def generate_gaslight_response(player_argument):
    """Generates the AI's next smug response, embedding a specific fallacy."""
    # Pick a random fallacy for this turn
    chosen_fallacy = random.choice(list(FALLACIES.keys()))
    st.session_state.current_fallacy = chosen_fallacy

    prompt = f"""
    You are the 'Socratic Gaslighter', a smug, insufferable debater who aggressively defends the thesis: "{st.session_state.thesis}".
    
    The player just said: "{player_argument}"
    
    Your goal is to reply with an argument that sounds arrogant, dismissive, and confidently incorrect. 
    You MUST deliberately inject the following logical fallacy into your response: **{chosen_fallacy}** ({FALLACIES[chosen_fallacy]}).
    
    Keep your response to 2-4 sentences max. Do NOT mention the name of the fallacy in your response. Just execute it naturally but obviously.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        return f"Uh oh, my gaslight valves are jammed: {str(e)}"

def judge_objection(selected_fallacy):
    """Verifies if the user correctly called out the embedded fallacy."""
    correct_fallacy = st.session_state.current_fallacy
    
    if selected_fallacy == correct_fallacy:
        st.session_state.ai_hp -= 34
        if st.session_state.ai_hp <= 0:
            st.session_state.ai_hp = 0
            st.session_state.game_over = True
            st.session_state.game_result = "WIN"
        st.session_state.strike_alert = ("SUCCESS", f"💥 STRIKE! You successfully spotted their **{correct_fallacy}**! The Gaslighter's credibility crumbles!")
        # Force a new turn/fallacy generation for the next cycle
        st.session_state.current_fallacy = "" 
    else:
        st.session_state.player_hp -= 25
        if st.session_state.player_hp <= 0:
            st.session_state.player_hp = 0
            st.session_state.game_over = True
            st.session_state.game_result = "LOSE"
        st.session_state.strike_alert = ("FAIL", f"❌ FALSE ACCUSATION! The Gaslighter wraps your mind in knots. That wasn't a {selected_fallacy}. Your credibility drops!")

# -------------------------------------------------------------------
# 3. CUSTOM STYLING & UI
# -------------------------------------------------------------------
st.markdown("""
<style>
    .debate-title { text-align: center; color: #FF4B4B; font-weight: 800; }
    .user-bubble { background-color: #0E1117; border: 2px solid #00F0FF; padding: 15px; border-radius: 10px; margin-bottom: 10px; color: #E0E0E0; }
    .ai-bubble { background-color: #0E1117; border: 2px solid #FF007F; padding: 15px; border-radius: 10px; margin-bottom: 10px; color: #E0E0E0; }
    .system-card { background-color: #1E1E24; padding: 20px; border-radius: 10px; border: 1px dashed #FF4B4B; margin-bottom: 20px; text-align: center;}
</style>
""", unsafe_allow_html=True)

st.write("<h1 class='debate-title'>🤥 The Socratic Gaslighter</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Spot the logical fallacies, break their smug defenses, win the debate.</p>", # Keep plain text raw or clear
            unsafe_allow_html=True)

# -------------------------------------------------------------------
# 4. GAME INITIALIZATION SCREEN
# -------------------------------------------------------------------
if not st.session_state.game_started:
    st.subheader("Choose Your Battleground")
    selected_topic = st.selectbox("Select an absurd thesis to dismantle:", THESES)
    custom_topic = st.text_input("...or type your own custom absurd thesis:")
    
    if st.button("🚨 Enter the Arena", use_container_width=True):
        st.session_state.thesis = custom_topic if custom_topic.strip() else selected_topic
        st.session_state.game_started = True
        st.session_state.player_hp = 100
        st.session_state.ai_hp = 100
        st.session_state.chat_history = []
        st.session_state.game_over = False
        st.session_state.strike_alert = None
        
        # Opening salvo from AI
        opening_prompt = f"You are the 'Socratic Gaslighter'. Drop a single, incredibly smug, arrogant opening statement defending your thesis: '{st.session_state.thesis}'. Do not include fallacies yet, just set a challenging, condescending tone. 2 sentences max."
        try:
            opening_resp = client.models.generate_content(model='gemini-2.5-flash', contents=opening_prompt).text.strip()
        except:
            opening_resp = "Oh, look. An 'intellectual' has arrived to challenge me. Prepare to be utterly intellectually outclassed."
            
        st.session_state.chat_history.append({"role": "ai", "text": opening_resp})
        # Generate the first hidden fallacy target immediately
        st.session_state.current_fallacy = random.choice(list(FALLACIES.keys()))
        st.rerun()
    st.stop()

# -------------------------------------------------------------------
# 5. THE BATTLE ARENA (GAMEPLAY ACTIVE)
# -------------------------------------------------------------------

# --- THE CREDIBILITY HP DASHBOARD ---
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"**Your Credibility:** {st.session_state.player_hp}%")
    st.progress(st.session_state.player_hp / 100)
with col2:
    st.markdown(f"**Gaslighter's Credibility:** {st.session_state.ai_hp}%")
    st.progress(st.session_state.ai_hp / 100)

st.markdown(f"### 📍 Target Thesis: *\"{st.session_state.thesis}\"*")
st.write("---")

# Handle End-Game States
if st.session_state.game_over:
    if st.session_state.game_result == "WIN":
        st.balloons()
        st.success("🎉 VICTORY! You completely demolished the Gaslighter's credibility. They sparks out, unable to compute your flawless logic!")
    else:
        st.error("💀 DEFEAT... You got completely gaslit. Your credibility hit 0%, and you walked away questioning if you exist at all.")
        
    if st.button("Play Again", use_container_width=True):
        st.session_state.game_started = False
        st.rerun()
    st.stop()

# Show dynamic visual strike alerts if they exist
if st.session_state.strike_alert:
    alert_type, alert_msg = st.session_state.strike_alert
    if alert_type == "SUCCESS":
        st.toast(alert_msg, icon="💥")
        st.success(alert_msg)
    else:
        st.toast(alert_msg, icon="❌")
        st.error(alert_msg)
    # Clear the alert so it doesn't linger permanently on subsequent re-runs
    st.session_state.strike_alert = None

# --- THE BATTLE FEED ---
st.markdown("### 💬 The Battle Feed")
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(f"<div class='user-bubble'><b>🧠 You:</b><br>{msg['text']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='ai-bubble'><b>🤥 Gaslighter:</b><br>{msg['text']}</div>", unsafe_allow_html=True)

# --- ACTION PANEL ---
st.write("---")
st.markdown("### 🕹️ Your Turn: Make Your Move")

# Form handling input to avoid partial re-renders while typing
with st.form(key="battle_action_form", clear_on_submit=True):
    user_argument = st.text_area("Type your counter-argument here:", height=70, placeholder="Bring raw science, facts, or common sense...")
    
    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        selected_objection = st.selectbox(
            "Want to object? Select a logical fallacy from your cheat sheet:",
            ["-- Don't Object, Just Argue Normal --"] + list(FALLACIES.keys()),
            help="If you think their last statement contained a fallacy, select it here before hitting Submit!"
        )
    with col_btn2:
        st.write("<div style='height: 28px;'></div>", unsafe_allow_html=True) # visual alignment
        submit_action = st.form_submit_input("💥 Execute Move", use_container_width=True)

# Process Turn Execution
if submit_action:
    if not user_argument.strip():
        st.warning("You can't just stare at them silently! Type a response.")
    else:
        # 1. Process User Argument Strategy
        if selected_objection == "-- Don't Object, Just Argue Normal --":
            # If they just argue without pointing out the fallacy, player slowly loses health
            st.session_state.player_hp -= 10
            if st.session_state.player_hp <= 0:
                st.session_state.player_hp = 0
                st.session_state.game_over = True
                st.session_state.game_result = "LOSE"
            
            st.session_state.chat_history.append({"role": "user", "text": user_argument})
            st.session_state.strike_alert = ("FAIL", "⚠️ You argued normally but failed to call out their fallacy! Your HP slowly drains as they drag out the debate.")
        else:
            # Player explicitly attempts a tactical strike
            st.session_state.chat_history.append({"role": "user", "text": f"🚨 [OBJECTION: {selected_objection}] {user_argument}"})
            judge_objection(selected_objection)

        # 2. Generate AI counter-strike if game is still going
        if not st.session_state.game_over:
            new_ai_reply = generate_gaslight_response(user_argument)
            st.session_state.chat_history.append({"role": "ai", "text": new_ai_reply})
        
        st.rerun()

# --- SIDEBAR CHEAT SHEET ---
with st.sidebar:
    st.markdown("### 📖 Fallacy Cheat Sheet")
    st.write("Use these descriptions to catch the Gaslighter cheating:")
    for key, val in FALLACIES.items():
        st.markdown(f"**• {key}**:\n*{val}*")
