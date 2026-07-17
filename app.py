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
    initial_sidebar_state="expanded", # Keep sidebar open for real-time tracking
)

# Initialize the Gemini Client using Streamlit Secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error("API Initialization Error: Make sure GEMINI_API_KEY is defined in your Streamlit secrets.")
    st.stop()

ACTIVE_MODEL = 'gemini-3.1-flash-lite'

# --- LOGICAL DICTIONARY TIER MAPPING ---
LEVEL_1_FALLACIES = {
    "Strawman": "Twisting, oversimplifying, or completely changing your opponent's argument to make it easier to knock down.",
    "Ad Hominem": "Bypassing the logic entirely to launch a personal attack on your opponent's intelligence, character, or tone.",
    "Circular Reasoning": "An argument that takes its own conclusion as its starting premise. (e.g., 'X is true because X is true').",
    "Moving the Goalposts": "An underhanded tactic where the criteria for a victory or proof is suddenly shifted after the original target was met.",
    "False Dilemma": "Presenting a complex situation as an oversimplified black-and-white choice between two extreme options.",
    "Slippery Slope": "Arguing without evidence that a small initial step will instantly cause a catastrophic, uncontrollable domino effect."
}

LEVEL_2_FALLACIES = {
    "Red Herring": "Introducing an entirely irrelevant side-issue to distract from the actual topic being debated.",
    "Appeal to Fear": "Using scare tactics, warnings of dark doom, or exaggerating danger to win an argument instead of using evidence.",
    "Bandwagon": "Claiming that an argument or idea must be true simply because a huge crowd of people currently believe it.",
    "Hasty Generalization": "Jumping to a massive, sweeping conclusion based on a tiny, single piece of unverified or isolated evidence."
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
# 2. PERSISTENT SEPARATED SCOREBOARD
# -------------------------------------------------------------------
if "wins_classic" not in st.session_state: st.session_state.wins_classic = 0
if "wins_endless" not in st.session_state: st.session_state.wins_endless = 0
if "wins_championship" not in st.session_state: st.session_state.wins_championship = 0

if "game_started" not in st.session_state: st.session_state.game_started = False
if "game_mode" not in st.session_state: st.session_state.game_mode = "Classic Duel"
if "lobby_level" not in st.session_state: st.session_state.lobby_level = 1
if "language_mode" not in st.session_state: st.session_state.language_mode = "Default"

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
if "processing" not in st.session_state: st.session_state.processing = False

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
    
    language_instruction = "Use elegant, dense, high-vocabulary, academic, and slightly pretentious English words."
    if st.session_state.language_mode == "Simple English":
        language_instruction = "Use extremely clear, basic, straightforward English words. Avoid complex vocabulary or long metaphors so that non-native speakers can follow easily."

    prompt = f"""
    You are the 'Socratic Gaslighter', a deeply smug, patronizing debater defending the absurd thesis: "{st.session_state.current_thesis}".
    {context_clause}
    {language_instruction}
    
    Your next statement must be written to sound organic, passive-aggressive, and condescending, but behind the scenes it MUST execute this exact logic:
    "{chosen['core_logic']}"
    
    CRITICAL INSTRUCTIONS:
    - Keep your total response short (2 to 4 sentences max).
    - Do NOT name or explicitly write out these fallback terms anywhere in your output: {chosen['fallacies']}. 
    """
    try:
        response = client.models.generate_content(model=ACTIVE_MODEL, contents=prompt)
        return response.text.strip()
    except:
        return f"Oh, typical. Your response framework has jammed my logic module. (Template logic: {chosen['core_logic']})"

def process_deflection(selected_choices, user_text):
    targets = st.session_state.current_targets
    is_correct = sorted(selected_choices) == sorted(targets)
    
    if CURRENT_TIER == 1: p_dmg, b_dmg = 25, 15
    elif CURRENT_TIER == 2: p_dmg, b_dmg = 20, 25
    else: p_dmg, b_dmg = 35, 35

    st.session_state.chat_history.append({"role": "user", "text": f"🛡️ [DEFLECT ATTEMPT: {', '.join(selected_choices)}] {user_text}"})

    if is_correct:
        st.session_state.boss_hp -= p_dmg
        if st.session_state.boss_hp <= 0:
            st.session_state.boss_hp = 0
            handle_match_victory()
        else:
            st.session_state.battle_report = ("SUCCESS", f"💥 **DIRECT HIT!** You parsed the logic block perfectly. Dealt **{p_dmg} damage**!")
    else:
        st.session_state.player_hp -= b_dmg
        if st.session_state.player_hp <= 0:
            st.session_state.player_hp = 0
            st.session_state.game_over = True
            st.session_state.game_result = "LOSE"
            st.session_state.battle_report = ("FAIL", "❌ **SYSTEM COLLAPSE!** Your credibility hit 0%.")
        else:
            joined_targets = ", ".join(targets)
            st.session_state.battle_report = ("FAIL", f"❌ **FALSE ACCUSATION!** You sustained **{b_dmg} damage**! The actual hidden flaw was **{joined_targets}**.")

def handle_match_victory():
    if st.session_state.game_mode == "Classic Duel":
        st.session_state.wins_classic += 1
        st.session_state.game_over = True
        st.session_state.game_result = "WIN"
        
    elif st.session_state.game_mode == "3-Round Championship":
        if st.session_state.championship_round < 3:
            st.session_state.championship_round += 1
            reset_match_state(keep_history=False)
            st.session_state.battle_report = ("SUCCESS", f"🏆 **ROUND CONQUERED!** Advancing to Tournament Round {st.session_state.championship_round}! Your HP has been reset to 100%.")
        else:
            st.session_state.wins_championship += 1
            st.session_state.game_over = True
            st.session_state.game_result = "WIN"
            
    elif st.session_state.game_mode == "Endless Mode (Survival)":
        st.session_state.wins_endless += 1
        st.session_state.player_hp = min(100, st.session_state.player_hp + 30)
        reset_match_state(keep_history=False)
        st.session_state.battle_report = ("SUCCESS", f"💀 **OPPONENT DISMANTLED!** Current survival streak is now {st.session_state.wins_endless}. Credibility patched (+30% HP)!")

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
    .badge-l1 { background-color: #065F46; color: #34D399; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 14px; }
    .badge-l2 { background-color: #92400E; color: #FBBF24; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 14px; }
    .badge-l3 { background-color: #991B1B; color: #FCA5A5; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 14px; }
    .chat-user { background-color: #1A1D29; border-left: 4px solid #38BDF8; padding: 12px; border-radius: 6px; margin-bottom: 10px; }
    .chat-ai { background-color: #1E1525; border-left: 4px solid #F43F5E; padding: 12px; border-radius: 6px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# PAGE 1: THE DESCRIPTION & LOBBY PANEL
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
            st.info("辨 <b>Classic Duel:</b> Fixed, standalone mental bout. Pick your target difficulty below.")
            selected_tier = st.slider("Select Match Level Target:", 1, 3, 1)
        elif mode_select == "Endless Mode (Survival)":
            st.warning("💀 <b>Survival Gauntlet:</b> Battle an endless loop of opponents. Fallacy difficulty triggers escalation automatically at 5 and 10 match wins!")
            selected_tier = 1
        else:
            st.success("🏆 <b>Championship Tournament:</b> Survive three consecutive rounds hard-scaled from Level 1 straight up to Level 3.")
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
# PAGE 2: CLEAN ACTIVE PLAYING ARENA (LOBBY IS COMPLETELY HIDDEN)
# -------------------------------------------------------------------
# PERSISTENT STATS SIDEBAR (Guarantees zero scrolling required to see health/stats)
with st.sidebar:
    st.markdown("<h2 style='color:#F43F5E; text-align:center;'>🤥 Status Display</h2>", unsafe_allow_html=True)
    st.write("---")
    
    # Live Health Gauges
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
    # Real-Time UI Language Switch
    st.session_state.language_mode = st.selectbox("Language Dialect Variant:", ["Default", "Simple English"])
    
    if st.button("🏳️ Abandon Match & Return to Lobby", use_container_width=True):
        st.session_state.game_started = False
        st.rerun()

# --- MAIN ARENA ROW HEADER (STICKY POPUPS FIRST) ---
st.markdown(f"### 🎯 Target Thesis: *\"{st.session_state.current_thesis}\"*")

# CRITICAL BATTLE REPORT AT TOP - No more scrolling down to check turn effects!
if st.session_state.battle_report:
    rep_type, rep_msg = st.session_state.battle_report
    if rep_type == "SUCCESS":
        st.success(rep_msg)
    else:
        st.error(rep_msg)
    st.session_state.battle_report = None

# Game-Over Processing Overlay Interceptor
if st.session_state.game_over:
    if st.session_state.game_result == "WIN":
        st.balloons()
        st.success("🏆 **VICTORY CONQUERED!** The opponent's rhetoric has been pulverized. Your profile scorecard records have updated.")
    else:
        st.error("💀 **DEFEAT.** You got completely turned around and gaslit.")
        if st.session_state.game_mode == "Endless Mode (Survival)":
            st.session_state.wins_endless = 0 # Reset streak on complete structural collapse
        
    if st.button("Return to Lobby Setup Panel", use_container_width=True):
        st.session_state.game_started = False
        st.rerun()
    st.stop()

# Split Layout: Feed Log Left, Tactical Control Matrix Right
col_feed, col_matrix = st.columns([3, 2])

with col_feed:
    st.markdown("### 💬 Arena Feed Log")
    # Reversed display sequence option keeps latest text visible, or default layout rendering
    for msg in st.session_state.chat_history:
        class_name = "chat-user" if msg["role"] == "user" else "chat-ai"
        speaker = "🧠 You" if msg["role"] == "user" else "🤥 Gaslighter"
        st.markdown(f"<div class='{class_name}'><b>{speaker}:</b><br>{msg['text']}</div>", unsafe_allow_html=True)

with col_matrix:
    st.markdown("### 🕹️ Counter-Strike Matrix")
    if CURRENT_TIER == 3:
        st.markdown("<div style='background-color:#450A0A; padding:10px; border-left:4px solid #EF4444; border-radius:4px; font-weight:bold; color:#FCA5A5;'>⚠️ MEMORY CHALLENGE ACTIVE: Fallacy definitions are blacked out! Select ALL active fallacies to avoid critical damage!</div>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color:#94A3B8; font-size:13px;'>Check the box for the fallback tactic being run below to load your strike package.</p>", unsafe_allow_html=True)

    with st.form(key="combat_input_form", clear_on_submit=True):
        user_argument = st.text_input("Provide your argument stance output:", placeholder="Type your counter-argument response here...")
        
        choices_status = {}
        f_keys = sorted(list(AVAILABLE_FALLACIES.keys()))
        
        for key in f_keys:
            if CURRENT_TIER == 3:
                # Level 3 Memory blackout mode
                choices_status[key] = st.checkbox(f"**{key}**")
            else:
                # Level 1 and 2 descriptive structural layout help
                choices_status[key] = st.checkbox(f"**{key}**", help=AVAILABLE_FALLACIES[key])
                st.markdown(f"<p style='color:#94A3B8; font-size:12px; margin-top:-10px; margin-left:28px; font-style:italic;'>{AVAILABLE_FALLACIES[key]}</p>", unsafe_allow_html=True)
                    
        submit_turn = st.form_submit_button("💥 ENGAGE COUNTER-DEFLECTION ACTION", use_container_width=True)

if submit_turn:
    active_selections = [k for k, v in choices_status.items() if v]
    if not user_argument.strip():
        st.warning("Provide a basic written statement alongside your checkbox targets!")
    elif not active_selections:
        st.warning("Load at least one targeted tactic onto the deflection rack!")
    else:
        st.session_state.processing = True
        st.rerun()

# Async Engine Handling State
if st.session_state.processing:
    active_selections = [k for k, v in choices_status.items() if v]
    process_deflection(active_selections, user_argument)
    
    if not st.session_state.game_over and st.session_state.boss_hp > 0:
        next_retort = generate_dressed_gaslight(player_input=user_argument)
        st.session_state.chat_history.append({"role": "ai", "text": next_retort})
        
    st.session_state.processing = False
    st.rerun()
