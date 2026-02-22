import streamlit as st
import json
import random
import time
import base64
import pandas as pd
from datetime import datetime

# --- Helper Functions ---

@st.cache_data
def load_questions():
    # Make sure this matches your exact filename in GitHub!
    try:
        with open('2025.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Error: '2025.json' not found.")
        return []

def generate_save_code():
    """Encodes the current game state AND history into a base64 string"""
    state_data = {
        'current_index': st.session_state.current_index,
        'score': st.session_state.score,
        'quiz_data': st.session_state.quiz_data,
        'history': st.session_state.history, 
        'incorrect_indices': st.session_state.incorrect_indices,
        'simulation_mode': st.session_state.simulation_mode,
        'user_answers': st.session_state.user_answers,
        'submitted_questions': st.session_state.submitted_questions,
        'notes': st.session_state.notes,
        'starred': st.session_state.starred,
        'time_limit': st.session_state.time_limit,
        'start_time': st.session_state.start_time
    }
    json_str = json.dumps(state_data, default=str)
    b64_str = base64.b64encode(json_str.encode()).decode()
    return b64_str

def load_save_code(code):
    """Decodes a save string and restores the game and history"""
    try:
        json_str = base64.b64decode(code).decode()
        state_data = json.loads(json_str)
        
        st.session_state.current_index = state_data.get('current_index', 0)
        st.session_state.score = state_data.get('score', 0)
        st.session_state.quiz_data = state_data.get('quiz_data', [])
        st.session_state.history = state_data.get('history', [])
        st.session_state.incorrect_indices = state_data.get('incorrect_indices', [])
        st.session_state.simulation_mode = state_data.get('simulation_mode', False)
        
        # Convert keys back to integers (JSON converts dict keys to strings)
        st.session_state.user_answers = {int(k): v for k, v in state_data.get('user_answers', {}).items()}
        st.session_state.notes = {int(k): v for k, v in state_data.get('notes', {}).items()}
        st.session_state.starred = {int(k): v for k, v in state_data.get('starred', {}).items()}
        
        st.session_state.submitted_questions = state_data.get('submitted_questions', [])
        st.session_state.time_limit = state_data.get('time_limit', 0)
        st.session_state.start_time = state_data.get('start_time', time.time())
        
        st.session_state.game_active = True
        st.session_state.quiz_finished = False
        return True
    except Exception as e:
        return False

# --- Initialization ---
if 'game_active' not in st.session_state: st.session_state.game_active = False
if 'quiz_finished' not in st.session_state: st.session_state.quiz_finished = False
if 'history' not in st.session_state: st.session_state.history = [] 
if 'incorrect_indices' not in st.session_state: st.session_state.incorrect_indices = [] 
if 'simulation_mode' not in st.session_state: st.session_state.simulation_mode = False
if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
if 'submitted_questions' not in st.session_state: st.session_state.submitted_questions = []
if 'notes' not in st.session_state: st.session_state.notes = {}
if 'starred' not in st.session_state: st.session_state.starred = {}
if 'time_limit' not in st.session_state: st.session_state.time_limit = 0
if 'start_time' not in st.session_state: st.session_state.start_time = None

raw_questions = load_questions()

# ==========================================
# SCREEN 1: THE START MENU (HOME)
# ==========================================
if not st.session_state.game_active and not st.session_state.quiz_finished:
    st.title("🎓 Exam Simulator Pro")
    st.markdown("Welcome back! Ready to master the material?")

    if st.session_state.history:
        with st.expander("🏆 Your Progress (Leaderboard)", expanded=False):
            df = pd.DataFrame(st.session_state.history)
            st.dataframe(df, use_container_width=True)
            if len(df) > 1:
                st.line_chart(df.set_index("Date")["Score (%)"])
            avg_score = df["Score (%)"].mean()
            st.metric("Average Performance", f"{avg_score:.1f}%")

    with st.container(border=True):
        st.subheader("⚙️ Settings")
        
        col_set1, col_set2 = st.columns(2)
        with col_set1:
            shuffle_opt = st.checkbox("Randomize Order", value=True)
            sim_mode = st.checkbox("DECA Simulation Mode", value=False, help="No immediate feedback. Review answers at the end.")
            allow_back = st.checkbox("Enable 'Previous' Button", value=True, help="Allow going back to previous questions.")
        with col_set2:
            max_qs = len(raw_questions)
            if max_qs == 0:
                st.warning("No questions found. Check your JSON filename.")
                st.stop()
            q_limit = st.slider("Question Count", 1, max_qs, min(100, max_qs))
            
            enable_timer = st.checkbox("Enable Exam Timer", value=False)
            if enable_timer:
                time_val = st.number_input("Time Limit (Minutes)", min_value=1, max_value=180, value=60)
            else:
                time_val = 0

    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("▶️ Start New Exam", type="primary", use_container_width=True):
            with st.spinner("Preparing exam..."):
                time.sleep(1)
            
            subset_questions = raw_questions[:] 
            if shuffle_opt: random.shuffle(subset_questions)
            
            st.session_state.quiz_data = subset_questions[:q_limit]
            st.session_state.current_index = 0
            st.session_state.score = 0
            st.session_state.incorrect_indices = []
            st.session_state.user_answers = {}
            st.session_state.submitted_questions = []
            st.session_state.notes = {}
            st.session_state.starred = {}
            st.session_state.simulation_mode = sim_mode
            st.session_state.allow_back = allow_back
            st.session_state.time_limit = time_val
            st.session_state.start_time = time.time()
            
            if "sim_scored" in st.session_state: del st.session_state.sim_scored
            
            st.session_state.game_active = True
            st.rerun()

    with col2:
        with st.popover("📂 Load Saved Game"):
            save_code_input = st.text_input("Paste Save Code:")
            if st.button("Resume"):
                if load_save_code(save_code_input):
                    st.success("Loaded!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Invalid Code.")

# ==========================================
# SCREEN 2: THE GAME
# ==========================================
elif st.session_state.game_active and not st.session_state.quiz_finished:
    
    # --- Check Timer ---
    if st.session_state.time_limit > 0:
        elapsed_seconds = time.time() - st.session_state.start_time
        remaining_seconds = (st.session_state.time_limit * 60) - elapsed_seconds
        
        if remaining_seconds <= 0:
            st.warning("⏰ Time is up! Submitting your exam automatically.")
            time.sleep(2)
            st.session_state.quiz_finished = True
            st.session_state.game_active = False
            st.rerun()

    with st.sidebar:
        st.header("⏸ Menu")
        if st.button("💾 Save Progress"):
            code = generate_save_code()
            st.code(code, language=None)
            st.warning("Copy this code to save your history and current spot!")
            
        if st.button("❌ Quit to Menu"):
            st.session_state.game_active = False
            st.rerun()

    questions = st.session_state.quiz_data
    total_qs = len(questions)
    current_idx = st.session_state.current_index
    
    # --- Top Bar Metrics ---
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        st.caption(f"Question {current_idx + 1} of {total_qs}")
        st.progress((current_idx + 1) / total_qs)
    with c2:
        if st.session_state.time_limit > 0:
            mins, secs = divmod(int(remaining_seconds), 60)
            st.caption("⏳ Time Remaining:")
            st.markdown(f"**{mins}:{secs:02d}**")
        else:
            st.caption("⏳ Timer:")
            st.markdown("**Off**")
    with c3:
        if st.session_state.simulation_mode:
            st.caption("Mode: 🛑 Simulation")
        else:
            qs_answered = len(st.session_state.submitted_questions)
            current_accuracy = (st.session_state.score / qs_answered) if qs_answered > 0 else 0.0
            st.caption(f"Accuracy: {current_accuracy:.0%}")

    # --- Display Question ---
    q = questions[current_idx]
    st.subheader(f"{q['question_text']}")
    
    options = q['options']
    choice_labels = [f"{key}: {value}" for key, value in sorted(options.items())]
    
    # Pre-select answer if they've chosen one already
    pre_selected = None
    saved_ans = st.session_state.user_answers.get(current_idx)
    if saved_ans:
        pre_selected = list(sorted(options.keys())).index(saved_ans)

    is_locked = current_idx in st.session_state.submitted_questions and not st.session_state.simulation_mode

    user_choice = st.radio(
        "Select Answer:", 
        choice_labels, 
        key=f"q_{current_idx}", 
        disabled=is_locked,
        index=pre_selected
    )

    # Save selection instantly
    if user_choice:
        st.session_state.user_answers[current_idx] = user_choice.split(":")[0]

    # --- Stars & Notes ---
    with st.expander("⭐ Star & Notes", expanded=False):
        is_starred = st.checkbox("Star this question for review", value=st.session_state.starred.get(current_idx, False), key=f"star_{current_idx}")
        st.session_state.starred[current_idx] = is_starred
        
        note_text = st.text_area("Personal Notes (Saved automatically):", value=st.session_state.notes.get(current_idx, ""), key=f"note_{current_idx}")
        st.session_state.notes[current_idx] = note_text

    st.write("---")

    # --- Navigation Logic ---
    col_prev, col_sub, col_next = st.columns([1, 1, 1])
    
    # PREVIOUS BUTTON
    with col_prev:
        if st.session_state.get('allow_back', True) and current_idx > 0:
            if st.button("⬅ Previous", use_container_width=True):
                st.session_state.current_index -= 1
                st.rerun()

    # STUDY MODE - SUBMIT & FEEDBACK
    if not st.session_state.simulation_mode:
        if not is_locked:
            with col_sub:
                if st.button("Submit Answer", type="primary", use_container_width=True):
                    if user_choice:
                        st.session_state.submitted_questions.append(current_idx)
                        st.rerun()
                    else:
                        st.toast("Please select an option first!", icon="⚠️")
        else:
            # Show Feedback
            correct_key = q['answer_key']
            if saved_ans == correct_key:
                st.success("✅ Correct!")
                if "scored_" + str(current_idx) not in st.session_state:
                    st.session_state.score += 1
                    st.session_state["scored_" + str(current_idx)] = True
            else:
                st.error(f"❌ Incorrect. Answer: {correct_key}")
                if "scored_" + str(current_idx) not in st.session_state:
                    st.session_state.incorrect_indices.append(q) 
                    st.session_state["scored_" + str(current_idx)] = True
            
            st.info(f"**Rationale:** {q['rationale']}")
            
            with col_next:
                if st.button("Next ➡", type="primary", use_container_width=True):
                    if current_idx + 1 < total_qs:
                        st.session_state.current_index += 1
                    else:
                        st.session_state.quiz_finished = True
                        st.session_state.game_active = False
                    st.rerun()

    # SIMULATION MODE - NEXT/FINISH
    else:
        with col_next:
            button_text = "Next ➡" if current_idx + 1 < total_qs else "Finish Exam 🏁"
            if st.button(button_text, type="primary", use_container_width=True):
                if current_idx + 1 < total_qs:
                    st.session_state.current_index += 1
                else:
                    st.session_state.quiz_finished = True
                    st.session_state.game_active = False
                st.rerun()

# ==========================================
# SCREEN 3: GAME OVER
# ==========================================
elif st.session_state.quiz_finished:
    
    # Score Calculation for Simulation Mode
    if st.session_state.simulation_mode and "sim_scored" not in st.session_state:
        st.session_state.score = 0
        st.session_state.incorrect_indices = []
        for i, q in enumerate(st.session_state.quiz_data):
            user_ans = st.session_state.user_answers.get(i)
            if user_ans == q['answer_key']:
                st.session_state.score += 1
            else:
                st.session_state.incorrect_indices.append(q)
        st.session_state.sim_scored = True

    st.balloons()
    st.title("🎉 Session Complete!")
    
    final_score = st.session_state.score
    total = len(st.session_state.quiz_data)
    percent = (final_score / total) * 100
    
    if "history_saved" not in st.session_state:
        st.session_state.history.append({
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Score": f"{final_score}/{total}",
            "Score (%)": round(percent, 1)
        })
        st.session_state.history_saved = True

    st.metric("Final Score", f"{final_score} / {total}", f"{percent:.1f}%")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🏠 Home Screen"):
            if "history_saved" in st.session_state: del st.session_state.history_saved
            if "sim_scored" in st.session_state: del st.session_state.sim_scored
            st.session_state.quiz_finished = False
            st.session_state.game_active = False
            st.rerun()

    with col2:
        missed_qs = st.session_state.incorrect_indices
        if len(missed_qs) > 0:
            if st.button(f"🔁 Retry {len(missed_qs)} Missed"):
                if "history_saved" in st.session_state: del st.session_state.history_saved
                if "sim_scored" in st.session_state: del st.session_state.sim_scored
                st.session_state.quiz_data = missed_qs[:]
                st.session_state.current_index = 0
                st.session_state.score = 0
                st.session_state.incorrect_indices = []
                st.session_state.user_answers = {}
                st.session_state.submitted_questions = []
                st.session_state.notes = {}
                st.session_state.starred = {}
                st.session_state.quiz_finished = False
                st.session_state.game_active = True
                st.rerun()
        else:
            st.button("🔁 Retry Missed", disabled=True)

    with col3:
        if st.button("🔄 New Exam"):
            if "history_saved" in st.session_state: del st.session_state.history_saved
            if "sim_scored" in st.session_state: del st.session_state.sim_scored
            st.session_state.current_index = 0
            st.session_state.score = 0
            st.session_state.incorrect_indices = []
            st.session_state.user_answers = {}
            st.session_state.submitted_questions = []
            st.session_state.notes = {}
            st.session_state.starred = {}
            st.session_state.quiz_finished = False
            st.session_state.game_active = False 
            st.rerun()
            
    st.write("---")

    # --- EXAM REVIEW ---
    if st.session_state.simulation_mode:
        st.subheader("📝 Exam Review")
        st.write("Review your answers, rationales, and notes below:")
        
        for i, q in enumerate(st.session_state.quiz_data):
            user_ans = st.session_state.user_answers.get(i, "Skipped")
            correct_ans = q['answer_key']
            is_correct = user_ans == correct_ans
            
            star_icon = "⭐" if st.session_state.starred.get(i, False) else ""
            status_icon = "✅" if is_correct else "❌"
            
            with st.expander(f"{star_icon} Question {i+1} {status_icon} (Click to expand)"):
                st.markdown(f"**{q['question_text']}**")
                
                for key, val in sorted(q['options'].items()):
                    if key == correct_ans:
                        st.markdown(f"**{key}: {val}** *(Correct Answer)*")
                    elif key == user_ans:
                        st.markdown(f"*{key}: {val}* *(Your Answer)*")
                    else:
                        st.markdown(f"{key}: {val}")
                        
                st.info(f"**Rationale:** {q['rationale']}")
                
                # Show notes if they exist
                note = st.session_state.notes.get(i, "")
                if note.strip() != "":
                    st.warning(f"**Your Notes:**\n\n{note}")
