"""
Cliente de API para Fizzy
Interactúa directamente con la API REST de Fizzy
"""
import os
import json
import requests
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Board:
    id: str
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Board':
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            description=data.get('description'),
            url=data.get('url')
        )


@dataclass
class Card:
    id: str
    title: str
    description: Optional[str] = None
    board_id: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed: Optional[bool] = None
    closed: Optional[bool] = None
    postponed: Optional[bool] = None
    number: Optional[int] = None
    tags: Optional[List[str]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Card':
        card = cls(
            id=data.get('id'),
            title=data.get('title'),
            description=data.get('description'),
            board_id=data.get('board_id') or (data.get('board', {}).get('id') if data.get('board') else None),
            status=data.get('status'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            completed=data.get('completed'),
            closed=data.get('closed'),
            postponed=data.get('postponed'),
            number=data.get('number'),
            tags=data.get('tags', [])
        )
        return card


class FizzyClient:
    """Cliente para interactuar con la API de Fizzy"""
    
    BASE_URL = "https://fizzy.soul23.cloud"
    
    def __init__(self, token: Optional[str] = None, account_id: str = "1"):
        self.token = token or os.getenv('FIZZY_TOKEN')
        if not self.token:
            raise ValueError("Se requiere un token de Fizzy. Usa FIZZY_TOKEN en .env")
        
        self.account_id = account_id
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Realiza una petición a la API"""
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            # Algunos endpoints pueden devolver JSON, otros no
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                return response.json()
            return response.text
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error en petición a Fizzy: {e}")
    
    def get_boards(self) -> List[Board]:
        """Obtiene todos los boards disponibles"""
        result = self._request('GET', f'/{self.account_id}/boards.json')
        
        # La API devuelve una lista directa, no un objeto con 'data'
        if isinstance(result, list):
            return [Board.from_dict(b) for b in result]
        elif isinstance(result, dict) and 'data' in result:
            return [Board.from_dict(b) for b in result.get('data', [])]
        return []
    
    def get_board(self, board_id: str) -> Board:
        """Obtiene un board específico"""
        result = self._request('GET', f'/{self.account_id}/boards/{board_id}.json')
        if isinstance(result, dict):
            return Board.from_dict(result)
        raise Exception(f"Respuesta inesperada: {result}")
    
    def get_cards(self, board_id: str) -> List[Card]:
        """Obtiene todas las cards de un board"""
        result = self._request('GET', f'/{self.account_id}/cards.json', params={'board_id': board_id})
        
        if isinstance(result, list):
            cards = [Card.from_dict(c) for c in result]
            return cards
        elif isinstance(result, dict) and 'data' in result:
            return [Card.from_dict(c) for c in result.get('data', [])]
        return []
    
    def get_card(self, card_id: str) -> Card:
        """Obtiene una card específica"""
        result = self._request('GET', f'/{self.account_id}/cards/{card_id}.json')
        if isinstance(result, dict):
            return Card.from_dict(result)
        raise Exception(f"Respuesta inesperada: {result}")
    
    def create_card(self, board_id: str, title: str, description: Optional[str] = None, 
                    column_id: Optional[str] = None) -> Card:
        """Crea una nueva card en un board"""
        data = {
            'card': {
                'title': title,
                'description': description or ''
            }
        }
        
        params = {'board_id': board_id}
        if column_id:
            params['column_id'] = column_id
            
        result = self._request('POST', f'/{self.account_id}/cards.json', 
                              params=params, json=data)
        
        if isinstance(result, dict):
            return Card.from_dict(result)
        raise Exception(f"Respuesta inesperada al crear card: {result}")
    
    def update_card(self, card_id: str, title: Optional[str] = None, 
                    description: Optional[str] = None, completed: Optional[bool] = None,
                    closed: Optional[bool] = None, postponed: Optional[bool] = None,
                    card_number: Optional[int] = None) -> Card:
        """Actualiza una card existente. Puede recibir el ID o el número de la card."""
        data = {'card': {}}
        if title is not None:
            data['card']['title'] = title
        if description is not None:
            data['card']['description'] = description
        if completed is not None:
            data['card']['completed'] = completed
        if closed is not None:
            data['card']['closed'] = closed
        if postponed is not None:
            data['card']['postponed'] = postponed
        
        # Usar el número si está disponible, si no el ID
        card_ref = str(card_number) if card_number else card_id
        result = self._request('PATCH', f'/{self.account_id}/cards/{card_ref}.json', json=data)
        
        if isinstance(result, dict):
            return Card.from_dict(result)
        raise Exception(f"Respuesta inesperada al actualizar card: {result}")
    
    def complete_card(self, card_id: str, card_number: Optional[int] = None) -> Card:
        """Marca una card como completada (cierra la card)"""
        return self.update_card(card_id, closed=True, card_number=card_number)
    
    def delete_card(self, card_id: str, card_number: Optional[int] = None) -> bool:
        """Elimina una card"""
        try:
            card_ref = str(card_number) if card_number else card_id
            self._request('DELETE', f'/{self.account_id}/cards/{card_ref}.json')
            return True
        except:
            return False
    
    def search_cards(self, query: str, board_id: Optional[str] = None) -> List[Card]:
        """Busca cards por query"""
        params = {'q': query}
        if board_id:
            params['board_id'] = board_id
        
        result = self._request('GET', f'/{self.account_id}/search.json', params=params)
        
        if isinstance(result, list):
            return [Card.from_dict(c) for c in result]
        elif isinstance(result, dict):
            if 'cards' in result:
                return [Card.from_dict(c) for c in result.get('cards', [])]
            elif 'data' in result:
                return [Card.from_dict(c) for c in result.get('data', [])]
        return []
    
    def get_columns(self, board_id: str) -> List[Dict[str, Any]]:
        """Obtiene las columnas de un board"""
        result = self._request('GET', f'/{self.account_id}/boards/{board_id}/columns.json')
        
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and 'data' in result:
            return result.get('data', [])
        return []


# Instancia singleton para uso global
_fizzy_client: Optional[FizzyClient] = None


def get_fizzy_client() -> FizzyClient:
    """Obtiene o crea una instancia del cliente Fizzy"""
    global _fizzy_client
    if _fizzy_client is None:
        _fizzy_client = FizzyClient()
    return _fizzy_client
