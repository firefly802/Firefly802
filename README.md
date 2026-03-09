# Firefly AI Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Firefly is a comprehensive, offline-capable productivity AI assistant built with Python. It integrates a local Large Language Model (LLM) for intelligent chat, voice interaction, and a comprehensive suite of productivity tools, all wrapped in a modern, intuitive GUI designed for work-from-home professionals.

## 🎯 What Makes Firefly Special

**Dashboard-Centric Design**: Everything you need is accessible from your home dashboard. No more clicking through menus—all major features are one click away with a clean Quick Actions grid.

**Voice-First Interface**: Available hands-free voice commands for every major feature. Simply say "Hey Firefly" or command directly: "open goals", "set a reminder", "what's the weather?"

**Offline & Private**: All AI processing happens locally on your machine. No cloud, no tracking, no data sharing.

## Features

### 🤖 AI & Chat
- **Local AI Chat**: Powered by GPT4All with Llama-3.2-3B-Instruct model for fully offline conversations
- **Voice Interaction**: Text-to-speech and speech-to-text for hands-free communication
- **Wake Word Detection**: Optional "Hey Firefly" activation for seamless voice access
- **Document Chat (RAG)**: Upload documents and ask questions about their content
- **Custom Knowledge Base**: Train AI with personal text files for personalized responses
- **Chat History**: Persistent conversation memory with context awareness
- **Multiple Personalities**: Choose from different AI personas (Default, Professional, Casual, etc.)

### 📊 Dashboard Hub (Your Command Center)
The dashboard is your productivity headquarters:
- **Daily Briefing**: Weather, schedule, and priorities at a glance
- **Real-Time Weather**: Current conditions for your location (configurable)
- **Today's Schedule**: Quick view of all appointments and events  
- **Top Priorities**: See your most urgent tasks instantly
- **Productivity Insights**: Real-time metrics on tasks, goals, and reminders
- **AI Suggestions**: Get personalized daily recommendations to boost productivity
- **Quick Actions Grid**: One-click access to 12 major features:
  - **Productivity**: New Task, View Calendar, Set Reminder
  - **Communication**: My Notes, Check Email, Read News
  - **Tools**: Google Search, Tools Hub, Analytics
  - **Wellness**: Goals, Zen Mode, Settings

### 📈 Analytics Tab
- **Task Completion Charts**: Visual trends of task completion over time
- **Productivity Metrics**: Track your activity patterns
- **Data-Driven Insights**: Identify what works for your productivity

### 📋 Productivity Management
- **To-Do List**: Create, manage, and track tasks with completion metrics
- **Reminders**: Time-based notifications with custom messages
- **Goals**: Set and monitor personal and professional goals
- **Notes Manager**: Organize and search your notes easily
- **Calendar**: View and manage appointments
- **Email Client**: Built-in email reader with inbox integration (configurable)

### ⚙️ System & Utilities
- **Office Suite**: Quick launch Word, Excel, PowerPoint, Outlook
- **System Tools**: Task Manager, Control Panel, CMD, Disk Management  
- **Power Controls**: Shutdown, restart, lock, system status
- **Health Monitor**: Real-time CPU & RAM usage in top bar
- **File Operations**: Quick search, organize, screenshots
- **Unit Converter**: Instant conversions between units
- **QR Code Generator**: Generate QR codes from text
- **Password Generator**: Create secure passwords with one click
- **JSON/Regex Tools**: Format JSON, test regex patterns
- **Base64 Converter**: Encode/decode Base64 strings
- **Battery & System Info**: Check battery, IP address, and system details

### 🌐 Web Features
- **Google Search**: Web search with direct browser launch
- **Translation**: Google Translate for 100+ languages
- **News**: Top headlines from major news sources
- **Wikipedia**: Quick knowledge lookup for any topic
- **Web Access**: Direct shortcuts to YouTube, Google, and other sites

### ⏰ Focus & Wellness
- **Pomodoro Timer**: 25/5 focus/break cycles with notifications
- **Countdown Timer**: Custom timer for any duration
- **Zen Mode**: Distraction-free mindfulness space
- **Idea Incubator**: AI-powered creative idea generation
- **Daily Quotes**: Inspirational quotes for motivation
- **Fun**: Random jokes and "On This Day" facts

## Voice Control Commands

Comprehensive voice support for hands-free operation:
- **Navigation**: "open chat", "open todo", "open reminders", "open goals", "open analytics", "open zen"
- **Tasks**: "new task", "set reminder", "add goal"
- **Information**: "weather", "time", "news", "what's my ip?"
- **System**: "lock computer", "shutdown", "restart", "system status"
- **Tools**: "calculator", "screenshot", "timer", "translator"

## User Interface Layout

**Top Navigation Bar** (Always Visible):
Home | Chat | To-Do | Reminders | Settings

**Dashboard View** (Home Tab):
- Daily Briefing at top
- Quick Actions grid (12 buttons)
- Productivity Metrics
- Today's Schedule
- AI Suggestions

**All Tabs Available**:
- Home (Dashboard)
- Chat (AI Conversation)
- To-Do (Task Management)
- Reminders (Notifications)
- Goals (Goal Tracking)
- Analytics (Productivity Charts)
- Zen (Mindfulness Mode)
- Settings (Configuration)
- Tools (System Utilities) - Accessible from Dashboard

## Prerequisites

- **Python 3.10+**
- **VLC Media Player** (optional, for media features)
- **C++ Build Tools** (optional, for some dependencies)
- **4GB RAM minimum** (8GB+ recommended)
- **~2GB disk space** for AI model

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/firefly-ai.git
   cd firefly-ai
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # macOS/Linux
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Download AI Model**:
   - Download `Llama-3.2-3B-Instruct-Q4_K_M.gguf` from:
     - [Hugging Face](https://huggingface.co/TheBloke/Llama-3.2-3B-Instruct-GGUF)
     - [GPT4All](https://www.nomic.ai/gpt4all)
   - Place in `models/` directory
   - Pre-configured in `modules/config.py`

5. **Run Application**:
   ```bash
   python main.py
   ```

## Configuration

### AI Model Selection
Edit `modules/config.py` to select your preferred model:
- **Llama-3.2-3B-Instruct-Q4_K_M.gguf** (Recommended - balanced speed/quality)
- **Llama-3.2-1B-Instruct-Q4_0.gguf** (Lightweight - faster on low-end systems)
- **DeepSeek-R1-Distill-Qwen-1.5B-Q4_0.gguf** (Fast alternative)
- **Gemma-3N-E2B-IT-Q4_K_M.gguf** (Experimental)

### Email Setup (Optional)
To enable email reading:

1. Copy `.env.example` to `.env`
2. Add credentials:
   ```env
   EMAIL_ADDRESS="your.email@gmail.com"
   EMAIL_PASSWORD="your_app_password"
   IMAP_SERVER="imap.gmail.com"
   SMTP_SERVER="smtp.gmail.com"
   SMTP_PORT="587"
   ```

**For Gmail**:
- Enable 2-Factor Authentication
- Generate App Password (not regular password)
- Use App Password in `.env`

### Customize Settings
- **Weather Location**: Edit `modules/dashboard.py` 
- **Voice**: Toggle in Settings tab
- **Theme**: Choose from Dark/Light in Settings
- **UI Scale**: Adjust font size and scaling

## Project Structure

```
firefly-ai/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── LICENSE                # MIT License
├── README.md              # This file
│
├── modules/               # Core functionality
│   ├── config.py          # Configuration & settings
│   ├── utils.py           # Helper functions & voice
│   ├── commands.py        # System commands & tools
│   ├── dashboard.py       # Dashboard UI & quick actions
│   ├── analytics.py       # Analytics charts & metrics
│   ├── database.py        # Data persistence (SQLite)
│   ├── email_client.py    # Email functionality
│   ├── todo.py            # Task management
│   ├── reminders.py       # Reminder notifications
│   ├── goals.py           # Goal tracking
│   ├── notes_manager.py   # Note management
│   ├── calendar_manager.py# Calendar views
│   └── appointments.py    # Appointment handling
│
├── models/                # AI model files (GGUF format)
├── tests/                 # Unit tests
└── screenshots/           # UI preview images
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Send chat message |
| `Ctrl+C` | Exit application |
| `🎤 Button` | Start voice input |

## Troubleshooting

### AI Model Issues
- **Model not found**: Verify file exists in `models/` directory
- **Slow responses**: Try smaller model (1B vs 3B)
- **Memory errors**: Increase virtual memory or use CPU-only mode

### Voice Problems
- **Microphone not working**: Check system audio settings
- **Speech recognition errors**: Speak clearly and slowly
- **Audio output issues**: Verify speakers and volume

### Email Issues
- **Connection refused**: Check IMAP/SMTP settings
- **Authentication failed**: Verify credentials and use App Password for Gmail
- **Timeout errors**: Check internet connection

### Performance
- **Slow dashboard**: Close unnecessary applications
- **Lag in chat**: Reduce chat history or restart app
- **High CPU usage**: Lower voice quality or disable features

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m "Add your feature"`
4. Push to branch: `git push origin feature/your-feature`
5. Submit pull request

## Roadmap

- [ ] Google Calendar sync
- [ ] Outlook calendar integration
- [ ] Advanced analytics with more chart types
- [ ] Habit tracking system
- [ ] Integration with productivity apps (Todoist, Notion)
- [ ] Mobile companion app
- [ ] Cloud backup option
- [ ] Machine learning productivity insights

## Known Limitations

- Email read-only (compose feature coming soon)
- Voice recognition requires internet for some models
- Calendar sync requires additional setup
- No multi-account support yet

## Performance Notes

- First run takes longer (AI model loading)
- Subsequent launches are instant
- Chat responses depend on system hardware
- Analytics charts update in background
- Voice processing may take 2-3 seconds per command

## License

MIT License - See [LICENSE](LICENSE) file for details.

**Created with ❤️ for work-from-home productivity**
