import os
import sys
from crewai import Crew, Process, LLM

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.agents.trading_agents import TradingAgents
from src.agents.trading_tasks import TradingTasks
from src.integration.tools_registry import TOOLS_REGISTRY

class TradingCrew:
    def __init__(self, market_data=None):
        """
        Initialize the Crew.
        args:
            market_data: Optional dict for context (e.g., date, market status).
        """
        self.market_data = market_data if market_data else {}
        
        self.agents_blueprint = TradingAgents()
        self.tasks_blueprint = TradingTasks()
        
        self.manager_llm = LLM(
            model="gemini/gemini-2.5-flash",
            temperature=0.1,
            api_key=os.getenv("GOOGLE_API_KEY")
        )

    def run(self):
        print("\n" + "="*50)
        print("🤖 ASSEMBLING THE TRADING CREW (UTILITY SECTOR)")
        print("="*50)
        
        # --- 1. INSTANTIATE AGENTS ---
        
        # Portfolio Coordinator
        coordinator = self.agents_blueprint.portfolio_coordinator(
            tools=TOOLS_REGISTRY['portfolio_coordinator']
        )
        print(f"✅ Portfolio Coordinator ready")

        # Monitor 1: ETR/AEP (Entergy / American Electric Power)
        monitor_etr_aep = self.agents_blueprint.monitor_etr_aep(
            tools=TOOLS_REGISTRY['pair_monitor']
        )
        
        # Monitor 2: AEP/ATO (American Electric Power / Atmos Energy)
        monitor_aep_ato = self.agents_blueprint.monitor_aep_ato(
            tools=TOOLS_REGISTRY['pair_monitor']
        )
        
        # Monitor 3: ETR/ATO (Entergy / Atmos Energy)
        monitor_etr_ato = self.agents_blueprint.monitor_etr_ato(
            tools=TOOLS_REGISTRY['pair_monitor']
        )
        print(f"✅ 3 Utility Pair Monitors ready")

        # Risk Manager
        risk_manager = self.agents_blueprint.risk_manager(
            tools=TOOLS_REGISTRY['risk_manager']
        )
        print(f"✅ Risk Manager ready")

        # Execution Agent
        executor = self.agents_blueprint.execution_agent(
            tools=TOOLS_REGISTRY['execution']
        )
        print(f"✅ Execution Agent ready")


        # --- 2. DEFINE TASKS ---
        print("\n📋 Assigning Tasks...")

        # Task 1: Analyze ETR/AEP
        task_1 = self.tasks_blueprint.analysis_task(
            agent=monitor_etr_aep, 
            pair_name="ETR/AEP", 
            context_data=self.market_data
        )
        
        # Task 2: Analyze AEP/ATO
        task_2 = self.tasks_blueprint.analysis_task(
            agent=monitor_aep_ato, 
            pair_name="AEP/ATO", 
            context_data=self.market_data
        )
        
        # Task 3: Analyze ETR/ATO
        task_3 = self.tasks_blueprint.analysis_task(
            agent=monitor_etr_ato, 
            pair_name="ETR/ATO", 
            context_data=self.market_data
        )

        # Task 4: Risk Assessment (Must happen after monitors)
        task_risk = self.tasks_blueprint.risk_assessment_task(
            agent=risk_manager,
            context_tasks=[task_1, task_2, task_3]
        )

        # Task 5: Allocation
        task_allocation = self.tasks_blueprint.allocation_task(
            agent=coordinator,
            context_tasks=[task_risk]
        )

        # Task 6: Execution
        task_execution = self.tasks_blueprint.execution_task(
            agent=executor,
            context_tasks=[task_allocation]
        )


        # --- 3. DEFINE CREW ---
        crew = Crew(
            agents=[
                monitor_etr_aep,
                monitor_aep_ato,
                monitor_etr_ato,
                risk_manager,
                coordinator,
                executor
            ],
            tasks=[
                task_1,
                task_2,
                task_3,
                task_risk,
                task_allocation,
                task_execution
            ],
            process=Process.sequential,
            verbose=True
        )

        print("\n🚀 STARTING TRADING SESSION...")
        print("="*50 + "\n")
        
        return crew.kickoff()

if __name__ == "__main__":
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ ERROR: GOOGLE_API_KEY not found. Please export it.")
    else:
        context = {
            "date": "2024-05-24",
            "market_status": "OPEN",
            "strategy": "Mean Reversion Pairs Trading (Utilities)"
        }
        
        trading_system = TradingCrew(market_data=context)
        result = trading_system.run()
        
        print("\n\n########################")
        print("## FINAL TRADING LOG  ##")
        print("########################\n")
        print(result)