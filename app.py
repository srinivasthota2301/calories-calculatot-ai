import streamlit as st
import cohere
import requests
import json
import re
from typing import Dict, List, Optional

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

# Nutritionix API URLs
NUTRITIONIX_NATURAL_URL = "https://trackapi.nutritionix.com/v2/natural/nutrients"
NUTRITIONIX_SEARCH_URL = "https://trackapi.nutritionix.com/v2/search/instant"

# Common food unit mappings for better parsing
UNIT_MAPPINGS = {
    'cup': 'cup', 'cups': 'cup',
    'tbsp': 'tablespoon', 'tablespoon': 'tablespoon', 'tablespoons': 'tablespoon',
    'tsp': 'teaspoon', 'teaspoon': 'teaspoon', 'teaspoons': 'teaspoon',
    'oz': 'ounce', 'ounce': 'ounce', 'ounces': 'ounce',
    'lb': 'pound', 'lbs': 'pound', 'pound': 'pound', 'pounds': 'pound',
    'g': 'gram', 'gram': 'gram', 'grams': 'gram',
    'kg': 'kilogram', 'kilogram': 'kilogram', 'kilograms': 'kilogram',
    'slice': 'slice', 'slices': 'slice',
    'piece': 'piece', 'pieces': 'piece',
    'serving': 'serving', 'servings': 'serving',
    'medium': 'medium', 'large': 'large', 'small': 'small'
}

def normalize_food_input(text: str) -> str:
    """
    Normalize and clean food input for better API recognition
    """
    # Remove extra whitespaces
    text = ' '.join(text.split())
    
    # Convert to lowercase for processing
    text_lower = text.lower()
    
    # Replace common abbreviations and normalize units
    for abbrev, full in UNIT_MAPPINGS.items():
        pattern = r'\b' + re.escape(abbrev) + r'\b'
        text_lower = re.sub(pattern, full, text_lower)
    
    # Fix common food name issues
    food_fixes = {
        'burger': 'hamburger',
        'fries': 'french fries',
        'soda': 'cola',
        'pop': 'cola',
        'sandwich': 'sandwich',
        'pizza slice': 'pizza',
    }
    
    for old, new in food_fixes.items():
        text_lower = text_lower.replace(old, new)
    
    return text_lower

def enhanced_food_parsing(user_input: str) -> str:
    """
    Enhanced food parsing using Cohere with better prompting
    """
    if not co:
        return normalize_food_input(user_input)
    
    try:
        prompt = f"""
        You are a nutrition expert. Convert this user input into a clear, standardized food description that a nutrition database would recognize.

        User input: "{user_input}"

        Rules:
        1. Include quantity and unit (e.g., "1 medium", "2 cups", "100 grams")
        2. Use standard food names (e.g., "hamburger" not "burger")
        3. Be specific about preparation when relevant (e.g., "grilled chicken breast")
        4. If multiple foods are mentioned, separate with commas
        5. Use common units: cup, tablespoon, teaspoon, ounce, gram, slice, piece, medium, large, small

        Examples:
        - "apple" → "1 medium apple"
        - "chicken burger" → "1 hamburger with chicken"
        - "2 pizza slices" → "2 slices pizza"
        - "bowl of rice" → "1 cup cooked white rice"

        Return only the cleaned food description:
        """
        
        response = co.generate(
            model="command",
            prompt=prompt,
            max_tokens=100,
            temperature=0.1,
            stop_sequences=["\n"]
        )
        
        parsed = response.generations[0].text.strip()
        return parsed if parsed else normalize_food_input(user_input)
        
    except Exception as e:
        st.warning("AI parsing unavailable, using basic parsing")
        return normalize_food_input(user_input)

def search_food_suggestions(query: str) -> List[str]:
    """
    Get food suggestions from Nutritionix search API
    """
    headers = {
        "x-app-id": NUTRITIONIX_APP_ID,
        "x-app-key": NUTRITIONIX_API_KEY,
    }
    
    try:
        params = {"query": query}
        response = requests.get(NUTRITIONIX_SEARCH_URL, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            suggestions = []
            
            # Get common foods
            if 'common' in data:
                for food in data['common'][:5]:  # Top 5 suggestions
                    suggestions.append(food['food_name'])
            
            return suggestions
    except:
        return []

def get_nutrition_data(food_query: str) -> Optional[Dict]:
    """
    Get nutrition data from Nutritionix with better error handling
    """
    headers = {
        "Content-Type": "application/json",
        "x-app-id": NUTRITIONIX_APP_ID,
        "x-app-key": NUTRITIONIX_API_KEY,
        "x-remote-user-id": "0"
    }
    
    payload = {
        "query": food_query,
        "timezone": "US/Eastern"
    }
    
    try:
        response = requests.post(NUTRITIONIX_NATURAL_URL, json=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("foods") and len(data["foods"]) > 0:
                food = data["foods"][0]
                return {
                    "name": food.get("food_name", "Unknown").title(),
                    "quantity": food.get("serving_qty", 1),
                    "unit": food.get("serving_unit", "serving"),
                    "calories": round(food.get("nf_calories", 0), 1),
                    "protein": round(food.get("nf_protein", 0), 1),
                    "carbs": round(food.get("nf_total_carbohydrate", 0), 1),
                    "fats": round(food.get("nf_total_fat", 0), 1),
                    "fiber": round(food.get("nf_dietary_fiber", 0), 1),
                    "sugar": round(food.get("nf_sugars", 0), 1),
                    "sodium": round(food.get("nf_sodium", 0), 1)
                }
        elif response.status_code == 404:
            return "not_found"
        else:
            return None
            
    except requests.exceptions.RequestException:
        return None

# --- UI Setup ---
st.set_page_config(page_title="Enhanced Calorie Calculator", layout="centered")

st.title("🍎 Enhanced Calorie Calculator")
st.markdown("*Improved accuracy with better food parsing and suggestions*")

# Initialize session state
if 'food_items' not in st.session_state:
    st.session_state.food_items = []

# Food Entry Form
with st.form("food_form", clear_on_submit=True):
    user_input = st.text_input(
        "What did you eat?", 
        placeholder="e.g., 1 medium apple, grilled chicken breast, 2 slices pepperoni pizza",
        help="Be specific! Include quantity, size, and preparation method for better accuracy."
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        submit = st.form_submit_button("Add Food", use_container_width=True)
    with col2:
        suggest = st.form_submit_button("Get Suggestions", use_container_width=True)

    if suggest and user_input:
        with st.spinner("Finding suggestions..."):
            suggestions = search_food_suggestions(user_input)
            if suggestions:
                st.info("**Suggestions:**")
                for suggestion in suggestions:
                    st.write(f"• {suggestion}")
            else:
                st.warning("No suggestions found. Try a different search term.")

    if submit and user_input:
        with st.spinner("Processing food..."):
            # Enhanced parsing
            parsed_food = enhanced_food_parsing(user_input)
            
            # Show what was parsed
            if parsed_food.lower() != user_input.lower():
                st.info(f"**Interpreted as:** {parsed_food}")
            
            # Get nutrition data
            result = get_nutrition_data(parsed_food)
            
            if isinstance(result, dict):
                st.session_state.food_items.append(result)
                st.success(f"✅ Added: {result['name']}")
                
            elif result == "not_found":
                st.error("❌ Food not found. Try:")
                st.write("• Being more specific (e.g., '1 medium apple' instead of 'apple')")
                st.write("• Using common food names")
                st.write("• Checking spelling")
                
                # Show suggestions for not found items
                suggestions = search_food_suggestions(user_input)
                if suggestions:
                    st.write("**Did you mean:**")
                    for suggestion in suggestions[:3]:
                        st.write(f"• {suggestion}")
            else:
                st.error("⚠️ Unable to process food. Please try again or check your internet connection.")

# Display food items and totals
if st.session_state.food_items:
    st.markdown("---")
    st.subheader("Your Food Log")
    
    # Calculate totals
    total_cal = sum(float(item.get("calories", 0)) for item in st.session_state.food_items)
    total_p = sum(float(item.get("protein", 0)) for item in st.session_state.food_items)
    total_c = sum(float(item.get("carbs", 0)) for item in st.session_state.food_items)
    total_f = sum(float(item.get("fats", 0)) for item in st.session_state.food_items)
    total_fiber = sum(float(item.get("fiber", 0)) for item in st.session_state.food_items)
    total_sodium = sum(float(item.get("sodium", 0)) for item in st.session_state.food_items)

    # Display totals in a nice grid
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🔥 Calories", f"{total_cal:.0f}")
        st.metric("🥩 Protein", f"{total_p:.1f}g")
    with col2:
        st.metric("🍞 Carbs", f"{total_c:.1f}g")
        st.metric("🧈 Fats", f"{total_f:.1f}g")
    with col3:
        st.metric("🌾 Fiber", f"{total_fiber:.1f}g")
        st.metric("🧂 Sodium", f"{total_sodium:.0f}mg")

    # Display individual items in an expandable format
    st.markdown("### Food Items")
    for idx, item in enumerate(st.session_state.food_items):
        with st.expander(f"{item.get('quantity', '')} {item.get('unit', '')} {item.get('name', '').title()} - {float(item.get('calories', 0)):.0f} cal"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Protein:** {item.get('protein', 0):.1f}g")
                st.write(f"**Carbs:** {item.get('carbs', 0):.1f}g")
            with col2:
                st.write(f"**Fats:** {item.get('fats', 0):.1f}g")
                st.write(f"**Fiber:** {item.get('fiber', 0):.1f}g")
            with col3:
                st.write(f"**Sugar:** {item.get('sugar', 0):.1f}g")
                st.write(f"**Sodium:** {item.get('sodium', 0):.0f}mg")
            
            if st.button("🗑️ Remove", key=f"remove_{idx}"):
                st.session_state.food_items.pop(idx)
                st.rerun()

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Clear All", use_container_width=True):
            st.session_state.food_items = []
            st.rerun()
    with col2:
        if st.button("📊 Export Data", use_container_width=True):
            # Create a simple text export
            export_text = "Food Log Export\n" + "="*20 + "\n\n"
            export_text += f"Total Calories: {total_cal:.0f}\n"
            export_text += f"Total Protein: {total_p:.1f}g\n"
            export_text += f"Total Carbs: {total_c:.1f}g\n"
            export_text += f"Total Fats: {total_f:.1f}g\n\n"
            export_text += "Individual Items:\n"
            for item in st.session_state.food_items:
                export_text += f"- {item.get('quantity', '')} {item.get('unit', '')} {item.get('name', '')} ({item.get('calories', 0):.0f} cal)\n"
            
            st.download_button(
                label="📥 Download",
                data=export_text,
                file_name="food_log.txt",
                mime="text/plain"
            )

else:
    st.info("👆 Add some food items above to start tracking your calories!")
    

# Footer
st.markdown("---")
st.markdown("Developed By SRINIVAS THOTA ")
