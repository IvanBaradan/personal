import telebot
import requests
import time

# Bot configuration
BOT_TOKEN = '8331997671:AAEUMEMOlgBliUGg5rwlbbud_b3TT98zJu8' 
SERVER_URL = 'http://localhost:5000'

bot = telebot.TeleBot(BOT_TOKEN)

# Store user states
user_states = {}

@bot.message_handler(commands=['start'])
def start(message):
    """Welcome message"""
    welcome_text = """
🐱 Welcome to Cat Game! 🐱

Use /join to start playing and control your cat through Telegram!

Commands:
/join - Join the game
/help - Show this help message
    """
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['help'])
def help_command(message):
    """Help command"""
    

    bot.reply_to(message)

@bot.message_handler(commands=['join'])
def join_game(message):
    """Join the game command"""
    user_id = str(message.from_user.id)
    username = message.from_user.username or message.from_user.first_name
    if user_id in user_states:
        bot.reply_to(message, "You're already in the game! Check your private messages for control buttons.")
        return
    try:
        response = requests.post(f'{SERVER_URL}/api/join', json={
            'telegram_id': user_id,
            'username': username
        })
        
        if response.status_code == 200:

            keyboard = telebot.types.InlineKeyboardMarkup()

            up_button = telebot.types.InlineKeyboardButton('⬆️ Up', callback_data='move_up')
            down_button = telebot.types.InlineKeyboardButton('⬇️ Down', callback_data='move_down')
            left_button = telebot.types.InlineKeyboardButton('⬅️ Left', callback_data='move_left')
            right_button = telebot.types.InlineKeyboardButton('➡️ Right', callback_data='move_right')
            
            keyboard.row(up_button)
            keyboard.row(left_button, right_button)
            keyboard.row(down_button)
            try:
                bot.send_message(
                    message.from_user.id,
                    f"🎉 Добро пожаловать в игру, {username}! 🎉\n\n"
                    f"Твой котик появился на экране, ты можешь им управлять следующими клавишами:\n\n"
                    f"⬆️ Вверх\n"
                    f"⬇️ Вниз\n"
                    f"⬅️ Влево\n"
                    f"➡️ Вправо\n\n"
                    f"Собирай монетки чтобы увеличить свой счёт!!! 🪙",
                    reply_markup=keyboard
                )
                

                user_states[user_id] = {
                    'username': username,
                    'last_move': time.time()
                }
                
                bot.reply_to(message, "✅ Вы в игре")
                
            except telebot.apihelper.ApiException:
                bot.reply_to(
                    message, 
                    "❌ Не могу начать работу, пожалуйста НАПИШИТЕ /start."
                )
        
        elif response.status_code == 400:
            data = response.json()
            if 'already exists' in data.get('error', ''):
                bot.reply_to(message, "Вы уже в игре.")

        else:
            bot.reply_to(message, "❌ Похоже котики уронили сервер, попробуй позже.")
            
    except requests.exceptions.RequestException:
        bot.reply_to(message, "❌ Не получается зайти к котикам, пожалуйста зайди позже.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('move_'))
def handle_move(call):
    user_id = str(call.from_user.id)
    direction = call.data.replace('move_', '')

    if user_id in user_states:
        current_time = time.time()
        if current_time - user_states[user_id]['last_move'] < 0.5: 
            bot.answer_callback_query(call.id, "⏳ Please wait before moving again!")
            return
        user_states[user_id]['last_move'] = current_time
    
    try:
        response = requests.post(f'{SERVER_URL}/api/move', json={
            'telegram_id': user_id,
            'direction': direction
        })
        
        if response.status_code == 200:
            bot.answer_callback_query(call.id, f"✅ Moved {direction}!")
        elif response.status_code == 404:
            bot.answer_callback_query(call.id, "❌ Игрок не найден, перезайдите в игру.")
        else:
            bot.answer_callback_query(call.id, "❌ Move failed. Please try again.")
            
    except requests.exceptions.RequestException:
        bot.answer_callback_query(call.id, "❌ Server error. Please try again later.")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    """Handle all other messages"""
    bot.reply_to(message, "Use /join to start playing or /help for more information!")

def main():
    """Main function"""
    print("🐱 Cat Game Bot started!")
    print("Make sure the Flask server is running on localhost:5000")
    print("Don't forget to set your bot token in the BOT_TOKEN variable!")
    
    try:
        bot.polling(none_stop=True)
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Bot error: {e}")

if __name__ == '__main__':
    main()
