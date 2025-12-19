# Alta Video Assistant - Streamlit Prototype

A standalone Streamlit chat interface for testing Alta Video security system APIs and conversational AI capabilities.

## Purpose

This is an experimental prototype application designed for:
- API testing and validation
- Conversational flow experimentation
- Intent recognition testing
- Context management validation
- User interaction pattern analysis

**Note**: This is NOT a production-ready system. It uses simulated API responses for testing purposes.

## Features

### Core Capabilities
- Natural language intent understanding
- Context-aware conversation handling
- Intelligent response summarization
- Frequently asked question tracking
- Smart follow-up suggestions
- Session-level conversation history

### Supported Intents
1. **System Information** - Get version, status, and uptime
2. **User Account** - View account details and role information
3. **Device Queries** - List all devices with status summaries
4. **Alert Monitoring** - Check ongoing alerts and issues
5. **Context-Based Filtering** - Filter previous results (e.g., offline devices)

## Available APIs

```
GET  /api/v1/about           - System information
GET  /api/v1/me              - User account details
POST /api/v1/query:devices   - Device listing (requires POST with empty body)
GET  /api/v1/ongoingAlerts   - Active alerts
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run app.py
```

3. Access the app at:
```
http://localhost:8501
```

## Usage

### Basic Interactions

**Get System Information:**
- "Show system information"
- "What version is this?"
- "Get system status"

**View Account Details:**
- "Show my account"
- "Who am I?"
- "My profile"

**Query Devices:**
- "Show all devices"
- "List cameras"
- "Show all cameras"

**Check Alerts:**
- "Check for alerts"
- "Any ongoing issues?"
- "Show active alerts"

### Context-Aware Follow-ups

After listing devices, you can ask:
- "Which ones are offline?"
- "Show online devices"
- "Which devices have issues?"

The assistant remembers your last query and provides contextual answers.

## Application Structure

```
.
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── .streamlit/
│   └── config.toml          # Streamlit configuration
└── README.md                # This file
```

## Key Components

### Intent Analysis
The `analyze_intent()` function maps natural language to structured API calls:
- Identifies user intent from text
- Determines required API endpoint
- Extracts parameters
- Decides if context is needed
- Generates follow-up suggestions

### Response Summarization
The `summarize_response()` function intelligently condenses large API responses:
- Focuses on counts and statuses
- Highlights anomalies and errors
- Avoids dumping raw technical data
- Provides clear, actionable information

### Context Management
- Tracks last intent and entities
- Maintains conversation history
- Enables context-aware follow-up questions
- Reduces need for repeated information

### Learning System
- Tracks frequently asked questions
- Identifies common user patterns
- Improves future recommendations
- Displays usage statistics in sidebar

## Simulated API Responses

Currently, the app uses mock data for testing. Key simulated scenarios:

**Devices (8 total):**
- 6 online cameras
- 2 offline cameras (Back Exit, Loading Dock)

**Alerts (2 active):**
- High severity: Back Exit offline for 2 hours
- Medium severity: Loading Dock offline for 30 minutes

**Account:**
- User: John Doe (Administrator)
- Organization: Acme Security

## Customization

### Adding Real API Integration

Replace the `simulate_api_call()` function with actual HTTP requests:

```python
import requests

def make_api_call(endpoint, method, params=None):
    base_url = "https://api.altavideo.com"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    if method == "GET":
        response = requests.get(f"{base_url}{endpoint}", headers=headers)
    elif method == "POST":
        response = requests.post(f"{base_url}{endpoint}", headers=headers, json=params or {})
    
    return response.json()
```

### Extending Intent Recognition

Add new intents in the `analyze_intent()` function:

```python
elif any(word in message_lower for word in ["recording", "playback", "video"]):
    return {
        "intent": "get_recordings",
        "api": "/api/v1/recordings",
        "method": "GET",
        ...
    }
```

## Sidebar Features

- **Session Info**: Message count and intent tracking
- **Last Intent**: Shows the most recent user intent
- **Most Asked**: Displays frequently asked questions
- **Available APIs**: Lists all accessible endpoints
- **Clear Chat**: Resets the conversation

## Design Philosophy

### Text-Only Interface
The app is intentionally simple with no complex dashboards, charts, or tables. All interaction is conversational text.

### Smart Summarization
Large API responses are automatically summarized to focus on what matters most to users.

### Context Awareness
The assistant remembers recent conversation context to provide more natural interactions.

### Learning Capability
The system tracks usage patterns to improve recommendations over time.

## Limitations

- This is a prototype for testing, not production use
- API responses are currently simulated
- No authentication or security implementation
- Session state is lost on app restart
- No persistent storage of conversation history

## Future Enhancements

Potential additions for production deployment:
- Real API integration with authentication
- Persistent conversation storage
- Multi-user session management
- Advanced filtering and search capabilities
- Export conversation history
- Custom alert configuration
- Device control actions (with confirmations)

## Troubleshooting

**App won't start:**
- Ensure Python 3.8+ is installed
- Check all dependencies are installed: `pip install -r requirements.txt`
- Verify port 8501 is available

**Suggestions not appearing:**
- Clear chat and restart conversation
- Check browser console for JavaScript errors
- Try refreshing the page

**Context not working:**
- Verify conversation history is maintained in sidebar
- Check that "Last Intent" shows the expected value
- Try asking more explicit follow-up questions

## Contributing

This is an experimental prototype. For testing improvements:
1. Test new conversational patterns
2. Document edge cases
3. Suggest intent improvements
4. Report bugs or unexpected behaviors

## License

Prototype application for testing purposes.

## Support

For questions about this prototype:
- Review the code documentation
- Check the Alta Video API documentation
- Test with different query patterns
