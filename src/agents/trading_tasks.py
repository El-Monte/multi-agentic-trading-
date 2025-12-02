from crewai import Task

class TradingTasks:
    def analysis_task(self, agent, pair_name, context_data=None):
        # We split the pair name (e.g., "NEE/CWEN") so the agent knows which tickers to feed the tool
        try:
            leg1, leg2 = pair_name.split('/')
        except ValueError:
            leg1, leg2 = "Unknown", "Unknown"

        return Task(
            description=(
                f"Analyze the {pair_name} trading pair. "
                f"Context: {context_data}. "
                f"1. USE THE TOOL 'Calculate Spread and Z-Score' with ticker_leg1='{leg1}' and ticker_leg2='{leg2}' (hedge_ratio=0.94). "
                f"2. Based on the Z-score returned, USE THE TOOL 'Generate Trade Signal'. "
                "3. Return a report specifying: Signal (OPEN_LONG / OPEN_SHORT / HOLD), Z-Score, and Confidence."
            ),
            expected_output=f"Analysis Report for {pair_name} with Z-score and Signal.",
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