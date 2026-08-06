"""MCP Server for S21 Task Intelligence Agent - Updated version using TeamPerformanceAgent."""
import json
import os
import sys
import logging
import traceback
from datetime import datetime
from typing import Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/s21_mcp_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

app = FastAPI(
    title="S21 Task Agent MCP",
    description="MCP server for intelligent task search and analysis",
    version="0.2.0",
)

from s21_team_performance.agent import TeamPerformanceAgent
from s21_team_performance.models import TeamAnalysisRequest

team_agent = TeamPerformanceAgent()
team_agent.load_team_members()


class QueryRequest(BaseModel):
    query: str


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for debugging."""
    request_id = datetime.now().isoformat()
    logger.info(f"[MCP REQUEST] {request_id} - {request.method} {request.url.path}")
    
    # Log request body if available
    if request.method == "POST":
        try:
            body = await request.body()
            if body:
                logger.info(f"[MCP REQUEST] {request_id} - Body: {body.decode()[:500]}")
        except Exception as e:
            logger.warning(f"[MCP REQUEST] {request_id} - Failed to read body: {e}")
    
    response = await call_next(request)
    
    # Log response
    logger.info(f"[MCP RESPONSE] {request_id} - Status: {response.status_code}")
    
    return response


@app.post("/query")
async def query_agent(request: QueryRequest):
    """Handle natural language queries using TeamPerformanceAgent."""
    query = request.query.strip()

    logger.info(f"[QUERY] Received query: {query}")
    logger.info(f"[REQUEST] Timestamp: {datetime.now().isoformat()}")
    logger.info(f"[REQUEST] Full request: {json.dumps({'query': query}, ensure_ascii=False)}")

    if not query:
        logger.warning("[RESPONSE] Empty query")
        return {"response": "Пожалуйста, задайте вопрос.", "type": "error", "tasks": []}

    try:
        # Reload modules and create fresh agent
        import importlib
        import sys

        # Reload team_performance module to get latest changes
        if 's21_team_performance' in sys.modules:
            del sys.modules['s21_team_performance']
        if 's21_team_performance.agent' in sys.modules:
            del sys.modules['s21_team_performance.agent']

        from s21_team_performance.agent import TeamPerformanceAgent
        fresh_agent = TeamPerformanceAgent()
        fresh_agent.load_team_members()

        # Load pending_sprint context from file
        context_file = os.path.expanduser('~/.task-tracker/pending_sprint.json')
        if os.path.exists(context_file):
            try:
                with open(context_file, 'r') as f:
                    fresh_agent.context["pending_sprint"] = json.load(f)
                with open('/tmp/s21_mcp.log', 'a') as f:
                    f.write(f"[CONTEXT] Loaded pending_sprint: {fresh_agent.context['pending_sprint']}\n")
            except Exception as e:
                with open('/tmp/s21_mcp.log', 'a') as f:
                    f.write(f"[CONTEXT] Failed to load context: {e}\n")

        # Use TeamPerformanceAgent to process the query
        logger.info("[PROCESS] Calling fresh_agent.analyze_by_query()")
        result = await fresh_agent.analyze_by_query(query)
        logger.info(f"[PROCESS] Analysis complete. Status: {result.status}, Findings count: {len(result.findings)}")

        # Map findings to response
        # Use max findings to show all available information
        findings_text = "\n".join(result.findings)
        logger.info(f"[RESPONSE] Findings preview: {findings_text[:200]}...")

        # Build response with sprint list if available
        response_data = {
            "response": findings_text,
            "type": "success" if result.status == "green" else "info",
            "tasks": result.tasks if hasattr(result, 'tasks') else [],
            "llm_used": True,
        }

        # Include sprint list for user selection
        if result.sprints:
            response_data["sprints"] = result.sprints
            response_data["default"] = result.default_sprint if hasattr(result, 'default_sprint') else result.sprints[0] if result.sprints else ""
            response_data["sprint_selection_required"] = True
            # Save pending_sprint context to file
            if hasattr(result, 'team_members') and result.team_members:
                context_file = os.path.expanduser('~/.task-tracker/pending_sprint.json')
                try:
                    with open(context_file, 'w') as f:
                        json.dump({"team_members": result.team_members, "products": getattr(result, 'products', [])}, f)
                    logger.info(f"[CONTEXT] Saved pending_sprint: {result.team_members}")
                except Exception as e:
                    logger.warning(f"[CONTEXT] Failed to save context: {e}")

        logger.info(f"[RESPONSE] Returning status 200")

        return response_data

    except Exception as e:
        logger.error(f"[ERROR] Exception occurred: {e}")
        logger.error(f"[ERROR] Full traceback: {traceback.format_exc()}")

        # Return friendly error message instead of raw exception
        error_response = {
            "response": "Не удалось обработать ваш запрос. Пожалуйста, уточните запрос.\n\nПримеры запросов, которые я понимаю:\n"
            "- Задачи Кондратчиковой в спринте (покажу список спринтов)\n"
            "- Задачи Кондратчиковой из спринта DMS-SPRNT-1 (покажу задачи из спринта)\n"
            "- Задачи Гаранина из спринта DMS-SPRNT-1 (покажу задачи из спринта)\n\n"
            "### Скиллы для анализа:\n"
            "- Здоровье спринта: 'здоровье спринта OLP-SPRNT-3'\n"
            "- Velocity: 'скорость команды' или 'velocity за последние 6 спринтов'\n"
            "- Flow metrics: 'поток задач за 30 дней'\n"
            "- Баланс загрузки: 'баланс загрузки команды'\n"
            "- Узкие места: 'бутылочное горлышко в спринте'\n"
            "- Прогноз: 'прогноз завершения спринта'\n"
            "- Компетенции: 'кто подходит для задачи'\n"
            "- Релизы: 'релизные задачи OLAP'",
            "type": "error",
            "tasks": []
        }
        logger.info(f"[RESPONSE] Returning error response")

        return error_response


@app.post("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "server": "s21-agent-mcp"}


@app.get("/health")
async def health_get():
    """Health check endpoint."""
    return {"status": "ok", "server": "s21-agent-mcp"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=3001)
