"""
Alta Video Assistant - Production Version
Connects to real Alta/Avigilon Cloud APIs for access control management
"""

import streamlit as st
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from alta_client import AltaClient, AltaAPIError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== PAGE CONFIGURATION ==========

st.set_page_config(
    page_title="Alta Video Assistant",
    page_icon="🔒",
    layout="centered"
)

# ========== SESSION STATE INITIALIZATION ==========

if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "last_intent" not in st.session_state:
    st.session_state.last_intent = None
if "last_entries" not in st.session_state:
    st.session_state.last_entries = None
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "api_client" not in st.session_state:
    st.session_state.api_client = None
if "frequent_questions" not in st.session_state:
    st.session_state.frequent_questions = {}

# ========== AUTHENTICATION & CLIENT INITIALIZATION ==========

def initialize_api_client():
    """
    Initialize Alta API client with credentials from secrets
    
    Expected secrets.toml format:
    [alta]
    base_url = "https://ifss-kenya-office.eu2.alta.avigilon.com"
    api_token = "your-api-token-here"
    """
    try:
        # Load credentials from Streamlit secrets
        base_url = st.secrets["alta"]["base_url"]
        api_token = st.secrets["alta"]["api_token"]
        
        # Initialize client
        client = AltaClient(base_url, api_token)
        
        # Get current user (optional - for display purposes)
        user = client.get_current_user()
        
        st.session_state.api_client = client
        st.session_state.current_user = user or {"name": "User"}
        
        logger.info(f"Successfully authenticated")
        return True
        
    except KeyError as e:
        st.error(f"❌ Missing configuration: {str(e)}")
        st.info("Please configure your Alta credentials in `.streamlit/secrets.toml`")
        st.code("""
[alta]
base_url = "https://ifss-kenya-office.eu2.alta.avigilon.com"
api_token = "your-api-token-here"
        """, language="toml")
        st.stop()
        return False
        
    except AltaAPIError as e:
        st.error(f"❌ API Error: {str(e)}")
        st.stop()
        return False
        
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        logger.exception("Failed to initialize API client")
        st.stop()
        return False

# Initialize API client if not already done
if st.session_state.api_client is None:
    initialize_api_client()

# ========== HELPER FUNCTIONS ==========

def track_question(intent: str):
    """Track frequently asked questions"""
    if intent in st.session_state.frequent_questions:
        st.session_state.frequent_questions[intent] += 1
    else:
        st.session_state.frequent_questions[intent] = 1

def get_most_frequent_questions(top_n: int = 3) -> List[str]:
    """Get the most frequently asked questions"""
    sorted_questions = sorted(
        st.session_state.frequent_questions.items(),
        key=lambda x: x[1],
        reverse=True
    )
    return [q[0] for q in sorted_questions[:top_n]]

# ========== INTENT ANALYSIS ==========

def analyze_intent(user_message: str) -> Dict:
    """
    Analyze user intent and map to Alta API calls
    
    Args:
        user_message: User's natural language query
        
    Returns:
        Dictionary with intent, API details, and follow-up suggestions
    """
    message_lower = user_message.lower()
    
    # ===== ACCESS HISTORY (MUST BE FIRST TO CATCH ALL VARIATIONS) =====
    if any(phrase in message_lower for phrase in ["access history", "my history", "access log", "entry log", "access logs", "entry logs"]):
        return {
            "intent": "get_entries_last_7_days",
            "api": "get_entries_last_n_days",
            "params": {"days": 7},
            "uses_context": False,
            "confidence_message": "Retrieving your access history from the last 7 days.",
            "requires_confirmation": False,
            "follow_up_suggestions": [
                "Show only denied entries",
                "Show only granted entries",
                "What doors do I have access to?"
            ]
        }
    
    # ===== DOOR ACCESS QUERIES =====
    elif any(word in message_lower for word in ["door", "doors", "access to", "which doors", "what doors", "access point"]):
        return {
            "intent": "get_access_points",
            "api": "get_access_points",
            "params": {},
            "uses_context": False,
            "confidence_message": "Retrieving your access control points.",
            "requires_confirmation": False,
            "follow_up_suggestions": [
                "Show my access history",
                "Where did I enter today?",
                "Check for denied access"
            ]
        }
    
    # ===== ENTRY HISTORY - TODAY =====
    elif any(phrase in message_lower for phrase in ["today", "entered today", "access today", "where did i enter today"]):
        return {
            "intent": "get_entries_today",
            "api": "get_entries_today",
            "params": {},
            "uses_context": False,
            "confidence_message": "Retrieving access entries from today.",
            "requires_confirmation": False,
            "follow_up_suggestions": [
                "Show yesterday's entries",
                "Show last 7 days",
                "What doors do I have access to?"
            ]
        }
    
    # ===== ENTRY HISTORY - YESTERDAY =====
    elif any(word in message_lower for word in ["yesterday", "entered yesterday"]):
        return {
            "intent": "get_entries_yesterday",
            "api": "get_entries_yesterday",
            "params": {},
            "uses_context": False,
            "confidence_message": "Retrieving access entries from yesterday.",
            "requires_confirmation": False,
            "follow_up_suggestions": [
                "Show today's entries",
                "Show last 7 days",
                "Check for denied access"
            ]
        }
    
    # ===== ENTRY HISTORY - LAST N DAYS =====
    elif any(phrase in message_lower for phrase in ["last 7 days", "last week", "past week", "last seven days"]):
        return {
            "intent": "get_entries_last_7_days",
            "api": "get_entries_last_n_days",
            "params": {"days": 7},
            "uses_context": False,
            "confidence_message": "Retrieving access entries from the last 7 days.",
            "requires_confirmation": False,
            "follow_up_suggestions": [
                "Show only denied entries",
                "Show only granted entries",
                "What doors do I have access to?"
            ]
        }
    
    elif any(phrase in message_lower for phrase in ["last 30 days", "last month", "past month"]):
        return {
            "intent": "get_entries_last_30_days",
            "api": "get_entries_last_n_days",
            "params": {"days": 30},
            "uses_context": False,
            "confidence_message": "Retrieving access entries from the last 30 days.",
            "requires_confirmation": False,
            "follow_up_suggestions": [
                "Show only denied entries",
                "Show only granted entries",
                "Filter by specific door"
            ]
        }
    
    # ===== LAST ENTRY =====
    elif any(phrase in message_lower for phrase in ["last entry", "last access", "most recent", "last time"]):
        return {
            "intent": "get_last_entry",
            "api": "get_last_entry",
            "params": {},
            "uses_context": False,
            "confidence_message": "Retrieving your most recent access entry.",
            "requires_confirmation": False,
            "follow_up_suggestions": [
                "Show today's entries",
                "Show last 7 days",
                "What doors do I have access to?"
            ]
        }
    
    # ===== DENIED ACCESS =====
    elif any(phrase in message_lower for phrase in ["denied", "denied access", "rejected", "failed access", "couldn't enter"]):
        return {
            "intent": "get_denied_entries",
            "api": "filter_denied_entries",
            "params": {},
            "uses_context": True,
            "confidence_message": "Checking for denied access attempts.",
            "requires_confirmation": False,
            "follow_up_suggestions": [
                "Show all entries",
                "Show granted entries only",
                "What doors do I have access to?"
            ]
        }
    
    # ===== GRANTED ACCESS =====
    elif any(phrase in message_lower for phrase in ["granted", "successful", "granted access", "successful access"]):
        return {
            "intent": "get_granted_entries",
            "api": "filter_granted_entries",
            "params": {},
            "uses_context": True,
            "confidence_message": "Retrieving successful access entries.",
            "requires_confirmation": False,
            "follow_up_suggestions": [
                "Show denied entries",
                "Show today's entries",
                "Check last entry"
            ]
        }
    
    # ===== ACCOUNT INFO =====
    elif any(phrase in message_lower for phrase in ["my account", "my profile", "my info", "who am i"]):
        return {
            "intent": "show_account",
            "api": None,
            "params": {},
            "uses_context": False,
            "confidence_message": None,
            "requires_confirmation": False,
            "follow_up_suggestions": [
                "What doors do I have access to?",
                "Show my access history",
                "Check for denied access"
            ]
        }
    
    # ===== HELP =====
    elif any(word in message_lower for word in ["help", "what can you do", "capabilities", "commands"]):
        return {
            "intent": "show_help",
            "api": None,
            "params": {},
            "uses_context": False,
            "confidence_message": None,
            "requires_confirmation": False,
            "follow_up_suggestions": [
                "What doors do I have access to?",
                "Show today's entries",
                "Show my account"
            ]
        }
    
    # ===== UNSUPPORTED =====
    else:
        return {
            "intent": "unsupported",
            "api": None,
            "params": {},
            "uses_context": False,
            "confidence_message": None,
            "requires_confirmation": False,
            "follow_up_suggestions": [
                "What doors do I have access to?",
                "Show today's entries",
                "Show my access history"
            ]
        }

# ========== API CALL EXECUTION ==========

def execute_api_call(intent_data: Dict) -> Dict:
    """
    Execute the appropriate API call based on intent
    
    Args:
        intent_data: Intent analysis result
        
    Returns:
        API response or error dictionary
    """
    client = st.session_state.api_client
    
    intent = intent_data.get("intent")
    api_method = intent_data.get("api")
    params = intent_data.get("params", {})
    
    try:
        # ===== ACCESS POINTS =====
        if api_method == "get_access_points":
            points = client.get_access_points()
            return {"success": True, "data": points, "type": "access_points"}
        
        # ===== TODAY'S ENTRIES =====
        elif api_method == "get_entries_today":
            entries = client.get_entries_today()
            st.session_state.last_entries = entries
            return {"success": True, "data": entries, "type": "entries"}
        
        # ===== YESTERDAY'S ENTRIES =====
        elif api_method == "get_entries_yesterday":
            entries = client.get_entries_yesterday()
            st.session_state.last_entries = entries
            return {"success": True, "data": entries, "type": "entries"}
        
        # ===== LAST N DAYS =====
        elif api_method == "get_entries_last_n_days":
            days = params.get("days", 7)
            entries = client.get_entries_last_n_days(days)
            st.session_state.last_entries = entries
            return {"success": True, "data": entries, "type": "entries", "days": days}
        
        # ===== LAST ENTRY =====
        elif api_method == "get_last_entry":
            entry = client.get_last_entry()
            return {"success": True, "data": [entry] if entry else [], "type": "entries"}
        
        # ===== FILTER DENIED =====
        elif api_method == "filter_denied_entries":
            if st.session_state.last_entries:
                entries = st.session_state.last_entries
            else:
                entries = client.get_entries_last_n_days(7)
                st.session_state.last_entries = entries
            
            denied = client.filter_denied_entries(entries)
            return {"success": True, "data": denied, "type": "entries"}
        
        # ===== FILTER GRANTED =====
        elif api_method == "filter_granted_entries":
            if st.session_state.last_entries:
                entries = st.session_state.last_entries
            else:
                entries = client.get_entries_last_n_days(7)
                st.session_state.last_entries = entries
            
            granted = client.filter_granted_entries(entries)
            return {"success": True, "data": granted, "type": "entries"}
        
        else:
            return {"success": False, "error": "Unknown API method"}
            
    except AltaAPIError as e:
        logger.error(f"API call failed: {str(e)}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.exception("Unexpected error during API call")
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

# ========== RESPONSE FORMATTING ==========

def format_access_points_response(points: List[Dict]) -> str:
    """
    Format access control points response
    
    Args:
        points: List of access point dictionaries
        
    Returns:
        Formatted string
    """
    if not points:
        return "No access control points found in the system."
    
    response = f"**Access Control Points (Doors): {len(points)}**\n\n"
    
    for point in points:
        name = point.get('name', point.get('access_point_name', 'Unknown Point'))
        site = point.get('site_name', point.get('site', 'Unknown Site'))
        point_type = point.get('type', 'Access Point')
        
        response += f"**{name}**\n"
        response += f"   Site: {site}\n"
        response += f"   Type: {point_type}\n\n"
    
    return response

def format_entry_response(entries: List[Dict], days: Optional[int] = None) -> str:
    """
    Format access entry response
    
    Args:
        entries: List of entry dictionaries
        days: Number of days (for context in message)
        
    Returns:
        Formatted string
    """
    if not entries:
        if days:
            return f"No access events recorded in the last {days} days."
        return "No denied access events were found in the selected period."
    
    # Sort by timestamp (most recent first)
    sorted_entries = sorted(
        entries,
        key=lambda x: x.get('time', 0),
        reverse=True
    )
    
    response = f"**Access Events: {len(entries)}**\n\n"
    
    for entry in sorted_entries[:20]:  # Limit to 20 most recent
        # Extract entry details
        time_ms = entry.get('time', 0)
        door_name = entry.get('access_point_name', entry.get('reader_name', 'Unknown Door'))
        site = entry.get('site_name', 'Unknown Site')
        event_type = entry.get('event_type', 'UNKNOWN')
        cardholder = entry.get('cardholder_name', '')
        
        # Determine access status based strictly on event_type
        if event_type == 'ACCESS_GRANTED':
            status_text = "Granted"
        elif event_type == 'ACCESS_DENIED':
            status_text = "Denied"
        elif event_type == 'HELD_OPEN':
            status_text = "Held Open"
        else:
            status_text = event_type
        
        # Convert epoch milliseconds to datetime
        try:
            if isinstance(time_ms, (int, float)) and time_ms > 0:
                dt = datetime.fromtimestamp(time_ms / 1000)
                time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            else:
                time_str = "Unknown time"
        except:
            time_str = "Unknown time"
        
        response += f"**{status_text}** - {door_name}\n"
        response += f"   Site: {site}\n"
        response += f"   Time: {time_str}\n"
        if cardholder:
            response += f"   User: {cardholder}\n"
        response += "\n"
    
    if len(sorted_entries) > 20:
        response += f"\nShowing 20 of {len(sorted_entries)} entries"
    
    return response

def format_account_response(user: Dict) -> str:
    """
    Format user account information
    
    Args:
        user: User dictionary
        
    Returns:
        Formatted string
    """
    response = "**Your Account:**\n\n"
    
    name = user.get('name', user.get('firstName', '') + ' ' + user.get('lastName', '')).strip()
    email = user.get('email', 'Not available')
    user_id = user.get('id', 'Not available')
    role = user.get('role', user.get('userRole', 'User'))
    
    response += f"**Name:** {name or 'Not available'}\n"
    response += f"**Email:** {email}\n"
    if user_id != 'Not available':
        response += f"**User ID:** {user_id}\n"
    response += f"**Role:** {role.title()}\n"
    
    return response

# ========== RESPONSE GENERATION ==========

def generate_response(intent_data: Dict) -> str:
    """
    Generate assistant response based on intent
    
    Args:
        intent_data: Intent analysis result
        
    Returns:
        Formatted response string
    """
    intent = intent_data.get("intent")
    
    # Track question
    track_question(intent)
    
    # ===== HELP =====
    if intent == "show_help":
        return """**Available Commands:**

**Door Access:**
- "What doors do I have access to?"
- "Show my access points"

**Entry History:**
- "Where did I enter today?"
- "Show yesterday's entries"
- "Show last 7 days"
- "What was my last entry?"
- "Show my access history"

**Access Status:**
- "Show denied access attempts"
- "Show granted entries"

**Account:**
- "Show my account"
- "Who am I?"

Ask me a question to get started."""
    
    # ===== ACCOUNT INFO =====
    elif intent == "show_account":
        user = st.session_state.current_user
        return format_account_response(user)
    
    # ===== UNSUPPORTED =====
    elif intent == "unsupported":
        return """Request not recognized.

Available functions:
- Access control points
- Access entry history
- Denied/granted access filtering
- Account information

Please rephrase your request."""
    
    # ===== API-BASED INTENTS =====
    confidence_message = intent_data.get("confidence_message")
    
    # Show what we're doing
    response = confidence_message + "\n\n" if confidence_message else ""
    
    # Execute API call
    api_response = execute_api_call(intent_data)
    
    # Handle errors
    if not api_response.get("success"):
        error_msg = api_response.get("error", "Unknown error occurred")
        return f"**Error:** {error_msg}\n\nPlease try again or contact support if the issue persists."
    
    # Format response based on type
    data = api_response.get("data", [])
    response_type = api_response.get("type")
    
    if response_type == "access_points":
        response += format_access_points_response(data)
    elif response_type == "entries":
        days = api_response.get("days")
        response += format_entry_response(data, days)
    else:
        response += "Request completed successfully."
    
    return response

# ========== UI COMPONENTS ==========

def display_follow_up_suggestions(suggestions: List[str]):
    """Display follow-up suggestions as clickable buttons"""
    if suggestions and len(suggestions) > 0:
        st.markdown("---")
        st.markdown("**Quick actions:**")
        
        cols = st.columns(min(len(suggestions), 3))
        
        for idx, suggestion in enumerate(suggestions):
            with cols[idx % 3]:
                if st.button(
                    suggestion,
                    key=f"suggest_{suggestion}_{len(st.session_state.messages)}",
                    use_container_width=True
                ):
                    process_user_message(suggestion)
                    st.rerun()

def process_user_message(message: str):
    """Process a user message and generate response"""
    st.session_state.messages.append({"role": "user", "content": message})
    
    intent_data = analyze_intent(message)
    st.session_state.last_intent = intent_data.get("intent")
    
    assistant_response = generate_response(intent_data)
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": assistant_response,
        "suggestions": intent_data.get("follow_up_suggestions", [])
    })
    
    st.session_state.conversation_history.append({
        "timestamp": datetime.now().isoformat(),
        "user_message": message,
        "intent": intent_data.get("intent"),
        "assistant_response": assistant_response
    })

# ========== MAIN APP ==========

st.title("Alta Video Assistant")
st.caption("Access control interface")

# Sidebar
with st.sidebar:
    st.header("Session Info")
    
    if st.session_state.current_user:
        user = st.session_state.current_user
        st.success(f"User: {user.get('name', user.get('email', 'User'))}")
    
    st.metric("Messages", len(st.session_state.messages))
    st.metric("Queries", len(st.session_state.conversation_history))
    
    if st.session_state.last_intent:
        st.info(f"Last Intent: {st.session_state.last_intent}")
    
    st.divider()
    
    if st.session_state.frequent_questions:
        st.subheader("Most Asked")
        top_questions = get_most_frequent_questions(3)
        for q in top_questions:
            st.text(f"• {q} ({st.session_state.frequent_questions[q]}x)")
    
    st.divider()
    
    st.subheader("Quick Actions")
    
    if st.button("My Doors", use_container_width=True):
        process_user_message("What doors do I have access to?")
        st.rerun()
    
    if st.button("Today's Entries", use_container_width=True):
        process_user_message("Show today's entries")
        st.rerun()
    
    if st.button("Denied Access", use_container_width=True):
        process_user_message("Show denied access attempts")
        st.rerun()
    
    st.divider()
    
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_history = []
        st.session_state.last_intent = None
        st.session_state.last_entries = None
        st.rerun()

# Display chat messages
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        if message["role"] == "assistant" and message.get("suggestions"):
            if idx == len(st.session_state.messages) - 1:
                display_follow_up_suggestions(message["suggestions"])

# Initial greeting
if len(st.session_state.messages) == 0:
    with st.chat_message("assistant"):
        user = st.session_state.current_user
        name = user.get('name', user.get('firstName', 'there'))
        
        greeting = f"""Hello {name}.

Alta Video access control assistant. Available functions:

**Door Access** - View accessible doors and access points
**Entry History** - View access event logs
**Denied Access** - Check failed access attempts
**Account Info** - View account details

What would you like to know?"""
        
        st.markdown(greeting)
        
        initial_suggestions = [
            "What doors do I have access to?",
            "Show today's entries",
            "Show my account"
        ]
        display_follow_up_suggestions(initial_suggestions)

# Chat input
if prompt := st.chat_input("Ask me about your access..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            intent_data = analyze_intent(prompt)
            st.session_state.last_intent = intent_data.get("intent")
            
            assistant_response = generate_response(intent_data)
            st.markdown(assistant_response)
            
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_response,
                "suggestions": intent_data.get("follow_up_suggestions", [])
            })
            
            st.session_state.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "user_message": prompt,
                "intent": intent_data.get("intent"),
                "assistant_response": assistant_response
            })
            
            display_follow_up_suggestions(intent_data.get("follow_up_suggestions", []))