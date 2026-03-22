import logging
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, ConversationHandler, MessageHandler, CallbackQueryHandler, filters

import config
import handlers
import scheduler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


async def main():
    logging.info("Iniciando Bot Escolar...")
    
    app = ApplicationBuilder() \
        .token(config.BOT_TOKEN) \
        .read_timeout(60) \
        .write_timeout(60) \
        .build()
    
    await app.initialize()
    
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", handlers.start),
            CallbackQueryHandler(handlers.button_handler),
        ],
        states={
            handlers.TASK_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.task_name_received)
            ],
            handlers.TASK_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.task_date_received)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", handlers.cancel),
            CallbackQueryHandler(handlers.button_handler),
        ]
    )
    
    app.add_handler(conv_handler)
    
    scheduler_instance = scheduler.start_scheduler(app)
    
    logging.info("Bot iniciado. Escuchando...")
    
    await app.start()
    await app.updater.start_polling()
    
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        scheduler_instance.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
