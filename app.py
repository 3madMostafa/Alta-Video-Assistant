import streamlit as st
import json
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="Alta Video Assistant",
    page_icon="🔒",
    layout="centered"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "last_intent" not in st.session_state:
    st.session_state.last_intent = None
if "last_entity" not in st.session_state:
    st.session_state.last_entity = None
if "last_api_response" not in st.session_state:
    st.session_state.last_api_response = None
if "frequent_questions" not in st.session_state:
    st.session_state.frequent_questions = {}

# API Configuration
AVAILABLE_APIS = {
    "about": {"endpoint": "/api/v1/about", "method": "GET"},
    "me": {"endpoint": "/api/v1/me", "method": "GET"},
    "devices": {"endpoint": "/api/v1/query:devices", "method": "POST"},
    "alerts": {"endpoint": "/api/v1/ongoingAlerts", "method": "GET"}
}

def track_question(intent):
    """Track frequently asked questions"""
    if intent in st.session_state.frequent_questions:
        st.session_state.frequent_questions[intent] += 1
    else:
        st.session_state.frequent_questions[intent] = 1

def get_most_frequent_questions(top_n=3):
    """Get the most frequently asked questions"""
    sorted_questions = sorted(
        st.session_state.frequent_questions.items(),
        key=lambda x: x[1],
        reverse=True
    )
    return [q[0] for q in sorted_questions[:top_n]]

def analyze_intent(user_message):
    """
    Analyze user intent and determine API call requirements
    """
    message_lower = user_message.lower()
    
    # Context-based follow-up handling
    if st.session_state.last_intent and any(word in message_lower for word in 
        ["which", "what about", "show me", "details", "more", "specific", "that", "those", "them"]):
        
        # Follow-up on devices
        if st.session_state.last_intent == "get_devices":
            if any(word in message_lower for word in ["offline", "down", "not working", "disconnected"]):
                return {
                    "intent": "filter_offline_devices",
                    "api": None,
                    "method": None,
                    "params": {},
                    "uses_context": True,
                    "confidence_message": "I'll filter the offline devices from the previous results.",
                    "requires_confirmation": False,
                    "follow_up_suggestions": [
                        "Show all online devices",
                        "Check for alerts on these devices",
                        "Get system information"
                    ]
                }
            elif any(word in message_lower for word in ["online", "working", "connected"]):
                return {
                    "intent": "filter_online_devices",
                    "api": None,
                    "method": None,
                    "params": {},
                    "uses_context": True,
                    "confidence_message": "I'll filter the online devices from the previous results.",
                    "requires_confirmation": False,
                    "follow_up_suggestions": [
                        "Show offline devices",
                        "Check device details",
                        "View ongoing alerts"
                    ]
                }
    
    # System information intents
    if any(word in message_lower for word in ["about", "version", "system", "info"]):
        return {
            "intent": "get_system_info",
            "api": "/api/v1/about",
            "method": "GET",
            "params": {},
            "uses_context": False,
            "confidence_message": "I will retrieve system information.",
            "requires_confirmation": False,
            "follow_up_suggestions": [
                "Show my account details",
                "List all devices",
                "Check for alerts"
            ]
        }
    
    # User account intents
    elif any(word in message_lower for word in ["my account", "my profile", "my info", "who am i", "account details"]):
        return {
            "intent": "get_user_account",
            "api": "/api/v1/me",
            "method": "GET",
            "params": {},
            "uses_context": False,
            "confidence_message": "I will retrieve your account information.",
            "requires_confirmation": False,
            "follow_up_suggestions": [
                "Show all devices",
                "Check ongoing alerts",
                "Get system information"
            ]
        }
    
    # Device query intents
    elif any(word in message_lower for word in ["camera", "cameras", "device", "devices", "list"]):
        return {
            "intent": "get_devices",
            "api": "/api/v1/query:devices",
            "method": "POST",
            "params": {},
            "uses_context": False,
            "confidence_message": "I will retrieve all registered devices.",
            "requires_confirmation": False,
            "follow_up_suggestions": [
                "Which devices are offline?",
                "Show device details",
                "Check for alerts"
            ]
        }
    
    # Alert intents
    elif any(word in message_lower for word in ["alert", "alerts", "notification", "notifications", "ongoing", "active", "issue", "issues"]):
        return {
            "intent": "get_ongoing_alerts",
            "api": "/api/v1/ongoingAlerts",
            "method": "GET",
            "params": {},
            "uses_context": False,
            "confidence_message": "I will check for ongoing alerts.",
            "requires_confirmation": False,
            "follow_up_suggestions": [
                "Show alert details",
                "View affected devices",
                "Get system status"
            ]
        }
    
    # Help and capabilities
    elif any(word in message_lower for word in ["help", "what can you do", "capabilities", "commands"]):
        return {
            "intent": "show_help",
            "api": None,
            "method": None,
            "params": {},
            "uses_context": False,
            "confidence_message": None,
            "requires_confirmation": False,
            "follow_up_suggestions": [
                "Show all devices",
                "Check for alerts",
                "Show my account"
            ]
        }
    
    # Unsupported query
    else:
        return {
            "intent": "unsupported",
            "api": None,
            "method": None,
            "params": {},
            "uses_context": False,
            "confidence_message": None,
            "requires_confirmation": False,
            "follow_up_suggestions": [
                "Show all devices",
                "Check for alerts",
                "Get system information"
            ]
        }

def simulate_api_call(api_endpoint, method):
    """
    Simulate API call with mock responses
    In production, replace this with actual API calls
    """
    time.sleep(0.5)  # Simulate network delay
    
    if api_endpoint == "/api/v1/about":
        return {
            "version": "2.3.1",
            "build": "20240115",
            "system_name": "Alta Video Security System",
            "uptime": "45 days",
            "status": "operational"
        }
    
    elif api_endpoint == "/api/v1/me":
        return {
            "user_id": "usr_12345",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "role": "administrator",
            "organization": "Acme Security",
            "created_at": "2023-06-15T10:30:00Z"
        }
    
    elif api_endpoint == "/api/v1/query:devices":
        return {
            "total_count": 8,
            "devices": [
                {"id": "cam_001", "name": "Front Entrance", "type": "camera", "status": "online", "location": "Building A"},
                {"id": "cam_002", "name": "Parking Lot", "type": "camera", "status": "online", "location": "Exterior"},
                {"id": "cam_003", "name": "Lobby Camera", "type": "camera", "status": "online", "location": "Building A"},
                {"id": "cam_004", "name": "Back Exit", "type": "camera", "status": "offline", "location": "Building B"},
                {"id": "cam_005", "name": "Server Room", "type": "camera", "status": "online", "location": "Building A"},
                {"id": "cam_006", "name": "Loading Dock", "type": "camera", "status": "offline", "location": "Warehouse"},
                {"id": "cam_007", "name": "Reception Area", "type": "camera", "status": "online", "location": "Building A"},
                {"id": "cam_008", "name": "Emergency Exit", "type": "camera", "status": "online", "location": "Building B"}
            ]
        }
    
    elif api_endpoint == "/api/v1/ongoingAlerts":
        return {
            "alert_count": 2,
            "alerts": [
                {
                    "id": "alert_001",
                    "type": "device_offline",
                    "severity": "high",
                    "device": "Back Exit (cam_004)",
                    "timestamp": "2024-01-15T14:23:00Z",
                    "message": "Camera offline for 2 hours"
                },
                {
                    "id": "alert_002",
                    "type": "device_offline",
                    "severity": "medium",
                    "device": "Loading Dock (cam_006)",
                    "timestamp": "2024-01-15T15:10:00Z",
                    "message": "Camera offline for 30 minutes"
                }
            ]
        }
    
    return None

def summarize_response(intent, api_response):
    """
    Intelligently summarize large API responses
    """
    if intent == "get_system_info":
        return f"""System Information:
- Version: {api_response.get('version')}
- Status: {api_response.get('status', 'unknown').upper()}
- Uptime: {api_response.get('uptime')}"""
    
    elif intent == "get_user_account":
        return f"""Your Account:
- Name: {api_response.get('name')}
- Email: {api_response.get('email')}
- Role: {api_response.get('role', 'unknown').title()}
- Organization: {api_response.get('organization')}"""
    
    elif intent == "get_devices":
        devices = api_response.get('devices', [])
        total = api_response.get('total_count', len(devices))
        online = sum(1 for d in devices if d.get('status') == 'online')
        offline = sum(1 for d in devices if d.get('status') == 'offline')
        
        summary = f"""Device Summary:
- Total devices: {total}
- Online: {online}
- Offline: {offline}"""
        
        if offline > 0:
            summary += "\n\nOffline Devices:"
            for device in devices:
                if device.get('status') == 'offline':
                    summary += f"\n- {device.get('name')} ({device.get('location')})"
        
        return summary
    
    elif intent == "get_ongoing_alerts":
        alerts = api_response.get('alerts', [])
        count = api_response.get('alert_count', len(alerts))
        
        if count == 0:
            return "No ongoing alerts. All systems operating normally."
        
        summary = f"""Active Alerts: {count}"""
        
        for alert in alerts:
            severity = alert.get('severity', 'unknown').upper()
            summary += f"\n\n[{severity}] {alert.get('message')}"
            summary += f"\nDevice: {alert.get('device')}"
        
        return summary
    
    return "Response received successfully."

def filter_devices_by_status(status):
    """
    Filter devices from last API response by status
    """
    if not st.session_state.last_api_response:
        return "No previous device data available."
    
    devices = st.session_state.last_api_response.get('devices', [])
    filtered = [d for d in devices if d.get('status') == status]
    
    if not filtered:
        return f"No {status} devices found."
    
    result = f"{status.title()} Devices ({len(filtered)}):\n"
    for device in filtered:
        result += f"\n- {device.get('name')} ({device.get('location')})"
    
    return result

def generate_response(intent_data):
    """
    Generate assistant response based on intent analysis
    """
    intent = intent_data.get("intent")
    
    # Track this question
    track_question(intent)
    
    # Handle help intent
    if intent == "show_help":
        return """I can help you with:

- System information and version details
- Your account information
- Device and camera queries
- Checking ongoing alerts

Try asking:
- "Show all devices"
- "Check for alerts"
- "Show my account"
- "Get system information"
"""
    
    # Handle unsupported intent
    if intent == "unsupported":
        return """I'm not sure I understand that request.

I can help you with:
- Checking devices and cameras
- Viewing ongoing alerts
- Account information
- System information

What would you like to do?"""
    
    # Handle context-based filtering
    if intent.startswith("filter_"):
        if intent == "filter_offline_devices":
            return filter_devices_by_status("offline")
        elif intent == "filter_online_devices":
            return filter_devices_by_status("online")
    
    # Handle API-based intents
    api_endpoint = intent_data.get("api")
    method = intent_data.get("method")
    confidence_message = intent_data.get("confidence_message")
    
    if not api_endpoint:
        return "Unable to process this request."
    
    # Show confidence message
    response = confidence_message + "\n\n"
    
    # Simulate API call
    api_response = simulate_api_call(api_endpoint, method)
    
    # Store response for context
    st.session_state.last_api_response = api_response
    
    # Summarize response
    summary = summarize_response(intent, api_response)
    response += summary
    
    return response

def display_follow_up_suggestions(suggestions):
    """
    Display follow-up suggestions as clickable buttons
    """
    if suggestions:
        st.markdown("---")
        st.markdown("**Suggestions:**")
        cols = st.columns(len(suggestions))
        for idx, suggestion in enumerate(suggestions):
            with cols[idx]:
                if st.button(suggestion, key=f"suggest_{suggestion}_{len(st.session_state.messages)}", use_container_width=True):
                    # Add user message
                    st.session_state.messages.append({"role": "user", "content": suggestion})
                    
                    # Process intent
                    intent_data = analyze_intent(suggestion)
                    
                    # Update context
                    st.session_state.last_intent = intent_data.get("intent")
                    
                    # Generate response
                    assistant_response = generate_response(intent_data)
                    
                    # Add assistant message
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_response,
                        "suggestions": intent_data.get("follow_up_suggestions", [])
                    })
                    
                    # Add to conversation history
                    st.session_state.conversation_history.append({
                        "timestamp": datetime.now().isoformat(),
                        "user_message": suggestion,
                        "intent": intent_data.get("intent"),
                        "api": intent_data.get("api"),
                        "assistant_response": assistant_response
                    })
                    
                    st.rerun()

# App Header
st.title("Alta Video Assistant")
st.caption("AI-powered security system interface")

# Sidebar
with st.sidebar:
    st.header("Session Info")
    
    st.metric("Messages", len(st.session_state.messages))
    st.metric("Intents Tracked", len(st.session_state.conversation_history))
    
    if st.session_state.last_intent:
        st.info(f"Last Intent: {st.session_state.last_intent}")
    
    st.divider()
    
    # Frequently asked questions
    if st.session_state.frequent_questions:
        st.subheader("Most Asked")
        top_questions = get_most_frequent_questions(3)
        for q in top_questions:
            st.text(f"- {q} ({st.session_state.frequent_questions[q]}x)")
    
    st.divider()
    
    st.subheader("Available APIs")
    for name, config in AVAILABLE_APIS.items():
        st.code(f"{config['method']} {config['endpoint']}", language="text")
    
    st.divider()
    
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_history = []
        st.session_state.last_intent = None
        st.session_state.last_entity = None
        st.session_state.last_api_response = None
        st.rerun()

# Display chat messages
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show suggestions for assistant messages
        if message["role"] == "assistant" and message.get("suggestions"):
            # Only show suggestions for the last assistant message
            if idx == len(st.session_state.messages) - 1:
                display_follow_up_suggestions(message["suggestions"])

# Initial greeting
if len(st.session_state.messages) == 0:
    with st.chat_message("assistant"):
        greeting = """Hello. I'm the Alta Video assistant.

I can help you with:
- System information and account details
- Device and camera queries
- Checking ongoing alerts

What would you like to do?"""
        st.markdown(greeting)
        
        # Initial suggestions
        initial_suggestions = ["Show all devices", "Check for alerts", "Show my account"]
        display_follow_up_suggestions(initial_suggestions)

# Chat input
if prompt := st.chat_input("Type your message..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process intent
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            intent_data = analyze_intent(prompt)
            
            # Update context
            st.session_state.last_intent = intent_data.get("intent")
            
            # Generate response
            assistant_response = generate_response(intent_data)
            
            # Display response
            st.markdown(assistant_response)
            
            # Add assistant message with suggestions
            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_response,
                "suggestions": intent_data.get("follow_up_suggestions", [])
            })
            
            # Add to conversation history
            st.session_state.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "user_message": prompt,
                "intent": intent_data.get("intent"),
                "api": intent_data.get("api"),
                "assistant_response": assistant_response
            })
            
            # Show suggestions
            display_follow_up_suggestions(intent_data.get("follow_up_suggestions", []))
