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
                         Agents will use tools to fetch actual prices.
        """
        self.market_data = market_data if market_data else {}
        
        self.agents_blueprint = TradingAgents()
        self.tasks_blueprint = TradingTasks()
        
        # LLM for the Manager (Portfolio Coordinator) logic during delegation
        self.manager_llm = LLM(
            model="gemini/gemini-2.5-flash",
            temperature=0.1,
            api_key=os.getenv("GOOGLE_API_KEY")
        )

    def run(self):
        print("\n" + "="*50)
        print("🤖 ASSEMBLING THE TRADING CREW")
        print("="*50)

        # ---------------------------------------------------------------------
        # STEP 1: INSTANTIATE AGENTS (WITH TOOLS INJECTED)
        # ---------------------------------------------------------------------
        # We pull the specific tool lists from TOOLS_REGISTRY for each role.
        
        # 1. Portfolio Coordinator (Manager)
        coordinator = self.agents_blueprint.portfolio_coordinator(
            tools=TOOLS_REGISTRY['portfolio_coordinator']
        )
        print(f"✅ Portfolio Coordinator ready ({len(TOOLS_REGISTRY['portfolio_coordinator'])} tools)")

        # 2. Pair Monitor: NEE/CWEN (Specialist)
        monitor_nee = self.agents_blueprint.monitor_nee_cwen(
            tools=TOOLS_REGISTRY['pair_monitor']
        )
        
        # 3. Pair Monitor: RUN/PBW (Specialist)
        monitor_run = self.agents_blueprint.monitor_run_pbw(
            tools=TOOLS_REGISTRY['pair_monitor']
        )
        
        # 4. Pair Monitor: PLUG/RUN (Specialist)
        monitor_plug = self.agents_blueprint.monitor_plug_run(
            tools=TOOLS_REGISTRY['pair_monitor']
        )
        print(f"✅ 3 Pair Monitors ready ({len(TOOLS_REGISTRY['pair_monitor'])} tools each)")

        # 5. Risk Manager
        risk_manager = self.agents_blueprint.risk_manager(
            tools=TOOLS_REGISTRY['risk_manager']
        )
        print(f"✅ Risk Manager ready ({len(TOOLS_REGISTRY['risk_manager'])} tools)")

        # 6. Execution Agent
        executor = self.agents_blueprint.execution_agent(
            tools=TOOLS_REGISTRY['execution']
        )
        print(f"✅ Execution Agent ready ({len(TOOLS_REGISTRY['execution'])} tools)")


        # ---------------------------------------------------------------------
        # STEP 2: DEFINE TASKS
        # ---------------------------------------------------------------------
        # We pass the instantiated agents to their specific tasks.
        
        print("\n📋 Assigning Tasks...")

        # Tasks 1-3: Analysis (Parallel-ish)
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

        # Task 4: Risk Assessment (Must happen after analysis)
        task_risk = self.tasks_blueprint.risk_assessment_task(
            agent=risk_manager,
            context_tasks=[task_nee, task_run, task_plug]
        )

        # Task 5: Allocation (Must happen after risk approval)
        task_allocation = self.tasks_blueprint.allocation_task(
            agent=coordinator,
            context_tasks=[task_risk]
        )

        # Task 6: Execution (Must happen after allocation)
        task_execution = self.tasks_blueprint.execution_task(
            agent=executor,
            context_tasks=[task_allocation]
        )


        # ---------------------------------------------------------------------
        # STEP 3: DEFINE CREW
        # ---------------------------------------------------------------------
        
        crew = Crew(
            agents=[
                monitor_nee,
                monitor_run,
                monitor_plug,
                risk_manager,
                coordinator,
                executor
            ],
            tasks=[
                task_nee,
                task_run,
                task_plug,
                task_risk,
                task_allocation,
                task_execution
            ],
            # We use Sequential to ensure the data flows logically:
            # Monitors -> Risk -> Coordinator -> Execution
            process=Process.sequential,
            verbose=True
        )

        print("\n🚀 STARTING TRADING SESSION...")
        print("="*50 + "\n")
        
        return crew.kickoff()

# ---------------------------------------------------------------------
# EXECUTION BLOCK (Run this file directly to test)
# ---------------------------------------------------------------------
if __name__ == "__main__":
    # Check for API Key
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ ERROR: GOOGLE_API_KEY not found in environment.")
        print("Run: export GOOGLE_API_KEY='your_key'")
    else:
        # Define context (Agents will fetch real prices via tools, this is just metadata)
        context = {
            "date": "2024-05-24",
            "market_status": "OPEN",
            "strategy": "Mean Reversion Pairs Trading"
        }
        
        # Initialize and Run
        trading_system = TradingCrew(market_data=context)
        result = trading_system.run()
        
        print("\n\n########################")
        print("## FINAL TRADING LOG  ##")
        print("########################\n")
        print(result)