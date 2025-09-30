# 🧠 Telegram Deep Link Content Delivery Bot

A secure Telegram bot that acts as a content gateway between private groups and public users via deep links.

## 📌 Overview

This bot listens for messages in a private group, stores them with unique IDs, and delivers them to users via shareable deep links.

## 🎯 Features

- ✅ **Private Group Listener** - Captures messages and generates unique deep links
- ✅ **Deep Link Delivery** - Users click links to receive original content
- ✅ **Chat-Type Awareness** - Different responses for private chats, groups, and channels
- ✅ **Robust Error Handling** - Graceful failures with user-friendly messages
- ✅ **Persistent Storage** - JSON-based storage with corruption protection

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.9+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Private group/channel ID

### 2. Installation

```bash
# Clone repository
git clone <your-repo-url>
cd telegram-content-bot

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

### 3. Configuration

Edit `.env` file:

```env
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
PRIVATE_CHANNEL_ID=-1001234567890
```

**How to get Channel ID:**
1. Add bot to your private group as admin
2. Forward a message from the group to [@userinfobot](https://t.me/userinfobot)
3. Copy the chat ID (include the `-100` prefix)

### 4. Run the Bot

```bash
python bot.py
```

## 📦 Deployment (Render)

1. Push code to GitHub
2. Create new Web Service on [Render](https://render.com)
3. Connect your repository
4. Add environment variables:
   - `BOT_TOKEN`
   - `PRIVATE_CHANNEL_ID`
5. Deploy!

## 🛠️ How It Works

1. Bot monitors messages in private group
2. Generates unique ID and deep link for each message
3. Replies with shareable link: `https://t.me/YourBot?start=abc123`
4. When user clicks link → bot delivers original content

## 📁 Project Structure

```
telegram-content-bot/
├── bot.py                 # Main bot logic
├── content_store.json     # Content ID mappings
├── .env                   # Environment variables
├── requirements.txt       # Dependencies
├── render.yaml           # Render config
└── README.md             # This file
```

## 🔒 Security Notes

- Never commit `.env` file
- Bot needs admin rights in private group
- Content IDs are cryptographically random
- JSON file stores only message references (not content)

## 🐛 Troubleshooting

**Bot not responding:**
- Check bot token is correct
- Ensure bot is added to group as admin

**Deep links not working:**
- Verify PRIVATE_CHANNEL_ID includes `-100` prefix
- Check bot has access to read messages

**Content not delivering:**
- Original message may have been deleted
- Bot may have lost access to private group

## 📝 License

MIT License - feel free to use and modify!

## 🤝 Contributing

Pull requests welcome! Please open an issue first to discuss changes.

---

Built with ❤️ using [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)

