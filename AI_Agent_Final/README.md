# 👨‍🍳 The Little Chef: Scheduling Agent (AI Agent Project)

## Overview

The Little Chef (Scheduling Agent) is an AI Agent designed to solve the common college student dilemma: food waste and limited budgets. It leverages the Gemini API to transform a natural language list of fridge ingredients into simple, cost-effective recipes and, critically, performs concrete, external actions based on the generated content.

This project demonstrates the core principle of Agentic AI: translating LLM output into executable commands across different application domains (Local File I/O and Simulated Scheduling/Calendar APIs).

## 🚀 Agent Architecture and Feature Summary

The Agent operates using a strict, multi-step pipeline:

1. **Input**: User provides ingredients and optional scheduling intent (cook at 7 PM).
2. **Context Injection**: Agent loads memory (meal history, disliked ingredients) and weather context to personalize recommendations.
3. **LLM Planning**: The Gemini LLM generates two distinct outputs: the Markdown Recipe Text and a structured Action Plan (DSL).
4. **Action Interpretation**: The custom Python interpreter parses the DSL block, validates commands, and maps them to the Executor functions.
5. **Execution & Logging**: The Executor executes the commands (e.g., saving a file, scheduling an event) and records the transaction in an Audit Log.
6. **Memory Update**: Successful recipes are added to meal history for future context.

| Component | Description | Agentic Action (DSL Examples) |
|-----------|-------------|-------------------------------|
| **Goal-Oriented Planning** | LLM analyzes the user's implicit goal (cook dinner) and generates a complete, multi-step plan. | LLM output includes `SAVE_RECIPE` and `ADD_CALENDAR_EVENT`. |
| **Time-Sensitive Scheduling** | Creates calendar events and reminders based on the recipe's Total Time and user-specified start time. | `ADD_CALENDAR_EVENT(time='7:00 PM', duration='30 minutes')` |
| **Persistent Storage** | Saves the full, structured recipe to a local Markdown file (`saved_recipes/`). | `SAVE_RECIPE(filename='...', content='...')` |
| **Auditability & Safety** | Logs every action (success, failure, parameters) to an audit file and requires explicit user authorization for scheduling. | `[SAFETY CHECK]` + Logging to `chef_agent_log.txt` |
| **Long-Term Memory** | Tracks last 10 recipes made and maintains a persistent list of disliked ingredients stored in `meal_history.json`. | Stores meal history and learns from deletions. |
| **Adaptive Learning** | When a recipe is deleted, the agent extracts ingredients and adds them to the disliked list. Users can also directly express dislikes in chat. | Intent classification: "I don't like X" updates memory automatically. |
| **Weather Awareness** | Simulated weather API adjusts recipe suggestions based on time of day and temperature (e.g., hot weather → no-cook meals). | Context-aware recipe generation. |
| **Dynamic UI** | Uses a persistent sidebar navigator and visualizes scheduled events on a 24-hour timeline. | N/A (UI Feature) |

## 🛠️ Technology Stack

- **Generative AI**: Gemini API (`gemini-2.5-flash`)
- **Application Framework**: Streamlit (Provides interactive web UI and managed session state)
- **Language**: Python
- **Core Architectural Components**: Custom Action Interpreter, Executor Mapping, Local File I/O (`os`), JSON-based Memory System
- **Data Storage**: 
  - Markdown files for recipes (`saved_recipes/`)
  - JSON file for long-term memory (`meal_history.json`)
  - Text file for audit logging (`chef_agent_log.txt`)

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

   > **Note**: The application uses only the Python standard library (`os`, `json`, `re`, `datetime`, `time`, `urllib`) in addition to Streamlit, so no additional dependencies are required.

### Execution

1. **Set Your API Key**: You must set your Gemini API key as an environment variable in your terminal. This is crucial for the API calls to work.

   - **Linux/macOS**: `export GEMINI_API_KEY='YOUR_KEY_HERE'`
   - **Windows (PowerShell)**: `$env:GEMINI_API_KEY='YOUR_KEY_HERE'`

2. **Run the App**: In the same terminal session, execute the Streamlit application:

   ```bash
   streamlit run app.py
   ```

   The application will open automatically in your browser.

## 📁 Project Structure

```
AI_Agent_Final/
├── app.py                      # Main Streamlit application
├── chef_agent_log.txt          # Audit log of all agent actions
├── meal_history.json           # Long-term memory (created on first run)
├── saved_recipes/              # Directory containing saved recipe files
│   ├── Recipe_Name_1.md
│   └── Recipe_Name_2.md
└── README.md                   # This file
```

## 💡 Usage Examples

The agent interprets ingredients, time-based intent, and preference learning.

| Goal | Example Input | Agent Actions |
|------|---------------|---------------|
| **Quick Default Schedule** | I have chicken, soy sauce, rice, and eggs. Make a quick dinner for two. | Generates recipe considering weather/time of day, schedules cooking event for 5 minutes from now + reminder for completion time. |
| **Specific Start Time** | Can you make a dinner with pasta, tomatoes, and cheese, and schedule me to start cooking at 6:45 PM? | Schedules cooking event for 6:45 PM + reminder for completion time. |
| **Express Dislikes** | I don't like mushrooms or bell peppers. | Agent learns preferences and avoids these ingredients in future recipes. |
| **Adaptive Learning** | (In Recipe Book) Delete a recipe → Agent asks which ingredients to avoid. | Adds specified ingredients to disliked list permanently stored in memory. |
| **Review Agent Work** | (After generating a recipe) Switch to the 📅 Scheduled Actions tab. | Displays the cooking event and reminder on the 24-hour timeline. |
| **Memory-Aware Recipes** | Ask for a second recipe after cooking one. | Agent avoids suggesting the exact same recipe name (checks last 10 meals). |
| **Cleanup** | (In the Recipe Book) Click 🗑️ Delete Recipe & Schedule. | Deletes the `.md` file, removes scheduled events, and optionally updates disliked ingredients list. |

## 🧠 Memory and Learning Features

The agent maintains persistent memory across sessions:

- **Meal History**: Tracks the last 10 recipes you've cooked to avoid repetition
- **Disliked Ingredients**: Permanently stores ingredients you want to avoid
- **Weather Context**: Adjusts recipe suggestions based on time of day and simulated weather conditions
- **Learning from Deletion**: When you delete a recipe, the agent extracts ingredients and offers to add them to your disliked list

All memory is stored locally in `meal_history.json` and persists between application sessions.

