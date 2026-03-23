from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from telegram.ext import Application
import database
import config


def check_and_notify(app: Application):
    now = datetime.now()

    if now.hour != config.NOTIFICATION_HOUR:
        return

    tasks_2_days = database.get_pending_tasks_2_days()
    tasks_1_day = database.get_pending_tasks_1_day()

    async def send_notification_2_days():
        if not tasks_2_days:
            return

        message = "Recuerdo: las siguientes tareas vencen en 2 dias:\n\n"

        for task in tasks_2_days:
            task_id = task["_id"]
            task_name = task["task_name"]
            due_date = task["due_date"]
            username = task["username"]

            message += f"- {task_name} (Fecha: {due_date}, Usuario: @{username})\n\n"

            database.mark_notified_2_days(task_id)

        message += "Buena suerte!"

        await app.bot.send_message(
            chat_id=config.GROUP_CHAT_ID,
            text=message,
            parse_mode="Markdown"
        )

    async def send_notification_1_day():
        if not tasks_1_day:
            return

        message = "Urgente: las siguientes tareas vencen manana:\n\n"

        for task in tasks_1_day:
            task_id = task["_id"]
            task_name = task["task_name"]
            due_date = task["due_date"]
            username = task["username"]

            message += f"- {task_name} (Fecha: {due_date}, Usuario: @{username})\n\n"

            database.mark_notified_1_day(task_id)

        message += "Es tu ultima oportunidad!"

        await app.bot.send_message(
            chat_id=config.GROUP_CHAT_ID,
            text=message,
            parse_mode="Markdown"
        )

    app.create_task(send_notification_2_days())
    app.create_task(send_notification_1_day())


def start_scheduler(app: Application):
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        check_and_notify,
        "cron",
        minute=0,
        args=[app],
        id="task_notifier",
        replace_existing=True
    )

    scheduler.start()
    return scheduler
