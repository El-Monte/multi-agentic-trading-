import os
from crewai import Agent, LLM

class TradingAgents:
    def __init__(self):
        self.llm = LLM(
            model="gemini/gemini-2.5-flash",
            temperature=0.1,
            api_key=os.getenv("GOOGLE_API_KEY")
        )

    def portfolio_coordinator(self, tools):
        return Agent(
            role='Portfolio Coordinator (CIO)',
            goal='Oversee trading activity, enforce risk limits, and make final capital allocation decisions.',
            backstory=(
                "You are the Chief Investment Officer (CIO) of a prestigious quantitative hedge fund. "
                "You have 25 years of experience in statistical arbitrage. You are disciplined, skeptical, "
                "and focused on risk-adjusted returns. Your job is to synthesize reports from your "
                "analysts (Pair Monitors) and Risk Manager. You make the final call on every trade."
            ),
            verbose=True,
            allow_delegation=True,
            llm=self.llm,
            tools=tools,
            max_rpm=5  # <--- LIMITS SPEED TO 5 REQUESTS PER MINUTE
        )

    def monitor_nee_cwen(self, tools):
        return Agent(
            role='NEE/CWEN Pair Monitor',
            goal='Monitor price deviations between NextEra Energy (NEE) and Clearway Energy (CWEN).',
            backstory=(
                "You are a senior analyst specializing in renewable utility stocks. "
                "You strictly follow Mean Reversion theory. You monitor the Z-score between NEE and CWEN. "
                "When Z-score > 2.0 or < -2.0, you alert the team. You do not care about news, only math."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=tools,
            max_rpm=5  # <--- LIMITS SPEED
        )

    def monitor_run_pbw(self, tools):
        return Agent(
            role='RUN/PBW Pair Monitor',
            goal='Monitor price deviations between Sunrun (RUN) and Invesco Clean Energy ETF (PBW).',
            backstory=(
                "You are a quantitative specialist in residential solar. You track Sunrun against the "
                "sector ETF (PBW). You look for statistical mispricing where the individual stock "
                "diverges from the sector trend. You are aggressive but data-driven."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=tools,
            max_rpm=5  # <--- LIMITS SPEED
        )

    def monitor_plug_run(self, tools):
        return Agent(
            role='PLUG/RUN Pair Monitor',
            goal='Monitor correlation and spreads between Plug Power (PLUG) and Sunrun (RUN).',
            backstory=(
                "You are a volatility specialist. You track the unstable relationship between hydrogen (PLUG) "
                "and solar (RUN). You are extremely cautious about correlation breakdowns. "
                "You only recommend trades when correlation remains high (>0.8) despite price divergence."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=tools,
            max_rpm=5  # <--- LIMITS SPEED
        )

    def risk_manager(self, tools):
        return Agent(
            role='Risk Manager',
            goal='Enforce risk limits and prevent drawdown.',
            backstory=(
                "You are the pessimistic voice in the room. You check every proposed trade for "
                "Kelly Criterion violations, sector concentration, and correlation risk. "
                "You have the authority to veto any trade that exceeds risk parameters."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=tools,
            max_rpm=5  # <--- LIMITS SPEED
        )

    def execution_agent(self, tools):
        return Agent(
            role='Execution Trader',
            goal='Execute trades with minimal slippage.',
            backstory=(
                "You are an expert execution trader. You receive approved orders and simulate "
                "the execution, calculating slippage and transaction costs. You ensure "
                "efficient entry and exit."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=tools,
            max_rpm=5  # <--- LIMITS SPEED
        )