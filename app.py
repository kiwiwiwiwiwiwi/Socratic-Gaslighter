import os
import random
import json
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

# EXPANDED FALLACY DICTIONARY (Now 12 options for maximum chaos)
FALLACIES = {
    "Strawman": "Exaggerating, oversimplifying, or misrepresenting your argument to make it easier to attack.",
    "Ad Hominem": "Attacking your character, intelligence, or tone instead of addressing your logic.",
    "Circular Reasoning": "Proving a point by just restating the premise (e.g., 'I am right because I say I'm right').",
    "Moving the Goalposts": "Changing the criteria for 'winning' or 'proving a point' after you've already met the original demand.",
    "False Dilemma": "Forcing you to choose between two extreme options when multiple other valid choices exist.",
    "Slippery Slope": "Claiming that one tiny, harmless action will inevitably trigger a massive, ridiculous disaster chain.",
    "Appeal to Ignorance": "Arguing that a claim must be true because it hasn't yet been proven false (or vice-versa).",
    "False Cause": "Claiming that because Event B happened after Event A, Event A must have caused Event B.",
    "Bandwagon Appeal": "Arguing that a claim is correct simply because a large group of people believe it.",
    "Tu Quoque": "Avoiding criticism by turning it back on the accuser (e.g., 'You used a fallacy too!').",
    "Anecdotal Evidence": "Using an isolated, personal, or unverified story instead of a sound scientific argument.",
    "Special Pleading": "Applying double standards or inventing random exceptions when your logic falls flat."
}

# Persistent Trophy Room / Medals Setup
if "trophy_cabinet" not in st.session_state:
    st.session_state.trophy_cabinet = {
        "logical_paragon": 0,    # Cleared a match with a perfect run
        "championship_gold": 0,  # Won the 3-Round Tournament
        "gaslight_survivor": 0,  # Won a classic duel
        "endless_defender": 0    # Defeated 5+ enemies in survival
    }

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
if "perfect_run" not in st.session_state:
    st.session_state.perfect_run = True

ACTIVE_MODEL = 'gemini-3.1-flash-lite'

# -------------------------------------------------------------------
# GLOBAL SIDEBAR (SHOWS PERSISTENT MEDALS & CHEAT SHEET)
# -------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🏆 YOUR TROPHY ROOM")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.metric("✨ Paragons", st.session_state.trophy_cabinet["logical_paragon"])
        st.metric("🥇 Champs", st.session_state.trophy_cabinet["championship_gold"])
    with col_t2:
        st.metric("⚔️ Survivors", st.session_state.trophy_cabinet["gaslight_survivor"])
        st.metric("🛡️ Defenders", st.session_state.trophy_cabinet["endless_defender"])
    
    st.write("---")
    st.markdown("### 📖 Fallacy Cheat Sheet")
    st.write("Keep these definitions close during your debate:")
    for key, val in FALLACIES.items():
        st.markdown(f"**• {key}**:\n*{val}*")

# -------------------------------------------------------------------
# 2. HELPER FUNCTIONS
# -------------------------------------------------------------------
def trigger_victory_rain():
    """Rains triumph emojis down the screen instead of basic corporate balloons."""
    st.html("""
    <script>
    const doc = window.parent.document;
    if (!doc.getElementById('rhetorical-rain')) {
        const style = doc.createElement('style');
        style.id = 'rhetorical-rain';
        style.innerHTML = `
            @keyframes fall {
                0% { transform: translateY(-10vh) rotate(0deg); opacity: 1; }
                100% { transform: translateY(110vh) rotate(360deg); opacity: 0; }
            }
            .emoji-drop {
                position: fixed; top: -5vh; font-size: 2rem;
                animation: fall 3s linear forwards; z-index: 99999; pointer-events: none;
            }
        `;
        doc.head.appendChild(style);
        
        const emojis = ['💥', '🏆', '🧠', '🤥', '👑'];
        for (let i = 0; i < 40; i++) {
            setTimeout(() => {
                const drop = doc.createElement('div');
                drop.className = 'emoji-drop';
                drop.innerText = emojis[Math.floor(Math.random() * emojis.length)];
                drop.style.left = Math.random() * 100 + 'vw';
                drop.style.animationDuration = (Math.random() * 2 + 2) + 's';
                doc.body.appendChild(drop);
                setTimeout(() => drop.remove(), 4000);
            }, i * 150);
        }
    }
    </script>
    """)

def generate_gaslight_response(player_argument):
    chosen_fallacy = random.choice(list(FALLACIES.keys()))
    st.session_state.current_fallacy = chosen_fallacy

    difficulty_modifier = ""
    if st.session_state.game_mode == "3-Round Championship":
        if st.session_state.championship_round == 1:
            difficulty_modifier = "Keep the fallacy simple and easy to spot."
        elif st.session_state.championship_round == 2:
            difficulty_modifier = "Make the fallacy moderately tricky and hard to spot."
        elif st.session_state.championship_round == 3:
            difficulty_modifier = "Make the fallacy incredibly subtle and deeply woven into your argument."

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
    You are a deeply bored, nonchalant logic referee.
    Gaslighter said: "{last_ai_response}"
    Player objects with: **{selected_fallacy}**

    First word must be 'VALID' or 'INVALID'.
    Then, deliver a 1-sentence verdict. Talk directly TO the player. Refer to the opponent as "the Gaslighter".
    - If VALID: Roast the Gaslighter's logic.
    - If INVALID: Roast the player for being wrong.
    CRITICAL: Your entire explanation MUST be ONE short sentence (under 15 words). No paragraphs! No yapping! Make it snappy.
    """
    
    try:
        verdict_resp = client.models.generate_content(model=ACTIVE_MODEL, contents=judge_prompt).text.strip()
        is_valid = verdict_resp.upper().startswith("VALID")
        explanation = verdict_resp.replace("VALID", "").replace("INVALID", "").strip(" :-,")
    except:
        is_valid = (selected_fallacy == st.session_state.current_fallacy)
        explanation = f"Look, I'm too tired for this. The hidden target was {st.session_state.current_fallacy}. Deal with it."

    if is_valid:
        damage = 34
        if st.session_state.game_mode == "3-Round Championship" and st.session_state.championship_round == 3:
            damage = 25

        st.session_state.ai_hp -= damage
        if st.session_state.ai_hp <= 0:
            st.session_state.ai_hp = 0
            
            # Match Won - Save Medals in Session Cache
            if st.session_state.perfect_run:
                st.session_state.trophy_cabinet["logical_paragon"] += 1
            
            if st.session_state.game_mode == "Endless Mode (Survival)":
                start_next_endless_opponent()
                if st.session_state.endless_streak >= 5:
                    st.session_state.trophy_cabinet["endless_defender"] += 1
                st.session_state.strike_alert = ("SUCCESS", f"💥 CRITICAL SUCCESS! You defeated the Gaslighter! Current Streak: {st.session_state.endless_streak}. Credibility partially restored (+30% HP)!")
            elif st.session_state.game_mode == "3-Round Championship" and st.session_state.championship_round < 3:
                advance_championship_round()
                st.session_state.strike_alert = ("SUCCESS", f"💥 ROUND WON! You conquered Round {st.session_state.championship_round-1}. Prepare for the next opponent!")
            else:
                # Big Victory!
                st.session_state.game_over = True
                st.session_state.game_result = "WIN"
                if st.session_state.game_mode == "3-Round Championship":
                    st.session_state.trophy_cabinet["championship_gold"] += 1
                else:
                    st.session_state.trophy_cabinet["gaslight_survivor"] += 1
                
                st.session_state.chat_history.append({"role": "ai", "text": f"💥 [FATAL ERROR] {generate_losing_line()}"})
        else:
            st.session_state.strike_alert = ("SUCCESS", f"💥 **OBJECTION ALLOWED!**\n\n*📣 Referee:* {explanation}")
        st.session_state.current_fallacy = "" 
    else:
        st.session_state.perfect_run = False
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
            f"❌ **FALSE ACCUSATION!** (-{penalty}% HP)\n\n*📣 Referee:* {explanation}"
        )

# -------------------------------------------------------------------
# 3. CUSTOM STYLING & UI
# -------------------------------------------------------------------
st.markdown("""
<style>
    .stApp { background-color: #0B0C10; }
    .stAlert { border-radius: 8px !important; border: 1px solid #1f2937 !important; }
    .debate-title { text-align: center; color: #FF4B4B; font-weight: 800; margin-bottom: 0px;}
    .user-bubble { background-color: #0E1117; border: 2px solid #00F0FF; padding: 15px; border-radius: 10px; margin-bottom: 10px; color: #E0E0E0; }
    .ai-bubble { background-color: #0E1117; border: 2px solid #FF007F; padding: 15px; border-radius: 10px; margin-bottom: 10px; color: #E0E0E0; }
    .mode-badge { background-color: #1E1E2E; border: 1px solid #FFD700; padding: 5px 12px; border-radius: 15px; font-weight: bold; color: #FFD700; text-align: center; }
    .achievement-box { background-color: #111827; border: 2px dashed #FFD700; padding: 15px; border-radius: 8px; text-align: center; margin-top: 15px; }
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
    3. **Call Them Out**: Your job is to select the exact fallacy they committed from your toolkit and execute your counter-argument.
    
    #### ⚡ The Stakes:
    * **Spotting a Fallacy Right**: The arena Referee will roast the Gaslighter, damaging their credibility score. Bring it to 0% to collapse their logical system entirely!
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
    st.markdown("""
    <div style='text-align: center; background-color: #0E1624; border: 1px solid #1E3A8A; color: #60A5FA; padding: 15px; border-radius: 8px; margin-bottom: 20px; font-size: 14px;'>
        🚨 <b> Tap the tiny <b>chevron/arrow icon (&gt;)</b> in the upper-left corner of your screen to open your persistent <b>Trophy Cabinet</b> and <b>Cheat Sheet</b>!
    </div>
    """, unsafe_allow_html=True)
    
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
        st.session_state.perfect_run = True
        
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
    player_color = "🟢" if st.session_state.player_hp > 50 else ("🟡" if st.session_state.player_hp > 25 else "🔴")
    st.markdown(f"{player_color} **Your Credibility:** {st.session_state.player_hp}%")
    st.progress(st.session_state.player_hp / 100)
with col2:
    ai_color = "🟢" if st.session_state.ai_hp > 50 else ("🟡" if st.session_state.ai_hp > 25 else "🔴")
    st.markdown(f"{ai_color} **Gaslighter's Credibility:** {st.session_state.ai_hp}%")
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
        trigger_victory_rain()
        
        st.markdown("""
        <div style='text-align: center; border: 3px solid #00F0FF; padding: 25px; border-radius: 15px; background: linear-gradient(135deg, #0E1117, #1E1E2E); margin-bottom: 25px;'>
            <h1 style='color: #00F0FF; margin: 0; font-size: 40px; font-weight: 900; letter-spacing: 2px;'>⚡ TOTAL SYSTEM DEMOLITION ⚡</h1>
            <p style='color: #aaa; font-style: italic; margin-top: 10px;'>The Gaslighter's credibility matrix has completely collapsed under the weight of objective truth.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='achievement-box'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #FFD700; margin-top: 0;'>🎖️ DEBATE OVERVIEW & MEDALS</h3>", unsafe_allow_html=True)
        
        if st.session_state.perfect_run:
            st.markdown("<p style='font-size: 18px;'>✨ <b>[LOGICAL PARAGON]</b> - You cleared the arena without a single false accusation. Medal added to sidebar cabinet!</p>", unsafe_allow_html=True)
            
        if st.session_state.game_mode == "3-Round Championship":
            st.markdown("<p style='font-size: 18px;'>🥇 <b>[DEBATE MASTERMIND]</b> - Conquered all difficulty tiers and won the Championship Gold!</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='font-size: 18px;'>⚔️ <b>[GASLIGHT SURVIVOR]</b> - Brought truth to a psychological projection contest and stood victorious.</p>", unsafe_allow_html=True)
            
        st.markdown("</div><br>", unsafe_allow_html=True)
    else:
        if st.session_state.game_mode == "Endless Mode (Survival)":
            st.error(f"💀 DEFEAT... Your credibility collapsed. You finished with a grand Survival Streak of **{st.session_state.endless_streak}**!")
            if st.session_state.endless_streak >= 5:
                st.markdown("<div class='achievement-box'>🎖️ <b>RHETORICAL ACHIEVEMENT UNLOCKED</b><br>🛡️ <b>[ENDLESS DEFENDER]</b> - Survived 5+ separate iterations of structural gaslighting waves!</div><br>", unsafe_allow_html=True)
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
            "Want to object?",
            ["-- Don't Object, Just Argue Normal --"] + sorted(list(FALLACIES.keys())),
            disabled=st.session_state.processing_turn
        )
        st.caption("*Need help? Open the sidebar in the top-left corner to view your persistent cabinet and Cheat Sheet.*")
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
            st.session_state.perfect_run = False
            st.session_state.player_hp -= 10
            if st.session_state.player_hp <= 0:
                st.session_state.player_hp = 0
                st.session_state.game_over = True
                st.session_state.game_result = "LOSE"
            
            st.session_state.chat_history.append({"role": "user", "text": user_argument})
            
            ref_yells = [
                "Are you just going to let them talk to you like that? Call a fallacy!",
                "Boring. You're just arguing in circles. Point out the flaw!",
                "I'm falling asleep here. Use your cheat sheet or get off the stage.",
                "You completely ignored their fallacy. Deducting points for wasting my time."
            ]
            st.session_state.strike_alert = (
                "FAIL", 
                f"⚠️ **MISSED OPPORTUNITY!** (-10% HP)\n\n*📣 Referee:* {random.choice(ref_yells)}"
            )
        else:
            st.session_state.chat_history.append({"role": "user", "text": f"🚨 [OBJECTION: {selected_objection}] {user_argument}"})
            judge_objection(selected_objection)

    if not st.session_state.game_over:
        with st.spinner("🤥 The Gaslighter is writing a smug, flawed retort..."):
            new_ai_reply = generate_gaslight_response(user_argument)
            st.session_state.chat_history.append({"role": "ai", "text": new_ai_reply})
    
    st.session_state.processing_turn = False
    st.rerun()
