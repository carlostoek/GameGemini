# GameGemini

GameGemini es un bot de Telegram construido con **aiogram**, **SQLAlchemy** asíncrono y **APScheduler**. Ofrece misiones, recompensas y niveles para gamificar comunidades.

## Características
- Sistema de puntos y niveles
- Misiones diarias, semanales y por reacción
- Gestión de recompensas con stock
- Soporte para eventos con multiplicadores

## Requisitos
- Python 3.12
- Dependencias en `requirements.txt`

## Uso
1. Instala las dependencias con `pip install -r requirements.txt`.
2. Configura las variables en `config.py` o mediante variables de entorno.
3. Ejecuta el bot con `python bot.py`.

## Desarrollo
El proyecto se organiza en:
- **handlers** – lógica de interacción con los usuarios y administradores.
- **services** – reglas de negocio (puntos, niveles, misiones, recompensas).
- **database** – modelos y utilidades de base de datos.
- **utils** – utilidades auxiliares como teclados y mensajes.

Se recomienda ejecutar `flake8` para verificar el estilo de código.
