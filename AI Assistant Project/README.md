### 👨‍🍳 The Little Chef (Assistant)



#### Project Overview



The Little Chef (Assistant) is a Minimum Viable Product (MVP) developed to solve the common college student dilemma: food waste and limited budgets. By leveraging the power of Generative AI, the application turns a random list of fridge ingredients into simple, cost-effective, and beginner-friendly recipes.



This project was built using prompt engineering techniques to ensure a structured, user-friendly, and goal-oriented AI output.



#### 🚀 Problem Solved



Feature



Description



Value to College Students



No Food Waste



Generates recipes only using the ingredients listed by the user.



Maximizes the use of existing groceries, saving money.



Beginner Friendly



The AI adopts a patient, encouraging tone and focuses on simple steps.



Reduces cooking anxiety for novice cooks.



Budget Focus



Output includes an estimated budget category and money-saving tips.



Reinforces the core mission of financial health.



#### 🛠️ Technology Stack



Generative AI: Gemini API (gemini-2.5-flash model)



Application Framework: Streamlit (for quick, responsive web UI development in Python)



Language: Python



Key Dependencies: google-genai, streamlit



#### ✨ Prompt Engineering Techniques (Assignment Focus)



This application integrates two specific prompt engineering patterns to enhance user experience and ensure reliable, structured output.



##### 1\. The Persona Pattern (Chef Remy)



Implementation: The system instruction assigns the AI the persona of Chef Remy, the expert rat chef from the movie Ratatouille.



Goal: To control the AI's tone and expertise. Remy's persona ensures the advice is encouraging, focuses on simplicity, and remains budget-conscious, making the experience more engaging for college students.



##### 2\. The Template Pattern (Structured Output)



Implementation: The user prompt includes a strict, multi-line Markdown template (using the <placeholder> method) that the AI must follow precisely.



Goal: To ensure the output is highly structured (Title, Servings, Budget, Instructions, Pro Tip). This structure is crucial for the Streamlit UI to display the recipe cleanly and reliably, improving usability.



#### ⚙️ Setup and Running the Application



##### Prerequisites



Python (3.8+)



A valid Gemini API Key



##### Installation



Clone the repository (or save the app.py file).



Install the required Python packages:



pip install google-genai streamlit





###### Execution



Set Your API Key: You must set your Gemini API key as an environment variable in your terminal. Do this step before starting Streamlit.



In PowerShell:



$env:GEMINI\_API\_KEY='YOUR\_ACTUAL\_KEY\_HERE'





In Command Prompt (CMD):



set GEMINI\_API\_KEY=YOUR\_ACTUAL\_KEY\_HERE





Run the App: In the same terminal session, execute the Streamlit application:



streamlit run app.py





The application will open automatically in your browser, ready for a live demo!

