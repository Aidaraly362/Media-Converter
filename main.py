import telebot
import os
from PIL import Image
from telebot import types
import yt_dlp
import json

# ⚠️ Өз токеніңізді қойыңыз:
TOKEN = '8451654980:AAG_Ko-MS5lJ-5NnWiQoNyqgDPG8dgb0UjE'
bot = telebot.TeleBot(TOKEN)

# ⚠️ ОСЫ ЖЕРГЕ ЖАҢАҒЫ ӨЗІҢІЗДІҢ TELEGRAM ID-ІҢІЗДІ ЖАЗЫҢЫЗ (мысалы: 512345678):
ADMIN_ID = 1393494332  # 0-дің орнына өз ID-іңізді жазыңыз

# Пайдаланушылар базасын сақтайтын файл
USERS_FILE = "users.json"
user_images = {}
admin_state = {} # Админнің хабарлама жіберу күйін бақылау

# Пайдаланушыны базаға қосу функциясы
def save_user(user_id):
    users = []
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            try:
                users = json.load(f)
            except:
                users = []
    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)

# Пайдаланушылар санын алу
def get_users_count():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            try:
                return len(json.load(f))
            except:
                return 0
    return 0

# Главное меню
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_info = types.KeyboardButton('ℹ️ О боте')
    btn_help = types.KeyboardButton('❓ Как пользоваться?')
    markup.add(btn_info, btn_help)
    return markup

# Видео/Аудио таңдау батырмалары (MP3 қосылды)
def get_video_quality_keyboard(url):
    markup = types.InlineKeyboardMarkup()
    btn_high = types.InlineKeyboardButton("🎬 720p (Высокое)", callback_data=f"high|{url}")
    btn_low = types.InlineKeyboardButton("📱 360p (Низкое)", callback_data=f"low|{url}")
    btn_mp3 = types.InlineKeyboardButton("🎵 Скачать только Аудио (MP3)", callback_data=f"mp3|{url}")
    markup.add(btn_high, btn_low)
    markup.add(btn_mp3)
    return markup

# PDF дайын батырмалары
def get_pdf_ready_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_done = types.KeyboardButton('✅ Готово, создать PDF')
    btn_cancel = types.KeyboardButton('❌ Отмена')
    markup.add(btn_done, btn_cancel)
    return markup

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.chat.id) # Пайдаланушыны базаға тіркеу
    if message.chat.id in user_images:
        del user_images[message.chat.id]
        
    welcome_text = (
        f"👋 **Приветствуем, {message.from_user.first_name}!**\n\n"
        "✨ Я ваш супер **Медиа & PDF ассистент v4.0**.\n"
        "📸 Отправьте **фото**, чтобы собрать многостраничный PDF.\n"
        "🔗 Отправьте **ссылку на видео**, чтобы скачать его или получить **MP3 музыку**!"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

# Команда /admin (Тек админ үшін)
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id == ADMIN_ID:
        count = get_users_count()
        markup = types.InlineKeyboardMarkup()
        btn_send = types.InlineKeyboardButton("📢 Сделать рассылку", callback_data="admin_broadcast")
        markup.add(btn_send)
        bot.send_message(message.chat.id, f"📊 **Панель Администратора**\n\n👥 Всего пользователей в базе: **{count}**", parse_mode='Markdown', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "❌ У вас нет прав доступа к этой команде.")

# Басты мәзір батырмалары
@bot.message_handler(func=lambda message: message.text in ['ℹ️ О боте', '❓ Как пользоваться?', '✅ Готово, создать PDF', '❌ Отмена'])
def handle_menu(message):
    chat_id = message.chat.id
    save_user(chat_id)
    
    if message.text == 'ℹ️ О боте':
        bot.send_message(chat_id, "🤖 **О боте:** v4.0 (Pro)\n• Объединение фото в PDF.\n• Скачивание видео (360p/720p) и аудио (MP3) из соцсетей.", parse_mode='Markdown')
    elif message.text == '❓ Как пользоваться?':
        bot.send_message(chat_id, "📝 **Инструкция:**\n1. Для PDF — отправляйте фото, затем нажмите 'Готово'.\n2. Для видео/аудио — отправьте ссылку и выберите нужный формат.", parse_mode='Markdown')
    elif message.text == '❌ Отмена':
        if chat_id in user_images:
            for img in user_images[chat_id]:
                if os.path.exists(img): os.remove(img)
            del user_images[chat_id]
        bot.send_message(chat_id, "❌ Сборщик изображений очищен.", reply_markup=get_main_keyboard())
    elif message.text == '✅ Готово, создать PDF':
        if chat_id not in user_images or len(user_images[chat_id]) == 0:
            bot.send_message(chat_id, "⚠️ Вы не отправили фото!", reply_markup=get_main_keyboard())
            return
        status_msg = bot.send_message(chat_id, "⚙️ *Создаю PDF...*", parse_mode='Markdown')
        try:
            img_list = user_images[chat_id]
            pdf_filename = f"document_{chat_id}.pdf"
            first_image = Image.open(img_list[0]).convert('RGB')
            remaining_images = [Image.open(img).convert('RGB') for img in img_list[1:]]
            first_image.save(pdf_filename, save_all=True, append_images=remaining_images)
            with open(pdf_filename, 'rb') as pdf_file:
                bot.send_document(chat_id, pdf_file, caption=f"✅ **PDF готов! Страниц: {len(img_list)}**", reply_markup=get_main_keyboard())
            bot.delete_message(chat_id, status_msg.message_id)
            for img in img_list: os.remove(img)
            del user_images[chat_id]
            os.remove(pdf_filename)
        except Exception as e:
            bot.send_message(chat_id, f"❌ Ошибка: {e}", reply_markup=get_main_keyboard())

# Админ хабарламасын қабылдау (Рассылка)
@bot.message_handler(func=lambda message: admin_state.get(message.chat.id) == 'waiting_broadcast')
def process_broadcast(message):
    admin_state[message.chat.id] = None # Күйді тазалау
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "❌ Рассылка отменена.")
        return
        
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
        
        success = 0
        bot.send_message(message.chat.id, f"🚀 Начинаю отправку хабарлама для {len(users)} пользователей...")
        for u_id in users:
            try:
                bot.send_message(u_id, f"📢 **Сообщение от администратора:**\n\n{message.text}", parse_mode='Markdown')
                success += 1
            except:
                pass # Ботты бұғаттап тастаған пайдаланушылар өткізіліп жіберіледі
        bot.send_message(message.chat.id, f"✅ Рассылка завершена успешно! Доставлено: {success}/{len(users)}")

# Сүртетерді қабылдау
@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    chat_id = message.chat.id
    save_user(chat_id)
    if chat_id not in user_images: user_images[chat_id] = []
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    local_filename = f"img_{chat_id}_{len(user_images[chat_id])}.jpg"
    with open(local_filename, 'wb') as new_file: new_file.write(downloaded_file)
    user_images[chat_id].append(local_filename)
    bot.reply_to(message, f"📥 **Фото №{len(user_images[chat_id])} принято!**", reply_markup=get_pdf_ready_keyboard(), parse_mode='Markdown')

# Сілтеме келгенде сұрау
@bot.message_handler(func=lambda message: message.text and (message.text.startswith('http://') or message.text.startswith('https://')))
def ask_video_quality(message):
    save_user(message.chat.id)
    bot.reply_to(message, "🎬 **Выберите формат для загрузки:**", reply_markup=get_video_quality_keyboard(message.text))

# Инлайн батырмаларды өңдеу (Видео және MP3 жүктеу)
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    
    # Админ батырмасын тексеру
    if call.data == "admin_broadcast":
        if chat_id == ADMIN_ID:
            admin_state[chat_id] = 'waiting_broadcast'
            bot.send_message(chat_id, "✍️ Введите текст для рассылки (или напишите `/cancel` для отмены):")
        return

    # Медиа жүктеу батырмаларын тексеру
    if '|' in call.data:
        quality_type, url = call.data.split('|', 1)
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
        
        outtmpl = f"media_{chat_id}.%(ext)s"
        ydl_opts = {'outtmpl': outtmpl, 'max_filesize': 50 * 1024 * 1024, 'quiet': True}
        
        if quality_type == 'high':
            ydl_opts['format'] = 'best[ext=mp4]/best'
            status_str, success_caption, is_audio = "Скачиваю видео 720p...", "🎬 Видео готово!", False
        elif quality_type == 'low':
            ydl_opts['format'] = 'worst[ext=mp4]/worst'
            status_str, success_caption, is_audio = "Скачиваю видео 360p...", "📱 Видео готово!", False
        elif quality_type == 'mp3':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
            status_str, success_caption, is_audio = "Извлекаю аудио в MP3...", "🎵 Музыка успешно скачана!", True

        status_msg = bot.send_message(chat_id, f"⏳ **{status_str}** пожалуйста, подождите...")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                if is_audio:
                    filename = os.path.splitext(filename)[0] + ".mp3"
                
            with open(filename, 'rb') as file_to_send:
                if is_audio:
                    bot.send_audio(chat_id, file_to_send, caption=success_caption)
                else:
                    bot.send_video(chat_id, file_to_send, caption=success_caption)
                    
            bot.delete_message(chat_id, status_msg.message_id)
            if os.path.exists(filename): os.remove(filename)
        except Exception as e:
            bot.delete_message(chat_id, status_msg.message_id)
            bot.send_message(chat_id, "❌ **Ошибка загрузки.** Возможно файл больше 50МБ.")
            print(f"Error: {e}")

import os
from threading import Thread
from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "Бот жұмыс істеп тұр!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# Серверді артқы фонда іске қосу (Render-ді алдау үшін)
Thread(target=run).start()

# Ботты іске қосу
print("Бот сәтті қосылды...")
bot.infinity_polling(timeout=10, long_polling_timeout=5)
