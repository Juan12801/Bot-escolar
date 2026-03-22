from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)
import database
import datetime
import logging

logger = logging.getLogger(__name__)

TASK_INPUT = 1


def get_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Ver Tareas", callback_data="list")],
        [InlineKeyboardButton("Añadir Tarea", callback_data="add")],
        [InlineKeyboardButton("Eliminar", callback_data="delete")],
        [InlineKeyboardButton("Ayuda", callback_data="help")]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Bot Escolar*\n\n"
        "Gestiona tus tareas y recibe recordatorios 2 dias antes a las 3 PM.\n\n"
        "Usa los botones para navegar:",
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    try:
        await query.answer()
    except Exception:
        pass

    data = query.data

    if data == "menu":
        await query.edit_message_text(
            "Selecciona una opcion:",
            reply_markup=get_main_menu()
        )

    elif data == "list":
        try:
            tasks = database.get_all_tasks()

            if not tasks:
                await query.edit_message_text(
                    "No hay tareas\n\nSelecciona:",
                    reply_markup=get_main_menu()
                )
                return

            text = "*Tareas:*\n\n"
            for t in tasks:
                text += f"- {t['task_name']} ({t['due_date']})\n"

            keyboard = [[InlineKeyboardButton("Menu", callback_data="menu")]]
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            await query.edit_message_text("Error al cargar tareas")

    elif data == "add":
        await query.edit_message_text(
            "Escribe la tarea y fecha en formato:\n"
            "`Tarea YYYY-MM-DD`\n\n"
            "Ejemplo: Matematicas 2026-03-21",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Cancelar", callback_data="menu")]
            ])
        )
        return TASK_INPUT

    elif data == "delete":
        try:
            tasks = database.get_all_tasks()

            if not tasks:
                await query.edit_message_text(
                    "No hay tareas\n\nSelecciona:",
                    reply_markup=get_main_menu()
                )
                return

            keyboard = []
            for task in tasks:
                keyboard.append([
                    InlineKeyboardButton(
                        f"Eliminar: {task['task_name']}",
                        callback_data=f"d_{task['_id']}"
                    )
                ])
            keyboard.append([InlineKeyboardButton("Cancelar", callback_data="menu")])

            await query.edit_message_text(
                "Selecciona tarea a eliminar:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Error in delete: {e}")
            await query.edit_message_text("Error")

    elif data == "help":
        await query.edit_message_text(
            "*Ayuda*\n\n"
            "- Ver Tareas: Lista todas las tareas\n"
            "- Anadir Tarea: Crea una tarea nueva\n"
            "- Eliminar: Elimina una tarea\n"
            "- Formato fecha: YYYY-MM-DD\n\n"
            "Recordatorio: 2 dias antes a las 3 PM",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )

    elif data.startswith("d_"):
        try:
            task_id = data[2:]
            task = database.get_task_by_id(task_id)

            if task:
                database.delete_task(task_id, task["user_id"])
                await query.edit_message_text(
                    f"Tarea eliminada: {task['task_name']}",
                    reply_markup=get_main_menu()
                )
            else:
                await query.edit_message_text(
                    "Tarea no encontrada",
                    reply_markup=get_main_menu()
                )
        except Exception as e:
            logger.error(f"Error deleting: {e}")
            await query.edit_message_text("Error al eliminar")


async def handle_task_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()

    parts = user_input.rsplit(" ", 1)

    if len(parts) != 2:
        await update.message.reply_text(
            "Formato incorrecto. Usa: `Tarea YYYY-MM-DD`\n\n"
            "Ejemplo: Matematicas 2026-03-21",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        return ConversationHandler.END

    task_name = parts[0].strip()
    due_date = parts[1].strip()

    try:
        datetime.datetime.strptime(due_date, "%Y-%m-%d")
    except ValueError:
        await update.message.reply_text(
            "Fecha invalida. Usa formato: YYYY-MM-DD\n\n"
            "Ejemplo: 2026-03-21",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        return ConversationHandler.END

    if not task_name:
        await update.message.reply_text(
            "El nombre de la tarea no puede estar vacio.",
            reply_markup=get_main_menu()
        )
        return ConversationHandler.END

    try:
        user_id = update.message.from_user.id
        username = update.message.from_user.username or update.message.from_user.first_name

        logger.info(f"Adding task: {task_name} for user {user_id}")

        task_id = database.add_task(user_id, username, task_name, due_date)
        logger.info(f"Task added with ID: {task_id}")

        await update.message.reply_text(
            f"Tarea creada:\n\n"
            f"*{task_name}*\n"
            f"Fecha: {due_date}",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        logger.error(f"Error adding task: {e}")
        await update.message.reply_text(
            f"Error al crear tarea: {str(e)}",
            reply_markup=get_main_menu()
        )

    return ConversationHandler.END


conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(button_handler)],
    states={
        TASK_INPUT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task_input)
        ],
    },
    fallbacks=[],
)
