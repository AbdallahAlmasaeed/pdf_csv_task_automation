#!/usr/bin/env python3
"""
Integrated Main Loop (Chat + Task only)
Mode numbers preserved: 1, 2, 4
Mode 3 intentionally removed
"""

import os
import sys
import asyncio
import logging
from enum import Enum
from pathlib import Path
import pandas as pd

# -------------------------
# Ensure agent_pipeline is importable
# -------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# -------------------------
# Imports
# -------------------------
from agent_pipeline.pipeline_integration import PipelineAgent
from agent_pipeline.agent_short_memory import upsert_fact
from agent_pipeline.workloop.workloop import set_memory_system
from agent_pipeline.project_profiles import ProfilesDB
from agent_pipeline.style_bank import StyleBank
from agent_pipeline.decision_templates import DecisionTemplates
from agent_pipeline.telemetry import init_telemetry_table

from rich.console import Console
from rich.panel import Panel

console = Console()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# -------------------------
# Constants
# -------------------------
VALID_MODEL = "phi3:mini"

class Mode(Enum):
    CHAT = "chat"
    TASK = "task"
    QUIT = "quit"

# =========================================================
# MAIN LOOP CLASS
# =========================================================
class IntegratedMainLoop:
    def __init__(self):
        console.print("[bold green][Main][/bold green] Initializing integrated pipeline...")
        self.agent = PipelineAgent(default_model=VALID_MODEL)
        self.memory = self.agent.memory
        set_memory_system(self.memory)

        try:
            init_telemetry_table(getattr(self.memory, 'conn', None))
        except Exception:
            pass

        self.profiles_db = ProfilesDB()
        self.style_bank = StyleBank()
        self.templates = DecisionTemplates()

        self._maybe_load_promptbuilder_defaults()

        console.print("[bold green][Main] Pipeline ready (Chat + Task modes)[/bold green]")

    # --------------------------------------------------------
    # Prompt mode (NUMBERS PRESERVED)
    # --------------------------------------------------------
    def prompt_mode(self):
        console.print("\n" + "=" * 60)
        console.print("[bold cyan]AGENT PIPELINE - SELECT MODE[/bold cyan]")
        console.print("=" * 60)
        console.print("1. Chat mode")
        console.print("2. Task mode")
        console.print("3. (Removed)")
        console.print("4. Quit")
        console.print("-" * 60)

        choice = input("Select (1-4): ").strip()

        if choice == "1":
            return Mode.CHAT
        elif choice == "2":
            return Mode.TASK
        elif choice == "4":
            return Mode.QUIT
        else:
            console.print("[Warning] Mode not available. Please select 1, 2, or 4.", style="yellow")
            return None

    # --------------------------------------------------------
    # Chat mode
    # --------------------------------------------------------
    def run_chat_mode(self):
        console.print(Panel("Chat Mode — type 'back' to exit", style="magenta"))
        while True:
            msg = input("\nYou: ").strip()
            if msg.lower() == "back":
                return
            result = self.agent.process_conversation_turn(msg)
            console.print(Panel(result["assistant_response"], style="cyan"))
            upsert_fact(self.agent.memory.stm_store, msg)

    # --------------------------------------------------------
    # Task mode (Dataset Analysis)
    # --------------------------------------------------------
    def run_task_mode(self):
        console.print(Panel("Task Mode — LLM-Powered Dataset Analysis", style="magenta"))

        file_path = input("Enter dataset file path (CSV/Excel): ").strip()
        if not Path(file_path).exists():
            console.print(f"[Error] File not found: {file_path}", style="red")
            return

        try:
            if file_path.endswith(".csv"):
                df = pd.read_csv(file_path)
            elif file_path.endswith((".xls", ".xlsx")):
                df = pd.read_excel(file_path)
            else:
                console.print("[Error] Unsupported file type. Use CSV or Excel.", style="red")
                return
        except Exception as e:
            console.print(f"[Error] Failed to read file: {e}", style="red")
            return

        console.print(f"[Info] Dataset loaded ({len(df)} rows, {len(df.columns)} columns)", style="green")
        console.print(f"Columns detected: {', '.join(df.columns)}")

        instructions = input("\nEnter your analysis instruction(s): ").strip()
        if not instructions:
            console.print("[Skip] No instructions provided.", style="yellow")
            return

        dataset_text = df.to_csv(index=False)

        prompt = f"""
You are an expert data analyst.

Dataset (CSV):
{dataset_text}

Instructions:
{instructions}

Provide clear, professional results.
"""

        try:
            result = self.agent.process_task(prompt)
            final_answer = result.get("final_answer") or result.get("text") or "No answer returned."
            console.print(Panel(final_answer, title="[Analysis Result]", style="cyan"))
        except Exception as e:
            console.print(f"[Error] LLM processing failed: {e}", style="red")

        console.print("\n[Task Complete]", style="bold green")

    # --------------------------------------------------------
    # Prompt defaults
    # --------------------------------------------------------
    def _maybe_load_promptbuilder_defaults(self):
        c = input("\n[Setup] Paste contract text (or Enter to skip): ").strip()
        if c:
            self.memory.set_kv("contract_text", c)
        s = input("[Setup] Style hint (optional): ").strip()
        if s:
            self.memory.set_kv("style_hint", s)

    # --------------------------------------------------------
    # Main run loop (KEEPS RUNNING)
    # --------------------------------------------------------
    async def run(self):
        console.print("\n" + "=" * 60)
        console.print("[bold cyan]INTEGRATED AGENT PIPELINE[/bold cyan]")
        console.print("=" * 60)

        while True:
            mode = self.prompt_mode()
            if mode is None:
                continue

            if mode == Mode.CHAT:
                self.run_chat_mode()
            elif mode == Mode.TASK:
                self.run_task_mode()
            elif mode == Mode.QUIT:
                console.print("[Goodbye] Session ended.", style="green")
                break

# --------------------------------------------------------
# Entry
# --------------------------------------------------------
def main():
    loop = IntegratedMainLoop()
    asyncio.run(loop.run())

if __name__ == "__main__":
    main()
