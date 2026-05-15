"""
Notificador de Telegram
Envía mensajes y actualizaciones sobre tareas Fizzy
"""
import os
import asyncio
from typing import Optional, List
from telegram import Bot
from telegram.constants import ParseMode
from dataclasses import dataclass
from src.fizzy_client import Card


@dataclass
class TelegramConfig:
    bot_token: str
    chat_id: str
    bot_name: str = "Talia"


class TelegramNotifier:
    """Envía notificaciones de Fizzy a Telegram"""
    
    def __init__(self, config: Optional[TelegramConfig] = None):
        if config is None:
            config = TelegramConfig(
                bot_token=os.getenv('TELEGRAM_BOT_TOKEN', ''),
                chat_id=os.getenv('TELEGRAM_CHAT_ID', ''),
                bot_name=os.getenv('BOT_NAME', 'Talia')
            )
        
        self.config = config
        self.bot: Optional[Bot] = None
        
        if config.bot_token:
            self.bot = Bot(token=config.bot_token)
    
    async def send_message(self, message: str, parse_mode: ParseMode = ParseMode.HTML) -> bool:
        """Envía un mensaje a Telegram"""
        if not self.bot or not self.config.chat_id:
            return False
        
        try:
            await self.bot.send_message(
                chat_id=self.config.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            return True
        except Exception as e:
            print(f"Error enviando mensaje a Telegram: {e}")
            return False
    
    def send_message_sync(self, message: str, parse_mode: ParseMode = ParseMode.HTML) -> bool:
        """Envía un mensaje de forma síncrona"""
        return asyncio.run(self.send_message(message, parse_mode))
    
    async def notify_new_task(self, card: Card, project_name: str) -> bool:
        """Notifica cuando se crea una nueva tarea"""
        message = f"""
📝 <b>Nueva tarea creada</b>

<b>Proyecto:</b> {project_name}
<b>Título:</b> {card.title}
<b>ID:</b> #{card.id}

{card.description or 'Sin descripción'}
        """.strip()
        
        return await self.send_message(message)
    
    async def notify_task_completed(self, card: Card, project_name: str) -> bool:
        """Notifica cuando se completa una tarea"""
        message = f"""
✅ <b>Tarea completada</b>

<b>Proyecto:</b> {project_name}
<b>Título:</b> {card.title}
<b>ID:</b> #{card.id}
        """.strip()
        
        return await self.send_message(message)
    
    async def notify_task_updated(self, card: Card, project_name: str, changes: List[str]) -> bool:
        """Notifica cuando se actualiza una tarea"""
        changes_text = '\n'.join([f"• {change}" for change in changes])
        
        message = f"""
🔄 <b>Tarea actualizada</b>

<b>Proyecto:</b> {project_name}
<b>Título:</b> {card.title}
<b>ID:</b> #{card.id}

<b>Cambios:</b>
{changes_text}
        """.strip()
        
        return await self.send_message(message)
    
    async def send_task_list(self, project_name: str, tasks: List[Card], show_status: bool = True) -> bool:
        """Envía una lista de tareas"""
        if not tasks:
            message = f"📋 <b>{project_name}</b>\n\nNo hay tareas pendientes. 🎉"
            return await self.send_message(message)
        
        tasks_text = []
        for i, task in enumerate(tasks, 1):
            status_emoji = "✅" if task.status == "completed" else "⏳"
            tasks_text.append(f"{i}. {status_emoji} <b>#{task.id}</b>: {task.title}")
        
        message = f"""
📋 <b>{project_name}</b>

{chr(10).join(tasks_text)}

Total: {len(tasks)} tareas
        """.strip()
        
        return await self.send_message(message)


# Instancia singleton
_notifier: Optional[TelegramNotifier] = None


def get_telegram_notifier() -> TelegramNotifier:
    """Obtiene o crea el notificador de Telegram"""
    global _notifier
    if _notifier is None:
        _notifier = TelegramNotifier()
    return _notifier
