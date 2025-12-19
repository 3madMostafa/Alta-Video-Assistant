# Quick Start Guide

## Installation

```bash
pip install -r requirements.txt
```

## Run the App

```bash
streamlit run app.py
```

Open your browser at: http://localhost:8501

## Try These Commands

### Basic Queries
- "Show all devices"
- "Check for alerts"
- "Show my account"
- "Get system information"

### Context-Aware Follow-ups
1. First ask: "Show all devices"
2. Then ask: "Which ones are offline?"
3. Or ask: "Show online devices"

## What to Expect

The assistant will:
- Understand your natural language questions
- Summarize large responses intelligently
- Remember context from previous questions
- Suggest relevant follow-up actions
- Track frequently asked questions

## Features

- **Clean Chat Interface**: Simple text-based conversation
- **Smart Summarization**: Focus on what matters (counts, statuses, issues)
- **Context Memory**: Ask follow-up questions naturally
- **Learning System**: Tracks common questions
- **Sidebar Info**: View session stats and API endpoints

## Notes

- This is a prototype with simulated API responses
- Session state resets when you close the browser
- Click "Clear Chat" to start a new conversation
