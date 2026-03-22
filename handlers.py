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
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Mañana", callback_data=f"t_{task_name}_1")],
        [InlineKeyboardButton("📅 Pasado mañana", callback_data=f"t_{task_name}_2")],
        [InlineKeyboardButton("📅 3 días", callback_data=f"t_{task_name}_3")],
        [InlineKeyboardButton("📅 1 semana", callback_data=f"t_{task_name}_7")],
        [InlineKeyboardButton("📅 Otra fecha", callback_data=f"o_{task_name}")]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin = await is_admin(update, context)
    await update.message.reply_text(
        "👋 *Bot Escolar*\n\nGestiona tareas y recibe recordatorios 2 días antes a las 3 PM.\n\nSelecciona:",
        parse_mode="Markdown",
        reply_markup=get_admin_menu() if admin else get_user_menu()
    )


async def is_admin(update, context):
    try:
        member = await context.bot.get_chat_member(
            update.effective_chat.id,
            update.effective_user.id
        )
        return member.status in ["administrator", "creator"]
    except:
        return False


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    admin = await is_admin(update, context)
    
    if data == "add":
        if not admin:
            await query.edit_message_text("❌ Solo administradores")
            return
        user_data[user_id] = "waiting_name"
        await query.edit_message_text("📝 Escribe el nombre de la tarea:")
    
    elif data == "list":
        tasks = database.get_all_tasks()
        menu = get_admin_menu() if admin else get_user_menu()
        
        if not tasks:
            await query.edit_message_text("📋 No hay tareas", reply_markup=menu)
            return
        
        text = "📋 *Tareas:*\n\n"
        for t in tasks:
            text += f"• {t['task_name']} ({t['due_date']}) - @{t['username']}\n"
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=menu)
    
    elif data == "delete":
        if not admin:
            await query.edit_message_text("❌ Solo administradores")
            return
        
        tasks = database.get_all_tasks()
        if not tasks:
            await query.edit_message_text("📋 No hay tareas", reply_markup=get_admin_menu())
            return
        
        keyboard = []
        for task in tasks:
            keyboard.append([InlineKeyboardButton(f"❌ {task['task_name']}", callback_data=f"d_{task['_id']}")])
        keyboard.append([InlineKeyboardButton("🔙 Menú", callback_data="menu")])
        
        await query.edit_message_text("🗑️ Selecciona tarea:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data == "help":
        menu = get_admin_menu() if admin else get_user_menu()
        await query.edit_message_text(
            "📚 *Ayuda*\n\n➕ Añadir: Crear tarea (admin)\n📋 Ver: Todas las tareas\n🗑️ Eliminar: Borrar tarea (admin)\n⏰ Recordatorio: 2 días antes 3 PM",
            parse_mode="Markdown",
            reply_markup=menu
        )
    
    elif data == "menu":
        admin = await is_admin(update, context)
        await query.edit_message_text("Selecciona:", reply_markup=get_admin_menu() if admin else get_user_menu())
    
    elif data.startswith("d_"):
        if not admin:
            await query.edit_message_text("❌ Solo administradores")
            return
        
        task_id = data[2:]
        task = database.get_task_by_id(task_id)
        
        if task:
            database.delete_task(task_id, task["user_id"])
            await query.edit_message_text(f"✅ Eliminada: {task['task_name']}", reply_markup=get_admin_menu())
        else:
            await query.edit_message_text("❌ No encontrada")
    
    elif data.startswith("t_"):
        if not admin:
            await query.edit_message_text("❌ Solo administradores")
            return
        
        parts = data.split("_", 2)
        if len(parts) >= 3:
            task_name = parts[1]
            days = int(parts[2])
            due_date = (datetime.date.today() + datetime.timedelta(days=days)).strftime("%Y-%m-%d")
            
            database.add_task(user_id, query.from_user.username or "user", task_name, due_date)
            await query.edit_message_text(f"✅ Creada: {task_name}\n📅 {due_date}", reply_markup=get_admin_menu())
    
    elif data.startswith("o_"):
        if not admin:
            await query.edit_message_text("❌ Solo administradores")
            return
        
        task_name = data[2:]
        user_data[user_id] = f"waiting_date_{task_name}"
        await query.edit_message_text(f"📝 {task_name}\n\n📅 Escribe la fecha (YYYY-MM-DD):")


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = user_data.get(user_id, "")
    
    if state == "waiting_name":
        admin = await is_admin(update, context)
        if not admin:
            await update.message.reply_text("❌ Solo administradores")
            del user_data[user_id]
            return
        
        task_name = update.message.text
        user_data[user_id] = "waiting_date"
        user_data[f"{user_id}_name"] = task_name
        
        await update.message.reply_text(
            f"📝 {task_name}\n\n📅 Selecciona la fecha:",
            reply_markup=get_date_menu(task_name)
        )
    
    elif state == "waiting_date":
        admin = await is_admin(update, context)
        if not admin:
            await update.message.reply_text("❌ Solo administradores")
            del user_data[user_id]
            return
        
        try:
            datetime.datetime.strptime(update.message.text, "%Y-%m-%d")
        except:
            await update.message.reply_text("⚠️ Formato inválido. Usa: YYYY-MM-DD\nEjemplo: 2026-03-25")
            return
        
        task_name = user_data.get(f"{user_id}_name", "Tarea")
        database.add_task(user_id, update.effective_user.username or "user", task_name, update.message.text)
        
        del user_data[user_id]
        del user_data[f"{user_id}_name"]
        
        await update.message.reply_text(f"✅ Creada: {task_name}\n📅 {update.message.text}", reply_markup=get_admin_menu())
    
    elif state.startswith("waiting_date_"):
        admin = await is_admin(update, context)
        if not admin:
            await update.message.reply_text("❌ Solo administradores")
            del user_data[user_id]
            return
        
        try:
            datetime.datetime.strptime(update.message.text, "%Y-%m-%d")
        except:
            await update.message.reply_text("⚠️ Formato inválido. Usa: YYYY-MM-DD")
            return
        
        task_name = state.replace("waiting_date_", "")
        database.add_task(user_id, update.effective_user.username or "user", task_name, update.message.text)
        
        del user_data[user_id]
        
        await update.message.reply_text(f"✅ Creada: {task_name}\n📅 {update.message.text}", reply_markup=get_admin_menu())
    
    else:
        await start(update, context)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_data:
        del user_data[user_id]
    if f"{user_id}_name" in user_data:
        del user_data[f"{user_id}_name"]
    
    admin = await is_admin(update, context)
    await update.message.reply_text("❌ Cancelado", reply_markup=get_admin_menu() if admin else get_user_menu())
