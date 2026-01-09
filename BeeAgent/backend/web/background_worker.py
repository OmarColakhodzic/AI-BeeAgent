# backend/web/background_worker.py
import asyncio
from application.runners.scoring_runner import ScoringAgentRunner

class BackgroundWorker:
    def __init__(self, scoring_runner: ScoringAgentRunner):
        self.scoring_runner = scoring_runner
        self.is_running = False
    
    async def run_agent_loop(self):
        self.is_running = True
        while self.is_running:
            result = self.scoring_runner.step()
            if result:
                # Emituj preko WebSocket-a
                await self.emit_to_frontend(result.to_dict())
                await asyncio.sleep(0.1)
            else:
                await asyncio.sleep(5)