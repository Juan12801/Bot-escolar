import logging
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters

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
    
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("cancel", handlers.cancel))
    app.add_handler(CallbackQueryHandler(handlers.button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.text_handler))
    
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
