from crewai import Task

class TradingTasks:
    def __init__(self):
        pass

    def analysis_task(self, agent, pair_name, tickers):
        """
        Task for the Specialist Monitors (Agents 2, 3, 4).
        It tells them to look at data and decide on a signal.
        """
        return Task(
            description=f"""
                1. Analyze the current market data for the pair: {pair_name} ({tickers}).
                2. Use your tools to fetch the current Z-Score and spread.
                3. Compare the Z-Score against the threshold (+/- 2.5).
                4. Check for any breaking news affecting these specific companies.
                5. Determine the signal:
                   - 'LONG_SPREAD' if Z-Score < -2.5
                   - 'SHORT_SPREAD' if Z-Score > +2.5
                   - 'EXIT' if Z-Score crosses 0
                   - 'HOLD' otherwise.
                
                You must be precise. Do not hallucinate data. Use the tools provided.
            """,
            agent=agent,
            expected_output="""
                A detailed report containing:
                - Current Z-Scores
                - The suggested SIGNAL (LONG_SPREAD, SHORT_SPREAD, EXIT, HOLD)
                - A brief reasoning paragraph explaining why based on the data.
            """
        )

    def risk_assessment_task(self, agent, proposed_trades):
        """
        Task for the Risk Manager (Agent 5).
        It reviews the signals from the monitors.
        """
        return Task(
            description=f"""
                1. Review the proposed trading signals from the Pair Monitors: {proposed_trades}
                2. Calculate the correlation impact on the total portfolio.
                3. Check if any position size limits would be violated.
                4. If a trade is too risky, change the signal to 'REJECTED'.
                5. If acceptable, approve the trade.
            """,
            agent=agent,
            expected_output="""
                A Risk Assessment Report:
                - List of Approved Trades
                - List of Rejected Trades (with reasons)
                - Final Risk Score of the portfolio (0-100)
            """
        )

    def allocation_task(self, agent, risk_report):
        """
        Task for the Portfolio Coordinator (Agent 1).
        Decides how much money to put in each approved trade.
        """
        return Task(
            description=f"""
                1. Review the Risk Assessment Report: {risk_report}
                2. For approved trades, calculate the optimal position size using the Kelly Criterion.
                3. Ensure the total capital allocated does not exceed 100%.
                4. Create the final execution orders.
            """,
            agent=agent,
            expected_output="""
                Final Order List (JSON format preferred for Execution Agent):
                [
                    {"pair": "NEE/CWEN", "action": "BUY", "amount": 10000},
                    ...
                ]
            """
        )

    def execution_task(self, agent, final_orders):
        """
        Task for the Execution Agent (Agent 6).
        Simulates the actual buying/selling.
        """
        return Task(
            description=f"""
                1. Read the Final Order List: {final_orders}
                2. For each order, simulate the execution using your tools.
                3. Calculate estimated slippage and fees.
                4. confirm the final execution prices.
            """,
            agent=agent,
            expected_output="""
                Execution Log:
                - Trade ID
                - Ticker
                - Fill Price
                - Timestamp
                - Status (FILLED/PARTIAL/FAILED)
            """
        )