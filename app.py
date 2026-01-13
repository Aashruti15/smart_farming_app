import streamlit as st
import requests
from datetime import datetime
import json

# Try to import openai, but don't fail if it's not available
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Smart Farming Assistant",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        background-color: #fffbeb;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #92400e 0%, #ca8a04 100%);
        color: white;
        border-radius: 12px;
        padding: 12px;
        font-weight: 600;
        border: none;
    }
    .stButton>button:hover {
        box-shadow: 0 4px 12px rgba(146, 64, 14, 0.3);
    }
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #fef3c7;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .feature-card {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 24px;
        border-radius: 16px;
        cursor: pointer;
        transition: all 0.3s;
    }
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(16, 185, 129, 0.3);
    }
    .demo-badge {
        background: #fef3c7;
        color: #92400e;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
    }
    .chat-message {
        padding: 12px 16px;
        border-radius: 16px;
        margin-bottom: 12px;
    }
    .user-message {
        background: linear-gradient(135deg, #92400e 0%, #ca8a04 100%);
        color: white;
        margin-left: 20%;
    }
    .assistant-message {
        background: #f3f4f6;
        color: #1f2937;
        margin-right: 20%;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration - Using Streamlit Secrets
OPENAI_API_KEY = ""
OPENWEATHER_API_KEY = ""

# Read secrets silently
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    OPENWEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]
except:
    pass

# Initialize OpenAI client silently
client = None

if OPENAI_AVAILABLE and OPENAI_API_KEY:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
    except:
        pass

# Initialize session state
if 'profile' not in st.session_state:
    st.session_state.profile = None
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'weather_data' not in st.session_state:
    st.session_state.weather_data = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'welcome'

# Demo responses - removed, only using real API
DEMO_RESPONSES = {}

# Helper functions
def call_openai(prompt):
    """Call OpenAI API"""
    if not client:
        st.error("Please configure your OpenAI API key in secrets.")
        st.stop()
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful and knowledgeable farming assistant. Provide practical, actionable advice for farmers. Be specific, detailed, and consider the farmer's unique situation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        st.error("Please check your API key and try again.")
        st.stop()

def fetch_weather(location):
    """Fetch weather data from OpenWeather API"""
    try:
        # Get coordinates
        geo_url = f"https://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={OPENWEATHER_API_KEY}"
        geo_response = requests.get(geo_url)
        geo_data = geo_response.json()
        
        if not geo_data:
            return None
        
        lat, lon = geo_data[0]['lat'], geo_data[0]['lon']
        
        # Get weather
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
        weather_response = requests.get(weather_url)
        weather = weather_response.json()
        
        return {
            'temp': round(weather['main']['temp']),
            'humidity': weather['main']['humidity'],
            'description': weather['weather'][0]['description'],
            'icon': weather['weather'][0]['icon']
        }
    except:
        return None

# Page functions
def welcome_page():
    st.markdown("<h1 style='text-align: center; color: #92400e;'>🌾 Welcome to Smart Farming</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 18px; color: #78350f;'>Your AI-powered farming companion for smarter, sustainable agriculture</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Get Started", use_container_width=True):
            st.session_state.current_page = 'profile_setup' if not st.session_state.profile else 'dashboard'
            st.rerun()
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div style='text-align: center;'><div style='font-size: 48px;'>🌾</div><p>Smart Crops</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='text-align: center;'><div style='font-size: 48px;'>🌤️</div><p>Weather</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div style='text-align: center;'><div style='font-size: 48px;'>🤖</div><p>AI Assistant</p></div>", unsafe_allow_html=True)

def profile_setup_page():
    st.title("👤 Create Your Farm Profile")
    st.markdown("Tell us about your farm for personalized advice")
    
    with st.form("profile_form"):
        name = st.text_input("Full Name *", placeholder="Your name")
        location = st.text_input("Location *", placeholder="City, State/Country")
        farm_size = st.selectbox("Farm Size", ["Small (< 5 acres)", "Medium (5-50 acres)", "Large (50-200 acres)", "Very Large (200+ acres)"])
        crops = st.text_input("Primary Crops", placeholder="e.g., Corn, Wheat, Soybeans")
        experience = st.selectbox("Experience Level", ["Beginner (0-2 years)", "Intermediate (3-10 years)", "Experienced (10+ years)"])
        
        submitted = st.form_submit_button("Create Profile")
        
        if submitted:
            if name and location:
                st.session_state.profile = {
                    'full_name': name,
                    'location': location,
                    'farm_size': farm_size.split()[0].lower(),
                    'primary_crops': crops,
                    'experience_level': experience.split()[0].lower(),
                    'created_at': datetime.now().isoformat()
                }
                st.success("✅ Profile created successfully!")
                st.session_state.current_page = 'dashboard'
                st.rerun()
            else:
                st.error("Please fill in all required fields")

def dashboard_page():
    profile = st.session_state.profile
    name = profile['full_name'].split()[0] if profile else 'Farmer'
    
    st.title(f"👋 Good Day, {name}!")
    st.markdown("Here's your farming dashboard for today")
    
    # Fetch weather data if location is available
    weather_data = None
    if profile and profile.get('location'):
        if st.session_state.weather_data is None:
            weather_data = fetch_weather(profile['location'])
            if weather_data:
                st.session_state.weather_data = weather_data
        else:
            weather_data = st.session_state.weather_data
    
    # Metrics with better styling
    if weather_data:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🌾 Active Crops", len(profile.get('primary_crops', '').split(',')) if profile.get('primary_crops') else 0)
        
        with col2:
            st.metric("📊 Recommendations", len(st.session_state.recommendations))
        
        with col3:
            st.metric("💬 Chat Messages", len(st.session_state.chat_history))
        
        with col4:
            st.metric("🌤️ Temperature", f"{weather_data['temp']}°C")
            st.caption(f"{weather_data['description'].title()} • Humidity: {weather_data['humidity']}%")
    else:
        # Show only 3 columns if weather is not available
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🌾 Active Crops", len(profile.get('primary_crops', '').split(',')) if profile.get('primary_crops') else 0)
        
        with col2:
            st.metric("📊 Recommendations", len(st.session_state.recommendations))
        
        with col3:
            st.metric("💬 Chat Messages", len(st.session_state.chat_history))
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🛠️ AI Farming Tools")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🌱 Crop Planner", use_container_width=True):
            st.session_state.current_page = 'crop_planner'
            st.rerun()
        
        if st.button("🐛 Pest Identifier", use_container_width=True):
            st.session_state.current_page = 'pest_identifier'
            st.rerun()
    
    with col2:
        if st.button("🌍 Soil Optimizer", use_container_width=True):
            st.session_state.current_page = 'soil_optimizer'
            st.rerun()
        
        if st.button("💰 Cost-Saving Tips", use_container_width=True):
            st.session_state.current_page = 'cost_tips'
            st.rerun()
    
    with col3:
        if st.button("⛈️ Weather Alerts", use_container_width=True):
            st.session_state.current_page = 'weather_alerts'
            st.rerun()
        
        if st.button("🤖 AI Assistant", use_container_width=True):
            st.session_state.current_page = 'chat'
            st.rerun()

def crop_planner_page():
    st.title("🌱 Crop Planner")
    st.markdown("Get AI-powered crop recommendations")
    
    with st.form("crop_form"):
        month = st.selectbox("Planting Month", ["January", "February", "March", "April", "May", "June", 
                                                 "July", "August", "September", "October", "November", "December"])
        weather = st.selectbox("Weather Conditions", ["Hot & Dry", "Hot & Humid", "Mild/Temperate", "Cold", "Rainy/Monsoon"])
        soil = st.selectbox("Soil Type", ["Clay", "Sandy", "Loamy", "Silty", "Peaty"])
        
        submitted = st.form_submit_button("Get Recommendations")
        
        if submitted:
            with st.spinner("Analyzing..."):
                response = call_openai(f"""As an expert agricultural advisor, recommend the best crops for a farmer with the following conditions:
                
Location: {st.session_state.profile.get('location', 'Not specified')}
Planting Month: {month}
Weather Conditions: {weather}
Soil Type: {soil}
Farm Size: {st.session_state.profile.get('farm_size', 'small')}
Current Crops: {st.session_state.profile.get('primary_crops', 'None')}
Experience: {st.session_state.profile.get('experience_level', 'beginner')}

Provide 3-5 specific crop recommendations with:
1. Crop name and variety
2. Why it's suitable for these conditions
3. Expected yield timeline
4. Key care tips
5. Potential challenges to watch for

Be practical and specific to the farmer's situation.""")
                
                if response:
                    st.session_state.recommendations.append({
                        'type': 'crop_planner',
                        'title': f'Crop Recommendations for {month}',
                        'response': response,
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.markdown(response)
                    st.success("✅ Recommendation saved to history!")
                else:
                    st.error("Failed to get recommendations. Please try again.")

def soil_optimizer_page():
    st.title("🌍 Soil Optimizer")
    st.markdown("Improve your soil health with AI analysis")
    
    with st.form("soil_form"):
        ph = st.number_input("Soil pH Level", min_value=0.0, max_value=14.0, step=0.1, value=6.5)
        soil_type = st.selectbox("Soil Type", ["Clay", "Sandy", "Loamy", "Silty", "Chalky"])
        problems = st.multiselect("Current Problems", ["Poor Drainage", "Compaction", "Low Nutrients", "Erosion"])
        
        submitted = st.form_submit_button("Analyze Soil")
        
        if submitted:
            with st.spinner("Analyzing..."):
                response = call_openai(f"""As a soil science expert, provide detailed recommendations for improving this farmer's soil:

Farmer Profile:
- Location: {st.session_state.profile.get('location', 'Not specified')}
- Crops: {st.session_state.profile.get('primary_crops', 'Various crops')}
- Farm Size: {st.session_state.profile.get('farm_size', 'small')}

Soil Analysis:
- pH Level: {ph}
- Soil Type: {soil_type}
- Problems: {', '.join(problems) if problems else 'None specified'}

Please provide:
1. Overall soil health assessment
2. Specific amendments needed
3. Organic matter recommendations
4. Cover crop suggestions
5. Long-term soil improvement plan
6. Cost-effective solutions suitable for their farm size

Be practical and actionable.""")
                
                if response:
                    st.session_state.recommendations.append({
                        'type': 'soil_optimizer',
                        'title': 'Soil Health Analysis',
                        'response': response,
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.markdown(response)
                    st.success("✅ Analysis saved to history!")
                else:
                    st.error("Failed to get analysis. Please try again.")

def pest_identifier_page():
    st.title("🐛 Pest Identifier")
    st.markdown("Identify pests and get treatment advice")
    
    with st.form("pest_form"):
        crop = st.text_input("Affected Crop", placeholder="e.g., Tomatoes, Corn")
        symptoms = st.text_area("Symptoms Observed", placeholder="Describe what you see: holes, discoloration, wilting...")
        
        submitted = st.form_submit_button("Identify Pest")
        
        if submitted:
            if crop and symptoms:
                with st.spinner("Identifying..."):
                    response = call_openai(f"""As an agricultural pest control expert, identify the pest and provide treatment recommendations:

Farmer Details:
- Location: {st.session_state.profile.get('location', 'Not specified')}
- Farm Size: {st.session_state.profile.get('farm_size', 'small')}

Problem Description:
- Affected Crop: {crop}
- Symptoms: {symptoms}

Please provide:
1. Most likely pest identification (with confidence level)
2. Alternative possibilities to consider
3. Immediate control measures
4. Long-term prevention strategies
5. Organic/natural treatment options
6. Chemical treatments (as last resort) with safety guidelines
7. When to seek professional help

Be specific and practical.""")
                    
                    if response:
                        st.session_state.recommendations.append({
                            'type': 'pest_identifier',
                            'title': f'Pest Identification for {crop}',
                            'response': response,
                            'created_at': datetime.now().isoformat()
                        })
                        
                        st.markdown(response)
                        st.success("✅ Report saved to history!")
                    else:
                        st.error("Failed to identify pest. Please try again.")
            else:
                st.error("Please provide crop name and symptoms")

def weather_alerts_page():
    st.title("⛈️ Weather Alerts")
    st.markdown("Get weather-based farming advice")
    
    with st.form("weather_form"):
        stage = st.selectbox("Current Crop Stage", ["Planting/Seeding", "Germination", "Vegetative Growth", 
                                                     "Flowering", "Fruiting", "Ready for Harvest"])
        activity = st.selectbox("Planned Activity", ["Irrigation/Watering", "Fertilizing", "Pesticide Spraying", 
                                                      "Harvesting", "Planting", "Soil Preparation"])
        urgency = st.radio("How Urgent?", ["Low", "Medium", "High"], horizontal=True)
        
        submitted = st.form_submit_button("Get Weather Advice")
        
        if submitted:
            with st.spinner("Analyzing..."):
                st.markdown(f"""
                ## Weather-Based Advice
                
                ### Current Situation
                - **Crop Stage**: {stage}
                - **Activity**: {activity}
                - **Urgency**: {urgency}
                
                ### Best Timing
                - Early morning (6-9 AM) or late afternoon (4-7 PM)
                - Avoid midday heat and windy conditions
                
                ### Activity-Specific Tips
                - Monitor weather forecasts daily
                - Plan activities around dry windows
                - Have backup plans ready
                """)
                st.success("✅ Advice generated!")

def cost_tips_page():
    st.title("💰 Cost-Saving Tips")
    st.markdown("Sustainable and economical farming methods")
    
    categories = {
        "💧 Water Conservation": "water",
        "🌿 Fertilizer Efficiency": "fertilizer",
        "🐛 Pest Control": "pest",
        "⚡ Energy Savings": "energy",
        "🌱 Planting Methods": "planting"
    }
    
    category = st.selectbox("Select Category", list(categories.keys()))
    
    if st.button("Get Tips"):
        with st.spinner("Loading tips..."):
            st.markdown(f"""
            ## Top 5 Money-Saving Strategies
            
            ### 1. DIY Solutions 💰 Save 40%
            - Build your own systems
            - Repurpose materials
            - Learn from free resources
            
            ### 2. Bulk Purchasing 💰 Save 25%
            - Join local co-ops
            - Split orders with neighbors
            - Buy during off-season
            
            ### 3. Natural Methods 💰 Save 35%
            - Use organic alternatives
            - Companion planting
            - Beneficial insects
            
            ### 4. Water Management 💰 Save 30%
            - Drip irrigation
            - Rainwater harvesting
            - Mulching
            
            ### 5. Preventive Care 💰 Save 20%
            - Regular monitoring
            - Early intervention
            - Soil health focus
            """)
            st.success("✅ Tips loaded!")

def chat_page():
    st.title("🤖 AI Farming Assistant")
    st.markdown("Ask me anything about farming")
    
    # Display chat history
    for msg in st.session_state.chat_history:
        if msg['role'] == 'user':
            st.markdown(f"<div class='chat-message user-message'>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-message assistant-message'>🤖 {msg['content']}</div>", unsafe_allow_html=True)
    
    # Chat input
    user_input = st.chat_input("Type your farming question...")
    
    if user_input:
        st.session_state.chat_history.append({'role': 'user', 'content': user_input})
        
        with st.spinner("Thinking..."):
            # Build comprehensive prompt for OpenAI
            profile_context = f"""
Farmer Profile:
- Name: {st.session_state.profile.get('full_name', 'Farmer')}
- Location: {st.session_state.profile.get('location', 'Not specified')}
- Farm Size: {st.session_state.profile.get('farm_size', 'small')}
- Crops: {st.session_state.profile.get('primary_crops', 'Various')}
- Experience: {st.session_state.profile.get('experience_level', 'beginner')}
"""
            
            full_prompt = f"""You are a friendly and knowledgeable AI farming assistant.

{profile_context}

Farmer's Question: {user_input}

Provide a helpful, conversational response. Be friendly but informative. Keep responses focused and practical. Use the farmer's profile information to give personalized advice."""

            response = call_openai(full_prompt)
            
            if response:
                st.session_state.chat_history.append({'role': 'assistant', 'content': response})
            else:
                st.error("Failed to get response. Please try again.")
        
        st.rerun()

def history_page():
    st.title("📚 Recommendation History")
    
    if not st.session_state.recommendations:
        st.info("No recommendations yet. Use the AI tools to get personalized advice!")
    else:
        for i, rec in enumerate(reversed(st.session_state.recommendations)):
            with st.expander(f"📊 {rec['title']} - {rec['created_at'][:10]}"):
                st.markdown(rec['response'])
                if st.button(f"Delete", key=f"del_{i}"):
                    st.session_state.recommendations.remove(rec)
                    st.rerun()

def settings_page():
    st.title("⚙️ Settings")
    
    if st.session_state.profile:
        st.subheader("👤 Profile Information")
        
        with st.form("settings_form"):
            name = st.text_input("Full Name", value=st.session_state.profile.get('full_name', ''))
            location = st.text_input("Location", value=st.session_state.profile.get('location', ''))
            crops = st.text_input("Primary Crops", value=st.session_state.profile.get('primary_crops', ''))
            
            if st.form_submit_button("Save Profile"):
                st.session_state.profile.update({
                    'full_name': name,
                    'location': location,
                    'primary_crops': crops
                })
                st.success("✅ Profile updated!")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📊 Data Management")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear Chat History"):
            st.session_state.chat_history = []
            st.success("Chat cleared!")
    
    with col2:
        if st.button("Clear Recommendations"):
            st.session_state.recommendations = []
            st.success("Recommendations cleared!")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Sign Out", type="secondary"):
        st.session_state.profile = None
        st.session_state.current_page = 'welcome'
        st.rerun()

# Main app
def main():
    # Sidebar navigation
    with st.sidebar:
        st.image("https://em-content.zobj.net/source/apple/391/sheaf-of-rice_1f33e.png", width=80)
        st.title("Smart Farming")
        
        if st.session_state.profile:
            st.markdown(f"**👤 {st.session_state.profile.get('full_name', 'Farmer')}**")
            st.markdown(f"📍 {st.session_state.profile.get('location', 'Unknown')}")
            st.divider()
            
            if st.button("🏠 Dashboard", use_container_width=True):
                st.session_state.current_page = 'dashboard'
                st.rerun()
            
            if st.button("📚 History", use_container_width=True):
                st.session_state.current_page = 'history'
                st.rerun()
            
            if st.button("💬 AI Chat", use_container_width=True):
                st.session_state.current_page = 'chat'
                st.rerun()
            
            if st.button("⚙️ Settings", use_container_width=True):
                st.session_state.current_page = 'settings'
                st.rerun()
    
    # Page routing
    if st.session_state.current_page == 'welcome':
        welcome_page()
    elif st.session_state.current_page == 'profile_setup':
        profile_setup_page()
    elif st.session_state.current_page == 'dashboard':
        dashboard_page()
    elif st.session_state.current_page == 'crop_planner':
        crop_planner_page()
    elif st.session_state.current_page == 'soil_optimizer':
        soil_optimizer_page()
    elif st.session_state.current_page == 'pest_identifier':
        pest_identifier_page()
    elif st.session_state.current_page == 'weather_alerts':
        weather_alerts_page()
    elif st.session_state.current_page == 'cost_tips':
        cost_tips_page()
    elif st.session_state.current_page == 'chat':
        chat_page()
    elif st.session_state.current_page == 'history':
        history_page()
    elif st.session_state.current_page == 'settings':
        settings_page()

if __name__ == "__main__":
    main()