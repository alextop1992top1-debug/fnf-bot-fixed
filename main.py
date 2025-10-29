#!/usr/bin/env python3
import asyncio
import logging
from core.bot import bot

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

async def main():
    logger.info("Запуск Friday Night Funkin MMO бота...")
    
    try:
        await bot.run()
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        logger.info("Бот остановлен")

if __name__ == '__main__':
    asyncio.run(main())