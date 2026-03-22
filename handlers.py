from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
import database
import datetime
import logging

logger = logging.getLogger(__name__)


def get_admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Ver Tareas", callback_data="list")],
        [InlineKeyboardButton("🗑️ Eliminar", callback_data="delete")],
        [InlineKeyboardButton("❓ Ayuda", callback_data="help")]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Bot Escolar*\n\n"
        "Gestiona tareas y recibe recordatorios 2 días antes a las 3 PM.\n\n"
        "Usa /add <nombre> para crear tarea\n"
        "Ejemplo: /add Tarea de mates\n\n"
        "O selecciona:",
        parse_mode="Markdown",
        reply_markup=get_admin_menu()
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    try:
        await query.answer()
    except:
        pass
    
    data = query.data
    
    if data == "list":
        try:
            tasks = database.get_all_tasks()
            
            if not tasks:
                await query.edit_message_text("📋 No hay tareas\n\nSelecciona:", reply_markup=get_admin_menu())
                return
            
            text = "📋 *Tareas:*\n\n"
            for t in tasks:
                text += f"• {t['task_name']} ({t['due_date']})\n"
            
            keyboard = [[InlineKeyboardButton("🔙 Menú", callback_data="menu")]]
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            await query.edit_message_text("❌ Error al cargar tareas")
    
    elif data == "delete":
        try:
            tasks = database.get_all_tasks()
            
            if not tasks:
                await query.edit_message_text("📋 No hay tareas\n\nSelecciona:", reply_markup=get_admin_menu())
                return
            
            keyboard = []
            for task in tasks:
                keyboard.append([InlineKeyboardButton(f"❌ {task['task_name']}", callback_data=f"d_{task['_id']}")])
            keyboard.append([InlineKeyboardButton("🔙 Menú", callback_data="menu")])
            
            await query.edit_message_text("🗑️ Selecciona tarea:", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            logger.error(f"Error in delete: {e}")
            await query.edit_message_text("❌ Error")
    
    elif data == "help":
        await query.edit_message_text(
            "📚 *Ayuda*\n\n"
            "/add <nombre> - Crear tarea\n"
            "   Ej: /add Tarea de mates\n\n"
            "/del <nombre> - Eliminar tarea\n"
            "   Ej: /del Tarea de mates\n\n"
            "📋 Ver - Ver todas las tareas\n"
            "⏰ Recordatorio: 2 días antes 3 PM",
            parse_mode="Markdown",
            reply_markup=get_admin_menu()
        )
    
    elif data == "menu":
        await query.edit_message_text("Selecciona:", reply_markup=get_admin_menu())
    
    elif data.startswith("d_"):
        try:
            task_id = data[2:]
            task = database.get_task_by_id(task_id)
            
            if task:
                database.delete_task(task_id, task["user_id"])
                await query.edit_message_text(f"✅ Eliminada: {task['task_name']}", reply_markup=get_admin_menu())
            else:
                await query.edit_message_text("❌ No encontrada", reply_markup=get_admin_menu())
        except Exception as e:
            logger.error(f"Error deleting: {e}")
            await query.edit_message_text("❌ Error al eliminar")


async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usa: /add <nombre de tarea>\nEjemplo: /add Tarea de mates")
        return
    
    try:
        task_name = " ".join(context.args)
        today = datetime.date.today()
        due_date = (today + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        
        user_id = update.message.from_user.id
        username = update.message.from_user.username or update.message.from_user.first_name
        
        logger.info(f"Adding task: {task_name} for user {user_id}")
        
        task_id = database.add_task(user_id, username, task_name, due_date)
        logger.info(f"Task added with ID: {task_id}")
        
        await update.message.reply_text(
            f"✅ *Tarea creada*\n\n📝 {task_name}\n📅 {due_date}",
            parse_mode="Markdown",
            reply_markup=get_admin_menu()
        )
    except Exception as e:
        logger.error(f"Error adding task: {e}")
        await update.message.reply_text(f"❌ Error al crear tarea: {str(e)}")


async def delete_task_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usa: /del <nombre de tarea>")
        return
    
    try:
        task_name = " ".join(context.args).lower()
        tasks = database.get_all_tasks()
        user_id = update.message.from_user.id
        
        deleted = False
        for task in tasks:
            if task["task_name"].lower() == task_name and task["user_id"] == user_id:
                database.delete_task(task["_id"], user_id)
                deleted = True
                break
        
        if deleted:
            await update.message.reply_text(f"✅ Eliminada: {task_name}", reply_markup=get_admin_menu())
        else:
            await update.message.reply_text("❌ Tarea no encontrada o no te pertenece", reply_markup=get_admin_menu())
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")
