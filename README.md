<p align="center">
  <a href="https://soul23.mx">
    <picture>
      <source
        media="(prefers-color-scheme: dark)"
        srcset="https://raw.githubusercontent.com/marcogll/mg_data_storage/refs/heads/main/soul23/logo/soul23_logo_wh.png">
      <source
        media="(prefers-color-scheme: light)"
        srcset="https://raw.githubusercontent.com/marcogll/mg_data_storage/refs/heads/main/soul23/logo/soul23_logo_blk.png">
      <img
        src="https://raw.githubusercontent.com/marcogll/mg_data_storage/refs/heads/main/soul23/logo/soul23_logo_blk.png"
        width="110"
        alt="Soul:23">
    </picture>
  </a>
</p>

<h1 align="center">Fizzy Manager</h1>

<p align="center">
  Sistema de gestión de tareas Fizzy con integración a Telegram para el bot Talia.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3a3a3a?style=flat-square&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Fizzy-3a3a3a?style=flat-square&logo=basecamp&logoColor=white">
  <img src="https://img.shields.io/badge/Telegram-3a3a3a?style=flat-square&logo=telegram&logoColor=white">
</p>

---

## Description

Sistema de gestión de tareas Fizzy con integración a Telegram para el bot Talia: creación y consulta de tareas directamente desde Telegram, con configuración por variables de entorno.

Python 3.9+, asyncio y python-telegram-bot.

## 📋 Características

- **Gestión de Proyectos**: Organiza tareas en proyectos (playground, alma, soul23)
- **Bot de Telegram**: Interactúa con Fizzy mediante comandos de Telegram
- **Notificaciones Automáticas**: Recibe alertas cuando se crean/modifican tareas
- **Sincronización**: Mapea automáticamente boards de Fizzy a proyectos

## 🚀 Instalación

1. **Clonar o navegar al directorio:**
```bash
cd fizzy_manager
```

2. **Crear entorno virtual:**
```bash
python -m venv venv
source venv/bin/activate  # En macOS/Linux
# o
venv\Scripts\activate  # En Windows
```

3. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno:**
```bash
cp .env.example .env
# Editar .env con tus tokens
```

5. **Configurar proyectos:**
```bash
python setup.py
```

6. **Iniciar el bot:**
```bash
python bot/telegram_bot.py
```

## ⚙️ Configuración

### Variables de Entorno (.env)

```env
# Fizzy API
FIZZY_TOKEN=tu_token_de_fizzy

# Telegram Bot
TELEGRAM_BOT_TOKEN=tu_token_de_botfather
TELEGRAM_CHAT_ID=tu_chat_id
BOT_NAME=Talia
```

### Configuración de Proyectos (config.yaml)

```yaml
projects:
  playground:
    name: "Plygroid - Personal"
    board_id: null  # Se asigna automáticamente
    description: "Proyectos personales"
    
  alma:
    name: "Alma - Socia"
    board_id: null
    description: "Tareas de mi socia"
    
  soul23:
    name: "Soul23 - Clientes"
    board_id: null
    description: "Tareas de otros clientes"
```

## 🤖 Comandos de Telegram

| Comando | Descripción | Ejemplo |
|---------|-------------|---------|
| `/proyectos` | Lista proyectos configurados | `/proyectos` |
| `/tareas [proyecto]` | Muestra tareas de un proyecto | `/tareas playground` |
| `/crear` | Crea una nueva tarea | `/crear` |
| `/completar [id]` | Marca tarea como completada | `/completar 123` |
| `/buscar [texto]` | Busca tareas | `/buscar urgente` |
| `/ayuda` | Muestra ayuda | `/ayuda` |

## 📁 Estructura del Proyecto

```
fizzy_manager/
├── bot/
│   ├── __init__.py
│   └── telegram_bot.py      # Bot de Telegram
├── src/
│   ├── __init__.py
│   ├── fizzy_client.py      # Cliente API de Fizzy
│   ├── project_manager.py   # Gestor de proyectos
│   └── telegram_notifier.py # Notificador de Telegram
├── .env                     # Variables de entorno (no subir a git)
├── .env.example             # Ejemplo de variables
├── config.yaml              # Configuración de proyectos
├── requirements.txt         # Dependencias
├── setup.py                 # Script de inicialización
└── README.md                # Este archivo
```

## 🔧 Uso

### Crear una tarea desde Telegram

1. Escribe `/crear`
2. Selecciona el proyecto
3. Escribe el título
4. Opcional: agrega descripción

### Ver tareas de un proyecto

```
/tareas playground
```

### Completar una tarea

```
/completar 123
```

## 📝 Notas

- El token de Fizzy se obtiene desde https://fizzy.do/settings/tokens
- El token de Telegram se obtiene de @BotFather
- El `TELEGRAM_CHAT_ID` se puede obtener escribiendo `/start` al bot y revisando los logs

## 🔒 Seguridad

- Nunca compartas tu `.env` o tokens
- Agrega `.env` a tu `.gitignore`
- El bot solo responde a tu `TELEGRAM_CHAT_ID` configurado

## 🐛 Troubleshooting

### Error de conexión con Fizzy
```bash
# Verificar token
python setup.py
```

### Bot no responde
- Verificar que `TELEGRAM_BOT_TOKEN` sea correcto
- Verificar que `TELEGRAM_CHAT_ID` coincida con tu usuario

### No encuentra boards
- Ejecuta `python setup.py` para sincronizar
- Verifica que tengas boards creados en Fizzy

## 📄 Licencia

Personal - Uso interno

---

Hecho con ❤️ para Talia 🤖
