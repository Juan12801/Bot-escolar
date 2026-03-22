from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, MessageHandler, filters
import database
import datetime


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
    await update.message.reply_text(
        "👋 *Bot Escolar*\n\nGestiona tareas y recibe recordatorios 2 días antes a las 3 PM.\n\nSelecciona:",
        parse_mode="Markdown",
        reply_markup=get_admin_menu() if admin else get_user_menu()
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    admin = await is_admin(update, context)
    
    if data == "add":
        if not admin:
            await query.edit_message_text("❌ Solo administradores")
            return
        await query.edit_message_text("📝 Escribe el nombre de la tarea (solo el nombre):")
    
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
        
        await query.edit_message_text("🗑️ Selecciona tarea para eliminar:", reply_markup=InlineKeyboardMarkup(keyboard))
    
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
    
    elif data.startswith("n_"):
        if not admin:
            await query.edit_message_text("❌ Solo administradores")
            return
        
        task_name = data[2:].replace("_", " ")
        
        keyboard = [
            [InlineKeyboardButton("📅 Mañana", callback_data=f"c_{task_name}_1")],
            [InlineKeyboardButton("📅 Pasado mañana", callback_data=f"c_{task_name}_2")],
            [InlineKeyboardButton("📅 3 días", callback_data=f"c_{task_name}_3")],
            [InlineKeyboardButton("📅 1 semana", callback_data=f"c_{task_name}_7")]
        ]
        
        await query.edit_message_text(
            f"📝 {task_name.replace('_', ' ')}\n\n📅 Selecciona la fecha de entrega:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data.startswith("c_"):
        if not admin:
            await query.edit_message_text("❌ Solo administradores")
            return
        
        parts = data[2:].split("_")
        if len(parts) >= 2:
            task_name = " ".join(parts[:-1]).replace("_", " ")
            days = int(parts[-1])
            due_date = (datetime.date.today() + datetime.timedelta(days=days)).strftime("%Y-%m-%d")
            
            database.add_task(user_id, query.from_user.username or "user", task_name, due_date)
            await query.edit_message_text(f"✅ *Tarea creada*\n\n📝 {task_name}\n📅 {due_date}", parse_mode="Markdown", reply_markup=get_admin_menu())


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    admin = await is_admin(update, context)
    
    if not admin:
        await update.message.reply_text("❌ Solo administradores", reply_markup=get_user_menu())
        return
    
    task_name_safe = text.replace(" ", "_")
    keyboard = [
        [InlineKeyboardButton("📅 Mañana", callback_data=f"c_{task_name_safe}_1")],
        [InlineKeyboardButton("📅 Pasado mañana", callback_data=f"c_{task_name_safe}_2")],
        [InlineKeyboardButton("📅 3 días", callback_data=f"c_{task_name_safe}_3")],
        [InlineKeyboardButton("📅 1 semana", callback_data=f"c_{task_name_safe}_7")]
    ]
    
    await update.message.reply_text(
        f"📝 {text}\n\n📅 Selecciona la fecha de entrega:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin = await is_admin(update, context)
    await update.message.reply_text("❌ Cancelado", reply_markup=get_admin_menu() if admin else get_user_menu())
