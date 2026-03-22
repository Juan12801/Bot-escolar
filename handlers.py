from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, MessageHandler, filters
import database
import datetime

user_states = {}


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
        text="👋 *Bot Escolar*\n\nGestiona tareas y recibe recordatorios 2 días antes a las 3 PM.\n\nSelecciona una opción:",
        parse_mode="Markdown",
        reply_markup=get_admin_menu() if admin else get_user_menu()
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    
    try:
        await query.answer("Cargando...")
    except:
        pass
    
    admin = await is_admin(update, context)
    
    if query.data == "add":
        if not admin:
            await context.bot.send_message(chat_id=chat_id, text="❌ Solo administradores")
            return
        
        user_states[user_id] = {"step": "name"}
        await context.bot.send_message(chat_id=chat_id, text="📝 Escribe el nombre de la tarea:")
        return
    
    elif query.data == "delete":
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
        
        await context.bot.send_message(chat_id=chat_id, text="🗑️ Selecciona tarea para eliminar:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    elif query.data == "list":
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
    
    elif query.data == "help":
        menu = get_admin_menu() if admin else get_user_menu()
        await context.bot.send_message(
            chat_id=chat_id,
            text="📚 *Ayuda*\n\n➕ Añadir: Crear tarea (admin)\n📋 Ver: Todas las tareas\n🗑️ Eliminar: Borrar tarea (admin)\n⏰ Recordatorio: 2 días antes 3 PM",
            parse_mode="Markdown",
            reply_markup=menu
        )
        return
    
    elif query.data == "menu":
        admin = await is_admin(update, context)
        await context.bot.send_message(chat_id=chat_id, text="Selecciona:", reply_markup=get_admin_menu() if admin else get_user_menu())
        return
    
    elif query.data.startswith("del_"):
        if not admin:
            await context.bot.send_message(chat_id=chat_id, text="❌ Solo administradores")
            return
        
        task_id = query.data.replace("del_", "")
        task = database.get_task_by_id(task_id)
        
        if not task:
            await context.bot.send_message(chat_id=chat_id, text="❌ No encontrada")
            return
        
        database.delete_task(task_id, task["user_id"])
        await context.bot.send_message(chat_id=chat_id, text=f"✅ Eliminada: {task['task_name']}", reply_markup=get_admin_menu())
        return


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if user_id not in user_states:
        await start(update, context)
        return
    
    state = user_states[user_id]
    admin = await is_admin(update, context)
    
    if state.get("step") == "name":
        if not admin:
            del user_states[user_id]
            await context.bot.send_message(chat_id=chat_id, text="❌ Solo administradores")
            return
        
        user_states[user_id] = {"step": "date", "name": update.message.text}
        await context.bot.send_message(chat_id=chat_id, text=f"📝 {update.message.text}\n\n📅 Escribe la fecha (YYYY-MM-DD):")
        return
    
    elif state.get("step") == "date":
        if not admin:
            del user_states[user_id]
            await context.bot.send_message(chat_id=chat_id, text="❌ Solo administradores")
            return
        
        try:
            datetime.datetime.strptime(update.message.text, "%Y-%m-%d")
        except:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ Formato inválido. Usa: YYYY-MM-DD")
            return
        
        name = state["name"]
        database.add_task(user_id, update.effective_user.username or "user", name, update.message.text)
        del user_states[user_id]
        await context.bot.send_message(chat_id=chat_id, text=f"✅ Creada: {name} - {update.message.text}", reply_markup=get_admin_menu())
        return


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_states:
        del user_states[user_id]
    admin = await is_admin(update, context)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Cancelado", reply_markup=get_admin_menu() if admin else get_user_menu())
