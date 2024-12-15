import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import json
import os

# Token for the bot
TOKEN = "7340973464:AAFM8WrkRELL4aSSYPBLQLf-hLWM3WbQ3mY"
bot = telebot.TeleBot(TOKEN)

# Path to the file where requests are stored
REQUESTS_FILE = "requests.json"
active_chats = {}

# Load existing requests from the file if it exists
def load_requests():
    if os.path.exists(REQUESTS_FILE):
        with open(REQUESTS_FILE, 'r', encoding='utf-8') as file:
            data = json.load(file)
            # Ensure the request IDs are integers
            return {int(key): value for key, value in data.items()}
    return {}

# Save the requests to the file
def save_requests():
    with open(REQUESTS_FILE, 'w', encoding='utf-8') as file:
        json.dump(requests, file, ensure_ascii=False, indent=4)

# Request storage
requests = load_requests()
request_counter = max(requests.keys(), default=0)  # Set counter to the highest ID in the requests file

# Administrators
ADMINS = [6514083156]

# Status options
STATUS_OPTIONS = ["Qabul qilindi", "Jarayonda", "Yakunlandi", "Bekor qilindi"]

# Client part
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Assalomu alaykum! Iltimos, so'rovingizni yuboring, biz uni tez orada hal qilamiz. Agar yordam kerak bo'lsa, yozing /chat.")

# Клиент: Включить чат с оператором
@bot.message_handler(commands=['chat'])
def start_chat_with_operator(message):
    client_id = message.chat.id
    if client_id in active_chats:
        bot.reply_to(message, "Siz allaqachon operator bilan bog'langansiz. Agar chiqmoqchi bo'lsangiz, /stopchat buyrug'ini yuboring.")
    else:
        active_chats[client_id] = None  # Отметить чат как активный
        bot.reply_to(message, "Siz operator bilan bog'landingiz. Iltimos, savolingizni yozing. Agar suhbatni tugatmoqchi bo'lsangiz, /stopchat buyrug'ini yuboring.")
        for admin in ADMINS:
            bot.send_message(admin, f"Yangi chat boshlandi! Mijoz: {message.from_user.full_name} (ID: {client_id})")

# Клиент: Завершить чат с оператором
@bot.message_handler(commands=['stopchat'])
def stop_chat_with_operator(message):
    client_id = message.chat.id
    if client_id in active_chats:
        del active_chats[client_id]  # Удалить чат из активных
        bot.reply_to(message, "Operator bilan muloqot yakunlandi. Bizga yana murojaat qilish uchun /chat buyrug'ini yuborishingiz mumkin.")
        for admin in ADMINS:
            bot.send_message(admin, f"Mijoz {message.from_user.full_name} (ID: {client_id}) operator bilan muloqotni tugatdi.")
    else:
        bot.reply_to(message, "Siz hozir operator bilan bog'langan emassiz.")

# Клиент: Сообщение в режиме чата
@bot.message_handler(func=lambda message: message.chat.id in active_chats)
def forward_message_to_operator(message):
    client_id = message.chat.id
    for admin in ADMINS:
        bot.send_message(admin, f"Yangi xabar mijozdan ({message.from_user.full_name}, ID: {client_id}):\n\n{message.text}")
    bot.reply_to(message, "Xabaringiz operatorga yuborildi. Javobni kuting.")

# Администратор: Ответ клиенту
@bot.message_handler(func=lambda message: message.chat.id in ADMINS and message.reply_to_message)
def reply_to_client(message):
    try:
        # Извлечь ID клиента из оригинального сообщения администратора
        original_text = message.reply_to_message.text
        client_id = int(original_text.split('ID: ')[-1].split(')')[0])

        if client_id in active_chats:
            bot.send_message(client_id, f"Operator javobi:\n\n{message.text}")
            bot.reply_to(message, "Javob yuborildi.")
        else:
            bot.reply_to(message, "Mijoz hozir operator bilan bog'lanmagan.")
    except Exception as e:
        bot.reply_to(message, f"Xatolik yuz berdi: {str(e)}")
    
@bot.message_handler(func=lambda message: not message.text.startswith('/') and message.chat.id not in active_chats)
def create_request(message):
    global request_counter
    request_counter += 1
    request_id = request_counter
    deadline = datetime.now() + timedelta(days=7)
    requests[request_id] = {
        "client_id": message.chat.id,
        "client_name": f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip(),
        "text": message.text,
        "status": "Yangi",
        "deadline": deadline.strftime('%Y-%m-%d %H:%M:%S')
    }
    save_requests()

    for admin in ADMINS:
        bot.send_message(
            admin,
            f"Yangi zayavka! #{request_id}\n"
            f"Ism: {requests[request_id]['client_name']}\n"
            f"Matn: {message.text}\n"
            f"Deadline: {deadline.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    bot.reply_to(
        message,
        f"Rahmat! So'rovingiz qabul qilindi. Uning raqami: <b>#{request_id}</b>\nDeadline: <b>{deadline.strftime('%Y-%m-%d %H:%M:%S')}</b>",
        parse_mode='HTML'
    )

@bot.message_handler(func=lambda message: not message.text.startswith('/') and message.chat.id in active_chats)
def chat_is_active_warning(message):
    bot.reply_to(message, "Siz operator bilan muloqotdasiz. Iltimos, suhbatni tugatish uchun /stopchat buyrug'ini yuboring.")

@bot.message_handler(commands=['myrequests'])
def my_requests(message):
    client_requests = [req_id for req_id, req in requests.items() if req["client_id"] == message.chat.id]
    if client_requests:
        keyboard = InlineKeyboardMarkup()
        for req_id in client_requests:
            status = requests[req_id]["status"]
            # Формируем кнопку с ID и статусом
            button = InlineKeyboardButton(text=f"#{req_id} - {status}", callback_data=f"view_request_{req_id}")
            keyboard.add(button)
        bot.send_message(
            message.chat.id,
            "<b>Sizning so'rovlaringiz:</b>\nKerakli so'rovni tanlang.",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    else:
        bot.send_message(message.chat.id, "Hozircha sizning hech qanday so'rovingiz mavjud emas.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("view_request_"))
def view_request(call):
    req_id = int(call.data.split("_")[2])
    request_info = requests.get(req_id)
    if request_info:
        client_name = request_info["client_name"]
        text = request_info["text"]
        status = request_info["status"]
        deadline = request_info["deadline"]
        
        details = (
            f"<b>So'rov #{req_id}</b>\n"
            f"<b>Mijoz:</b> {client_name}\n"
            f"<b>Matn:</b> {text}\n"
            f"<b>Status:</b> {status}\n"
            f"<b>Deadline:</b> {deadline}"
        )
        
        # Добавление кнопки "⬅️ Orqaga"
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_requests"))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=details,
            parse_mode='HTML',
            reply_markup=keyboard
        )
    else:
        bot.answer_callback_query(call.id, "So'rov topilmadi.")

@bot.callback_query_handler(func=lambda call: call.data == "back_to_requests")
def back_to_requests(call):
    client_requests = [req_id for req_id, req in requests.items() if req["client_id"] == call.message.chat.id]
    if client_requests:
        keyboard = InlineKeyboardMarkup()
        for req_id in client_requests:
            status = requests[req_id]["status"]
            # Формируем кнопку с ID и статусом
            button = InlineKeyboardButton(text=f"#{req_id} - {status}", callback_data=f"view_request_{req_id}")
            keyboard.add(button)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="<b>Sizning so'rovlaringiz:</b>\nKerakli so'rovni tanlang.",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    else:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Hozircha sizning hech qanday so'rovingiz mavjud emas."
        )

@bot.message_handler(func=lambda message: message.text.startswith('#'))
def view_request_details(message):
    try:
        request_id = int(message.text.strip('#'))
        request_info = requests.get(request_id)
        if request_info and request_info['client_id'] == message.chat.id:
            deadline = request_info['deadline']
            text = (f"<b>Zayavka #{request_id}</b>\n"
                    f"<b>Ism</b>: {request_info['client_name']}\n"
                    f"<b>Matn</b>: {request_info['text']}\n"
                    f"<b>Status</b>: {request_info['status']}\n"
                    f"<b>Deadline</b>: {deadline}")
            bot.reply_to(message, text, parse_mode='HTML')
        else:
            bot.reply_to(message, "Bu so'rov sizga tegishli emas yoki topilmadi.")
    except ValueError:
        bot.reply_to(message, "Iltimos, to'g'ri raqam kiriting.")

# Admin panel part
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id in ADMINS:
        markup = InlineKeyboardMarkup()
        for request_id in requests:
            markup.add(InlineKeyboardButton(f"Zayavka #{request_id}", callback_data=f"view_{request_id}"))
        markup.add(InlineKeyboardButton("Yuborish xabar", callback_data="send_message"))
        bot.send_message(message.chat.id, "Iltimos, boshqarish uchun so'rovni tanlang:", reply_markup=markup)
    else:
        bot.reply_to(message, "Sizning admin paneliga kirish huquqingiz yo'q.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("view_"))
def view_request_admin(call):
    if call.message.chat.id in ADMINS:
        request_id = int(call.data.split("_")[1])
        request_info = requests.get(request_id)
        if request_info:
            text = (f"<b>Zayavka #{request_id}</b>\n"
                    f"<b>Ism</b>: {request_info['client_name']}\n"
                    f"<b>ID klient</b>: {request_info['client_id']}\n"
                    f"<b>Matn</b>: {request_info['text']}\n"
                    f"<b>Status</b>: {request_info['status']}\n"
                    f"<b>Deadline</b>: {request_info['deadline']}")
            markup = InlineKeyboardMarkup()
            for status in STATUS_OPTIONS:
                markup.add(InlineKeyboardButton(status, callback_data=f"status_{request_id}_{status}"))
            markup.add(InlineKeyboardButton("Orqaga", callback_data="back_to_admin"))
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='HTML')
        else:
            bot.answer_callback_query(call.id, "Zayavka topilmadi.")
    else:
        bot.answer_callback_query(call.id, "Kirishga huquqingiz yo'q.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("status_"))
def change_status(call):
    if call.message.chat.id in ADMINS:
        _, request_id, new_status = call.data.split("_")
        request_id = int(request_id)
        if request_id in requests:
            requests[request_id]["status"] = new_status
            client_id = requests[request_id]["client_id"]
            # Send a message to the client if the status is "Yakunlandi"
            if new_status == "Yakunlandi":
                bot.send_message(client_id, 
                                 f"Sizning so'rovingiz <b>#{request_id}</b> yakunlandi. "
                                 "Savol va takliflar bo'yicha qo'shimcha ma'lumot olish uchun, +998940571171 raqamiga murojat qiling.",
                                 parse_mode='HTML')
            elif new_status == "Bekor qilindi":
                bot.send_message(client_id, 
                                 f"Sizning so'rovingiz <b>#{request_id}</b> bekor qilindi. "
                                 "Agar boshqa savollar bo'lsa, biz bilan bog'laning.",
                                 parse_mode='HTML')
            else: bot.send_message(client_id, f"Sizning so'rovingiz <b>#{request_id}</b> holati o'zgartirildi: <b>{new_status}</b>", parse_mode='HTML')
            
            save_requests()  # Save the updated status to the file
            bot.answer_callback_query(call.id, "Holat yangilandi.")
            bot.edit_message_text(f"<b>Zayavka #{request_id}</b>\nIsm: {requests[request_id]['client_name']}\nID klient: {requests[request_id]['client_id']}\nMatn: {requests[request_id]['text']}\nHolat: {new_status}\nDeadline: {requests[request_id]['deadline']}",
                                  call.message.chat.id, call.message.message_id, parse_mode='HTML')
            # Add "Back" button after updating the status
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Orqaga", callback_data="back_to_admin"))
            bot.send_message(call.message.chat.id, "Status o'zgartirildi. Orqaga qaytish uchun tugmani bosing.", reply_markup=markup)
        else:
            bot.answer_callback_query(call.id, "Zayavka topilmadi.")
    else:
        bot.answer_callback_query(call.id, "Kirishga huquqingiz yo'q.")
# Button for "Back to Admin"
@bot.callback_query_handler(func=lambda call: call.data == "back_to_admin")
def back_to_admin(call):
    if call.message.chat.id in ADMINS:
        markup = InlineKeyboardMarkup()
        for request_id in requests:
            markup.add(InlineKeyboardButton(f"Zayavka #{request_id}", callback_data=f"view_{request_id}"))
        markup.add(InlineKeyboardButton("Yuborish xabar", callback_data="send_message"))
        bot.edit_message_text("Iltimos, boshqarish uchun so'rovni tanlang:", call.message.chat.id, call.message.message_id, reply_markup=markup)

# Admin message sending
# Словарь для хранения текстов сообщений по уникальным ID
message_storage = {}

@bot.callback_query_handler(func=lambda call: call.data == "send_message")
def send_message_to_client(call):
    if call.message.chat.id in ADMINS:
        bot.send_message(call.message.chat.id, "Iltimos, yuboriladigan xabarni kiriting:")
        bot.register_next_step_handler(call.message, process_message)

def process_message(message):
    if message.chat.id in ADMINS:
        # Сохраняем текст сообщения, который администратор хочет отправить
        text_to_send = message.text
        # Сохраняем текст сообщения в словарь по уникальному ключу
        unique_key = f"message_{message.chat.id}"  # Можно использовать уникальный ID
        message_storage[unique_key] = text_to_send
        
        bot.send_message(message.chat.id, "Sizning so'rovingiz tekshirilmoqda, iltimos kuting.")
        
        markup = InlineKeyboardMarkup()
        for request_id in requests:
            client_id = requests[request_id]['client_id']
            # Используем только ID заявки или клиента в callback_data
            callback_data = f"client_{client_id}_{request_id}"
            markup.add(InlineKeyboardButton(f"#{request_id} - {requests[request_id]['client_name']}", callback_data=callback_data))
        
        bot.send_message(message.chat.id, "Mijozni tanlang:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("client_"))
def send_message_to_client_handler(call):
    if call.message.chat.id in ADMINS:
        # Извлекаем данные из callback_data
        client_id, request_id = call.data.split("_")[1], call.data.split("_")[2]
        client_id = int(client_id)
        
        # Извлекаем сообщение из словаря по ключу
        unique_key = f"message_{call.message.chat.id}"  # Используем тот же ключ
        if unique_key in message_storage:
            message_to_send = message_storage[unique_key]
            bot.send_message(client_id, message_to_send)
            bot.answer_callback_query(call.id, "Xabar yuborildi.")
        else:
            bot.answer_callback_query(call.id, "Xabar topilmadi.")

# Check for expired deadlines
import time

def check_deadlines():
    while True:
        now = datetime.now()
        for request_id, request_info in requests.items():
            if request_info["status"] != "Yakunlandi" and datetime.strptime(request_info["deadline"], '%Y-%m-%d %H:%M:%S') < now:
                requests[request_id]["status"] = "Yakunlandi"
                bot.send_message(request_info["client_id"], f"Sizning so'rovingiz #{request_id}ning deadline muddati o'tdi va holati <b>'Yakunlandi'</b> deb o'zgartirildi.", parse_mode='HTML')
                save_requests()  # Save the updated status to the file
        time.sleep(60)  # Check every minute

# Start deadline checking in a separate thread
import threading
threading.Thread(target=check_deadlines, daemon=True).start()

if __name__ == "__main__":
    print("Bot ishga tushdi")
    bot.polling(none_stop=True)
