import logging
import json
import os
import secrets
import re
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from telegram.error import (
    TelegramError, NetworkError, BadRequest,
    TimedOut, Forbidden, RetryAfter
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot_errors.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==========================================
# CUSTOM EXCEPTIONS
# ==========================================

class ContentNotFoundError(Exception):
    pass

class StorageError(Exception):
    pass

class InvalidDeepLinkError(Exception):
    pass

# ==========================================
# CONTENT STORE CLASS
# ==========================================

class ContentStore:
    def __init__(self, filepath='content_store.json'):
        self.filepath = filepath
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        try:
            with open(self.filepath, 'r') as f:
                json.load(f)
        except FileNotFoundError:
            with open(self.filepath, 'w') as f:
                json.dump({}, f)
            logger.info(f"Created new storage file: {self.filepath}")
        except json.JSONDecodeError:
            logger.error("Corrupted JSON file, creating backup")
            import shutil
            shutil.copy(self.filepath, f"{self.filepath}.backup")
            with open(self.filepath, 'w') as f:
                json.dump({}, f)
    
    def save_content(self, content_id: str, chat_id: int, message_id: int) -> None:
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
            
            data[content_id] = {
                'chat_id': chat_id,
                'message_id': message_id,
                'created_at': datetime.now().isoformat()
            }
            
            with open(self.filepath, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved content: {content_id}")
            
        except (IOError, json.JSONDecodeError) as e:
            logger.critical(f"Failed to save content {content_id}: {e}")
            raise StorageError(f"Could not save content: {e}")
    
    def get_content(self, content_id: str) -> dict:
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
            
            if content_id not in data:
                raise ContentNotFoundError(f"Content ID {content_id} not found")
            
            return data[content_id]
            
        except FileNotFoundError:
            logger.error("Storage file not found")
            raise StorageError("Storage file missing")
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted storage file: {e}")
            raise StorageError("Storage file corrupted")

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def generate_unique_id() -> str:
    return secrets.token_urlsafe(8)

def is_valid_content_id(content_id: str) -> bool:
    return bool(re.match(r'^[A-Za-z0-9_-]{8,}$', content_id))

# ==========================================
# BOT HANDLERS
# ==========================================

async def handle_private_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        private_channel_id = int(os.getenv('PRIVATE_CHANNEL_ID', 0))
        
        if update.message.chat_id != private_channel_id:
            return
        
        content_id = generate_unique_id()
        
        store = ContentStore()
        store.save_content(
            content_id,
            update.message.chat_id,
            update.message.message_id
        )
        
        bot_username = context.bot.username
        deep_link = f"https://t.me/{bot_username}?start={content_id}"
        
        await update.message.reply_text(
            f"✅ Content saved!\n🔗 Share this link:\n{deep_link}",
            disable_web_page_preview=True
        )
        
        logger.info(f"Created deep link for message {update.message.message_id}")
        
    except StorageError:
        await update.message.reply_text("❌ Failed to save content. Please try again.")
    except Exception as e:
        logger.error(f"Error in private group handler: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again.")

async def handle_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_type = update.effective_chat.type
        
        if chat_type in ['group', 'supergroup']:
            await update.message.reply_text("👋 Hey! Please message me directly for content access.")
            return
        
        if chat_type == 'channel':
            await update.message.reply_text("📢 Use the links shared here to access exclusive content!")
            return
        
        if not context.args:
            await update.message.reply_text(
                "👋 Welcome to the CodeNova Bot! created by CodeNova team.\n\n"
                "🔗 Click on a shared link to access exclusive content.\n"
                "💬 Links are shared in our public channel/group."
            )
            return
        
        content_id = context.args[0]
        
        if not is_valid_content_id(content_id):
            await update.message.reply_text("⚠️ Invalid link format. Please use a valid link.")
            return
        
        store = ContentStore()
        content_info = store.get_content(content_id)
        
        await context.bot.copy_message(
            chat_id=update.effective_chat.id,
            from_chat_id=content_info['chat_id'],
            message_id=content_info['message_id']
        )
        
        logger.info(f"Delivered content {content_id} to user {update.effective_user.id}")
        
    except ContentNotFoundError:
        logger.warning(f"Content not found: {context.args[0] if context.args else 'none'}")
        await update.message.reply_text("⚠️ This content is no longer available or the link is invalid.")
    except Forbidden:
        logger.error("Bot lost access to source message")
        await update.message.reply_text("⚠️ This content is no longer accessible.")
    except BadRequest as e:
        logger.error(f"Cannot copy message: {e}")
        await update.message.reply_text("❌ Unable to retrieve content. It may have been deleted.")
    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again later.")

async def error_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error: {context.error}")
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text("😔 Something went wrong. Please try again.")
        except Exception:
            pass

# ==========================================
# MAIN FUNCTION
# ==========================================

def main():
    bot_token = os.getenv('BOT_TOKEN')
    
    if not bot_token:
        logger.error("BOT_TOKEN not found in environment variables!")
        return
    
    application = Application.builder().token(bot_token).build()
    
    application.add_handler(CommandHandler('start', handle_start_command))
    application.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS | filters.ChatType.SUPERGROUP,
            handle_private_group_message
        )
    )
    
    application.add_error_handler(error_callback)
    
    logger.info("Bot started successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()