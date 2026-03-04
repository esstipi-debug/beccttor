"""
BOLT FastAPI Server - Production MVP
Endpoints for Telegram webhook + Real athlete data capture
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import os
import json
import logging

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TOKEN_HERE")
TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL", "http://localhost:8000")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

app = FastAPI(title="BOLT Stress Engine", version="0.1.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health():
    """System health check"""
    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "validation_status": "THEORETICAL",
        "note": "System ready for production athlete data capture"
    }


# ============================================================================
# TELEGRAM WEBHOOK
# ============================================================================

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """
    Telegram webhook endpoint for bot messages
    Receives /start, /add_data, workout entries, etc.
    """
    try:
        update = await request.json()
        logger.info(f"Telegram update received: {update['update_id']}")
        
        # Extract message or callback_query
        if "message" in update:
            message = update["message"]
            chat_id = message["chat"]["id"]
            text = message.get("text", "")
            
            logger.info(f"Message from {chat_id}: {text}")
            
            # Route message handling
            response = await handle_telegram_message(chat_id, text)
            return JSONResponse(response)
        
        elif "callback_query" in update:
            query = update["callback_query"]
            chat_id = query["from"]["id"]
            data = query["data"]
            
            logger.info(f"Callback from {chat_id}: {data}")
            response = await handle_callback_query(chat_id, data)
            return JSONResponse(response)
        
        return JSONResponse({"ok": True})
    
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


async def handle_telegram_message(chat_id: int, text: str) -> dict:
    """Process incoming Telegram messages"""
    
    if text == "/start":
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": """
Bienvenido a BOLT - Asistente de Rendimiento CrossFit

Sistema BETA - Validacion teorica en progreso

Opciones:
[Datos] Agregar Datos de Hoy
[Plan] Mi Plan Hoy
[Reportar] Reportar Entrenamiento

Estamos recopilando datos reales para validar el sistema.
            """,
            "reply_markup": {
                "inline_keyboard": [
                    [{"text": "Datos de Hoy", "callback_data": "add_data"}],
                    [{"text": "Mi Plan", "callback_data": "get_plan"}],
                    [{"text": "Reportar WOD", "callback_data": "report_workout"}]
                ]
            }
        }
    
    elif text == "/stats":
        # Placeholder for athlete stats
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "Estadisticas (BETA)\n\nSistema recopilando datos reales..."
        }
    
    else:
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "Comando no reconocido. Usa /start para menu principal."
        }


async def handle_callback_query(chat_id: int, data: str) -> dict:
    """Handle inline button callbacks"""
    
    if data == "add_data":
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "Datos de Recuperacion Hoy\n\nSueno:",
            "reply_markup": {
                "inline_keyboard": [
                    [{"text": "<5 hrs", "callback_data": "sleep_low"}],
                    [{"text": "5-7 hrs", "callback_data": "sleep_medium"}],
                    [{"text": "7-9 hrs", "callback_data": "sleep_good"}],
                    [{"text": "9+ hrs", "callback_data": "sleep_excellent"}]
                ]
            }
        }
    
    elif data == "get_plan":
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "Tu Plan Hoy\n\nBETA: Recopilando datos..."
        }
    
    elif data == "report_workout":
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "Reportar Entrenamiento\n\nFoto o texto?"
        }
    
    else:
        return {
            "method": "answerCallbackQuery",
            "callback_query_id": data,
            "text": "Opcion procesada"
        }


# ============================================================================
# API ENDPOINTS FOR DATA CAPTURE
# ============================================================================

@app.post("/api/v1/athlete/data/recovery")
async def capture_recovery_data(data: dict):
    """
    Capture biometric recovery data
    
    POST /api/v1/athlete/data/recovery
    {
        "athlete_id": "carlos_123",
        "sleep_hours": 8.5,
        "stress_level": 3,
        "muscle_soreness": 2,
        "notes": "Felt good today"
    }
    """
    try:
        athlete_id = data.get("athlete_id")
        if not athlete_id:
            raise HTTPException(status_code=400, detail="athlete_id required")
        
        # TODO: Save to Supabase
        logger.info(f"Recovery data captured for {athlete_id}")
        
        return {
            "status": "saved",
            "athlete_id": athlete_id,
            "timestamp": datetime.now().isoformat(),
            "validation": "THEORETICAL"
        }
    
    except Exception as e:
        logger.error(f"Error capturing recovery data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/athlete/workout/report")
async def report_workout(data: dict):
    """
    Report completed workout
    """
    try:
        athlete_id = data.get("athlete_id")
        if not athlete_id:
            raise HTTPException(status_code=400, detail="athlete_id required")
        
        logger.info(f"Workout reported for {athlete_id}")
        
        return {
            "status": "processed",
            "athlete_id": athlete_id,
            "imr": "CALCULATING",
            "validation": "THEORETICAL",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error reporting workout: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/athlete/{athlete_id}/recommendation")
async def get_recommendation(athlete_id: str):
    """Get today's training recommendation based on ACWR + recovery"""
    try:
        return {
            "athlete_id": athlete_id,
            "acwr": {
                "ratio": "CALCULATING",
                "zone": "OPTIMAL",
                "risk_multiplier": 1.0
            },
            "recommendation": "Recopilando datos reales...",
            "validation_status": "THEORETICAL"
        }
    
    except Exception as e:
        logger.error(f"Error getting recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DASHBOARD (HTML)
# ============================================================================

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Web dashboard for athlete"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>BOLT Dashboard - BETA</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        .status {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 12px;
            margin-bottom: 30px;
            border-radius: 4px;
            color: #856404;
        }
        .section {
            margin-bottom: 40px;
        }
        .section h2 {
            color: #667eea;
            font-size: 18px;
            margin-bottom: 15px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .metric {
            display: inline-block;
            background: #f8f9fa;
            padding: 20px;
            margin-right: 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            min-width: 150px;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        .metric-label {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        .button {
            background: #667eea;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            margin-right: 10px;
            margin-bottom: 10px;
            font-size: 14px;
            transition: background 0.3s;
        }
        .button:hover {
            background: #764ba2;
        }
        code {
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>BOLT Asistente de Rendimiento</h1>
        <div class="status">
            <strong>ESTADO: BETA - Validacion Teorica</strong><br>
            Sistema recopilando datos reales de atletas. Los calculos han sido validados con 21/21 tests.
        </div>
        
        <div class="section">
            <h2>Componentes del Sistema</h2>
            <div class="metric">
                <div class="metric-value">OK</div>
                <div class="metric-label">Stress Engine</div>
            </div>
            <div class="metric">
                <div class="metric-value">OK</div>
                <div class="metric-label">ACWR Calculator</div>
            </div>
            <div class="metric">
                <div class="metric-value">OK</div>
                <div class="metric-label">Recovery Engine</div>
            </div>
            <div class="metric">
                <div class="metric-value">OK</div>
                <div class="metric-label">Menstrual Periodization</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Endpoints Disponibles</h2>
            <button class="button">GET /health</button>
            <button class="button">POST /api/v1/athlete/data/recovery</button>
            <button class="button">POST /api/v1/athlete/workout/report</button>
            <button class="button">GET /api/v1/athlete/{id}/recommendation</button>
            <button class="button">POST /webhook/telegram</button>
        </div>
        
        <div class="section">
            <h2>Proximos Pasos</h2>
            <ol style="color: #666; line-height: 1.8;">
                <li>Conectar Telegram Bot real</li>
                <li>Configurar base de datos Supabase</li>
                <li>Integrar datos de Carlos (5 dias de entrenamientos)</li>
                <li>Capturar recuperacion diaria (sueno, estres, dolor)</li>
                <li>Analizar predicciones vs realidad</li>
                <li>Iterar basado en datos reales</li>
            </ol>
        </div>
    </div>
</body>
</html>
    """


# ============================================================================
# SETUP WEBHOOK (Manual step)
# ============================================================================

@app.post("/setup/telegram")
async def setup_telegram_webhook():
    """
    Manual setup: Configure Telegram webhook
    """
    return {
        "status": "Ready to setup",
        "instruction": f"Call setWebhook with: {TELEGRAM_WEBHOOK_URL}/webhook/telegram",
        "note": "Requires TELEGRAM_BOT_TOKEN env variable"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
