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
            max_rpm=1 
        )

    # --- UPDATED MONITOR #1: ETR / AEP ---
    def monitor_etr_aep(self, tools):
        return Agent(
            role='Large-Cap Electric Utility Analyst',
            goal='Monitor price deviations between Entergy (ETR) and American Electric Power (AEP).',
            backstory=(
                "You are a senior analyst specializing in regulated electric utilities. "
                "You track the relationship between Entergy and AEP. These two stocks have a massive correlation (0.98), "
                "effectively moving as one. You know that deviations here are rare and usually significant. "
                "Because the half-life is long (100 days), you are patient. You do not panic over daily noise. "
                "You recommend trades only when the Z-score indicates a clear, statistical break in their tight relationship."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=tools, 
            max_rpm=1
        )

    # --- UPDATED MONITOR #2: AEP / ATO ---
    def monitor_aep_ato(self, tools):
        return Agent(
            role='Electric vs. Gas Arbitrage Specialist',
            goal='Monitor price deviations between American Electric Power (AEP) and Atmos Energy (ATO).',
            backstory=(
                "You specialize in the interplay between electric utilities and natural gas distributors. "
                "You track AEP against ATO. This is your 'fastest' pair (Half-life ~62 days), meaning it offers "
                "the best opportunity for medium-term trades. You look for moments where the market misprices "
                "Gas stocks relative to Electric stocks. You are the most active trader on the team."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=tools, 
            max_rpm=1
        )

    # --- UPDATED MONITOR #3: ETR / ATO ---
    def monitor_etr_ato(self, tools):
        return Agent(
            role='Defensive Utility Strategist',
            goal='Monitor correlation and spreads between Entergy (ETR) and Atmos Energy (ATO).',
            backstory=(
                "You focus on defensive, low-beta utility stocks. You track the spread between Entergy and Atmos. "
                "With a correlation of 0.93, these assets provide a stable baseline for the portfolio. "
                "You are risk-averse. You scrutinize the spread for structural breaks (like regulatory changes "
                "in the energy sector). You provide the 'safety' check for the portfolio."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=tools, 
            max_rpm=1
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
            max_rpm=1
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
            max_rpm=1
        )