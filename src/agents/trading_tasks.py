from crewai import Task

class TradingTasks:
    def analysis_task(self, agent, pair_name, context_data=None):
        try:
            leg1, leg2 = pair_name.split('/')
        except ValueError:
            leg1, leg2 = "Unknown", "Unknown"

        return Task(
            description=(
                f"Analyze the {pair_name} trading pair. "
                f"Context: {context_data}. "
                f"1. USE 'Calculate Spread and Z-Score' for {leg1} and {leg2} with lookback_window=20.. "
                f"2. USE 'Analyze Reddit Sentiment' for {leg1}. This will run a FinBERT model on raw data. " 
                f"3. USE 'Generate Trade Signal' based on the Z-score. "
                "4. SYNTHESIS: If Z-score suggests SHORT but Sentiment is BULLISH, downgrade the confidence. "
                "5. Return report with Signal, Z-Score, Sentiment Score, and Final Confidence."
            ),
            expected_output=f"Analysis Report for {pair_name} including Z-score, Sentiment, and Signal.",
            agent=agent
        )

    def risk_assessment_task(self, agent, context_tasks):
        return Task(
            description=(
                "Review the analysis reports from the pair monitors. "
                "1. If there are no 'OPEN' signals, report 'NO TRADES'. "
                "2. If there are signals, USE THE TOOL 'Check Risk Limits' to ensure leverage is safe. "
                "3. USE THE TOOL 'Check Portfolio Correlation' to ensure we aren't too concentrated. "
                "4. Output a list of APPROVED signals."
            ),
            expected_output="Risk Report listing approved trades vs rejected trades.",
            agent=agent,
            context=context_tasks
        )

    def allocation_task(self, agent, context_tasks):
        return Task(
            description=(
                "Review the Approved Signals from the Risk Manager. "
                "1. If no trades are approved, stop. "
                "2. For approved trades, USE THE TOOL 'Calculate Position Size' (total_capital=100000). "
                "3. Output the final 'Target Allocation' (exact dollar amount) for each pair."
            ),
            expected_output="Capital Allocation Order with specific dollar amounts.",
            agent=agent,
            context=context_tasks
        )

    def execution_task(self, agent, context_tasks):
        return Task(
            description=(
                "Review the Allocation Order. "
                "1. If no allocation, output 'No Trades Executed'. "
                "2. Otherwise, USE THE TOOL 'Execute Pairs Trade' for each allocated trade. "
                "3. Report the final execution confirmation."
            ),
            expected_output="Execution Log confirming filled orders.",
            agent=agent,
            context=context_tasks
        )
