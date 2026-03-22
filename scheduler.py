from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from telegram.ext import Application
import database
import config


def check_and_notify(app: Application):
    now = datetime.now()
    
    if now.hour != config.NOTIFICATION_HOUR:
        return
    
    tasks = database.get_pending_tasks_2_days()
    
    if not tasks:
        return
    
    async def send_notification():
        message = "⏰ *¡Recordatorio de tareas!*\n\n"
        message += "Las siguientes tareas vencen en 2 días:\n\n"
        
        for task in tasks:
            task_id = task["_id"]
            task_name = task["task_name"]
            due_date = task["due_date"]
            username = task["username"]
            
            message += f"📝 *{task_name}*\n"
            message += f"   📅 Fecha: {due_date}\n"
            message += f"   👤 @{username}\n\n"
            
            database.mark_notified(task_id)
        
        message += "Buena suerte! 🎓"
        
        await app.bot.send_message(
            chat_id=config.GROUP_CHAT_ID,
            text=message,
            parse_mode="Markdown"
        )
    
    app.create_task(send_notification())


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
