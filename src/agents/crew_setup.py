import os
import sys
from crewai import Crew, Process, LLM
from langchain_google_genai import ChatGoogleGenerativeAI

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.agents.trading_agents import TradingAgents
from src.agents.trading_tasks import TradingTasks

class TradingCrew:
    def __init__(self, market_data=None):
        self.market_data = market_data if market_data else {}
        
        self.agents = TradingAgents()
        self.tasks = TradingTasks()
        
        self.manager_llm = LLM(
            model="gemini/gemini-2.5-flash",
            temperature=0.1, 
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )

    def run(self):
        # Agents
        coordinator = self.agents.portfolio_coordinator()
        monitor_nee = self.agents.monitor_nee_cwen()
        monitor_run = self.agents.monitor_run_pbw()
        monitor_plug = self.agents.monitor_plug_run()
        risk_manager = self.agents.risk_manager()
        executor = self.agents.execution_agent()

        # --- Tasks ---

        # 1. Analysis Tasks
        task_nee = self.tasks.analysis_task(
            agent=monitor_nee, 
            pair_name="NEE/CWEN", 
            context_data=self.market_data 
        )

        task_run = self.tasks.analysis_task(
            agent=monitor_run, 
            pair_name="RUN/PBW", 
            context_data=self.market_data
        )

        task_plug = self.tasks.analysis_task(
            agent=monitor_plug, 
            pair_name="PLUG/RUN", 
            context_data=self.market_data
        )

        # 2. Risk Assessment (Needs to see the output of the analysis tasks)
        task_risk = self.tasks.risk_assessment_task(
            agent=risk_manager,
            context_tasks=[task_nee, task_run, task_plug] # CrewAI context
        )

        # 3. Allocation (Needs to see the Risk decision)
        task_allocation = self.tasks.allocation_task(
            agent=coordinator,
            context_tasks=[task_risk]
        )

        # 4. Execution (Needs to see the Allocation order)
        task_execution = self.tasks.execution_task(
            agent=executor,
            context_tasks=[task_allocation]
        )

        # --- Crew ---
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
            process=Process.sequential,
            verbose=True
        )

        # Kickoff
        print(f"## Starting Crew with inputs: {self.market_data} ##")
        result = crew.kickoff() 
        return result

if __name__ == "__main__":
    dummy_data = {
        "date": "2024-05-20", 
        "market_status": "OPEN",
        "NEE_price": 75.50, "CWEN_price": 28.10,
        "RUN_price": 12.40, "PBW_price": 24.00,
        "PLUG_price": 3.10
    }
    
    trading_system = TradingCrew(market_data=dummy_data)
    result = trading_system.run()
    
    print("\n\n########################")
    print("## TRADING DAY RESULT ##")
    print("########################\n")
    print(result)