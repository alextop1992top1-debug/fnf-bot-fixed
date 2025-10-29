#!/usr/bin/env python3
import logging
from core.bot import bot

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("Запуск Friday Night Funkin MMO бота...")
    bot.application.run_polling()
