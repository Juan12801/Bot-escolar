from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
import database
import datetime

TASK_NAME, TASK_DATE = range(2)


def get_admin_menu():
    keyboard = [
        [InlineKeyboardButton("➕ Añadir Tarea", callback_data="add")],
        [InlineKeyboardButton("📋 Ver Todas", callback_data="list")],
        [InlineKeyboardButton("🗑️ Eliminar Tarea", callback_data="delete")],
        [InlineKeyboardButton("❓ Ayuda", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_user_menu():
    keyboard = [
        [InlineKeyboardButton("📋 Ver Todas", callback_data="list")],
        [InlineKeyboardButton("❓ Ayuda", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin = await is_admin(update, context)
    menu = get_admin_menu() if admin else get_user_menu()
    
    text = "👋 *Bienvenido al Bot Escolar*\n\n"
    text += "Gestiona tus tareas y recibe recordatorios 2 días antes.\n\n"
    if admin:
        text += "✅ Eres administrador\n\n"
    else:
        text += "📖 Puedes ver las tareas\n\n"
    text += "Selecciona una opción:"
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode="Markdown",
        reply_markup=menu
    )
    return ConversationHandler.END


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    admin = await is_admin(update, context)
    
    print(f"[DEBUG] Callback: {query.data} | User: {user_id} | Admin: {admin}")
    
    if query.data == "add":
        if not admin:
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Solo los administradores pueden añadir tareas.",
                reply_markup=get_user_menu()
            )
            return ConversationHandler.END
        
        await context.bot.send_message(
            chat_id=chat_id,
            text="📝 Escribe el nombre de la tarea:"
        )
        return TASK_NAME
    
    elif query.data == "delete":
        if not admin:
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Solo los administradores pueden eliminar tareas.",
                reply_markup=get_user_menu()
            )
            return ConversationHandler.END
        
        tasks = database.get_all_tasks()
        
        if not tasks:
            await context.bot.send_message(
                chat_id=chat_id,
                text="📋 No hay tareas para eliminar.\n\nSelecciona una opción:",
                reply_markup=get_admin_menu()
            )
            return ConversationHandler.END
        
        message = "🗑️ *Selecciona una tarea para eliminar:*\n\n"
        keyboard = []
        
        for task in tasks:
            task_id = task["_id"]
            task_name = task["task_name"]
            due_date = task["due_date"]
            username = task["username"]
            
            message += f"📝 {task_name}\n   📅 {due_date} • @{username}\n\n"
            keyboard.append(
                [InlineKeyboardButton(f"❌ {task_name}", callback_data=f"del_{task_id}")]
            )
        
        keyboard.append([InlineKeyboardButton("🔙 Menú", callback_data="menu")])
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END
    
    elif query.data == "list":
        tasks = database.get_all_tasks()
        
        if not tasks:
            menu = get_admin_menu() if admin else get_user_menu()
            await context.bot.send_message(
                chat_id=chat_id,
                text="📋 No hay tareas.\n\nSelecciona una opción:",
                reply_markup=menu
            )
            return ConversationHandler.END
        
        message = "📋 *Todas las tareas:*\n\n"
        
        for task in tasks:
            task_name = task["task_name"]
            due_date = task["due_date"]
            username = task["username"]
            
            message += f"📝 {task_name}\n   📅 {due_date} • @{username}\n\n"
        
        menu = get_admin_menu() if admin else get_user_menu()
        message += "Selecciona una opción:"
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
            reply_markup=menu
        )
        return ConversationHandler.END
    
    elif query.data == "help":
        text = "📚 *Ayuda*\n\n"
        text += "👤 *Usuarios:*\n"
        text += "📋 Ver Todas: Ver todas las tareas\n\n"
        text += "👑 *Administradores:*\n"
        text += "➕ Añadir: Crear nueva tarea\n"
        text += "🗑️ Eliminar: Borrar cualquier tarea\n\n"
        text += "⏰ Recordatorio: 2 días antes a 3 PM\n\n"
        text += "Selecciona una opción:"
        
        menu = get_admin_menu() if admin else get_user_menu()
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=menu
        )
        return ConversationHandler.END
    
    return ConversationHandler.END


async def delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    admin = await is_admin(update, context)
    
    if not admin:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Solo los administradores pueden eliminar tareas.",
            reply_markup=get_user_menu()
        )
        return ConversationHandler.END
    
    task_id = query.data.replace("del_", "")
    
    task = database.get_task_by_id(task_id)
    
    if not task:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Tarea no encontrada.",
            reply_markup=get_admin_menu()
        )
        return ConversationHandler.END
    
    success = database.delete_task(task_id, task["user_id"])
    
    if success:
        await context.bot.send_message(
            chat_id=chat_id,
            text="✅ Tarea eliminada.\n\nSelecciona una opción:",
            reply_markup=get_admin_menu()
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Error al eliminar.\n\nSelecciona una opción:",
            reply_markup=get_admin_menu()
        )
    
    return ConversationHandler.END


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    admin = await is_admin(update, context)
    menu = get_admin_menu() if admin else get_user_menu()
    
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Selecciona una opción:",
        reply_markup=menu
    )
    return ConversationHandler.END


async def task_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin = await is_admin(update, context)
    
    if not admin:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Solo los administradores pueden añadir tareas.",
            reply_markup=get_user_menu()
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    context.user_data["task_name"] = update.message.text
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"📝 {update.message.text}\n\n"
             "📅 Escribe la fecha (YYYY-MM-DD)\n"
             "Ej: 2026-03-25\n\n"
             "/cancel para cancelar"
    )
    return TASK_DATE


async def task_date_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin = await is_admin(update, context)
    
    if not admin:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Solo los administradores pueden añadir tareas.",
            reply_markup=get_user_menu()
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    date_text = update.message.text
    
    try:
        datetime.datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠️ Formato inválido. Usa: YYYY-MM-DD\n\n/cancel para cancelar"
        )
        return TASK_DATE
    
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    task_name = context.user_data["task_name"]
    
    database.add_task(user_id, username, task_name, date_text)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"✅ *Tarea creada*\n\n📝 {task_name}\n📅 {date_text}",
        parse_mode="Markdown",
        reply_markup=get_admin_menu()
    )
    
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin = await is_admin(update, context)
    menu = get_admin_menu() if admin else get_user_menu()
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="❌ Cancelado.\n\nSelecciona una opción:",
        reply_markup=menu
    )
    context.user_data.clear()
    return ConversationHandler.END
