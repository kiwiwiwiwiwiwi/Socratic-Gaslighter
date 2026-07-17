def judge_objection(selected_fallacy):
    """Uses the LLM as a dynamic referee to see if the player's objection is valid for the text."""
    last_ai_response = ""
    for msg in reversed(st.session_state.chat_history):
        if msg["role"] == "ai" and not msg["text"].startswith("💥") and not msg["text"].startswith("🔄") and not msg["text"].startswith("🏆"):
            last_ai_response = msg["text"]
            break

    # The updated prompt that keeps the referee focused on addressing the player
    judge_prompt = f"""
    You are an incredibly nonchalant, deeply bored, and slightly rude logic tournament referee. You hate your job and find both the player and the gaslighter exhausting.
    The opponent (Gaslighter) said: "{last_ai_response}"
    The player objects and accuses them of committing this fallacy: **{selected_fallacy}** ({FALLACIES[selected_fallacy]}).
    
    First, decide if the player's accusation is reasonably valid based on the text.
    Respond with exactly 'VALID' or 'INVALID' as the first word.
    
    Then, deliver your verdict with peak nonchalance and a biting insult targeting the loser. 
    CRITICAL: Talk directly TO the player. Address the Gaslighter in the third person as "the Gaslighter" or "the opponent":
    - If VALID: Break it down for the player by insulting the Gaslighter's terrible logic (e.g., "The Gaslighter's argument is pathetic...", "The opponent is completely dynamic-less...").
    - If INVALID: Roast the player directly for being wrong (e.g., "You completely missed the mark...", "Your accusation is trash...").
    Keep your full response under 3 sentences.
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
            st.session_state.strike_alert = ("SUCCESS", f"💥 **OBJECTION ALLOWED!**\n\n*📣 Referee:* {explanation}")
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
            f"❌ **FALSE ACCUSATION!** (-{penalty}% HP)\n\n*📣 Referee:* {explanation}"
        )
