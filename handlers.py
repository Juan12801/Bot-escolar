from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, MessageHandler, filters
import database
import datetime

user_data = {}


def get_admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Añadir Tarea", callback_data="add")],
        [InlineKeyboardButton("📋 Ver Todas", callback_data="list")],
        [InlineKeyboardButton("🗑️ Eliminar", callback_data="delete")],
        [InlineKeyboardButton("❓ Ayuda", callback_data="help")]
    ])


def get_user_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Ver Todas", callback_data="list")],
        [InlineKeyboardButton("❓ Ayuda", callback_data="help")]
    ])


def get_date_menu(task_name):
    keyboard = [
        [InlineKeyboardButton("📅 Mañana", callback_data=f"date_tomorrow_{task_name}")],
        [InlineKeyboardButton("📅 Pasado mañana", callback_data=f"date_dayafter_{task_name}")],
        [InlineKeyboardButton("📅 3 días", callback_data=f"date_3days_{task_name}")],
        [InlineKeyboardButton("📅 1 semana", callback_data=f"date_week_{task_name}")],
        [InlineKeyboardButton("📅 Otra fecha", callback_data=f"date_other_{task_name}")]
    ]
    return InlineKeyboardMarkup(keyboard)


async def is_admin(update, context):
    try:
        member = await context.bot.get_chat_member(
            update.effective_chat.id,
            update.effective_user.id
        )
        return member.status in ["administrator", "creator"]
    except:
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin = await is_admin(update, context)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="👋 *Bot Escolar*\n\nGestiona tareas y recibe recordatorios 2 días antes a las 3 PM.\n\nSelecciona:",
        parse_mode="Markdown",
        reply_markup=get_admin_menu() if admin else get_user_menu()
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    
    try:
        await query.answer()
    except:
        pass
    
    admin = await is_admin(update, context)
    data = query.data
    
    if data == "add":
        if not admin:
            await context.bot.send_message(chat_id=chat_id, text="❌ Solo administradores")
            return
        
        user_data[user_id] = {"step": "name"}
        await context.bot.send_message(chat_id=chat_id, text="📝 Escribe el nombre de la tarea:")
        return
    
    elif data == "delete":
        if not admin:
            await context.bot.send_message(chat_id=chat_id, text="❌ Solo administradores")
            return
        
        tasks = database.get_all_tasks()
        if not tasks:
            await context.bot.send_message(chat_id=chat_id, text="📋 No hay tareas", reply_markup=get_admin_menu())
            return
        
        keyboard = []
        for task in tasks:
            keyboard.append([InlineKeyboardButton(f"❌ {task['task_name']}", callback_data=f"del_{task['_id']}")])
        keyboard.append([InlineKeyboardButton("🔙 Menú", callback_data="menu")])
        
        await context.bot.send_message(chat_id=chat_id, text="🗑️ Selecciona tarea:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    elif data == "list":
        tasks = database.get_all_tasks()
        menu = get_admin_menu() if admin else get_user_menu()
        
        if not tasks:
            await context.bot.send_message(chat_id=chat_id, text="📋 No hay tareas", reply_markup=menu)
            return
        
        text = "📋 *Tareas:*\n\n"
        for t in tasks:
            text += f"• {t['task_name']} ({t['due_date']}) - @{t['username']}\n"
        
        await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown", reply_markup=menu)
        return
    
    elif data == "help":
        menu = get_admin_menu() if admin else get_user_menu()
        await context.bot.send_message(
            chat_id=chat_id,
            text="📚 *Ayuda*\n\n➕ Añadir: Crear tarea (admin)\n📋 Ver: Todas las tareas\n🗑️ Eliminar: Borrar tarea (admin)\n⏰ Recordatorio: 2 días antes 3 PM",
            parse_mode="Markdown",
            reply_markup=menu
        )
        return
    
    elif data == "menu":
        admin = await is_admin(update, context)
        await context.bot.send_message(chat_id=chat_id, text="Selecciona:", reply_markup=get_admin_menu() if admin else get_user_menu())
        return
    
    elif data.startswith("del_"):
        if not admin:
            await context.bot.send_message(chat_id=chat_id, text="❌ Solo administradores")
            return
        
        task_id = data.replace("del_", "")
        task = database.get_task_by_id(task_id)
        
        if not task:
            await context.bot.send_message(chat_id=chat_id, text="❌ No encontrada")
            return
        
        database.delete_task(task_id, task["user_id"])
        await context.bot.send_message(chat_id=chat_id, text=f"✅ Eliminada: {task['task_name']}", reply_markup=get_admin_menu())
        return
    
    elif data.startswith("date_"):
        if not admin:
            await context.bot.send_message(chat_id=chat_id, text="❌ Solo administradores")
            return
        
        task_name = data.replace("date_tomorrow_", "").replace("date_dayafter_", "").replace("date_3days_", "").replace("date_week_", "").replace("date_other_", "")
        
        if "_other" in data:
            user_data[user_id] = {"step": "date", "name": task_name}
            await context.bot.send_message(chat_id=chat_id, text=f"📝 {task_name}\n\n📅 Escribe la fecha (YYYY-MM-DD):")
            return
        
        due_date = None
        if "_tomorrow" in data:
            due_date = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        elif "_dayafter" in data:
            due_date = (datetime.date.today() + datetime.timedelta(days=2)).strftime("%Y-%m-%d")
        elif "_3days" in data:
            due_date = (datetime.date.today() + datetime.timedelta(days=3)).strftime("%Y-%m-%d")
        elif "_week" in data:
            due_date = (datetime.date.today() + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        
        if due_date:
            database.add_task(user_id, query.from_user.username or "user", task_name, due_date)
            await context.bot.send_message(chat_id=chat_id, text=f"✅ Creada: {task_name}\n📅 Fecha: {due_date}", reply_markup=get_admin_menu())
        return


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if user_id not in user_data:
        await start(update, context)
        return
    
    state = user_data.get(user_id, {})
    admin = await is_admin(update, context)
    
    if state.get("step") == "name":
        if not admin:
            del user_data[user_id]
            await context.bot.send_message(chat_id=chat_id, text="❌ Solo administradores")
            return
        
        task_name = update.message.text
        user_data[user_id] = {"step": "date", "name": task_name}
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"📝 {task_name}\n\n📅 Selecciona la fecha de entrega:",
            reply_markup=get_date_menu(task_name)
        )
        return
    
    elif state.get("step") == "date":
        if not admin:
            del user_data[user_id]
            await context.bot.send_message(chat_id=chat_id, text="❌ Solo administradores")
            return
        
        try:
            datetime.datetime.strptime(update.message.text, "%Y-%m-%d")
        except:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ Formato inválido. Usa: YYYY-MM-DD\nEjemplo: 2026-03-25")
            return
        
        name = state["name"]
        database.add_task(user_id, update.effective_user.username or "user", name, update.message.text)
        del user_data[user_id]
        await context.bot.send_message(chat_id=chat_id, text=f"✅ Creada: {name}\n📅 {update.message.text}", reply_markup=get_admin_menu())
        return


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_data:
        del user_data[user_id]
    admin = await is_admin(update, context)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Cancelado", reply_markup=get_admin_menu() if admin else get_user_menu())
