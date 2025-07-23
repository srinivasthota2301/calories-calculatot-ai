import streamlit as st
import cohere
import requests
import json

# --- API CONFIGURATION ---
# ⚠️ SECURITY WARNING: Regenerate these keys immediately after testing!
COHERE_API_KEY = "7Inil0a76TZkMeSnu63ZAlW7f7HYQH1Iduuca8Kv"
NUTRITIONIX_APP_ID = "f2458a93"
NUTRITIONIX_API_KEY = "67637366ff82c52a7dd267eeed0bda7f"

# Initialize Cohere client
try:
    co = cohere.Client(COHERE_API_KEY)
except Exception as e:
    co = None

# Nutritionix API URL
NUTRITIONIX_URL = "https://trackapi.nutritionix.com/v2/natural/nutrients"

# --- UI Setup ---
st.set_page_config(page_title="Calorie Calculator", layout="centered")

st.title("🍎 Calorie Calculator")

# Initialize session state
if 'food_items' not in st.session_state:
    st.session_state.food_items = []

# Food Entry Form
with st.form("food_form", clear_on_submit=True):
    user_input = st.text_input("What did you eat?", placeholder="e.g., 1 apple, chicken burger, 2 slices pizza")
    submit = st.form_submit_button("Add Food")

    if submit and user_input:
        with st.spinner("Processing..."):
            # Use Cohere to clean/parse the food input (if available)
            parsed_food = user_input
            
            if co:
                try:
                    prompt = f"""
                    Clean and format this food description for a nutrition API:
                    "{user_input}"
                    
                    Return only the cleaned food description (e.g., "1 medium apple", "2 slices pizza")
                    """
                    
                    response = co.generate(
                        model="command",
                        prompt=prompt,
                        max_tokens=50,
                        temperature=0.2
                    )
                    parsed_food = response.generations[0].text.strip()
                except Exception as e:
                    pass  # Continue with original input if AI parsing fails

            # Call Nutritionix API
            headers = {
                "Content-Type": "application/json",
                "x-app-id": NUTRITIONIX_APP_ID,
                "x-app-key": NUTRITIONIX_API_KEY,
                "x-remote-user-id": "0"
            }
            
            payload = {"query": parsed_food}
            
            try:
                res = requests.post(NUTRITIONIX_URL, json=payload, headers=headers, timeout=15)
                
                if res.status_code == 200:
                    data = res.json()
                    if data.get("foods") and len(data["foods"]) > 0:
                        food = data["foods"][0]
                        item = {
                            "name": food.get("food_name", "Unknown"),
                            "quantity": food.get("serving_qty", 1),
                            "unit": food.get("serving_unit", "serving"),
                            "calories": round(food.get("nf_calories", 0), 1),
                            "protein": round(food.get("nf_protein", 0), 1),
                            "carbs": round(food.get("nf_total_carbohydrate", 0), 1),
                            "fats": round(food.get("nf_total_fat", 0), 1)
                        }
                        st.session_state.food_items.append(item)
                        st.success(f"Added: {item['name']}")
                    else:
                        st.error("Food not found. Try being more specific.")
                else:
                    st.error("Unable to process food. Please try again.")
                    
            except requests.exceptions.RequestException as e:
                st.error("Connection error. Please try again.")

# Display food items and totals
if st.session_state.food_items:
    st.markdown("---")
    
    # Calculate totals
    total_cal = sum(float(item.get("calories", 0)) for item in st.session_state.food_items)
    total_p = sum(float(item.get("protein", 0)) for item in st.session_state.food_items)
    total_c = sum(float(item.get("carbs", 0)) for item in st.session_state.food_items)
    total_f = sum(float(item.get("fats", 0)) for item in st.session_state.food_items)

    # Display totals
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Calories", f"{total_cal:.0f}")
    with col2:
        st.metric("Protein", f"{total_p:.0f}g")
    with col3:
        st.metric("Carbs", f"{total_c:.0f}g")
    with col4:
        st.metric("Fats", f"{total_f:.0f}g")

    # Display individual items
    for idx, item in enumerate(st.session_state.food_items):
        col1, col2 = st.columns([5, 1])
        with col1:
            st.write(f"{item.get('quantity', '')} {item.get('unit', '')} {item.get('name', '').title()} - {float(item.get('calories', 0)):.0f} cal")
        with col2:
            if st.button("✕", key=f"remove_{idx}"):
                st.session_state.food_items.pop(idx)
                st.rerun()

    # Reset button
    if st.button("Clear All"):
        st.session_state.food_items = []
        st.rerun()