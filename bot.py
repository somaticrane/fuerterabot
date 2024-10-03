import telebot
import sqlite3
import time
import os
import psycopg2
from urllib.parse import urlparse
from telebot import types

DATABASE_URL = os.getenv('DATABASE_URL', 'dbname=fuerterabot user=postgres password=fabiodb2005')
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()

TOKEN = '6983811138:AAHX-vDEaDx9QqFm2PFfqA18N4-vqmzA_Rg'
bot = telebot.TeleBot(TOKEN)

user_states = {}
user_transaction_data = {}
messages_to_delete = {}

MAIN_MENU = 'MAIN MENU'
YOURCREDIT_MENU = 'YOURCREDIT_MENU'
ASSISTANCE_MENU = 'ASSISTANCE_MENU'
DONATE_MENU = 'DONATE_MENU'
HOWDOESITWORK_MENU = 'HOWDOESITWORK_MENU'
LAST5TRANS_MENU = 'LAST5TRANS_MENU'
SEND_MENU = 'SEND_MENU'
AMOUNT_MENU = 'AMOUNT_MENU'


# Crea una tabella per memorizzare i saldi utenti, se non esiste già
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                  user_id BIGINT PRIMARY KEY,
                  username VARCHAR(100),
                  balance DECIMAL(10, 2) DEFAULT 0.00)''')
conn.commit()

# Funzione per registrare un utente
def register_user(user_id, username):
    cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (user_id, username) VALUES (%s, %s)", (user_id, username))
        conn.commit()

# Funzione per ottenere il saldo dell'utente
def get_user_balance(user_id):
    cursor.execute("SELECT balance FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return 0  # Se l'utente non è trovato, ritorna 0

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == AMOUNT_MENU)
def handle_amount_menu(message):
    print(f"Current state: {AMOUNT_MENU}")
    print(f"Received message: {message.text}")
    
    if message.text in ['20', '50', '100', '250']:
        amount = int(message.text)
        send_credit(message, amount)
    elif message.text == '>500':
        bot.reply_to(message, "[Contact us to make this transaction!](https://t.me/depart_ok)", parse_mode="Markdown")
        user_states[message.chat.id] = MAIN_MENU
    elif message.text == 'Altro':
        bot.reply_to(message, "Please enter the desired amount:")
    elif message.text == 'Back':
        user_states[message.chat.id]==MAIN_MENU
        start(message)
    else:
        try:
            amount = int(message.text)
            if amount > 0:
                send_credit(message, amount)
            else:
                bot.reply_to(message, "Please enter a valid amount.")
        except ValueError:
            bot.reply_to(message, "Please enter a valid number.")

def send_credit(message, amount):
    sender_id = message.chat.id
    recipient_username = user_transaction_data.get(sender_id, {}).get('username')

    if recipient_username:
        # Recupera recipient_id dal database
        recipient_id = cursor.execute("SELECT user_id FROM users WHERE username = ?", (recipient_username,)).fetchone()

        if recipient_id:
            recipient_id = recipient_id[0]  # Prendi il primo elemento della tupla
            sender_balance = get_user_balance(sender_id)

            if sender_balance >= amount:
                # Aggiorna i saldi nel database
                cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, sender_id))
                cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, recipient_id))
                conn.commit()
                bot.reply_to(message, f"{amount} credits have been sent to {recipient_username}.")
            else:
                bot.reply_to(message, "You don't have enough credits to send.")
        else:
            bot.reply_to(message, "Recipient not found.")
    else:
        bot.reply_to(message, "Recipient username not set.")

        bot.reply_to(message, "Destinatario non trovato. Assicurati di aver inserito l'username corretto.")

    # Reimposta lo stato e cancella i dati temporaneipy 
    user_states[message.chat.id] = YOURCREDIT_MENU
    user_transaction_data.pop(message.chat.id, None)
    start(message)

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    username = message.from_user.username
    register_user(user_id, username)
    user_states[message.chat.id] = MAIN_MENU
    print(f"State set to: {MAIN_MENU}")  # Debugging

    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    itembtn1 = types.KeyboardButton('Your credit')
    itembtn2 = types.KeyboardButton('Assistance')
    itembtn3 = types.KeyboardButton('Donate')
    itembtn4 = types.KeyboardButton('How does it work?')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4)

    bot.reply_to(message, "Welcome!", reply_markup=markup)


@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    state = user_states.get(message.chat.id)
    
    # Aggiungi i print per il debug
    print(f"Current state: {state}")
    print(f"Received message: {message.text}")

    if state == SEND_MENU:
        print(f"Handling SEND_MENU state")  # Debug
        if 'username' not in user_transaction_data.get(message.chat.id, {}):
            recipient_username = message.text
            print(f"Recipient username: {recipient_username}")  # Debug
            cursor.execute("SELECT user_id FROM users WHERE username = ?", (recipient_username,))
            result = cursor.fetchone()

            if result:
                user_transaction_data[message.chat.id] = {'username': recipient_username}
                user_states[message.chat.id] = AMOUNT_MENU
                print(f"State changed to: {AMOUNT_MENU}")  # Debug

                markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
                itembtn_20 = types.KeyboardButton('20')
                itembtn_50 = types.KeyboardButton('50')
                itembtn_100 = types.KeyboardButton('100')
                itembtn_250 = types.KeyboardButton('250')
                itembtn_500plus = types.KeyboardButton('>500')
                itembtn_other = types.KeyboardButton('Altro')
                itembtn_back = types.KeyboardButton('Back')
                markup.add(itembtn_20, itembtn_50, itembtn_100, itembtn_250, itembtn_500plus, itembtn_other, itembtn_back)
                bot.reply_to(message, "Scegli l'importo da inviare:", reply_markup=markup)
            else:
                bot.reply_to(message, "Destinatario non trovato. Inserisci un username valido.")
        elif state == AMOUNT_MENU:
            print(f"Handling AMOUNT_MENU state")  # Debug
            if message.text in ['20', '50', '100', '250']:
                amount = int(message.text)
                send_credit(message, amount)
            elif message.text == '>500':
                bot.reply_to(message, "Please contact us to make this transation!")
            elif message.text == 'Altro':
                bot.reply_to(message, "Please insert the amount:")
            else:
                try:
                    amount = int(message.text)
                    if amount > 0:
                        send_credit(message, amount)
                    else:
                        bot.reply_to(message, "Please, insert a valid amount.")
                except ValueError:
                    bot.reply_to(message, "Please, insert a valid amount.")
    elif message.text == "Back":
        user_states[message.chat.id] = MAIN_MENU
        start(message)
    elif message.text == 'Your credit':
        user_states[message.chat.id] = YOURCREDIT_MENU
        balance = get_user_balance(message.from_user.id)
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        itembtn_back = types.KeyboardButton('Back')
        itembtn_lastrans = types.KeyboardButton('Last 5 transactions')
        itembtn_send = types.KeyboardButton('Send')
        itembtn_withdrawal = types.KeyboardButton('Withdrawal')
        markup.add(itembtn_lastrans, itembtn_send, itembtn_withdrawal, itembtn_back)
        bot.reply_to(message, f"Your current balance is: {balance} credits 🪙", reply_markup=markup)
    elif message.text == 'Send':
        user_states[message.chat.id] = SEND_MENU
        print(f"State changed to: {SEND_MENU}")  # Debug
        bot.reply_to(message, "Insert the destination username:")
    elif message.text == 'Assistance':
        user_states[message.chat.id] = ASSISTANCE_MENU
        bot.reply_to(message, "For assistance,  the modder: [Click here](https://t.me/depart_ok)", parse_mode="Markdown")
    elif message.text == 'Donate':
        user_states[message.chat.id] = DONATE_MENU
        # Gestione delle donazioni, se necessario
    elif message.text == 'How does it work?':
        user_states[message.chat.id] = HOWDOESITWORK_MENU
        # Gestione delle informazioni su come funziona, se necessario


bot.polling()
