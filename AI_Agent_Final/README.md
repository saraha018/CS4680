# 👨‍🍳 The Little Chef: Scheduling Agent (AI Agent Project)

## Overview

The Little Chef (Scheduling Agent) is an AI Agent designed to solve the common college student dilemma: food waste and limited budgets. It leverages the Gemini API to transform a natural language list of fridge ingredients into simple, cost-effective recipes and, critically, performs concrete, external actions based on the generated content.

This project demonstrates the core principle of Agentic AI: translating LLM output into executable commands across different application domains (Local File I/O and Simulated Scheduling/Calendar APIs).

## 🚀 Agent Architecture and Feature Summary

The Agent operates using a strict, multi-step pipeline:

1. **Input**: User provides ingredients and optional scheduling intent (cook at 7 PM).
2. **LLM Planning**: The Gemini LLM generates two distinct outputs: the Markdown Recipe Text and a structured Action Plan (DSL).
3. **Action Interpretation**: The custom Python interpreter parses the DSL block, validates commands, and maps them to the Executor functions.
4. **Execution & Logging**: The Executor executes the commands (e.g., saving a file, scheduling an event) and records the transaction in an Audit Log.

| Component | Description | Agentic Action (DSL Examples) |
|-----------|-------------|-------------------------------|
| **Goal-Oriented Planning** | LLM analyzes the user's implicit goal (cook dinner) and generates a complete, multi-step plan. | LLM output includes `SAVE_RECIPE` and `ADD_CALENDAR_EVENT`. |
| **Time-Sensitive Scheduling** | Creates calendar events and reminders based on the recipe's Total Time and user-specified start time. | `ADD_CALENDAR_EVENT(time='7:00 PM', duration='30 minutes')` |
| **Persistent Storage** | Saves the full, structured recipe to a local Markdown file (`saved_recipes/`). | `SAVE_RECIPE(filename='...', content='...')` |
| **Auditability & Safety** | Logs every action (success, failure, parameters) to an audit file and requires explicit user authorization for scheduling. | `[SAFETY CHECK]` + Logging to `chef_agent_log.txt` |
| **Dynamic UI** | Uses a persistent sidebar navigator and visualizes scheduled events on a 24-hour timeline. | N/A (UI Feature) |

## 🛠️ Technology Stack

- **Generative AI**: Gemini API (`gemini-2.5-flash`)
- **Application Framework**: Streamlit (Provides interactive web UI and managed session state)
- **Language**: Python
- **Core Architectural Components**: Custom Action Interpreter, Executor Mapping, Local File I/O (`os`)

## ⚙️ Setup and Running the Application

### Prerequisites

- Python (3.8+)
- A valid Gemini API Key

### Installation

1. Clone this repository or ensure you have the `app.py` file saved.

2. Install the required Python packages:

   ```bash
   pip install streamlit
   ```

### Execution

1. **Set Your API Key**: You must set your Gemini API key as an environment variable in your terminal. This is crucial for the API calls to work.

   - **Linux/macOS**: `export GEMINI_API_KEY='YOUR_KEY_HERE'`
   - **Windows (PowerShell)**: `$env:GEMINI_API_KEY='YOUR_KEY_HERE'`

2. **Run the App**: In the same terminal session, execute the Streamlit application:

   ```bash
   streamlit run app.py
   ```

   The application will open automatically in your browser.

## 💡 Usage Examples

The agent interprets both ingredients and time-based intent.

| Goal | Example Input | Agent Actions |
|------|---------------|---------------|
| **Quick Default Schedule** | I have chicken, soy sauce, rice, and eggs. Make a quick dinner for two. | Schedules cooking event for 5 minutes from now + reminder for completion time. |
| **Specific Start Time** | Can you make a dinner with pasta, tomatoes, and cheese, and schedule me to start cooking at 6:45 PM? | Schedules cooking event for 6:45 PM + reminder for completion time. |
| **Review Agent Work** | (After generating a recipe) Switch to the 📅 Scheduled Actions tab. | Displays the cooking event and reminder on the 24-hour timeline. |
| **Cleanup** | (In the Recipe Book) Click 🗑️ Delete Recipe & Schedule. | Deletes the `.md` file and removes the associated entries from the Scheduled Actions log. |

