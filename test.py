"""
Script de pruebas para Fizzy Manager
"""
import os
import sys
import asyncio
from pathlib import Path

# Agregar directorio padre al path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from src.fizzy_client import get_fizzy_client, FizzyClient
from src.project_manager import get_project_manager, ProjectManager
from src.telegram_notifier import get_telegram_notifier, TelegramNotifier

# Cargar variables de entorno
load_dotenv()


def test_env():
    """Prueba 1: Verificar variables de entorno"""
    print("=" * 60)
    print("🔍 PRUEBA 1: Variables de Entorno")
    print("=" * 60)
    
    fizzy_token = os.getenv('FIZZY_TOKEN')
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    bot_name = os.getenv('BOT_NAME')
    
    print(f"FIZZY_TOKEN: {'✅ Configurado' if fizzy_token else '❌ No configurado'}")
    if fizzy_token:
        print(f"   Token: {fizzy_token[:10]}...{fizzy_token[-5:]}")
    
    print(f"TELEGRAM_BOT_TOKEN: {'✅ Configurado' if telegram_token else '❌ No configurado'}")
    if telegram_token:
        print(f"   Token: {telegram_token[:15]}...{telegram_token[-10:]}")
    
    print(f"TELEGRAM_CHAT_ID: {'✅ ' + chat_id if chat_id else '❌ No configurado'}")
    print(f"BOT_NAME: {'✅ ' + bot_name if bot_name else '❌ No configurado'}")
    
    return all([fizzy_token, telegram_token, chat_id])


def test_fizzy_connection():
    """Prueba 2: Conexión con Fizzy API"""
    print("\n" + "=" * 60)
    print("🔍 PRUEBA 2: Conexión con Fizzy API")
    print("=" * 60)
    
    try:
        client = get_fizzy_client()
        print("✅ Cliente Fizzy creado exitosamente")
        
        # Intentar obtener boards
        print("\n📋 Obteniendo boards...")
        boards = client.get_boards()
        
        print(f"✅ Conexión exitosa! Encontrados {len(boards)} boards:\n")
        for board in boards:
            print(f"   • ID: {board.id} | Nombre: {board.name}")
        
        return True, boards
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, []


def test_project_manager():
    """Prueba 3: Gestor de Proyectos"""
    print("\n" + "=" * 60)
    print("🔍 PRUEBA 3: Gestor de Proyectos")
    print("=" * 60)
    
    try:
        pm = get_project_manager()
        print("✅ Project Manager inicializado")
        
        projects = pm.get_all_projects()
        print(f"\n📁 Proyectos configurados ({len(projects)}):")
        
        for proj in projects:
            board_status = "✅" if proj.board_id else "⚠️ (sin board)"
            print(f"   {board_status} {proj.key}: {proj.name}")
            if proj.description:
                print(f"      {proj.description}")
        
        return True, projects
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, []


def test_fizzy_operations(boards):
    """Prueba 4: Operaciones de Fizzy"""
    print("\n" + "=" * 60)
    print("🔍 PRUEBA 4: Operaciones de Fizzy (CRUD)")
    print("=" * 60)
    
    if not boards:
        print("❌ No hay boards disponibles para probar")
        return False
    
    client = get_fizzy_client()
    test_board = boards[0]
    
    print(f"Usando board: {test_board.name} (ID: {test_board.id})\n")
    
    try:
        # Obtener cards existentes
        print("📋 Obteniendo cards existentes...")
        cards = client.get_cards(test_board.id)
        print(f"✅ Encontradas {len(cards)} cards")
        
        if cards:
            print("\n📝 Primeras 3 cards:")
            for card in cards[:3]:
                status = "✅" if card.status == "completed" else "⏳"
                print(f"   {status} #{card.id}: {card.title}")
        
        # Crear card de prueba
        print("\n🆕 Creando card de prueba...")
        test_card = client.create_card(
            board_id=test_board.id,
            title="🧪 Tarea de prueba - Fizzy Manager",
            description="Esta es una tarea de prueba creada automáticamente"
        )
        print(f"✅ Card creada: #{test_card.number or test_card.id} - {test_card.title}")
        
        # Actualizar card
        print("\n🔄 Actualizando card...")
        updated_card = client.update_card(
            card_id=test_card.id,
            card_number=test_card.number,  # Usar número para PATCH
            description="Descripción actualizada desde pruebas"
        )
        print(f"✅ Card actualizada")
        
        # Completar card
        print("\n✅ Completando card...")
        completed_card = client.complete_card(
            card_id=test_card.id,
            card_number=test_card.number  # Usar número para PATCH
        )
        print(f"✅ Card completada - Cerrada: {completed_card.closed}")
        
        # Eliminar card de prueba
        print("\n🗑️ Eliminando card de prueba...")
        deleted = client.delete_card(
            card_id=test_card.id,
            card_number=test_card.number  # Usar número para DELETE
        )
        if deleted:
            print("✅ Card eliminada")
        else:
            print("⚠️ No se pudo eliminar la card (puede requerir permisos)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_telegram_connection():
    """Prueba 5: Conexión con Telegram"""
    print("\n" + "=" * 60)
    print("🔍 PRUEBA 5: Conexión con Telegram")
    print("=" * 60)
    
    try:
        notifier = get_telegram_notifier()
        
        if not notifier.bot:
            print("❌ Bot de Telegram no configurado")
            return False
        
        print("✅ Notificador de Telegram inicializado")
        print(f"   Chat ID: {notifier.config.chat_id}")
        print(f"   Bot Name: {notifier.config.bot_name}")
        
        # Enviar mensaje de prueba
        print("\n📨 Enviando mensaje de prueba...")
        message = f"""
🧪 <b>Prueba de Fizzy Manager</b>

Esta es una prueba del sistema de notificaciones.

<b>Estado:</b> ✅ Funcionando correctamente
<b>Bot:</b> {notifier.config.bot_name}
<b>Fecha:</b> {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        success = await notifier.send_message(message)
        
        if success:
            print("✅ Mensaje enviado exitosamente!")
        else:
            print("❌ No se pudo enviar el mensaje")
        
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_project_sync(boards):
    """Prueba 6: Sincronización de Proyectos"""
    print("\n" + "=" * 60)
    print("🔍 PRUEBA 6: Sincronización de Proyectos")
    print("=" * 60)
    
    try:
        pm = get_project_manager()
        
        # Crear mapa de boards por nombre
        board_map = {b.name.lower(): b.id for b in boards}
        
        print("Sincronizando proyectos con boards...\n")
        
        synced = 0
        for key, project in pm.projects.items():
            if project.board_id:
                print(f"   ✅ {key}: Ya tiene board_id ({project.board_id})")
                synced += 1
            else:
                # Buscar por nombre
                search_terms = [
                    project.name.lower(),
                    project.key.lower(),
                ]
                
                found_id = None
                for term in search_terms:
                    if term in board_map:
                        found_id = board_map[term]
                        break
                
                if found_id:
                    pm.set_board_id(key, found_id)
                    print(f"   ✅ {key}: Asignado board_id {found_id}")
                    synced += 1
                else:
                    print(f"   ⚠️ {key}: No se encontró board automáticamente")
                    print(f"      Buscado: {search_terms}")
        
        print(f"\n✅ {synced}/{len(pm.projects)} proyectos sincronizados")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Ejecuta todas las pruebas"""
    print("\n" + "🧪 " * 30)
    print("   INICIANDO PRUEBAS DE FIZZY MANAGER")
    print("🧪 " * 30 + "\n")
    
    results = {}
    
    # Prueba 1: Variables de entorno
    results['env'] = test_env()
    
    if not results['env']:
        print("\n❌ Pruebas detenidas: Faltan variables de entorno")
        return results
    
    # Prueba 2: Conexión Fizzy
    fizzy_ok, boards = test_fizzy_connection()
    results['fizzy_connection'] = fizzy_ok
    
    if not fizzy_ok:
        print("\n❌ Pruebas detenidas: No se pudo conectar con Fizzy")
        return results
    
    # Prueba 3: Project Manager
    pm_ok, projects = test_project_manager()
    results['project_manager'] = pm_ok
    
    # Prueba 4: Operaciones Fizzy
    if boards:
        results['fizzy_operations'] = test_fizzy_operations(boards)
    
    # Prueba 6: Sincronización
    results['project_sync'] = test_project_sync(boards)
    
    # Prueba 5: Telegram (async)
    print("\n" + "-" * 60)
    print("Ejecutando pruebas de Telegram...")
    results['telegram'] = asyncio.run(test_telegram_connection())
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"   {status}: {test_name}")
    
    print(f"\n{passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("\n🎉 ¡Todas las pruebas pasaron! El sistema está listo.")
    else:
        print(f"\n⚠️ {total - passed} prueba(s) fallaron. Revisa los errores arriba.")
    
    return results


if __name__ == "__main__":
    run_all_tests()
