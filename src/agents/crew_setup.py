# File: src/agents/crew_setup.py

import os
import sys
from crewai import Crew, Process, LLM

# Aggiungo il path del progetto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.agents.trading_agents import TradingAgents
from src.agents.trading_tasks import TradingTasks
from src.integration.tools_registry import TOOLS_REGISTRY


class TradingCrew:
    def __init__(self, market_data=None):
        """
        Inizializza la Crew di trading.

        market_data:
            Dizionario opzionale con meta-informazioni (data, status mercato, ecc.).
            NON contiene prezzi: per quelli gli agenti useranno i tools.
        """
        self.market_data = market_data if market_data else {}

        self.agents_blueprint = TradingAgents()
        self.tasks_blueprint = TradingTasks()

        # LLM del manager (non strettamente necessario, ma pronto per future estensioni)
        self.manager_llm = LLM(
            model="gemini/gemini-2.5-flash",
            temperature=0.1,
            api_key=os.getenv("GOOGLE_API_KEY")
        )

    def run(self):
        print("\n" + "=" * 60)
        print(" ASSEMBLING THE TRADING CREW")
        print("=" * 60 + "\n")

        # ==========================
        # 1. CREA GLI AGENTI CON TOOLS
        # ==========================
        coordinator = self.agents_blueprint.portfolio_coordinator(
            tools=TOOLS_REGISTRY["portfolio_coordinator"]
        )

        monitor_nee = self.agents_blueprint.monitor_nee_cwen(
            tools=TOOLS_REGISTRY["pair_monitor"]
        )

        monitor_run = self.agents_blueprint.monitor_run_pbw(
            tools=TOOLS_REGISTRY["pair_monitor"]
        )

        monitor_plug = self.agents_blueprint.monitor_plug_run(
            tools=TOOLS_REGISTRY["pair_monitor"]
        )

        risk_manager = self.agents_blueprint.risk_manager(
            tools=TOOLS_REGISTRY["risk_manager"]
        )

        executor = self.agents_blueprint.execution_agent(
            tools=TOOLS_REGISTRY["execution"]
        )

        print(" Agents created with tools:")
        print(f"  • Pair Monitors: {len(TOOLS_REGISTRY['pair_monitor'])} tools")
        print(f"  • Risk Manager: {len(TOOLS_REGISTRY['risk_manager'])} tools")
        print(f"  • Coordinator: {len(TOOLS_REGISTRY['portfolio_coordinator'])} tools")
        print(f"  • Execution: {len(TOOLS_REGISTRY['execution'])} tools")

        # ==========================
        # 2. CREA I TASKS
        # ==========================

        print("\n📋 Creating tasks...\n")

        # Analisi per ogni coppia
        task_nee = self.tasks_blueprint.analysis_task(
            agent=monitor_nee,
            pair_name="NEE/CWEN",
            context_data=self.market_data
        )

        task_run = self.tasks_blueprint.analysis_task(
            agent=monitor_run,
            pair_name="RUN/PBW",
            context_data=self.market_data
        )

        task_plug = self.tasks_blueprint.analysis_task(
            agent=monitor_plug,
            pair_name="PLUG/RUN",
            context_data=self.market_data
        )

        # Risk Management riceve i 3 report come contesto
        task_risk = self.tasks_blueprint.risk_assessment_task(
            agent=risk_manager,
            context_tasks=[task_nee, task_run, task_plug]
        )

        # Allocation riceve il Risk Report
        task_allocation = self.tasks_blueprint.allocation_task(
            agent=coordinator,
            context_tasks=[task_risk]
        )

        # Execution riceve le allocazioni
        task_execution = self.tasks_blueprint.execution_task(
            agent=executor,
            context_tasks=[task_allocation]
        )

        # ==========================
        # 3. DEFINISCI LA CREW
        # ==========================

        crew = Crew(
            agents=[
                monitor_nee,
                monitor_run,
                monitor_plug,
                risk_manager,
                coordinator,
                executor,
            ],
            tasks=[
                task_nee,
                task_run,
                task_plug,
                task_risk,
                task_allocation,
                task_execution,
            ],
            process=Process.sequential,  # Ordine: Monitors -> Risk -> Allocation -> Exec
            verbose=True,
        )

        print("\n STARTING TRADING SESSION...")
        print("=" * 60 + "\n")

        result = crew.kickoff()
        return result


if __name__ == "__main__":
    if not os.getenv("GOOGLE_API_KEY"):
        print(" GOOGLE_API_KEY mancante nell'ambiente.")
    else:
        context = {
            "date": "2024-05-24",
            "market_status": "OPEN",
            "strategy": "Mean Reversion Pairs Trading"
        }

        trading_system = TradingCrew(market_data=context)
        final_result = trading_system.run()

        print("\n\n########################")
        print("## FINAL TRADING LOG  ##")
        print("########################\n")
        print(final_result)
