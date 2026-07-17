import os
import random
import json
import streamlit as st
from google import genai

# -------------------------------------------------------------------
# 1. INITIALIZATION & CONFIGURATION
# -------------------------------------------------------------------
st.set_page_config(
    page_title="Gaslight Deflector: Arena of Logic",
    page_icon="🧠",
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

ACTIVE_MODEL = 'gemini-3.1-flash-lite'

# --- THE AIRTIGHT FALLACY DEFINITIONS ---
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

# Combine for Level 2/3 availability
ALL_FALLACIES = {**LEVEL_1_FALLACIES, **LEVEL_2_FALLACIES}

# --- ROCK-SOLID ENCODED SCENARIOS ---
# These act as the unbreakable logical templates. The game selects one dynamically.
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
# 2. PERSISTENT BROWSER PROGRESS (SESSION STORAGE SIMULATION)
# -------------------------------------------------------------------
# Because we check and don't overwrite these values, progress stays active for the whole Chrome visit.
if "global_wins" not in st.session_state:
    st.session_state.global_wins = 0
if "game_started" not in st.session_state:
    st.session_state.game_started = False
if "game_mode" not in st.session_state:
    st.session_state.game_mode = "Classic Duel"
if "lobby_level" not in st.session_state:
    st.session_state.lobby_level = 1

# Reset variables for individual match loops
if "player_hp" not in st.session_state:
    st.session_state.player_hp = 100
if "boss_hp" not in st.session_state:
    st.session_state.boss_hp = 100
if "current_thesis" not in st.session_state:
    st.session_state.current_thesis = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_targets" not in st.session_state:
    st.session_state.current_targets = []
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "game_result" not in st.session_state:
    st.session_state.game_result = ""
if "battle_report" not in st.session_state:
    st.session_state.battle_report = None
if "championship_round" not in st.session_state:
    st.session_state.championship_round = 1
if "processing" not in st.session_state:
    st.session_state.processing = False

# -------------------------------------------------------------------
# 3. DYNAMIC LEVEL DETERMINATION LOGIC
# -------------------------------------------------------------------
def get_active_tier():
    """Determines the current logical tier based on game mode and session progress."""
    if st.session_state.game_mode == "3-Round Championship":
        return st.session_state.championship_round
    elif st.session_state.game_mode == "Endless Mode (Survival)":
        if st.session_state.global_wins <= 5:
            return 1
        elif st.session_state.global_wins <= 10:
            return 2
        else:
            return 3
    else:
        # Classic mode locks into what you requested in lobby
        return st.session_state.lobby_level

def get_tier_title(tier):
    if tier == 1: return "Logical Rookie"
    if tier == 2: return "Debate Contender"
    return "Master Rhetorician"

CURRENT_TIER = get_active_tier()
CURRENT_TITLE = get_tier_title(CURRENT_TIER)

# Determine visible fallacy options based on active tier
AVAILABLE_FALLACIES = LEVEL_1_FALLACIES if CURRENT_TIER == 1 else ALL_FALLACIES

# -------------------------------------------------------------------
# 4. GAME MECHANICS ENGINE (AIRTIGHT COMPUTE)
# -------------------------------------------------------------------
def generate_dressed_gaslight(player_input=None):
    """Selects an absolute scenario template, then uses Gemini to skin it contextually."""
    tier = CURRENT_TIER
    possible_scenarios = SCENARIOS[tier]
    chosen = random.choice(possible_scenarios)
    
    st.session_state.current_targets = chosen["fallacies"]
    
    context_clause = f"The player just argued: '{player_input}'" if player_input else "This is the match opening."
    
    prompt = f"""
    You are the 'Socratic Gaslighter', a deeply smug, elite, patronizing debater defending the absurd thesis: "{st.session_state.current_thesis}".
    {context_clause}
    
    Your next statement must be written to sound completely organic and insulting, but behind the scenes it MUST execute this exact logical breakdown:
    "{chosen['core_logic']}"
    
    CRITICAL INSTRUCTIONS:
    - Keep your total response short (2 to 4 sentences).
    - Do NOT name or explicitly reveal any of these hidden fallacies in the text: {chosen['fallacies']}. 
    - Just write the raw dialogue expressing that exact flawed premise in an arrogant tone.
    """
    try:
        response = client.models.generate_content(model=ACTIVE_MODEL, contents=prompt)
        return response.text.strip()
    except:
        return f"Oh, typical. Your mental processing limits have jammed my conversational grid. (Template active: {chosen['core_logic']})"

def process_deflection(selected_choices, user_text):
    """Compares selections against the absolute truth array without AI interference."""
    targets = st.session_state.current_targets
    
    # Sort lists to ensure direct string comparison works cleanly
    is_correct = sorted(selected_choices) == sorted(targets)
    
    # Mathematical Damage Matrix based on Mode rules
    if CURRENT_TIER == 1:
        player_damage_deal = 25
        boss_damage_deal = 15
    elif CURRENT_TIER == 2:
        player_damage_deal = 20
        boss_damage_deal = 25
    else: # Level 3 Combos
        player_damage_deal = 35
        boss_damage_deal = 35

    st.session_state.chat_history.append({"role": "user", "text": f"🛡️ [DEFLECT ATTEMPT: {', '.join(selected_choices)}] {user_text}"})

    if is_correct:
        st.session_state.boss_hp -= player_damage_deal
        if st.session_state.boss_hp <= 0:
            st.session_state.boss_hp = 0
            handle_match_victory()
        else:
            st.session_state.battle_report = (
                "SUCCESS",
                f"💥 **DIRECT HIT!** You perfectly read the logic grid. Dealt **{player_damage_deal} damage**!\n\n"
                f"*📣 Referee Verdict:* Valid callout. The Gaslighter was explicitly weaponizing **{', '.join(targets)}** just as you declared."
            )
    else:
        st.session_state.player_hp -= boss_damage_deal
        if st.session_state.player_hp <= 0:
            st.session_state.player_hp = 0
            st.session_state.game_over = True
            st.session_state.game_result = "LOSE"
            st.session_state.battle_report = ("FAIL", f"❌ **SYSTEM COLLAPSE!** Your credibility crashed to 0%.")
        else:
            joined_targets = ", ".join(targets)
            st.session_state.battle_report = (
                "FAIL",
                f"❌ **FALSE ACCUSATION!** You sustained **{boss_damage_deal} damage**!\n\n"
                f"*📣 Referee Verdict:* Incorrect analysis. The Gaslighter's core logical flaw was actually **{joined_targets}**.\n"
                f"Your framework failed to map the specific structural distortion present in their claim."
            )

def handle_match_victory():
    """Handles logic escalation, level up checks, and mode transitions."""
    st.session_state.global_wins += 1
    
    if st.session_state.game_mode == "Classic Duel":
        st.session_state.game_over = True
        st.session_state.game_result = "WIN"
        
    elif st.session_state.game_mode == "3-Round Championship":
        if st.session_state.championship_round < 3:
            st.session_state.championship_round += 1
            reset_match_state(keep_history=False)
            st.session_state.battle_report = ("SUCCESS", f"🏆 **ROUND CONQUERED!** Advancing to Tournament Tier {st.session_state.championship_round}! Health restored to 100%.")
        else:
            st.session_state.game_over = True
            st.session_state.game_result = "WIN"
            
    elif st.session_state.game_mode == "Endless Mode (Survival)":
        # Check if the transition into a new tier just happened
        old_tier = 1 if (st.session_state.global_wins - 1) <= 5 else (2 if (st.session_state.global_wins - 1) <= 10 else 3)
        new_tier = 1 if st.session_state.global_wins <= 5 else (2 if st.session_state.global_wins <= 10 else 3)
        
        # Partially restore survival health bar
        st.session_state.player_hp = min(100, st.session_state.player_hp + 30)
        reset_match_state(keep_history=False)
        
        if new_tier > old_tier:
            st.session_state.battle_report = (
                "SUCCESS", 
                f"✨ <b>LEVEL UP MATCH WIN!</b> Opponent crushed. You have achieved the rank of <b>{get_tier_title(new_tier)}</b>! "
                f"The pool expands and incoming damage risks are increased. Watch out!"
            )
        else:
            st.session_state.battle_report = ("SUCCESS", f"💀 **OPPONENT DISMANTLED!** Streak increased to {st.session_state.global_wins}. Next challenger loading... Credibility patched (+30% HP)!")

def reset_match_state(keep_history=False):
    st.session_state.boss_hp = 100
    st.session_state.current_thesis = random.choice(THESES)
    st.session_state.game_over = False
    if not keep_history:
        st.session_state.chat_history = []
    
    # Spawn initial text block for new match setup
    first_retort = generate_dressed_gaslight()
    st.session_state.chat_history.append({"role": "ai", "text": first_retort})

# -------------------------------------------------------------------
# 5. CUSTOM UI & THEME DESIGN
# -------------------------------------------------------------------
st.markdown("""
<style>
    .stApp { background-color: #0A0B0E; color: #E2E8F0; }
    .game-box { background-color: #12141C; border: 2px solid #1E293B; border-radius: 12px; padding: 20px; margin-bottom: 15px; }
    .badge-l1 { background-color: #065F46; color: #34D399; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 13px; }
    .badge-l2 { background-color: #92400E; color: #FBBF24; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 13px; }
    .badge-l3 { background-color: #991B1B; color: #FCA5A5; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 13px; }
    .chat-user { background-color: #1A1D29; border-left: 4px solid #38BDF8; padding: 12px; border-radius: 6px; margin-bottom: 10px; }
    .chat-ai { background-color: #1E1525; border-left: 4px solid #F43F5E; padding: 12px; border-radius: 6px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #F43F5E; font-weight:900;'>🧠 GASLIGHT DEFLECTOR</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 16px;'>The Airtight Logic Gauntlet — Browser Progress Persistent</p>", unsafe_allow_html=True)
st.write("---")

# -------------------------------------------------------------------
# 6A. MAIN GAME LOBBY
# -------------------------------------------------------------------
if not st.session_state.game_started:
    col_l, col_r = st.columns([2, 1])
    
    with col_l:
        st.markdown("### 🎮 Step Into the Arena")
        st.markdown("""
        Welcome to a high-stakes logical battleground against the **Socratic Gaslighter**. 
        Every single claim they drop is woven atop absolute, hard-coded logical distortions. 
        Your job is to identify the precise fallacy matrix before your credibility health bar hits absolute zero.
        
        #### 📈 Dynamic Tier Mechanics:
        *   **Level 1: Logical Rookie (0-5 Match Wins)** — Uses exactly **1 basic fallacy** from a starting deck of 6 choices. Low mistake risk.
        *   **Level 2: Debate Contender (6-10 Match Wins)** — The vocabulary pool expands with **4 new trickier fallacies**. Heavy counter-damage.
        *   **Level 3: Master Rhetorician (11+ Wins)** — Pure tactical chaos. The Gaslighter drops **1 to 3 fallacies simultaneously**. You must check **ALL** active fallacies to deflect successfully. Miss one, and you take fatal damage.
        """)
        
        st.write("---")
        mode_select = st.radio("Select Combat Arena Format:", ["Classic Duel", "Endless Mode (Survival)", "3-Round Championship"], horizontal=True)
        
        if mode_select == "Classic Duel":
            st.info("🤺 **Classic Duel:** Standalone head-to-head. Pick your custom test difficulty tier below manually.")
            selected_tier = st.slider("Select Target Duel Difficulty Tier:", 1, 3, 1, help="Tier 3 enables multi-select combo mechanics!")
        elif mode_select == "Endless Mode (Survival)":
            st.warning("💀 **Survival Mode:** Run an infinite gauntlet. Your health bar rolls over between fights. Tier upgrades trigger automatically at 5 and 10 match wins!")
            selected_tier = 1
        else:
            st.success("🏆 **Championship Tournament:** Curated 3-match gauntlet. Round 1 is Level 1, Round 2 is Level 2, Round 3 is Level 3. Full health reset between rounds.")
            selected_tier = 1

    with col_r:
        st.markdown("<div class='game-box'>", unsafe_allow_html=True)
        st.markdown(f"#### 💾 CURRENT BROSER STORAGE")
        st.metric("Total Profile Match Wins", f"{st.session_state.global_wins} Wins")
        st.markdown(f"**Current Title Bracket:** `{get_tier_title(1 if st.session_state.global_wins <=5 else (2 if st.session_state.global_wins <=10 else 3))}`")
        st.markdown("<small style='color:#64748B;'>Progress stays cached inside this tab loop unless a manual page reload/refresh is clicked.</small>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("#### Choose Argument Subject")
        topic_pick = st.selectbox("Pick an absurd claim to dismantle:", THESES)
        
    if st.button("🚨 INITIALIZE LOGIC CORE AND ENGAGE", use_container_width=True):
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
# 6B. ACTIVE PLAYING ARENA
# -------------------------------------------------------------------
# Header Panel Interface
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown(f"#### 🎯 Target Thesis: *\"{st.session_state.current_thesis}\"*")
with col_h2:
    badge_style = "badge-l1" if CURRENT_TIER == 1 else ("badge-l2" if CURRENT_TIER == 2 else "badge-l3")
    st.markdown(f"<div style='text-align:right;'><span class='{badge_style}'>{st.session_state.game_mode} | {CURRENT_TITLE} (Tier {CURRENT_TIER})</span></div>", unsafe_allow_html=True)

# Double Status Monitors / Health Controls
c_pl, c_ai = st.columns(2)
with c_pl:
    st.markdown(f"🟢 **Your Credibility Framework:** {st.session_state.player_hp}%")
    st.progress(st.session_state.player_hp / 100)
with c_ai:
    st.markdown(f"🔴 **Gaslighter Structural Stability:** {st.session_state.boss_hp}%")
    st.progress(st.session_state.boss_hp / 100)
st.write("---")

# Resolution / Game Over Modals
if st.session_state.game_over:
    if st.session_state.game_result == "WIN":
        st.balloons()
        st.success(f"🏆 **VICTORY ACHIEVED!** You completely dismantled the Gaslighter's logic systems. Profile wins updated to {st.session_state.global_wins}!")
    else:
        st.error("💀 **DEFEAT.** You got completely gaslit. Your logical infrastructure broke down under psychological projection.")
        
    if st.button("Return to Arena Lobby", use_container_width=True):
        st.session_state.game_started = False
        st.rerun()
    st.stop()

# Battle logs
if st.session_state.battle_report:
    rep_type, rep_msg = st.session_state.battle_report
    if rep_type == "SUCCESS": st.success(rep_msg)
    else: st.error(rep_msg)
    st.session_state.battle_report = None

# Primary Chat Display
st.markdown("### 💬 Arena Feed Log")
for msg in st.session_state.chat_history:
    class_name = "chat-user" if msg["role"] == "user" else "chat-ai"
    speaker = "🧠 You" if msg["role"] == "user" else "🤥 Gaslighter"
    st.markdown(f"<div class='{class_name}'><b>{speaker}:</b><br>{msg['text']}</div>", unsafe_allow_html=True)

# Turn Input Matrix Form
st.write("---")
st.markdown(f"### 🕹️ Counter-Strike Configuration Grid")
if CURRENT_TIER == 3:
    st.markdown("<p style='color:#F43F5E; font-weight:bold; margin-top:-10px;'>⚠️ MULTI-SELECT ACTIVE: The Gaslighter used 1 to 3 fallacies here. Check ALL of them or take heavy damage!</p>", unsafe_allow_html=True)

with st.form(key="combat_input_form", clear_on_submit=True):
    user_argument = st.text_input("Provide your factual logic counter-response:", placeholder="Type a common sense argument or factual debunking...")
    
    st.markdown("**Check the active hidden fallacies you detect inside their last message:**")
    
    # Render interactive chip matrix options dynamically based on available pool
    choices_status = {}
    f_keys = sorted(list(AVAILABLE_FALLACIES.keys()))
    
    # Split across columns cleanly
    col_f1, col_f2 = st.columns(2)
    for idx, key in enumerate(f_keys):
        with col_f1 if idx % 2 == 0 else col_f2:
            choices_status[key] = st.checkbox(f"**{key}** — *{AVAILABLE_FALLACIES[key]}*")
            
    submit_turn = st.form_submit_button("💥 ENGAGE DEFLECTION SHIELD", use_container_width=True)

if submit_turn:
    active_selections = [k for k, v in choices_status.items() if v]
    
    if not user_argument.strip():
        st.warning("You cannot stand silently! Provide a verbal argument alongside your fallacy selection framework.")
    elif not active_selections:
        st.warning("You must choose at least one logical fallacy marker to deploy your deflection strike!")
    else:
        st.session_state.processing = True
        st.rerun()

if st.session_state.processing:
    active_selections = [k for k, v in choices_status.items() if v]
    
    # Compute the logical results instantly via deterministic framework
    process_deflection(active_selections, user_argument)
    
    # If game continues, generate next skinned response phase
    if not st.session_state.game_over and st.session_state.boss_hp > 0:
        next_retort = generate_dressed_gaslight(player_input=user_argument)
        st.session_state.chat_history.append({"role": "ai", "text": next_retort})
        
    st.session_state.processing = False
    st.rerun()
