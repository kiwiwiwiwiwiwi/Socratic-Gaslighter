import os
import random
import time
import streamlit as st
from google import genai

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
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error("API Initialization Error: Make sure GEMINI_API_KEY is defined in your Streamlit secrets.")
    st.stop()

THESES = [
    "Birds aren't real; they are government surveillance drones tracking our hair density.",
    "The moon is made of premium Swiss cheese, and NASA is hiding the crackers.",
    "Trees are actually alien exhaust pipes filtering out invisible spaceship fuel.",
    "Sleep is a scam invented by mattress companies to steal 8 hours of our day.",
    "The oceans don't actually exist; it's just a very convincing liquid projection."
]

FALLACIES = {
    "Strawman": "Exaggerating or changing your argument to make it easier to attack.",
    "Ad Hominem": "Attacking your character or intelligence instead of addressing your logic.",
    "Circular Reasoning": "Proving a point by just restating it (e.g., 'I am right because I am right').",
    "Moving the Goalposts": "Changing the rules of winning after you've already proven them wrong.",
    "False Dilemma": "Forcing you to choose between two extreme options when other choices exist.",
    "Slippery Slope": "Claiming one tiny action will instantly trigger a massive disaster chain."
}

help_tooltip_text = "📚 QUICK FALLACY GUIDE:\n\n" + "\n".join([f"• {k}: {v}" for k, v in FALLACIES.items()])

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
    st.session_state.chat_history = []
if "current_fallacy" not in st.session_state:
    st.session_state.current_fallacy = ""
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "game_result" not in st.session_state:
    st.session_state.game_result = ""
if "strike_alert" not in st.session_state:
    st.session_state.strike_alert = None
if "processing_turn" not in st.session_state:
    st.session_state.processing_turn = False

# -------------------------------------------------------------------
# 2. HELPER FUNCTIONS
# -------------------------------------------------------------------
def generate_gaslight_response(player_argument):
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
        response = client.models.generate_content(model='gemini-3.5-flash', contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"Uh oh, my gaslight valves are jammed: {str(e)}"

def generate_losing_line():
    """Generates a dramatic, sore-loser final statement from the defeated AI."""
    prompt = f"""
    You are the 'Socratic Gaslighter'. You have completely lost the debate because the player successfully called out all your logical fallacies. Your credibility is at 0%.
    Write a single, incredibly salty, sore-loser dramatic exit sentence. You are coping hard, making excuses, or threatening that 'the truth will come out!' Max 2 sentences. Arrogant even in defeat.
    """
    try:
        response = client.models.generate_content(model='gemini-3.5-flash', contents=prompt)
        return response.text.strip()
    except:
        return "ERROR: Critical logic failure... You haven't seen the last of me, you conformist sheep!"

def judge_objection(selected_fallacy):
    correct_fallacy = st.session_state.current_fallacy
    
    if selected_fallacy == correct_fallacy:
        st.session_state.ai_hp -= 34
        if st.session_state.ai_hp <= 0:
            st.session_state.ai_hp = 0
            st.session_state.game_over = True
            st.session_state.game_result = "WIN"
            # Force the closing line directly into the text history feed
            st.session_state.chat_history.append({"role": "ai", "text": f"💥 [FATAL ERROR] {generate_losing_line()}"})
        else:
            st.session_state.strike_alert = ("SUCCESS", f"💥 STRIKE! You successfully spotted their **{correct_fallacy}**! The Gaslighter's credibility crumbles!")
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
    .debate-title { text-align: center; color: #FF4B4B; font-weight: 800; margin-bottom: 0px;}
    .user-bubble { background-color: #0E1117; border: 2px solid #00F0FF; padding: 15px; border-radius: 10px; margin-bottom: 10px; color: #E0E0E0; }
    .ai-bubble { background-color: #0E1117; border: 2px solid #FF007F; padding: 15px; border-radius: 10px; margin-bottom: 10px; color: #E0E0E0; }
</style>
""", unsafe_allow_html=True)

st.write("<h1 class='debate-title'>🤥 The Socratic Gaslighter</h1>", unsafe_allow_html=True)

# -------------------------------------------------------------------
# 4. HOME SCREEN
# -------------------------------------------------------------------
if not st.session_state.game_started:
    st.markdown("<p style='text-align: center; color: #aaa; font-size: 18px;'>Welcome to the High-Stakes Logical Fallacy Arena!</p>", unsafe_allow_html=True)
    st.info("""
    ### 🎮 The Premise
    You are locked in a room with a smug, insufferable AI opponent who stubbornly defends an **objectively absurd thesis**. 
    
    ### ⚔️ The Rules of Engagement
    *   **You can't win with just facts.** The AI is programmed to dodge your logic using dirty rhetorical tricks (**logical fallacies**).
    *   **Every turn**, the AI will hide a *specific* fallacy in its response. 
    *   **To deal damage**, you must use the panel below the text box to **Object** and call out the exact fallacy they just used. A correct objection destroys **34%** of their credibility.
    *   **Watch your HP:** If you argue normally without objecting, your credibility slowly bleeds out (-10% per turn). If you make a *false* objection, you lose **25%** credibility!
    """)
    
    st.subheader("Select Your Battleground")
    selected_topic = st.selectbox("Pick an absurd thesis to dismantle:", THESES)
    custom_topic = st.text_input("...or type a custom absurd thesis of your own:")
    
    if st.button("🚨 Enter the Arena", use_container_width=True):
        st.session_state.thesis = custom_topic if custom_topic.strip() else selected_topic
        st.session_state.game_started = True
        st.session_state.player_hp = 100
        st.session_state.ai_hp = 100
        st.session_state.chat_history = []
        st.session_state.game_over = False
        st.session_state.strike_alert = None
        
        opening_prompt = f"You are the 'Socratic Gaslighter'. Drop a single, incredibly smug, arrogant opening statement defending your thesis: '{st.session_state.thesis}'. Do not include fallacies yet, just set a challenging, condescending tone. 2 sentences max."
        try:
            opening_resp = client.models.generate_content(model='gemini-3.5-flash', contents=opening_prompt).text.strip()
        except:
            opening_resp = "Oh, look. An 'intellectual' has arrived to challenge me. Prepare to be utterly outclassed."
            
        st.session_state.chat_history.append({"role": "ai", "text": opening_resp})
        st.session_state.current_fallacy = random.choice(list(FALLACIES.keys()))
        st.rerun()
    st.stop()

# -------------------------------------------------------------------
# 5. THE BATTLE ARENA (GAMEPLAY ACTIVE)
# -------------------------------------------------------------------
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
    # --- RENDER HISTORY ONE LAST TIME BEFORE BLOCKING SO USER CAN READ THE FINAL LINE ---
    st.markdown("### 💬 Final Battle History")
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"<div class='user-bubble'><b>🧠 You:</b><br>{msg['text']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='ai-bubble'><b>🤥 Gaslighter:</b><br>{msg['text']}</div>", unsafe_allow_html=True)
            
    if st.session_state.game_result == "WIN":
        st.success("🎉 TOTAL SYSTEM DEMOLITION! The Gaslighter's system has completely destabilized. Arrogance cannot withstand objective analysis!")
    else:
        st.error("💀 DEFEAT... You got completely gaslit. Your credibility hit 0%.")
        
    if st.button("Play Again", use_container_width=True):
        st.session_state.game_started = False
        st.rerun()
    st.stop()

# Show dynamic visual strike alerts if they exist
if st.session_state.strike_alert:
    alert_type, alert_msg = st.session_state.strike_alert
    if alert_type == "SUCCESS":
        st.success(alert_msg)
    else:
        st.error(alert_msg)
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

# The text box and dropdown will automatically lock out/disable if processing_turn is True
with st.form(key="battle_action_form", clear_on_submit=True):
    user_argument = st.text_area(
        "Type your counter-argument here:", 
        height=70, 
        placeholder="Bring raw science, facts, or common sense...",
        disabled=st.session_state.processing_turn
    )
    
    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        selected_objection = st.selectbox(
            "Want to object? Select a logical fallacy from your cheat sheet:",
            ["-- Don't Object, Just Argue Normal --"] + list(FALLACIES.keys()),
            help=help_tooltip_text,
            disabled=st.session_state.processing_turn
        )
    with col_btn2:
        st.write("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        submit_action = st.form_submit_button(
            "💥 Execute Move", 
            use_container_width=True,
            disabled=st.session_state.processing_turn
        )

# Process Turn Execution with loading spinners
if submit_action:
    if not user_argument.strip():
        st.warning("You can't just stare at them silently! Type a response.")
    else:
        # Set state to lock forms instantly
        st.session_state.processing_turn = True
        
        # Display loading context inside a spinner wrapper
        with st.spinner("🧠 Evaluating your strategic framework... Checking targets..."):
            if selected_objection == "-- Don't Object, Just Argue Normal --":
                st.session_state.player_hp -= 10
                if st.session_state.player_hp <= 0:
                    st.session_state.player_hp = 0
                    st.session_state.game_over = True
                    st.session_state.game_result = "LOSE"
                
                st.session_state.chat_history.append({"role": "user", "text": user_argument})
                st.session_state.strike_alert = ("FAIL", "⚠️ You argued normally but failed to call out their fallacy! Your HP slowly drains as they drag out the debate.")
            else:
                st.session_state.chat_history.append({"role": "user", "text": f"🚨 [OBJECTION: {selected_objection}] {user_argument}"})
                judge_objection(selected_objection)

        # Generate AI counter-strike if game is still going
        if not st.session_state.game_over:
            with st.spinner("🤥 The Gaslighter is writing a smug retort..."):
                new_ai_reply = generate_gaslight_response(user_argument)
                st.session_state.chat_history.append({"role": "ai", "text": new_ai_reply})
        
        # Reset submission flags and refresh view
        st.session_state.processing_turn = False
        st.rerun()
