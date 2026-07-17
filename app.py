import os
import random
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
    "The oceans don't actually exist; it's just a very convincing liquid projection.",
    "Gravity is a social construct invented by shoe companies to sell more footwear.",
    "Clouds are actually industrialized cotton candy operations masking aerial city grids.",
    "Cats are liquid-based cartographers sent to map the structural integrity of our furniture.",
    "The sun is just a massive LED light bulb, and the eclipse happens when they change the fuse.",
    "Time moves backward on Tuesdays, but our brains lack the RAM to process it.",
    "Rain is just the sky crying because your logical arguments are so deeply flawed.",
    "Mountains are giant sleeping tortoises waiting for the ultimate cosmic whistle.",
    "Dogs are undercover tax auditors analyzing our spending habits via aggressive sniffing."
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

# Initialize Session State Variables
if "show_intro" not in st.session_state:
    st.session_state.show_intro = True
if "game_started" not in st.session_state:
    st.session_state.game_started = False
if "game_mode" not in st.session_state:
    st.session_state.game_mode = "Classic Duel"
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

# Game-mode specific tracking variables
if "endless_streak" not in st.session_state:
    st.session_state.endless_streak = 0
if "endless_high_score" not in st.session_state:
    st.session_state.endless_high_score = 0
if "championship_round" not in st.session_state:
    st.session_state.championship_round = 1

ACTIVE_MODEL = 'gemini-3.1-flash-lite'

# -------------------------------------------------------------------
# GLOBAL SIDEBAR (PLAYS MUSIC EVERYWHERE & SHOWS CHEAT SHEET)
# -------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🎵 Arena Soundtrack")
    st.write("Tune into the official Socratic debate synth theme:")
    
    music_source = "background_music.mp3"
    if not os.path.exists(music_source):
        music_source = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
    
    try:
        st.audio(
            music_source, 
            format="audio/mp3", 
            loop=True, 
            autoplay=False
        )
    except Exception as e:
        st.info("💡 Unable to load soundtrack.")
        
    st.write("---")
    st.markdown("### 📖 Fallacy Cheat Sheet")
    st.write("Keep these definitions close during your debate:")
    for key, val in FALLACIES.items():
        st.markdown(f"**• {key}**:\n*{val}*")

# -------------------------------------------------------------------
# 2. HELPER FUNCTIONS
# -------------------------------------------------------------------
def generate_gaslight_response(player_argument):
    chosen_fallacy = random.choice(list(FALLACIES.keys()))
    st.session_state.current_fallacy = chosen_fallacy

    difficulty_modifier = ""
    if st.session_state.game_mode == "3-Round Championship":
        if st.session_state.championship_round == 1:
            difficulty_modifier = "Keep the fallacy very simple, obvious, and almost cartoonish."
        elif st.session_state.championship_round == 2:
            difficulty_modifier = "Make the fallacy moderately tricky and hard to spot."
        elif st.session_state.championship_round == 3:
            difficulty_modifier = "Make the fallacy extremely subtle, clever, and deeply woven into your argument."

    prompt = f"""
    You are the 'Socratic Gaslighter', a smug, insufferable debater who aggressively defends the thesis: "{st.session_state.thesis}".
    The player just said: "{player_argument}"
    Your goal is to reply with an argument that sounds arrogant, dismissive, and confidently incorrect. 
    You MUST deliberately inject the following logical fallacy into your response: **{chosen_fallacy}** ({FALLACIES[chosen_fallacy]}).
    {difficulty_modifier}
    Keep your response to 2-4 sentences max. Do NOT mention the name of the fallacy in your response. Just execute it naturally but obviously.
    """
    try:
        response = client.models.generate_content(model=ACTIVE_MODEL, contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"Uh oh, my gaslight valves are jammed: {str(e)}"

def generate_losing_line():
    prompt = f"""
    You are the 'Socratic Gaslighter'. You have completely lost the debate because the player successfully called out all your logical fallacies. Your credibility is at 0%.
    Write a single, incredibly salty, sore-loser dramatic exit sentence. You are coping hard, making excuses, or threatening that 'the truth will come out!' Max 2 sentences. Arrogant even in defeat.
    """
    try:
        response = client.models.generate_content(model=ACTIVE_MODEL, contents=prompt)
        return response.text.strip()
    except:
        return "ERROR: Critical logic failure... You haven't seen the last of me, you conformist sheep!"

def start_next_endless_opponent():
    """Resets the Gaslighter for the next survival fight while preserving Player state."""
    st.session_state.endless_streak += 1
    if st.session_state.endless_streak > st.session_state.endless_high_score:
        st.session_state.endless_high_score = st.session_state.endless_streak
        
    st.session_state.player_hp = min(100, st.session_state.player_hp + 30)
    st.session_state.ai_hp = 100
    st.session_state.thesis = random.choice(THESES)
    
    boss_intro_prompt = f"You are the 'Socratic Gaslighter'. You are a brand new, even more arrogant debater stepping into the ring. Drop a single, condescending, smug opening statement defending your new ridiculous thesis: '{st.session_state.thesis}'."
    try:
        opening_resp = client.models.generate_content(model=ACTIVE_MODEL, contents=boss_intro_prompt).text.strip()
    except:
        opening_resp = f"A new challenger? Fine. Let's talk about why {st.session_state.thesis} is an absolute cosmic truth."
        
    st.session_state.chat_history = [{"role": "ai", "text": f"🔄 **OPPONENT DEFEATED!** A new challenger steps forward...\n\n {opening_resp}"}]
    st.session_state.current_fallacy = random.choice(list(FALLACIES.keys()))

def advance_championship_round():
    """Moves to the next match of the tournament."""
    st.session_state.championship_round += 1
    st.session_state.player_hp = 100
    st.session_state.ai_hp = 100
    st.session_state.thesis = random.choice(THESES)
    
    round_intro_prompt = f"You are the 'Socratic Gaslighter'. This is Round {st.session_state.championship_round} of the tournament. Drop an opening statement defending: '{st.session_state.thesis}'. Make it sound even more intensely smug than the previous round."
    try:
        opening_resp = client.models.generate_content(model=ACTIVE_MODEL, contents=round_intro_prompt).text.strip()
    except:
        opening_resp = f"Round {st.session_state.championship_round}. Prepare to be thoroughly dismantled."
        
    st.session_state.chat_history = [{"role": "ai", "text": f"🏆 **ROUND {st.session_state.championship_round} BEGINS!**\n\n {opening_resp}"}]
    st.session_state.current_fallacy = random.choice(list(FALLACIES.keys()))

def judge_objection(selected_fallacy):
    """Uses the LLM as a dynamic referee to see if the player's objection is valid for the text."""
    last_ai_response = ""
    for msg in reversed(st.session_state.chat_history):
        if msg["role"] == "ai" and not msg["text"].startswith("💥") and not msg["text"].startswith("🔄") and not msg["text"].startswith("🏆"):
            last_ai_response = msg["text"]
            break

    judge_prompt = f"""
    You are an objective, fair logic tournament referee evaluating a debate performance.
    The opponent just said: "{last_ai_response}"
    The player objects and accuses them of committing this fallacy: **{selected_fallacy}** ({FALLACIES[selected_fallacy]}).
    
    Is the player's accusation reasonably valid based on the text provided? (Keep in mind a sentence can contain multiple fallacies, if they spotted a legitimate one, rule it VALID).
    Respond with exactly 'VALID' or 'INVALID' as the first word. 
    Followed by a brief, 1-sentence explanation of why.
    """
    
    try:
        verdict_resp = client.models.generate_content(model=ACTIVE_MODEL, contents=judge_prompt).text.strip()
        is_valid = verdict_resp.upper().startswith("VALID")
        explanation = verdict_resp.replace("VALID", "").replace("INVALID", "").strip(" :-,")
    except:
        is_valid = (selected_fallacy == st.session_state.current_fallacy)
        explanation = f"Hidden intended target was {st.session_state.current_fallacy}."

    if is_valid:
        damage = 34
        if st.session_state.game_mode == "3-Round Championship" and st.session_state.championship_round == 3:
            damage = 25

        st.session_state.ai_hp -= damage
        if st.session_state.ai_hp <= 0:
            st.session_state.ai_hp = 0
            
            if st.session_state.game_mode == "Endless Mode (Survival)":
                start_next_endless_opponent()
                st.session_state.strike_alert = ("SUCCESS", f"💥 CRITICAL SUCCESS! You defeated the Gaslighter! Current Streak: {st.session_state.endless_streak}. Credibility partially restored (+30% HP)!")
            elif st.session_state.game_mode == "3-Round Championship" and st.session_state.championship_round < 3:
                advance_championship_round()
                st.session_state.strike_alert = ("SUCCESS", f"💥 ROUND WON! You conquered Round {st.session_state.championship_round-1}. Prepare for the next opponent!")
            else:
                st.session_state.game_over = True
                st.session_state.game_result = "WIN"
                st.session_state.chat_history.append({"role": "ai", "text": f"💥 [FATAL ERROR] {generate_losing_line()}"})
        else:
            st.session_state.strike_alert = ("SUCCESS", f"💥 STRIKE! The referee rules your objection valid! {explanation}")
        st.session_state.current_fallacy = "" 
    else:
        penalty = 25
        if st.session_state.game_mode == "3-Round Championship" and st.session_state.championship_round == 3:
            penalty = 50
            
        st.session_state.player_hp -= penalty
        if st.session_state.player_hp <= 0:
            st.session_state.player_hp = 0
            st.session_state.game_over = True
            st.session_state.game_result = "LOSE"
            
        st.session_state.strike_alert = (
            "FAIL", 
            f"❌ **FALSE ACCUSATION!** (-{penalty}% HP)\n\n*Referee Verdict: {explanation}*"
        )

# -------------------------------------------------------------------
# 3. CUSTOM STYLING & UI
# -------------------------------------------------------------------
st.markdown("""
<style>
    .debate-title { text-align: center; color: #FF4B4B; font-weight: 800; margin-bottom: 0px;}
    .user-bubble { background-color: #0E1117; border: 2px solid #00F0FF; padding: 15px; border-radius: 10px; margin-bottom: 10px; color: #E0E0E0; }
    .ai-bubble { background-color: #0E1117; border: 2px solid #FF007F; padding: 15px; border-radius: 10px; margin-bottom: 10px; color: #E0E0E0; }
    .mode-badge { background-color: #1E1E2E; border: 1px solid #FFD700; padding: 5px 12px; border-radius: 15px; font-weight: bold; color: #FFD700; text-align: center; }
</style>
""", unsafe_allow_html=True)

st.write("<h1 class='debate-title'>🤥 The Socratic Gaslighter</h1>", unsafe_allow_html=True)

# -------------------------------------------------------------------
# 4A. GAME TITLE SCREEN / DESCRIPTION (PHASE 1)
# -------------------------------------------------------------------
if st.session_state.show_intro:
    st.markdown("<p style='text-align: center; color: #aaa; font-size: 18px;'>The Ultimate Logical Fallacy Battleground</p>", unsafe_allow_html=True)
    st.write("---")
    
    st.markdown("""
    ### 📖 Welcome to the Arena
    You are stepping into a high-stakes rhetorical arena facing **The Socratic Gaslighter**—an insufferably confident, aggressively smug debater who relies entirely on invalid logic, psychological projection, and corrupted debate practices to win arguments about entirely ridiculous facts.
    
    #### 🕹️ How It Works:
    1. **The Core Loop**: The Gaslighter will state an absurd thesis statement (e.g., *"Birds are government surveillance drones"*).
    2. **Spot the Flaw**: In every single response, the Gaslighter will intentionally deploy a major **logical fallacy** (such as *Ad Hominem*, *Strawman*, or *Circular Reasoning*).
    3. **Call Them Out**: Your job is to draft a counter-argument and **accurately choose the fallacy** they committed from your toolkit.
    
    #### ⚡ The Stakes:
    * **Spotting a Fallacy Right**: Damages the Gaslighter's credibility score. Bring it to 0% to collapse their logical system entirely!
    * **Blindly Arguing / Accusing Wrong**: Drains your own credibility health bar. If you crash to 0%, you lose the argument and get completely gaslit!
    """)
    
    st.write("---")
    if st.button("🎮 Enter the Arena Lobby", use_container_width=True):
        st.session_state.show_intro = False
        st.rerun()
    st.stop()

# -------------------------------------------------------------------
# 4B. LOBBY CONFIGURATION SCREEN (PHASE 2)
# -------------------------------------------------------------------
if not st.session_state.game_started:
    st.markdown("<p style='text-align: center; color: #aaa; font-size: 18px;'>Configure Your Rhetorical Gauntlet</p>", unsafe_allow_html=True)
    
    if st.session_state.endless_high_score > 0:
        st.markdown(f"<p style='text-align: center; font-size: 20px; color: #FFD700; font-weight: bold;'>🏆 Current Endless Mode High Score Streak: {st.session_state.endless_high_score} Opponents Defeated!</p>", unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("🎯 Choose Your Game Mode")
    
    mode_selection = st.radio(
        "Select your preferred rhetorical gauntlet:",
        ["Classic Duel", "Endless Mode (Survival)", "3-Round Championship"],
        index=0,
        horizontal=True
    )
    
    if mode_selection == "Classic Duel":
        st.info("💡 **Classic Duel:** A pure head-to-head. Spot 3 logical fallacies before you run out of credibility to win.")
    elif mode_selection == "Endless Mode (Survival)":
        st.warning(f"💀 **Endless Mode:** Survival of the fittest. When you defeat an AI, they reset with a new thesis. Spotting fallacies restores some HP. [Your Current Best Streak: {st.session_state.endless_high_score}]")
    elif mode_selection == "3-Round Championship":
        st.success("🏆 **3-Round Championship:** A scaling tournament. Round 1 has easy fallacies. Round 2 is tricky. Round 3 is an intense showdown where false accusations take double damage!")
        
    st.write("---")
    st.subheader("Select Your Battleground")
    selected_topic = st.selectbox("Pick an absurd thesis to dismantle:", THESES)
    custom_topic = st.text_input("...or type a custom absurd thesis of your own:")
    
    if st.button("🚨 Start the Match", use_container_width=True):
        st.session_state.game_mode = mode_selection
        st.session_state.thesis = custom_topic if custom_topic.strip() else selected_topic
        st.session_state.game_started = True
        st.session_state.player_hp = 100
        st.session_state.ai_hp = 100
        st.session_state.chat_history = []
        st.session_state.game_over = False
        st.session_state.strike_alert = None
        st.session_state.endless_streak = 0
        st.session_state.championship_round = 1
        
        opening_prompt = f"You are the 'Socratic Gaslighter'. Drop a single, incredibly smug, arrogant opening statement defending your thesis: '{st.session_state.thesis}'. Do not include fallacies yet, just set a challenging, condescending tone. 2 sentences max."
        try:
            opening_resp = client.models.generate_content(model=ACTIVE_MODEL, contents=opening_prompt).text.strip()
        except:
            opening_resp = "Oh, look. An 'intellectual' has arrived to challenge my superior logic. Prepare to be utterly outclassed."
            
        st.session_state.chat_history.append({"role": "ai", "text": opening_resp})
        st.session_state.current_fallacy = random.choice(list(FALLACIES.keys()))
        st.rerun()
    st.stop()

# -------------------------------------------------------------------
# 5. THE BATTLE ARENA (GAMEPLAY ACTIVE)
# -------------------------------------------------------------------
col_header_1, col_header_2 = st.columns([3, 1])
with col_header_1:
    st.markdown(f"### 📍 Target Thesis: *\"{st.session_state.thesis}\"*")
with col_header_2:
    if st.session_state.game_mode == "Classic Duel":
        st.markdown("<div class='mode-badge'>🤺 Classic Duel</div>", unsafe_allow_html=True)
    elif st.session_state.game_mode == "Endless Mode (Survival)":
        st.markdown(f"<div class='mode-badge'>💀 Survival (Streak: {st.session_state.endless_streak})</div>", unsafe_allow_html=True)
    elif st.session_state.game_mode == "3-Round Championship":
        st.markdown(f"<div class='mode-badge'>🏆 Tournament (Round: {st.session_state.championship_round}/3)</div>", unsafe_allow_html=True)

st.write("---")

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"**Your Credibility:** {st.session_state.player_hp}%")
    st.progress(st.session_state.player_hp / 100)
with col2:
    st.markdown(f"**Gaslighter's Credibility:** {st.session_state.ai_hp}%")
    st.progress(st.session_state.ai_hp / 100)

st.write("---")

if st.session_state.game_over:
    st.markdown("### 💬 Final Battle History")
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"<div class='user-bubble'><b>🧠 You:</b><br>{msg['text']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='ai-bubble'><b>🤥 Gaslighter:</b><br>{msg['text']}</div>", unsafe_allow_html=True)
            
    if st.session_state.game_result == "WIN":
        if st.session_state.game_mode == "3-Round Championship":
            st.success("🏆 CHAMPIONSHIP CLEARED! You outmaneuvered the ultimate gaslighting grandmaster and claimed the trophy of logical supremacy!")
        else:
            st.success("🎉 TOTAL SYSTEM DEMOLITION! The Gaslighter's system has completely destabilized. Arrogance cannot withstand objective analysis!")
    else:
        if st.session_state.game_mode == "Endless Mode (Survival)":
            st.error(f"💀 DEFEAT... Your credibility collapsed. You finished with a grand Survival Streak of **{st.session_state.endless_streak}**!")
        else:
            st.error("💀 DEFEAT... You got completely gaslit. Your credibility hit 0%.")
        
    if st.button("Play Again / Back to Lobby", use_container_width=True):
        st.session_state.game_started = False
        st.rerun()
    st.stop()

if st.session_state.strike_alert:
    alert_type, alert_msg = st.session_state.strike_alert
    if alert_type == "SUCCESS":
        st.success(alert_msg)
    else:
        st.error(alert_msg)
    st.session_state.strike_alert = None

st.markdown("### 💬 The Battle Feed")
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(f"<div class='user-bubble'><b>🧠 You:</b><br>{msg['text']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='ai-bubble'><b>🤥 Gaslighter:</b><br>{msg['text']}</div>", unsafe_allow_html=True)

st.write("---")
st.markdown("### 🕹️ Your Turn: Make Your Move")

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

if submit_action:
    if not user_argument.strip():
        st.warning("You can't just stare at them silently! Type a response.")
    else:
        st.session_state.processing_turn = True
        st.rerun()

if st.session_state.processing_turn:
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

    if not st.session_state.game_over:
        with st.spinner("🤥 The Gaslighter is writing a smug, flawed retort..."):
            new_ai_reply = generate_gaslight_response(user_argument)
            st.session_state.chat_history.append({"role": "ai", "text": new_ai_reply})
    
    st.session_state.processing_turn = False
    st.rerun()
