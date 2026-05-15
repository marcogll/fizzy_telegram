"""
Script de inicialización para Fizzy Manager
Sincroniza los boards de Fizzy con la configuración de proyectos
"""
import os
import sys
from pathlib import Path

# Agregar el directorio padre al path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from src.fizzy_client import get_fizzy_client
from src.project_manager import get_project_manager


def setup_projects():
    """Configura los proyectos sincronizando con los boards de Fizzy"""
    print("🔧 Configurando Fizzy Manager...\n")
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Verificar token
    if not os.getenv('FIZZY_TOKEN'):
        print("❌ Error: FIZZY_TOKEN no configurado")
        print("   Copia .env.example a .env y configura tu token")
        return False
    
    try:
        # Obtener cliente y proyectos
        fizzy = get_fizzy_client()
        projects = get_project_manager()
        
        # Obtener boards de Fizzy
        print("📋 Obteniendo boards de Fizzy...")
        boards = fizzy.get_boards()
        
        print(f"   Encontrados {len(boards)} boards:\n")
        for board in boards:
            print(f"   • #{board.id}: {board.name}")
        
        print()
        
        # Mapear boards a proyectos
        board_map = {board.name.lower(): board.id for board in boards}
        
        updated = False
        for project_key, project in projects.projects.items():
            print(f"🔍 Proyecto: {project.key} ({project.name})")
            
            if project.board_id:
                print(f"   ✓ Ya tiene board_id: {project.board_id}")
            else:
                # Intentar encontrar board por nombre
                search_names = [
                    project.name.lower(),
                    project.key.lower(),
                    project.name.lower().replace(' - ', ' '),
                ]
                
                found_id = None
                for search_name in search_names:
                    if search_name in board_map:
                        found_id = board_map[search_name]
                        break
                
                if found_id:
                    projects.set_board_id(project_key, found_id)
                    print(f"   ✅ Asignado board_id: {found_id}")
                    updated = True
                else:
                    print(f"   ⚠️ No se encontró board automáticamente")
                    print(f"   Boards disponibles: {[b.name for b in boards]}")
        
        if updated:
            print("\n💾 Configuración guardada en config.yaml")
        
        print("\n✅ Configuración completada!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def test_connection():
    """Prueba la conexión con Fizzy"""
    print("\n🧪 Probando conexión con Fizzy...")
    
    try:
        fizzy = get_fizzy_client()
        boards = fizzy.get_boards()
        print(f"   ✅ Conexión exitosa! {len(boards)} boards disponibles")
        return True
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
        return False


if __name__ == "__main__":
    if setup_projects():
        test_connection()
        print("\n🚀 Listo para usar!")
        print("   Ejecuta: python bot/telegram_bot.py")
    else:
        sys.exit(1)
