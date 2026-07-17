import os
import random
import json
import streamlit as st
from google import genai

# -------------------------------------------------------------------
# 1. INITIALIZATION & CONFIGURATION
# -------------------------------------------------------------------
st.set_page_config(
    page_title="The Socratic Gaslighter",
    page_icon="🤥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize the Gemini Client using Streamlit Secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error("API Initialization Error: Make sure GEMINI_API_KEY be defined in your Streamlit secrets.")
    st.stop()

ACTIVE_MODEL = 'gemini-3.1-flash-lite'

# --- LOGICAL DICTIONARY TIER MAPPING ---
LEVEL_1_FALLACIES = {
    "Strawman": "Twisting/oversimplifying an argument to knock it down.",
    "Ad Hominem": "Launching a personal attack on character or tone.",
    "Circular Reasoning": "An argument that uses its conclusion as its premise.",
    "Moving the Goalposts": "Shifting the criteria of proof after it has been met.",
    "False Dilemma": "Presenting a complex situation as a simple binary choice.",
    "Slippery Slope": "Arguing without evidence that one step leads to catastrophe."
}

LEVEL_2_FALLACIES = {
    "Red Herring": "Introducing an irrelevant issue to distract from the topic.",
    "Appeal to Fear": "Using scare tactics or exaggerating real danger.",
    "Bandwagon": "Claiming an idea is true because a crowd believes it.",
    "Hasty Generalization": "Jumping to conclusions based on isolated evidence."
}

ALL_FALLACIES = {**LEVEL_1_FALLACIES, **LEVEL_2_FALLACIES}

# --- UNBREAKABLE LOGICAL SCENARIOS ---
SCENARIOS = {
    1: [
        {"fallacies": ["Strawman"], "core_logic": "You say we should monitor bird behavior, but they twist it into claiming you want to execute all domestic pets to secure the airspace."},
        {"fallacies": ["Ad Hominem"], "core_logic": "You bring up scientific data, but they claim data is a crutch for people with small brains who can't handle pure instinct."},
        {"fallacies": ["Circular Reasoning"], "core_logic": "The government drones are flawless because they were built by the Bureau of Flawless Design, which only designs things flawlessly."},
        {"fallacies": ["Moving the Goalposts"], "core_logic": "You proved birds have organic hearts? Well, that doesn't count. Prove every single atom of their feathers wasn't manufactured in an underground lab."},
        {"fallacies": ["False Dilemma"], "core_logic": "Either you completely agree that birds are surveillance drones, or you hate national security and want chaos."},
        {"fallacies": ["Slippery Slope"], "core_logic": "If we let people feed pigeons in public parks today, by tomorrow the surveillance grid collapses, society fails, and humanity goes extinct."}
    ],
    2: [
        {"fallacies": ["Red Herring"], "core_logic": "When asked about the mechanics of the cheese moon, they pivot to lecturing you about the history of cracker manufacturing in the late 1800s."},
        {"fallacies": ["Appeal to Fear"], "core_logic": "If you keep questioning the moon's dairy composition, the deep-space forces will mark your household for immediate cosmic reclamation."},
        {"fallacies": ["Bandwagon"], "core_logic": "Millions of truth-seekers online are actively buying cracker stocks right now. Are you claiming all of them are wrong while you are right?"},
        {"fallacies": ["Hasty Generalization"], "core_logic": "I saw a single white mouse look at the sky last night. This instantly proves the entire celestial lunar core is made of dairy products."}
    ],
    3: [
        {"fallacies": ["Ad Hominem", "Strawman"], "core_logic": "They claim your simple question could only come from a completely uneducated mind, and then twist your argument into an absurd stance."},
        {"fallacies": ["Slippery Slope", "False Dilemma"], "core_logic": "They give you a harsh ultimatum between two choices, claiming that choosing your way will instantly trigger a chain reaction destroying the planet."},
        {"fallacies": ["Circular Reasoning", "Appeal to Fear"], "core_logic": "The mothership is real because it says it is real on page 1, and if you don't accept it, terrifying things will happen to your family."},
        {"fallacies": ["Ad Hominem", "Strawman", "Slippery Slope"], "core_logic": "An ultimate combo: insulting your cognitive abilities, completely rewriting your premise into a joke, and warning it will destroy society."}
    ]
}

THESES = [
    "Birds aren't real; they are government surveillance drones tracking our hair density.",
    "The moon is made of premium Swiss cheese, and NASA is hiding the crackers.",
    "Trees are actually alien exhaust pipes filtering out invisible spaceship fuel.",
    "Sleep is a scam invented by mattress companies to steal 8 hours of our day.",
    "Gravity is a social construct invented by shoe companies to sell more footwear."
]

# -------------------------------------------------------------------
# 2. PERSISTENT SCOREBOARD
# -------------------------------------------------------------------
if "wins_classic" not in st.session_state: st.session_state.wins_classic = 0
if "wins_endless" not in st.session_state: st.session_state.wins_endless = 0
if "wins_championship" not in st.session_state: st.session_state.wins_championship = 0

if "game_started" not in st.session_state: st.session_state.game_started = False
if "game_mode" not in st.session_state: st.session_state.game_mode = "Classic Duel"
if "lobby_level" not in st.session_state: st.session_state.lobby_level = 1
if "language_mode" not in st.session_state: st.session_state.language_mode = "Pretentious Elite"

# Match states
if "player_hp" not in st.session_state: st.session_state.player_hp = 100
if "boss_hp" not in st.session_state: st.session_state.boss_hp = 100
if "current_thesis" not in st.session_state: st.session_state.current_thesis = ""
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "current_targets" not in st.session_state: st.session_state.current_targets = []
if "game_over" not in st.session_state: st.session_state.game_over = False
if "game_result" not in st.session_state: st.session_state.game_result = ""
if "battle_report" not in st.session_state: st.session_state.battle_report = None
if "championship_round" not in st.session_state: st.session_state.championship_round = 1
if "action_type" not in st.session_state: st.session_state.action_type = None

# -------------------------------------------------------------------
# 3. ENGINE MECHANICS
# -------------------------------------------------------------------
def get_active_tier():
    if st.session_state.game_mode == "3-Round Championship":
        return st.session_state.championship_round
    elif st.session_state.game_mode == "Endless Mode (Survival)":
        if st.session_state.wins_endless <= 5: return 1
        elif st.session_state.wins_endless <= 10: return 2
        else: return 3
    else:
        return st.session_state.lobby_level

def get_tier_title(tier):
    if tier == 1: return "Logical Rookie"
    if tier == 2: return "Debate Contender"
    return "Master Rhetorician"

CURRENT_TIER = get_active_tier()
CURRENT_TITLE = get_tier_title(CURRENT_TIER)
AVAILABLE_FALLACIES = LEVEL_1_FALLACIES if CURRENT_TIER == 1 else ALL_FALLACIES

def generate_dressed_gaslight(player_input=None):
    tier = CURRENT_TIER
    chosen = random.choice(SCENARIOS[tier])
    st.session_state.current_targets = chosen["fallacies"]
    
    context_clause = f"The player just argued: '{player_input}'" if player_input else "This is the match opening."
    
    language_instruction = "Use elegant, dense, high-vocabulary, academic, and highly pretentious English words."
    if st.session_state.language_mode == "Direct Cut":
        language_instruction = "Use extremely clear, basic, plain, and straightforward English words. Keep the sentence structure simple."

    prompt = f"""
    You are the 'Socratic Gaslighter', a deeply smug, patronizing debater defending the absurd thesis: "{st.session_state.current_thesis}".
    {context_clause}
    {language_instruction}
    
    Your next statement must sound organic, passive-aggressive, and condescending, executing this exact hidden logic:
    "{chosen['core_logic']}"
    
    CRITICAL CONSTRAINT:
    - Keep your total response short, snappy, and punchy. It MUST NOT exceed 50 words total!
    - Do NOT name or explicitly write out these fallback fallacy terms anywhere in your response text: {chosen['fallacies']}.
    """
    try:
        response = client.models.generate_content(model=ACTIVE_MODEL, contents=prompt)
        return response.text.strip()
    except:
        return f"Oh, typical. Your mental capacity has bottlenecked my processing grid."

def process_deflection(selected_choices, user_text):
    targets = st.session_state.current_targets
    is_correct = sorted(selected_choices) == sorted(targets)
    
    if CURRENT_TIER == 1: p_dmg, b_dmg = 25, 15
    elif CURRENT_TIER == 2: p_dmg, b_dmg = 20, 25
    else: p_dmg, b_dmg = 35, 35

    st.session_state.chat_history.append({"role": "user", "text": f"🛡️ [DEFLECT & ACCUSE: {', '.join(selected_choices)}] {user_text}"})

    if is_correct:
        st.session_state.boss_hp -= p_dmg
        if st.session_state.boss_hp <= 0:
            st.session_state.boss_hp = 0
            handle_match_victory()
        else:
            st.session_state.battle_report = ("SUCCESS", f"💥 **DIRECT HIT!** Parsed flawlessly! Dealt **{p_dmg} damage**!")
    else:
        st.session_state.player_hp -= b_dmg
        if st.session_state.player_hp <= 0:
            st.session_state.player_hp = 0
            st.session_state.game_over = True
            st.session_state.game_result = "LOSE"
            st.session_state.battle_report = ("FAIL", "❌ **SYSTEM COLLAPSE!** Your credibility hit 0%.")
        else:
            joined_targets = ", ".join(targets)
            st.session_state.battle_report = ("FAIL", f"❌ **FALSE ACCUSATION!** Took **{b_dmg} damage**! Hidden flaw: **{joined_targets}**.")

def handle_match_victory():
    if st.session_state.game_mode == "Classic Duel":
        st.session_state.wins_classic += 1
        st.session_state.game_over = True
        st.session_state.game_result = "WIN"
        
    elif st.session_state.game_mode == "3-Round Championship":
        if st.session_state.championship_round < 3:
            st.session_state.championship_round += 1
            reset_match_state(keep_history=False)
            st.session_state.battle_report = ("SUCCESS", f"🏆 **ROUND CONQUERED!** Advancing to Round {st.session_state.championship_round}! HP restored.")
        else:
            st.session_state.wins_championship += 1
            st.session_state.game_over = True
            st.session_state.game_result = "WIN"
            
    elif st.session_state.game_mode == "Endless Mode (Survival)":
        st.session_state.wins_endless += 1
        st.session_state.player_hp = min(100, st.session_state.player_hp + 30)
        reset_match_state(keep_history=False)
        st.session_state.battle_report = ("SUCCESS", f"💀 **OPPONENT DISMANTLED!** Current streak: {st.session_state.wins_endless}. Gained +30% HP!")

def reset_match_state(keep_history=False):
    st.session_state.boss_hp = 100
    st.session_state.current_thesis = random.choice(THESES)
    st.session_state.game_over = False
    if not keep_history:
        st.session_state.chat_history = []
    
    first_retort = generate_dressed_gaslight()
    st.session_state.chat_history.append({"role": "ai", "text": first_retort})

# -------------------------------------------------------------------
# 4. GLOBAL STYLING
# -------------------------------------------------------------------
st.markdown("""
<style>
    .stApp { background-color: #0A0B0E; color: #E2E8F0; }
    .game-box { background-color: #12141C; border: 2px solid #1E293B; border-radius: 12px; padding: 20px; margin-bottom: 15px; }
    .badge-l1 { background-color: #065F46; color: #34D399; padding: 4px 10px; border-radius: 20px; font-weight: bold; font-size: 13px; }
    .badge-l2 { background-color: #92400E; color: #FBBF24; padding: 4px 10px; border-radius: 20px; font-weight: bold; font-size: 13px; }
    .badge-l3 { background-color: #991B1B; color: #FCA5A5; padding: 4px 10px; border-radius: 20px; font-weight: bold; font-size: 13px; }
    .chat-user { background-color: #1A1D29; border-left: 4px solid #38BDF8; padding: 10px; border-radius: 6px; margin-bottom: 8px; font-size: 14px; }
    .chat-ai { background-color: #1E1525; border-left: 4px solid #F43F5E; padding: 10px; border-radius: 6px; margin-bottom: 8px; font-size: 14px; }
    .fallacy-text { color: #94A3B8; font-size: 11px; margin-top: -6px; margin-bottom: 6px; font-style: italic; line-height: 1.2; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# PAGE 1: DESCRIPTION & LOBBY PANEL
# -------------------------------------------------------------------
if not st.session_state.game_started:
    st.markdown("<h1 style='text-align: center; color: #F43F5E; font-weight:900;'>🤥 The Socratic Gaslighter</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8;'>Dismantle logical structures, track fallacy anomalies, and preserve your structural sanity.</p>", unsafe_allow_html=True)
    st.write("---")

    col_l, col_r = st.columns([2, 1])
    
    with col_l:
        st.markdown("### 🎮 Arena Configurations")
        mode_select = st.radio("Select Match Variant:", ["Classic Duel", "Endless Mode (Survival)", "3-Round Championship"], horizontal=True)
        
        if mode_select == "Classic Duel":
            st.info("🤺 **Classic Duel:** Fixed, standalone mental bout. Pick your target difficulty below.")
            selected_tier = st.slider("Select Match Level Target:", 1, 3, 1)
        elif mode_select == "Endless Mode (Survival)":
            st.warning("💀 **Survival Gauntlet:** Battle an endless loop of opponents. Difficulty scales automatically at streak 5 and 10!")
            selected_tier = 1
        else:
            st.success("🏆 **Championship Tournament:** Survive three consecutive rounds hard-scaled from Level 1 up to Level 3.")
            selected_tier = 1

        st.write("---")
        st.markdown("#### Choose Argument Premise")
        topic_pick = st.selectbox("Pick an absurd thesis to neutralize:", THESES)

    with col_r:
        st.markdown("<div class='game-box'>", unsafe_allow_html=True)
        st.markdown("### 💾 PROFILE HISTORIC SCORECARD")
        st.write(f"🤺 **Classic Duels Won:** `{st.session_state.wins_classic}`")
        st.write(f"💀 **Endless Current Streak:** `{st.session_state.wins_endless}`")
        st.write(f"🏆 **Championships Claimed:** `{st.session_state.wins_championship}`")
        st.markdown("</div>", unsafe_allow_html=True)
        
    if st.button("🚨 ACCESS COMBAT INTERFACE PANEL", use_container_width=True):
        st.session_state.game_mode = mode_select
        st.session_state.lobby_level = selected_tier
        st.session_state.game_started = True
        st.session_state.player_hp = 100
        st.session_state.battle_report = None
        if mode_select == "3-Round Championship":
            st.session_state.championship_round = 1
        reset_match_state(keep_history=False)
        st.rerun()
    st.stop()

# -------------------------------------------------------------------
# PAGE 2: COMBAT ARENA
# -------------------------------------------------------------------
with st.sidebar:
    st.markdown("<h2 style='color:#F43F5E; text-align:center;'>🤥 Status Display</h2>", unsafe_allow_html=True)
    st.write("---")
    
    st.markdown(f"🟢 **Your Credibility:** `{st.session_state.player_hp}%`")
    st.progress(st.session_state.player_hp / 100)
    
    st.markdown(f"🔴 **Gaslighter Stability:** `{st.session_state.boss_hp}%`")
    st.progress(st.session_state.boss_hp / 100)
    
    st.write("---")
    st.markdown("### 📊 Active Match Info")
    badge_style = "badge-l1" if CURRENT_TIER == 1 else ("badge-l2" if CURRENT_TIER == 2 else "badge-l3")
    st.markdown(f"Variant: <span class='{badge_style}'>{st.session_state.game_mode}</span>", unsafe_allow_html=True)
    st.markdown(f"Rank-Tier: **{CURRENT_TITLE} (Level {CURRENT_TIER})**")
    
    st.write("---")
    st.session_state.language_mode = st.selectbox("Diction Profile:", ["Pretentious Elite", "Direct Cut"])
    
    if st.button("🏳️ Abandon Match & Return to Lobby", use_container_width=True):
        st.session_state.game_started = False
        st.rerun()

st.markdown(f"### 🎯 Target Thesis: *\"{st.session_state.current_thesis}\"*")

if st.session_state.battle_report:
    rep_type, rep_msg = st.session_state.battle_report
    if rep_type == "SUCCESS": st.success(rep_msg)
    else: st.error(rep_msg)
    st.session_state.battle_report = None

if st.session_state.game_over:
    if st.session_state.game_result == "WIN":
        st.balloons()
        st.success("🏆 **VICTORY CONQUERED!** The opponent's rhetoric has been pulverized.")
    else:
        st.error("💀 **DEFEAT.** You got completely turned around and gaslit.")
        if st.session_state.game_mode == "Endless Mode (Survival)":
            st.session_state.wins_endless = 0 
        
    if st.button("Return to Lobby Setup Panel", use_container_width=True):
        st.session_state.game_started = False
        st.rerun()
    st.stop()

# 50/50 Split Layout
col_feed, col_matrix = st.columns([1, 1])

with col_feed:
    st.markdown("### 💬 Arena Feed Log")
    with st.container(height=450):
        for msg in st.session_state.chat_history:
            class_name = "chat-user" if msg["role"] == "user" else "chat-ai"
            speaker = "🧠 You" if msg["role"] == "user" else "🤥 Gaslighter"
            st.markdown(f"<div class='{class_name}'><b>{speaker}:</b><br>{msg['text']}</div>", unsafe_allow_html=True)

with col_matrix:
    st.markdown("### 🕹️ Action & Strategy Matrix")
    
    with st.container(height=450):
        user_argument = st.text_input("Your Counter-Argument Stance:", placeholder="Type your argument line here...")
        
        st.markdown("---")
        if CURRENT_TIER == 3:
            st.markdown("<span style='color:#EF4444; font-size:12px; font-weight:bold;'>⚠️ MEMORY CHALLENGE ACTIVE (Definitions Blacked Out)</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='color:#94A3B8; font-size:12px;'>Select checkboxes only if accusing:</span>", unsafe_allow_html=True)
        
        choices_status = {}
        f_keys = sorted(list(AVAILABLE_FALLACIES.keys()))
        
        # FIXED: Distributed checkboxes into a 2-column grid layout to eliminate scrolling
        grid_col1, grid_col2 = st.columns(2)
        
        for idx, key in enumerate(f_keys):
            target_col = grid_col1 if idx % 2 == 0 else grid_col2
            with target_col:
                choices_status[key] = st.checkbox(f"**{key}**", key=f"chk_{key}")
                if CURRENT_TIER != 3:
                    st.markdown(f"<div class='fallacy-text'>{AVAILABLE_FALLACIES[key]}</div>", unsafe_allow_html=True)
        
        st.write("")
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            submit_accuse = st.button("💥 DEFLECT & ACCUSE", use_container_width=True)
        with c_btn2:
            # BRANDING FIXED: Changed from weak "Just Converse" to aggressive "Fire Back Argument"
            submit_talk = st.button("🔥 FIRE BACK ARGUMENT", use_container_width=True)

# Handle Submissions
if submit_accuse:
    active_selections = [k for k, v in choices_status.items() if v]
    if not user_argument.strip():
        st.warning("Provide a written argument statement alongside your tactical targets!")
    elif not active_selections:
        st.warning("Select at least one active fallacy checkbox target to launch an accusation!")
    else:
        st.session_state.action_type = ("ACCUSE", active_selections, user_argument)
        st.rerun()

if submit_talk:
    if not user_argument.strip():
        st.warning("Provide a written argument to hit back!")
    else:
        st.session_state.action_type = ("TALK", [], user_argument)
        st.rerun()

# Run Backend Turns
if st.session_state.action_type:
    act_mode, selections, txt = st.session_state.action_type
    
    if act_mode == "ACCUSE":
        process_deflection(selections, txt)
    else:
        st.session_state.chat_history.append({"role": "user", "text": f"🔥 {txt}"})
        st.session_state.battle_report = ("SUCCESS", "📝 **Argument landed.** Conversation continues without damage calculations.")
        
    if not st.session_state.game_over and st.session_state.boss_hp > 0:
        next_retort = generate_dressed_gaslight(player_input=txt)
        st.session_state.chat_history.append({"role": "ai", "text": next_retort})
        
    st.session_state.action_type = None
    st.rerun()
