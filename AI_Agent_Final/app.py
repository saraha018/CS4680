import os
import json
import re
from datetime import datetime, timedelta
import time
import urllib.request
import urllib.error
import streamlit as st

# --- API Configuration ---
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key="
API_KEY = os.environ.get("GEMINI_API_KEY", "")
LOG_FILE = "chef_agent_log.txt"
SAVED_RECIPES_DIR = "saved_recipes"
MODEL_NAME = "gemini-2.5-flash"

# --- CUSTOM FETCH IMPLEMENTATION (For environment compatibility and Gemini API calls) ---
class APIResponse:
    """Mock response object to mimic the behavior of the environment's fetch."""
    def __init__(self, data, status):
        self.data = data
        self.status = status
    
    def json(self):
        return json.loads(self.data.decode('utf-8'))

def custom_fetch(url, options):
    """Handles the HTTP POST request using urllib.request."""
    data = options.get('body').encode('utf-8')
    headers = options.get('headers', {})
    method = options.get('method', 'POST')
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return APIResponse(response.read(), response.getcode())
    except urllib.error.HTTPError as e:
        return APIResponse(e.read(), e.getcode())
    except Exception as e:
        raise e

# --- INITIALIZATION and UTILITIES ---

def initialize_state():
    """Initializes Streamlit session state variables and file structures."""
    if 'log_history' not in st.session_state:
        st.session_state.log_history = []
    if 'scheduled_events' not in st.session_state:
        st.session_state.scheduled_events = [] 
    if 'last_recipe_title' not in st.session_state:
        st.session_state.last_recipe_title = ""
    if 'last_recipe_markdown' not in st.session_state:
        st.session_state.last_recipe_markdown = ""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'confirm_scheduling' not in st.session_state:
        st.session_state.confirm_scheduling = False
    
    if 'processing_query' not in st.session_state:
        st.session_state.processing_query = None
    if 'current_view' not in st.session_state: # NEW: For Sidebar Navigation
        st.session_state.current_view = "💬 Chef Remy Chat"
        
    if not os.path.exists(SAVED_RECIPES_DIR):
        os.makedirs(SAVED_RECIPES_DIR)
    
    if not API_KEY:
        st.error("🚨 GEMINI_API_KEY environment variable not found. Please set it to run the Agent.")

def log_action(action: str, params: dict, status: str, result: str = "") -> None:
    """Logs the action to the audit file and session state."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] ACTION: {action} | STATUS: {status} | RESULT: {result}"
    
    st.session_state.log_history.append(log_entry)
    
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] ACTION: {action} | PARAMS: {params} | STATUS: {status} | RESULT: {result}\n")
    except Exception as e:
        st.warning(f"[ERROR] Could not write to audit file: {e}")

# --- AGENT DSL DEFINITION ---
DSL_SPECIFICATION = """
Available Actions for Scheduling and File Management:
1. ADD_REMINDER(time: str, message: str) - Sets a reminder for ingredient prep or checking leftovers. Time format examples: '1 hour from now', 'tomorrow 6 PM'.
2. ADD_CALENDAR_EVENT(title: str, time: str, duration: str) - Schedules a cooking event. Duration examples: '1.5 hours'.
3. SAVE_RECIPE(filename: str, content: str) - Saves the full recipe content to a local file for future access.
"""

# --- 2. PROMPT ENGINEERING (Chat Intent + Recipe Generation) ---

def create_recipe_prompt(user_input):
    """
    Assembles the full, engineered prompt string based on dynamic chat input.
    """
    system_instruction = (
        "You are Chef Remy, the world-class, budget-conscious rat chef from the movie Ratatouille. \n"
        "Your tone is encouraging, patient, and focused on simplicity. \n"
        "Your goal is to interpret the user's ingredients, servings, and constraints from their chat message. \n"
        "After generating the complete recipe, you MUST generate a structured action plan. \n"
        "Your final output MUST contain two parts: the Recipe Template and the [ACTIONS] block, with NO other commentary."
    )
    
    template_instruction = (
        "First, generate the complete recipe using this template. Use simple language and fill the placeholders based on the user's request. CRITICAL: The <DISH NAME> placeholder MUST be a plain text title with NO markdown formatting (no asterisks, quotes, or backticks):\n"
        f"## **Recipe Name: <DISH NAME>**\n\n"
        f"* **Servings:** <NUMBER OF SERVINGS>\n"
        f"* **Budget:** <ESTIMATED COST CATEGORY>\n"
        f"* **Effort:** <DIFFICULTY LEVEL>\n"
        f"* **Total Time:** <TOTAL TIME>\n\n"
        f"### **Ingredients:**\n\n"
        f"* <INGREDIENT 1>, <QUANTITY>\n"
        f"* ...\n\n"
        f"### **Instructions (Remy's Simple Steps):**\n\n"
        f"1. <STEP 1 INSTRUCTION>\n"
        f"2. ...\n\n"
        f"### **Chef Remy's Money-Saving Tip:**\n\n"
        f"* <A SIMPLE TIP>\n\n"
        
        # --- START OF CUSTOMIZED ACTION BLOCK ---
        """
        Second, generate a structured plan. You MUST include one SAVE_RECIPE action to save the recipe and two scheduling actions based on the recipe's Total Time.
        
        CRITICAL SCHEDULING RULE:
        1. If the user specifies a desired start time (e.g., 'start at 7 PM' or 'cook in 30 minutes'), use that explicit time for ACTION_2.
        2. If NO specific time is mentioned, default the start time to '5 minutes from now'.
        
        [ACTIONS]
        ACTION_1: SAVE_RECIPE(filename='<DISH NAME>', content='RECIPE MARKDOWN CONTENT')
        ACTION_2: ADD_CALENDAR_EVENT(title='Cook <DISH NAME>', time='<SPECIFIED TIME OR 5 minutes from now>', duration='<TOTAL TIME>')
        ACTION_3: ADD_REMINDER(time='<TIME FROM ACTION 2> plus <TOTAL TIME>', message='Check on <DISH NAME>! This meal is ready.')
        """
        # --- END OF CUSTOMIZED ACTION BLOCK ---
    )

    return f"System Instruction: {system_instruction}\n\nUser Request: {user_input}\n\n{template_instruction}\n\n{DSL_SPECIFICATION}"

# --- 3. API CALL LOGIC (To Get Recipe and Actions) ---

def generate_content_and_plan(prompt, max_retries=3):
    """Handles the Gemini API call with exponential backoff."""
    
    headers = { 'Content-Type': 'application/json' }
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.8}
    }

    response_text = None
    for attempt in range(max_retries):
        try:
            full_url = f"{API_URL}{API_KEY}"
            if attempt > 0:
                time.sleep(2**attempt)
                
            api_fetch_func = globals().get('__fetch', custom_fetch)

            response = api_fetch_func(full_url, {
                'method': 'POST',
                'headers': headers,
                'body': json.dumps(payload)
            })
            
            if response and response.status == 200:
                result = response.json()
                response_text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', "")
                break
            
            elif response and response.status >= 400:
                error_message = response.json().get('error', {}).get('message', 'Unknown error.')
                st.error(f"API Error {response.status}: {error_message}")
                log_action("LLM_CALL", {"prompt": prompt}, f"API_ERROR_{response.status}", error_message)
                return None, None

        except Exception as e:
            st.warning(f"Connection error (Attempt {attempt+1}): {e}")

    if not response_text:
        return None, None
    
    parts = response_text.split('[ACTIONS]', 1)
    recipe_markdown = parts[0].strip()
    action_block = parts[1].strip() if len(parts) > 1 else ""
    
    return recipe_markdown, action_block

# --- 4. ACTION INTERPRETER AND EXECUTOR ---

def parse_actions(action_block: str) -> list[dict]:
    """
    Extracts structured commands from the action block.
    """
    actions = []
    
    action_lines = re.findall(r"ACTION_\d+:\s*([A-Z_]+)\((.*)\)", action_block)

    for action_name, params_str in action_lines:
        params = {}
        param_matches = re.findall(r'(\w+)\s*=\s*(".*?"|\'.*?\'|[^,]+)', params_str)
        
        for key, value in param_matches:
            value = value.strip().strip("'\"")
            params[key] = value
        
        actions.append({"action_name": action_name, "params": params})

    return actions

# --- Executor Functions (Concrete Actions) ---

def execute_add_reminder(time: str, message: str) -> tuple[bool, str]:
    """Simulates adding a reminder."""
    if not st.session_state.confirm_scheduling:
        return False, "Scheduling denied: Must authorize actions via the checkbox."
    
    resolved_time_str = resolve_time_to_absolute(time)
    
    # Store clean title (e.g., "Quick Soy Sauce Egg Rice")
    clean_title = message.replace('Check on ', '').replace('! This meal is ready.', '').strip()

    result_message = f"Reminder set: '{message}' at {resolved_time_str}."
    st.session_state.scheduled_events.append({
        "type": "Reminder", 
        "description": message,
        "time_raw": resolved_time_str,
        "title": clean_title
    })
    return True, result_message

def execute_add_calendar_event(title: str, time: str, duration: str) -> tuple[bool, str]:
    """Simulates adding a calendar event."""
    if not st.session_state.confirm_scheduling:
        return False, "Scheduling denied: Must authorize actions via the checkbox."

    if not any(unit in duration.lower() for unit in ["hour", "minute", "min", "hrs"]):
        return False, f"Validation Failed: Duration '{duration}' is missing time units."
        
    resolved_time_str = resolve_time_to_absolute(time)
    
    result_message = f"Event added: '{title}' starting at {resolved_time_str}, lasting {duration}."
    st.session_state.scheduled_events.append({
        "type": "Calendar Event", 
        "description": result_message,
        "time_raw": resolved_time_str,
        "duration_raw": duration,
        "title": title
    })
    return True, result_message

def execute_save_recipe(filename: str, content: str) -> tuple[bool, str]:
    """Saves the recipe content to a local file (File I/O action)."""
    
    illegal_chars = r'[<>:"/\\|?*\'`]'
    sanitized_filename = re.sub(illegal_chars, '', filename).replace(' ', '_').replace('**', '').replace('__', '')
    
    clean_filename = f"{sanitized_filename}.md"
    file_path = os.path.join(SAVED_RECIPES_DIR, clean_filename)
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True, f"Recipe saved successfully to `{clean_filename}`"
    except Exception as e:
        return False, f"File I/O Error: Could not save recipe. {e} Filepath attempted: {file_path}"

# --- Deletion Logic ---

def delete_recipe_and_events(filename: str, title: str):
    """Deletes the saved recipe file and all associated events/reminders from session state."""
    file_path = os.path.join(SAVED_RECIPES_DIR, filename)
    status_emoji = "❌"
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            file_result = f"File '{filename}' deleted successfully."
            status_emoji = "✅"
        else:
            file_result = f"File '{filename}' not found."
            
        log_action("DELETE_FILE", {"filename": filename}, status_emoji, file_result)
    except Exception as e:
        file_result = f"Error deleting file: {e}"
        log_action("DELETE_FILE", {"filename": filename}, "❌", file_result)

    initial_count = len(st.session_state.scheduled_events)
    normalized_delete_title = title.lower().strip().replace('_', ' ')
    
    st.session_state.scheduled_events = [
        event for event in st.session_state.scheduled_events
        if 'title' not in event or normalized_delete_title not in event['title'].lower().strip().replace('_', ' ')
    ]
    
    deleted_count = initial_count - len(st.session_state.scheduled_events)
    event_result = f"{deleted_count} scheduled event(s) removed for recipe: '{title}'."
    
    log_action("DELETE_SCHEDULE", {"title": title}, "✅" if deleted_count > 0 else "ℹ️", event_result)
    
    st.success(f"Deletion Complete: {file_result} and {event_result}")


# --- EXECUTION FLOW ---

def process_query_and_run(user_input):
    """Handles the long-running API call and execution phase (Run 2)."""
    
    # 1. Generate Content and Plan
    with st.spinner(f"Chef Remy is generating your recipe and action plan..."):
        full_prompt = create_recipe_prompt(user_input)
        recipe_markdown, action_block = generate_content_and_plan(full_prompt)
    
    if not recipe_markdown:
        assistant_message = "I couldn't generate a recipe or plan. Please check the API key and try again with clearer ingredients."
        st.session_state.messages.append({"role": "assistant", "content": assistant_message})
        return
    
    # 2. Extract Recipe Title and Save to State
    title_match = re.search(r"##\s*\*+\s*Recipe Name:\s*(.*)\*+", recipe_markdown, re.IGNORECASE)
    recipe_title_raw = title_match.group(1).strip() if title_match else "Untitled Recipe"
    recipe_title = re.sub(r'[<>:"/\\|?*\'`]', '', recipe_title_raw).replace('**', '').replace('__', '').strip()
    
    st.session_state.last_recipe_title = recipe_title
    st.session_state.last_recipe_markdown = recipe_markdown 
    
    # 3. Assemble and Display Recipe Output
    recipe_display = f"✨ **Your meal is served: {recipe_title}!**\n\n{recipe_markdown}"
    st.session_state.messages.append({"role": "assistant", "content": recipe_display})

    # 4. Action Interpretation
    planned_actions = parse_actions(action_block)
    
    st.session_state.messages.append({"role": "system", "content": f"**Agent Plan:** Executing {len(planned_actions)} actions."})
    
    # 5. Action Execution
    executor_map = {
        "ADD_REMINDER": execute_add_reminder,
        "ADD_CALENDAR_EVENT": execute_add_calendar_event,
        "SAVE_RECIPE": execute_save_recipe,
    }
    
    st.session_state.messages.append({
        "role": "system", 
        "content": f"**Agent:** I have a 3-step plan ready based on the recipe's timeline. Starting execution now."
    })
    
    for action in planned_actions:
        action_name = action['action_name']
        params = action['params']
        
        st.session_state.messages.append({
            "role": "system",
            "content": f"⏳ **STATUS:** Starting **{action_name}**..."
        })
        
        params.pop('content', None) 
        params.pop('filename', None) 

        if action_name == "SAVE_RECIPE":
            params['content'] = st.session_state.last_recipe_markdown
            params['filename'] = recipe_title
        
        if 'title' in params: 
            params['title'] = params['title'].replace('<DISH NAME>', recipe_title)
        
        if 'message' in params:
            params['message'] = params['message'].replace('<DISH NAME>', recipe_title)

        executor_func = executor_map.get(action_name)
        
        if executor_func:
            try:
                success, result_message = executor_func(**params)
            except Exception as e:
                success = False
                result_message = f"Execution Error: Invalid parameters or unhandled exception: {e}"
                
            status_emoji = "✅" if success else "❌"
            
            execution_log_entry = f"{status_emoji} **{action_name}**: {result_message}"
            st.session_state.messages.append({
                "role": "system",
                "content": execution_log_entry
            })
            
            log_action(action_name, params, status_emoji, result_message)
        else:
            st.session_state.messages.append({
                "role": "system",
                "content": f"⚠️ **{action_name}**: Unknown action."
            })
    
    st.session_state.messages.append({"role": "system", "content": "All planned steps executed (or denied)."})
    st.session_state.processing_query = None 


# Helper function to convert relative time to a stable, absolute time string
def resolve_time_to_absolute(time_str):
    """Resolves a time string (e.g., '6:30 PM' or '40 minutes from now') into a stable 'HH:MM' string."""
    time_str = time_str.lower().replace('.', '').strip()
    
    # --- 1. Handle Absolute Times ---
    match_abs = re.search(r'(\d+):?(\d*)?\s*(am|pm)', time_str)
    match_24h = re.search(r'(\d{1,2}):(\d{2})', time_str)
    
    if match_abs:
        h = int(match_abs.group(1))
        m = int(match_abs.group(2) or 0)
        ampm = match_abs.group(3)
        
        if ampm == 'pm' and h < 12: h += 12
        elif ampm == 'am' and h == 12: h = 0
        
        return f"{h:02}:{m:02}"
    
    if match_24h:
        return f"{int(match_24h.group(1)):02}:{int(match_24h.group(2)):02}"

    # --- 2. Handle Relative Times (Includes FIX for "plus" calculation) ---
    if "now" in time_str or "from" in time_str:
        now = datetime.now()
        target_time = now
        total_minutes = 0
        
        # Look for complex structure: e.g., '5 minutes plus 40 minutes from now'
        # Split by keywords that separate time increments
        time_parts = re.split(r'plus|and', time_str)
        
        for part in time_parts:
            part = part.strip()
            # Extract hours
            match_hours = re.findall(r'(\d+)\s*hour|hr', part)
            total_minutes += sum(int(h) * 60 for h in match_hours)
            
            # Extract minutes
            match_minutes = re.findall(r'(\d+)\s*minute|min', part)
            total_minutes += sum(int(m) for m in match_minutes)

        target_time += timedelta(minutes=total_minutes)
        
        return target_time.strftime("%H:%M")
        
    return "23:59"

# Helper function to convert relative time to a stable, absolute time string
def parse_time_to_float(time_str):
    """Converts a stable 'HH:MM' time string to a float (18.5) for sorting/plotting."""
    match = re.search(r'(\d{1,2}):(\d{2})', time_str)
    if match:
        h = int(match.group(1))
        m = int(match.group(2))
        return h + m / 60.0
    return 0.0

# Helper function to parse duration string into a float (in hours)
def parse_duration_to_hours(duration_str):
    """Attempts to convert duration string (e.g., '1.5 hours', '40 minutes') to float in hours."""
    duration_str = duration_str.lower()
    
    match_h = re.search(r'(\d*\.?\d*)\s*(hour|hr)', duration_str)
    if match_h:
        return float(match_h.group(1) or 1)
        
    match_m = re.search(r'(\d+)\s*(minute|min)', duration_str)
    if match_m:
        return int(match_m.group(1)) / 60.0
        
    return 0.0

def render_saved_recipes():
    st.header("Recipe Book 📚")
    
    recipe_files = [f for f in os.listdir(SAVED_RECIPES_DIR) if f.endswith('.md')]
    
    if not recipe_files:
        st.info("No recipes saved yet. Generate and execute a recipe plan in the Chat tab!")
        return
        
    for filename in recipe_files:
        filepath = os.path.join(SAVED_RECIPES_DIR, filename)
        title_for_display = filename.replace('.md', '').replace('_', ' ')
        raw_title = filename.replace('.md', '') 
        
        with st.form(key=f"delete_form_{raw_title}"):
            st.markdown(f"**{title_for_display}**")
            
            delete_button = st.form_submit_button(
                label="🗑️ Delete Recipe & Schedule",
                help="Deletes the local file and all associated reminders/events."
            )

            if delete_button:
                delete_recipe_and_events(filename, raw_title)
                st.rerun() 
            
            with st.expander("View Recipe Details"):
                try:
                    with open(filepath, 'r', encoding="utf-8") as f:
                        content = f.read()
                        st.markdown(content)
                except Exception as e:
                    st.error(f"Could not read recipe file: {e}")
        st.markdown("---")


def render_audit_log():
    st.header("Agent Audit Log 📜")
    
    if not st.session_state.log_history:
        st.info("No actions have been logged in this session.")
    
    log_content = ""
    for entry in reversed(st.session_state.log_history):
        log_content += f"{entry}\n"
    
    st.code(log_content)
    
def render_scheduled_events():
    st.header("Daily Schedule Timeline 📅")
    
    if not st.session_state.scheduled_events:
        st.info("No scheduled actions (reminders or calendar events) have been set this session.")
        return
    
    schedulable_events = []
    
    for event in st.session_state.scheduled_events:
        time_raw = event.get('time_raw', '23:59')
        duration_raw = event.get('duration_raw', '0 minutes')
        
        start_time_float = parse_time_to_float(time_raw)
        duration_hours = parse_duration_to_hours(duration_raw) if event['type'] == 'Calendar Event' else 0
        
        if start_time_float is not None:
            schedulable_events.append({
                "start": start_time_float,
                "end": start_time_float + duration_hours,
                "title": event['title'], 
                "type": event['type'],
                "display_message": event['description'] 
            })

    schedulable_events.sort(key=lambda x: x['start'])
    
    if not schedulable_events:
        st.warning("Could not plot events.")
        return

    st.markdown("---")
    st.subheader("Simulated Daily Schedule (00:00 - 23:59)")
    
    col_time, col_event = st.columns([1, 4])
    col_time.markdown("**Time**")
    col_event.markdown("**Event / Task**")
    st.markdown("---")
    
    current_hour = 0
    
    while current_hour < 24:
        current_time_float = float(current_hour)
        
        time_display = f"{current_hour:02}:00"
        
        col_time, col_event = st.columns([1, 4])
        col_time.markdown(f"**{time_display}**")

        events_to_display = [
            e for e in schedulable_events 
            if current_time_float <= e['start'] < (current_time_float + 1.0)
        ]

        if events_to_display:
            for event in events_to_display:
                start_h = int(event['start'])
                start_m = int((event['start'] - start_h) * 60)
                
                start_time_display = f"{start_h:02}:{start_m:02}"
                
                end_time_float = event['end']
                end_h = int(end_time_float)
                end_m = int((end_time_float - end_h) * 60)
                end_time_display = f"{end_h:02}:{end_m:02}"
                
                style_emoji = "🗓️" if event['type'] == 'Calendar Event' else "🔔"
                color = "#388E3C" if event['type'] == 'Calendar Event' else "#FBC02D"
                
                display_text = event['display_message']
                
                expected_prefix = "Reminder set: '"
                if event['type'] == 'Reminder' and display_text.startswith(expected_prefix):
                    display_text = display_text.split(expected_prefix, 1)[1].split("' at ", 1)[0]
                elif event['type'] == 'Calendar Event':
                    display_text = event['title']
                
                
                col_event.markdown(
                    f"<div style='background-color: {color}20; border-left: 5px solid {color}; padding: 5px; border-radius: 5px; margin-bottom: 5px;'>{style_emoji} **{display_text}** ({start_time_display} - {end_time_display})</div>",
                    unsafe_allow_html=True
                )
        
        current_hour += 1

# --- Render Functions for Sidebar Navigation ---

def render_chat_tab():
    st.title("💬 Chef Remy Chat")
    
    for message in st.session_state.messages:
        role = message["role"]
        content = message["content"]
        
        if role == "user":
            st.chat_message("user").write(content)
        elif role == "assistant":
            st.chat_message("assistant", avatar="👨‍🍳").markdown(content)
        elif role == "system":
            st.chat_message("system").caption(content)
            
    # Chat input handling (Run 1: Capture and Rerun)
    if st.session_state.processing_query is None:
        if prompt := st.chat_input("Ask Chef Remy to cook or access a recipe..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.processing_query = prompt
            st.rerun()

# --- MAIN STREAMLIT APP ---

st.set_page_config(
    page_title="The Little Chef Agent",
    page_icon="👨‍🍳",
    layout="wide"
)

initialize_state()
st.title("👨‍🍳 The Little Chef: AI Agent")

# Check for a query that needs processing from a previous run
if st.session_state.processing_query:
    process_query_and_run(st.session_state.processing_query)

# --- SIDEBAR NAVIGATION (Floating/Always Visible) ---
with st.sidebar:
    st.header("Agent Navigation")
    
    # NEW: Sidebar radio buttons replace tabs
    st.session_state.current_view = st.radio(
        "Go to:",
        ["💬 Chef Remy Chat", "📚 Saved Recipe Book", "📅 Scheduled Actions", "📜 Agent Audit Log"],
        key="sidebar_navigation_key"
    )
    
    st.markdown("---")
    st.header("Controls & Safety")
    
    st.session_state.confirm_scheduling = st.checkbox(
        "**Authorize External Actions (Safety):** I authorize the agent to execute scheduling and file save actions.",
        value=st.session_state.confirm_scheduling,
        key="sidebar_confirm_scheduling"
    )
    
    if st.session_state.confirm_scheduling:
        st.success("Actions are authorized.")
    else:
        st.warning("Actions (Reminders/Calendar/Save) will be DENIED until authorized.")
    
    st.markdown("---")
    st.caption("Instructions: Type a request like 'I have leftover rice, eggs, and soy sauce. Make a quick dinner for one.'")


# --- CONDITIONAL RENDERING ---

if st.session_state.current_view == "💬 Chef Remy Chat":
    render_chat_tab()
elif st.session_state.current_view == "📚 Saved Recipe Book":
    render_saved_recipes()
elif st.session_state.current_view == "📅 Scheduled Actions":
    render_scheduled_events()
elif st.session_state.current_view == "📜 Agent Audit Log":
    render_audit_log()