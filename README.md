🥗 Enhanced Calorie Calculator
This Streamlit web application allows users to track calories and nutritional data for the food they consume. It enhances food parsing using the Cohere NLP API and retrieves nutritional information from the Nutritionix API.
🔍 Features
•	🧠 AI-enhanced food parsing using Cohere for better recognition and standardization
•	🍔 Food suggestions from Nutritionix for misspelled or unclear entries
•	🧮 Automatic calculation of total calories, protein, carbs, fats, fiber, and sodium
•	🗃️ Expandable view for each food item’s nutritional breakdown
•	🧹 Remove or clear all logged food items easily
•	📥 Export food log as a downloadable `.txt` report
•	✅ User-friendly UI built using Streamlit
🚀 How to Run

1. Install Dependencies

pip install -r requirements.txt

2. Set API Keys
Open `app.py` and update your API keys:

COHERE_API_KEY = "your_cohere_api_key"
NUTRITIONIX_APP_ID = "your_nutritionix_app_id"
NUTRITIONIX_API_KEY = "your_nutritionix_api_key"

3. Run the App

streamlit run app.py

📦 Dependencies
•	streamlit
•	cohere
•	requests
📄 File Structure

.
├── app.py               # Main Streamlit app
├── requirements.txt     # Python dependencies
├── screenshot.png       # Demo image (upload this separately)
└── README.docx          # This file

🧑‍💻 Developer
Developed by Srinivas Thota

🛡️ Disclaimer
This app is for educational and personal health tracking purposes only. Always consult a professional for dietary advice.
