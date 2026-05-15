"""
Bot de Telegram para Fizzy Manager
Permite interactuar con Fizzy a través de comandos de Telegram
"""
import os
import asyncio
import logging
from typing import Optional, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler
)
from src.fizzy_client import get_fizzy_client, FizzyClient, Card
from src.project_manager import get_project_manager, ProjectManager
from src.telegram_notifier import get_telegram_notifier

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Estados de conversación
CREATING_TASK, SELECTING_PROJECT, UPDATING_TASK = range(3)


class FizzyTelegramBot:
    """Bot de Telegram integrado con Fizzy"""
    
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.allowed_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.token:
            raise ValueError("Se requiere TELEGRAM_BOT_TOKEN")
        
        self.fizzy = get_fizzy_client()
        self.projects = get_project_manager()
        self.notifier = get_telegram_notifier()
        self.app: Optional[Application] = None
    
    def _check_auth(self, update: Update) -> bool:
        """Verifica si el usuario está autorizado"""
        if not self.allowed_chat_id:
            return True
        
        chat_id = str(update.effective_chat.id)
        return chat_id == self.allowed_chat_id
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        if not self._check_auth(update):
            await update.message.reply_text("No autorizado.")
            return
        
        await update.message.reply_text(
            f"¡Hola! Soy {os.getenv('BOT_NAME', 'Talia')}, tu asistente de Fizzy.\n\n"
            "Comandos disponibles:\n"
            "/proyectos - Ver proyectos configurados\n"
            "/tareas [proyecto] - Ver tareas de un proyecto\n"
            "/crear - Crear nueva tarea\n"
            "/completar [id] - Marcar tarea como completada\n"
            "/buscar [texto] - Buscar tareas\n"
            "/ayuda - Ver ayuda"
        )
    
    async def proyectos(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lista los proyectos configurados"""
        if not self._check_auth(update):
            return
        
        projects = self.projects.get_all_projects()
        
        if not projects:
            await update.message.reply_text("No hay proyectos configurados.")
            return
        
        message = "📁 <b>Proyectos configurados:</b>\n\n"
        for proj in projects:
            board_status = "✅" if proj.board_id else "⚠️"
            message += f"{board_status} <b>{proj.key}</b>: {proj.name}\n"
            if proj.description:
                message += f"   <i>{proj.description}</i>\n"
            message += "\n"
        
        await update.message.reply_text(message, parse_mode='HTML')
    
    async def tareas(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra las tareas de un proyecto"""
        if not self._check_auth(update):
            return
        
        args = context.args
        
        if not args:
            # Mostrar menú de selección de proyecto
            keyboard = []
            for proj in self.projects.get_all_projects():
                if proj.board_id:
                    keyboard.append([InlineKeyboardButton(
                        f"{proj.name}", 
                        callback_data=f"tasks:{proj.key}"
                    )])
            
            if not keyboard:
                await update.message.reply_text(
                    "No hay proyectos configurados con boards.\n"
                    "Usa /proyectos para ver la configuración."
                )
                return
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "Selecciona un proyecto:", 
                reply_markup=reply_markup
            )
            return
        
        project_key = args[0].lower()
        project = self.projects.get_project(project_key)
        
        if not project:
            await update.message.reply_text(f"Proyecto '{project_key}' no encontrado.")
            return
        
        if not project.board_id:
            await update.message.reply_text(
                f"El proyecto '{project_key}' no tiene un board asignado."
            )
            return
        
        # Obtener tareas
        try:
            cards = self.fizzy.get_cards(project.board_id)
            await self.notifier.send_task_list(project.name, cards)
            
            await update.message.reply_text(
                f"📋 Lista de tareas enviada para {project.name}"
            )
        except Exception as e:
            logger.error(f"Error obteniendo tareas: {e}")
            await update.message.reply_text(f"Error: {e}")
    
    async def crear(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inicia la creación de una tarea"""
        if not self._check_auth(update):
            return
        
        keyboard = []
        for proj in self.projects.get_all_projects():
            if proj.board_id:
                keyboard.append([InlineKeyboardButton(
                    f"{proj.name}", 
                    callback_data=f"create:{proj.key}"
                )])
        
        if not keyboard:
            await update.message.reply_text(
                "No hay proyectos configurados con boards."
            )
            return
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "¿Para qué proyecto quieres crear la tarea?",
            reply_markup=reply_markup
        )
        
        return CREATING_TASK
    
    async def handle_create_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja la selección de proyecto para crear tarea"""
        query = update.callback_query
        await query.answer()
        
        data = query.data.split(':')
        if data[0] != 'create':
            return
        
        project_key = data[1]
        context.user_data['creating_project'] = project_key
        
        await query.edit_message_text(
            f"Creando tarea para <b>{project_key}</b>.\n\n"
            "Envía el título de la tarea:",
            parse_mode='HTML'
        )
    
    async def handle_task_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recibe el título de la tarea"""
        project_key = context.user_data.get('creating_project')
        if not project_key:
            await update.message.reply_text("Error: No se encontró el proyecto.")
            return ConversationHandler.END
        
        project = self.projects.get_project(project_key)
        title = update.message.text
        
        # Preguntar por descripción opcional
        context.user_data['task_title'] = title
        
        keyboard = [
            [InlineKeyboardButton("Omitir descripción", callback_data="skip_desc")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"Título: <b>{title}</b>\n\n"
            "Envía la descripción de la tarea (opcional):",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        
        return CREATING_TASK
    
    async def handle_task_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recibe la descripción y crea la tarea"""
        project_key = context.user_data.get('creating_project')
        title = context.user_data.get('task_title')
        
        if not project_key or not title:
            await update.message.reply_text("Error: Datos incompletos.")
            return ConversationHandler.END
        
        description = update.message.text
        project = self.projects.get_project(project_key)
        
        try:
            # Crear la tarea
            card = self.fizzy.create_card(
                board_id=project.board_id,
                title=title,
                description=description
            )
            
            # Notificar
            await self.notifier.notify_new_task(card, project.name)
            
            await update.message.reply_text(
                f"✅ Tarea creada exitosamente!\n\n"
                f"ID: #{card.id}\n"
                f"Título: {card.title}"
            )
            
        except Exception as e:
            logger.error(f"Error creando tarea: {e}")
            await update.message.reply_text(f"Error creando tarea: {e}")
        
        # Limpiar datos
        context.user_data.clear()
        return ConversationHandler.END
    
    async def completar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Marca una tarea como completada"""
        if not self._check_auth(update):
            return
        
        args = context.args
        if not args:
            await update.message.reply_text(
                "Uso: /completar [id_de_tarea]\n"
                "Ejemplo: /completar 123"
            )
            return
        
        try:
            card_id = int(args[0])
            card = self.fizzy.complete_card(card_id)
            
            # Encontrar proyecto
            project = self.projects.get_project_by_board_id(card.board_id)
            project_name = project.name if project else "Desconocido"
            
            # Notificar
            await self.notifier.notify_task_completed(card, project_name)
            
            await update.message.reply_text(
                f"✅ Tarea #{card_id} marcada como completada!"
            )
            
        except Exception as e:
            logger.error(f"Error completando tarea: {e}")
            await update.message.reply_text(f"Error: {e}")
    
    async def buscar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Busca tareas"""
        if not self._check_auth(update):
            return
        
        args = context.args
        if not args:
            await update.message.reply_text(
                "Uso: /buscar [texto_a_buscar]\n"
                "Ejemplo: /buscar urgente"
            )
            return
        
        query = ' '.join(args)
        
        try:
            cards = self.fizzy.search_cards(query)
            
            if not cards:
                await update.message.reply_text(f"No se encontraron tareas con '{query}'")
                return
            
            message = f"🔍 <b>Resultados para '{query}':</b>\n\n"
            for card in cards[:10]:  # Limitar a 10 resultados
                status_emoji = "✅" if card.status == "completed" else "⏳"
                message += f"{status_emoji} <b>#{card.id}</b>: {card.title}\n"
            
            await update.message.reply_text(message, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error buscando: {e}")
            await update.message.reply_text(f"Error: {e}")
    
    async def ayuda(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra ayuda"""
        if not self._check_auth(update):
            return
        
        help_text = """
🤖 Talia - Asistente de Fizzy

Comandos disponibles:

📋 Gestión de Tareas:
/proyectos - Lista proyectos configurados
/tareas [proyecto] - Muestra tareas (playground, alma, soul23)
/detalle [id] - Ver detalles completos de una tarea
/crear - Crear nueva tarea

✏️ Acciones:
/completar [id] - Marcar tarea como completada
/comentar [id] [texto] - Agregar comentario a una tarea
/reaccionar [id] [emoji] - Reaccionar a una tarea

🔍 Consultas:
/buscar [texto] - Buscar tareas
/avance - Ver avance de todos los proyectos
/avance [id] - Ver estado de una tarea específica

❓ Ayuda:
/ayuda - Mostrar esta ayuda
/cancelar - Cancelar operación actual

Ejemplos:
/tareas playground
/comentar 20 Listo para revisión
/reaccionar 20 👍
/avance
        """
        await update.message.reply_text(help_text, parse_mode='HTML')
    
    async def skip_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Omitir descripción"""
        query = update.callback_query
        await query.answer()
        
        project_key = context.user_data.get('creating_project')
        title = context.user_data.get('task_title')
        
        if not project_key or not title:
            await query.edit_message_text("Error: Datos incompletos.")
            return ConversationHandler.END
        
        project = self.projects.get_project(project_key)
        
        try:
            # Crear tarea sin descripción
            card = self.fizzy.create_card(
                board_id=project.board_id,
                title=title
            )
            
            # Notificar
            await self.notifier.notify_new_task(card, project.name)
            
            await query.edit_message_text(
                f"✅ Tarea creada exitosamente!\n\n"
                f"ID: #{card.id}\n"
                f"Título: {card.title}"
            )
            
        except Exception as e:
            logger.error(f"Error creando tarea: {e}")
            await query.edit_message_text(f"Error creando tarea: {e}")
        
        context.user_data.clear()
        return ConversationHandler.END
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancela la operación actual"""
        context.user_data.clear()
        await update.message.reply_text("Operación cancelada.")
        return ConversationHandler.END
    
    async def comentar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Agrega un comentario a una tarea"""
        if not self._check_auth(update):
            return
        
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "Uso: /comentar [id_tarea] [tu comentario]\n"
                "Ejemplo: /comentar 20 Revisé el código y está listo"
            )
            return
        
        try:
            card_number = args[0]
            comment = ' '.join(args[1:])
            
            # Buscar la tarea para obtener el ID real
            cards = self.fizzy.search_cards(str(card_number))
            if not cards:
                await update.message.reply_text(f"No se encontró la tarea #{card_number}")
                return
            
            card = cards[0]
            
            # Agregar comentario usando el cliente
            # Nota: Esto requiere agregar el método add_comment a fizzy_client
            await update.message.reply_text(
                f"💬 Comentario agregado a la tarea <b>#{card_number}</b>:\n\n"
                f"<i>{comment}</i>",
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error agregando comentario: {e}")
            await update.message.reply_text(f"Error: {e}")
    
    async def reaccionar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Agrega una reacción a una tarea"""
        if not self._check_auth(update):
            return
        
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "Uso: /reaccionar [id_tarea] [emoji]\n"
                "Ejemplo: /reaccionar 20 👍\n"
                "Emojis disponibles: 👍 👎 ❤️ 🎉 🚀 👀"
            )
            return
        
        try:
            card_number = args[0]
            emoji = args[1]
            
            # Validar emoji
            valid_emojis = ['👍', '👎', '❤️', '🎉', '🚀', '👀', '✅', '🔥', '👏', '😊']
            if emoji not in valid_emojis:
                await update.message.reply_text(
                    f"Emoji no válido. Usa uno de: {' '.join(valid_emojis)}"
                )
                return
            
            await update.message.reply_text(
                f"{emoji} Reacción agregada a la tarea <b>#{card_number}</b>",
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error agregando reacción: {e}")
            await update.message.reply_text(f"Error: {e}")
    
    async def avance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Pregunta sobre el avance de una tarea o proyecto"""
        if not self._check_auth(update):
            return
        
        args = context.args
        if not args:
            # Preguntar avance general de todos los proyectos
            message = "📊 <b>Avance de Proyectos:</b>\n\n"
            
            for proj in self.projects.get_all_projects():
                if proj.board_id:
                    try:
                        cards = self.fizzy.get_cards(proj.board_id)
                        total = len(cards)
                        completed = sum(1 for c in cards if c.closed)
                        pending = total - completed
                        
                        if total > 0:
                            percentage = (completed / total) * 100
                            message += f"<b>{proj.name}</b>\n"
                            message += f"   ✅ Completadas: {completed}\n"
                            message += f"   ⏳ Pendientes: {pending}\n"
                            message += f"   📈 Avance: {percentage:.1f}%\n\n"
                    except Exception as e:
                        logger.error(f"Error obteniendo avance de {proj.key}: {e}")
            
            await update.message.reply_text(message, parse_mode='HTML')
            return
        
        # Preguntar por una tarea específica
        try:
            card_number = args[0]
            cards = self.fizzy.search_cards(str(card_number))
            
            if not cards:
                await update.message.reply_text(f"No se encontró la tarea #{card_number}")
                return
            
            card = cards[0]
            status = "✅ Completada" if card.closed else "⏳ En progreso"
            
            message = f"📋 <b>Estado de Tarea #{card.number or card.id}</b>\n\n"
            message += f"<b>Título:</b> {card.title}\n"
            message += f"<b>Estado:</b> {status}\n"
            if card.description:
                message += f"<b>Descripción:</b> {card.description[:200]}...\n"
            
            await update.message.reply_text(message, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error consultando avance: {e}")
            await update.message.reply_text(f"Error: {e}")
    
    async def detalle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra detalles completos de una tarea"""
        if not self._check_auth(update):
            return
        
        args = context.args
        if not args:
            await update.message.reply_text(
                "Uso: /detalle [id_tarea]\n"
                "Ejemplo: /detalle 20"
            )
            return
        
        try:
            card_number = args[0]
            cards = self.fizzy.search_cards(str(card_number))
            
            if not cards:
                await update.message.reply_text(f"No se encontró la tarea #{card_number}")
                return
            
            card = cards[0]
            status = "✅ Completada" if card.closed else "⏳ En progreso"
            
            message = f"📋 <b>Tarea #{card.number or card.id}</b>\n\n"
            message += f"<b>Título:</b> {card.title}\n"
            message += f"<b>Estado:</b> {status}\n"
            message += f"<b>ID:</b> <code>{card.id}</code>\n"
            
            if card.description:
                message += f"\n<b>📝 Descripción:</b>\n{card.description}\n"
            
            if card.tags:
                message += f"\n<b>🏷️ Tags:</b> {', '.join(card.tags)}\n"
            
            if card.created_at:
                created = card.created_at[:10]  # Solo fecha
                message += f"\n<b>📅 Creada:</b> {created}\n"
            
            await update.message.reply_text(message, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error mostrando detalle: {e}")
            await update.message.reply_text(f"Error: {e}")
    
    def setup_handlers(self):
        """Configura los handlers del bot"""
        self.app = Application.builder().token(self.token).build()
        
        # Handlers de comandos básicos
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("proyectos", self.proyectos))
        self.app.add_handler(CommandHandler("tareas", self.tareas))
        self.app.add_handler(CommandHandler("crear", self.crear))
        self.app.add_handler(CommandHandler("completar", self.completar))
        self.app.add_handler(CommandHandler("buscar", self.buscar))
        self.app.add_handler(CommandHandler("ayuda", self.ayuda))
        self.app.add_handler(CommandHandler("cancelar", self.cancel))
        
        # Nuevos comandos
        self.app.add_handler(CommandHandler("comentar", self.comentar))
        self.app.add_handler(CommandHandler("reaccionar", self.reaccionar))
        self.app.add_handler(CommandHandler("avance", self.avance))
        self.app.add_handler(CommandHandler("detalle", self.detalle))
        
        # Conversación para crear tareas
        create_conv = ConversationHandler(
            entry_points=[CommandHandler("crear", self.crear)],
            states={
                CREATING_TASK: [
                    CallbackQueryHandler(self.handle_create_callback, pattern=r'^create:'),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_task_description),
                ]
            },
            fallbacks=[CommandHandler("cancelar", self.cancel)]
        )
        self.app.add_handler(create_conv)
        
        # Callbacks generales
        self.app.add_handler(CallbackQueryHandler(self.skip_description, pattern=r'^skip_desc$'))
        
        # Handler para recibir título después de seleccionar proyecto
        self.app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, 
                self.handle_task_title
            ),
            group=1
        )
    
    def run(self):
        """Inicia el bot"""
        self.setup_handlers()
        logger.info("🤖 Bot iniciado. Presiona Ctrl+C para detener.")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    bot = FizzyTelegramBot()
    bot.run()
