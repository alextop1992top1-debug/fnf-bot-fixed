#!/usr/bin/env python3
import asyncio
import logging
import sys
import os

# Добавляем пути для импортов
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'game'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'content'))

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

async def main():
    from core.bot import bot
    logger.info("Запуск Friday Night Funkin MMO бота...")
    
    try:
        await bot.application.run_polling()
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        logger.info("Бот остановлен")

if __name__ == '__main__':
    asyncio.run(main())
