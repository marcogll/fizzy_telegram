"""
Gestor de proyectos Fizzy
Mapea proyectos a boards específicos
"""
import os
import yaml
from typing import Dict, Optional, List
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Project:
    key: str
    name: str
    board_id: Optional[int] = None
    description: str = ""


class ProjectManager:
    """Gestiona la configuración de proyectos y sus boards asociados"""
    
    CONFIG_FILE = Path(__file__).parent.parent / 'config.yaml'
    
    def __init__(self):
        self.projects: Dict[str, Project] = {}
        self._load_config()
    
    def _load_config(self):
        """Carga la configuración desde config.yaml"""
        if not self.CONFIG_FILE.exists():
            return
        
        with open(self.CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)
        
        projects_data = config.get('projects', {})
        for key, data in projects_data.items():
            self.projects[key] = Project(
                key=key,
                name=data.get('name', key),
                board_id=data.get('board_id'),
                description=data.get('description', '')
            )
    
    def save_config(self):
        """Guarda la configuración actual a config.yaml"""
        config = {
            'projects': {}
        }
        
        for key, project in self.projects.items():
            config['projects'][key] = {
                'name': project.name,
                'board_id': project.board_id,
                'description': project.description
            }
        
        with open(self.CONFIG_FILE, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    def get_project(self, key: str) -> Optional[Project]:
        """Obtiene un proyecto por su clave"""
        return self.projects.get(key.lower())
    
    def get_all_projects(self) -> List[Project]:
        """Obtiene todos los proyectos configurados"""
        return list(self.projects.values())
    
    def set_board_id(self, project_key: str, board_id: int):
        """Asigna un board_id a un proyecto"""
        project = self.get_project(project_key)
        if project:
            project.board_id = board_id
            self.save_config()
    
    def get_project_by_board_id(self, board_id: int) -> Optional[Project]:
        """Encuentra un proyecto por su board_id"""
        for project in self.projects.values():
            if project.board_id == board_id:
                return project
        return None


# Instancia singleton
_project_manager: Optional[ProjectManager] = None


def get_project_manager() -> ProjectManager:
    """Obtiene o crea el gestor de proyectos"""
    global _project_manager
    if _project_manager is None:
        _project_manager = ProjectManager()
    return _project_manager
