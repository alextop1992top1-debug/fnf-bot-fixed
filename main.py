#!/usr/bin/env python3
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

def main():
    try:
        from core.bot import bot
        
        logger.info("Запуск Friday Night Funkin MMO бота...")
        logger.info("Удаляем старые вебхуки...")
        
        # Останавливаем все предыдущие подключения
        bot.application.bot.delete_webhook(drop_pending_updates=True)
        
        logger.info("Бот запускается в режиме polling...")
        bot.application.run_polling()
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        logger.info("Бот остановлен")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
