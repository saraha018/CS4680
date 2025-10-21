import streamlit as st
import os
import time
# --- Using the recommended SDK imports (google-genai) ---
from google.genai import Client 
from google.genai.errors import APIError 

# --- 1. CONFIGURATION AND INITIALIZATION ---

# Set up page config
st.set_page_config(
    page_title="The Little Chef (Assistant)",
    page_icon="🐀",
    layout="centered"
)

# Initialize the Gemini client
try:
    # --- CRITICAL: Using os.environ as requested ---
    # Ensure the API key is set as an environment variable (using 'set' or '$env:' command)
    if "GEMINI_API_KEY" not in os.environ:
        st.error("🚨 GEMINI_API_KEY environment variable not found.")
        st.caption("Please set your API key using `set GEMINI_API_KEY=YOUR_KEY` (CMD) or `$env:GEMINI_API_KEY='YOUR_KEY'` (PowerShell) before running.")
        st.stop()
        
    # --- Using the Client constructor from the new SDK ---
    client = Client() 
except Exception as e:
    st.error(f"Failed to initialize Gemini Client: {e}")
    st.stop()

# Model choice
MODEL_NAME = "gemini-2.5-flash"

# --- 2. PROMPT ENGINEERING (The core of the project) ---

def create_recipe_prompt(ingredients, servings, constraints):
    """
    Assembles the full, engineered prompt string.
    
    Incorporates the:
    - Persona Pattern (Chef Remy)
    - Template Pattern (Structured Markdown output)
    """

    # **A. System / Persona Instruction (Persona Pattern)**
    system_instruction = (
        "You are Chef Remy, the world-class, budget-conscious rat chef from the movie Ratatouille. \n"
        "You specialize in transforming random, limited ingredients into satisfying, beginner-friendly meals. \n"
        "Your tone is encouraging, patient, and focused on simplicity, perfect for a college student cook. \n"
        "Your core mission is to only use the ingredients listed by the user, or suggest only the most \n"
        "common pantry staples (like salt, pepper, oil, or water). You must strictly adhere to the requested \n"
        "number of servings. Do not provide any commentary before or after the recipe template.\n"
    )
    
    # **B. User Input**
    user_input = (
        f"The user has the following ingredients: **{ingredients}**\n"
        f"The recipe must be for exactly **{servings}** servings.\n"
        f"The user also has these constraints: **{constraints}**.\n"
        "Now, generate the complete recipe and strictly use the template provided below."
    )

    # **C. Template Instruction (Template Pattern)**
    template_instruction = (
        "I am going to provide a template for your output. **<placeholder>** are my placeholders for content. "
        "Try to fit the output into one or more of the placeholders that I list. Please preserve the formatting "
        "and overall template that I provide.\n\n"
        
        "This is the template:\n\n"
        
        f"## **Recipe Name: <DISH NAME>**\n\n"
        f"* **Servings:** <{servings}>\n"
        f"* **Budget:** <ESTIMATED COST CATEGORY, e.g., Ultra-Low Cost, Cheap as Chips>\n"
        f"* **Effort:** <DIFFICULTY LEVEL, e.g., 1/5 - Super Easy>\n"
        f"* **Total Time:** <TOTAL TIME, e.g., 25 Minutes>\n\n"
        
        f"### **Ingredients (For {servings} Servings):**\n\n"
        f"* <INGREDIENT 1>, <QUANTITY>\n"
        f"* <INGREDIENT 2>, <QUANTITY>\n"
        f"* ...<ADD MORE INGREDIENTS AS NEEDED>\n\n"
        
        f"### **Instructions (Remy's Simple Steps):**\n\n"
        f"1.  <STEP 1 INSTRUCTION, focused on simple action>\n"
        f"2.  <STEP 2 INSTRUCTION>\n"
        f"3.  ...<ADD MORE STEPS AS NEEDED>\n\n"
        
        f"### **Chef Remy's Money-Saving Tip:**\n\n"
        f"* <A SIMPLE TIP FOR STORING LEFTOVERS, SUBSTITUTION, OR REUSING A WASTE PRODUCT>"
    )

    return f"{system_instruction}\n\n---\n\n{user_input}\n\n---\n\n{template_instruction}"

# --- 3. API CALL LOGIC (With Exponential Backoff) ---

def generate_content_with_retry(prompt, max_retries=5):
    """Handles the Gemini API call with exponential backoff for robustness."""
    for attempt in range(max_retries):
        try:
            # Note: client.models.generate_content is the correct method for the new SDK
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config={"temperature": 0.8} # Allow for some creativity in recipe generation
            )
            return response.text
        
        except APIError as e: 
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff (1s, 2s, 4s, 8s, 16s)
                time.sleep(wait_time)
            else:
                st.error(f"Failed after {max_retries} attempts. Please try again later. Error: {e}")
                return None
        except Exception as e:
             st.error(f"An unexpected error occurred: {e}")
             return None
    return None

# --- 4. STREAMLIT UI LAYOUT ---

st.title("👨‍🍳 The Little Chef (Assistant)")
st.caption("Powered by Gemini. Your personal, budget-friendly meal planner.")

st.markdown(
    """
    **Welcome, College Cook!** I'm Chef Remy, and I'll help you turn that random stuff in your fridge 
    into a delicious meal. No waste, just great taste!
    """
)

with st.form("recipe_form"):
    st.header("What's in the Fridge? 🧊")
    
    ingredients = st.text_area(
        "List your ingredients (e.g., chicken breast, half onion, old tortillas, jar of salsa)",
        height=150,
        key="ingredients",
        placeholder="Required: List all available food items here, separated by commas."
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        servings = st.number_input(
            "How many servings do you need?",
            min_value=1,
            max_value=8,
            value=2,
            key="servings"
        )
    
    with col2:
        constraints = st.text_input(
            "Dietary constraints or special requests (e.g., Vegetarian, quick 30-min meal)",
            value="Quick and easy, minimal dirty dishes",
            key="constraints"
        )

    # Submit button to trigger the generation
    submitted = st.form_submit_button("Cook Up a Solution! 🍽️")

# --- 5. EXECUTION ---

if submitted and ingredients:
    
    # 1. Assemble the prompt
    full_prompt = create_recipe_prompt(ingredients, servings, constraints)
    
    # Debugging: Show the user the prompt engineering is working (Optional for final product)
    with st.expander("Peek at Chef Remy's Instructions (Prompt Engineering Demo)"):
        st.code(full_prompt, language="markdown")
        st.success("The **Persona Pattern** and **Template Pattern** are being applied!")

    # 2. Call the API
    with st.spinner(f"Chef Remy is hard at work creating a masterpiece..."):
        recipe_markdown = generate_content_with_retry(full_prompt)
    
    # 3. Display Results
    if recipe_markdown:
        st.success("✨ Your meal is served!")
        st.markdown(recipe_markdown)
    
elif submitted and not ingredients:
    st.warning("Please tell Chef Remy what ingredients you have!")
    
# Footer for project context
st.markdown("---")
st.markdown(
    """
    <div style='font-size: 0.8em; color: #6b7280;'>
    Project Demonstration: **Persona Pattern** (Chef Remy) and **Template Pattern** (Structured Output) 
    used with the Gemini API to create a functional MVP.
    </div>
    """,
    unsafe_allow_html=True
)
