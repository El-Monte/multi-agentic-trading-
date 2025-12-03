from crewai import Task

class TradingTasks:
    def __init__(self):
        pass

    def analysis_task(self, agent, pair_name: str, context_data=None) -> Task:
        """
        Task for Pair Monitor agents (NEE/CWEN, RUN/PBW, PLUG/RUN).

        - Fa capire all'agente QUALI tool usare
        - Gli dice quali ticker passare
        - Gli ricorda di NON inventare i dati
        """

        # 1. Ricaviamo i due ticker dal nome della coppia
        try:
            leg1, leg2 = pair_name.split("/")
        except ValueError:
            leg1, leg2 = "UNKNOWN1", "UNKNOWN2"

        # 2. Hedge ratio per ogni coppia (dai tuoi risultati Day 1)
        hedge_map = {
            "NEE/CWEN": 0.948,
            "RUN/PBW": 0.940,
            "PLUG/RUN": 0.872,
        }
        hedge_ratio = hedge_map.get(pair_name, 1.0)

        description = f"""
You are the specialist monitor for the pair {pair_name}.

Market context (do NOT use as price source, tools will fetch real data):
{context_data}

Your job is to use ONLY your tools to decide if there is a mean-reversion opportunity.

STEP 1 – Call the tool "Calculate Spread and Z-Score"
- Use these parameters:
  - ticker_leg1 = "{leg1}"
  - ticker_leg2 = "{leg2}"
  - hedge_ratio = {hedge_ratio}
  - lookback_window = 20

This tool will return at least:
- z_score
- spread
- leg1_price
- leg2_price
- rolling_mean
- rolling_std

STEP 2 – Read the z_score from the tool output.

STEP 3 – Call the tool "Generate Trade Signal"
- Use this parameter:
  - z_score = <the z_score returned in STEP 1>

This tool will return:
- signal  (OPEN_LONG, OPEN_SHORT, CLOSE, HOLD)
- confidence  (0.0 – 1.0)
- reason
- parameters

STEP 4 – Based ONLY on these tool outputs, prepare a short report:
- Pair: {pair_name}
- z_score
- signal
- confidence
- Whether you suggest trading the spread now or staying flat.

IMPORTANT RULES:
- Do NOT invent prices or z-scores.
- Do NOT use news, sentiment or rumors.
- You MUST base your reasoning only on the tool outputs.
        """

        expected_output = f"""
Structured analysis report for {pair_name}, including:
- z_score (numeric)
- signal (OPEN_LONG / OPEN_SHORT / CLOSE / HOLD)
- confidence (0.0 – 1.0)
- 3–5 sentences of reasoning based ONLY on tool outputs.
        """

        return Task(
            description=description,
            expected_output=expected_output,
            agent=agent
        )

    def risk_assessment_task(self, agent, context_tasks) -> Task:
        """
        Task per il Risk Manager.
        Usa i report dei monitor come contesto.
        """
        description = """
You are the Risk Manager.

You receive the analysis reports from the three Pair Monitors as context.
Your job is to decide which signals are acceptable from a RISK perspective.

STEP 1 – Read all analysis reports in context.
Identify any signals that are:
- OPEN_LONG
- OPEN_SHORT

If there are NO open-type signals, output:
- status = "NO_TRADES"
- reason = "No monitor generated trade entries."

STEP 2 – For each proposed trade:
Use your risk tools where appropriate:

- Call "Check Risk Limits" to ensure leverage stays below the limit.
  You may assume:
    - total_capital = 100000
    - current_positions_value = 50000 (approximation for this demo)
    - new_trade_value = 10000 for each new trade proposal

- Optionally call "Check Portfolio Correlation"
  if multiple trades involve highly related tickers.

- Optionally call "Check Volatility Regime" for the pair
  to ensure we are not in a HIGH_VOL regime.

STEP 3 – For each trade proposal, decide:
- APPROVED  or  REJECTED
and explain WHY.

Your output MUST be structured:
- approved_trades: list of trades with pair, action, and notes
- rejected_trades: list with reasons
- high_level_comment: short summary of portfolio risk.
        """

        expected_output = """
Risk Report JSON-like structure, for example:
{
  "approved_trades": [
    {"pair": "NEE/CWEN", "action": "OPEN_LONG", "reason": "..."}
  ],
  "rejected_trades": [
    {"pair": "PLUG/RUN", "action": "OPEN_SHORT", "reason": "Too high correlation / volatility"}
  ],
  "high_level_comment": "Short summary of leverage and concentration."
}
        """

        return Task(
            description=description,
            expected_output=expected_output,
            agent=agent,
            context=context_tasks
        )

    def allocation_task(self, agent, context_tasks) -> Task:
        """
        Task per il Portfolio Coordinator.
        Decide quanto capitale allocare ai trade APPROVATI.
        """
        description = """
You are the Portfolio Coordinator (CIO).

You receive the Risk Report from the Risk Manager (context).
Your job is to translate APPROVED trades into position sizes.

STEP 1 – Read the Risk Report from context.
If there are no approved trades:
- Output an empty allocation list and a message "NO_ALLOCATIONS".

STEP 2 – For each approved trade:
Call the tool "Calculate Position Size" with:
- total_capital = 100000
- confidence_score = use the confidence reported by the Pair Monitor,
  or if not available, assume 0.6 for strong signals, 0.3 for weaker ones.
- max_allocation_pct = 0.20 (20% max per pair)

STEP 3 – Build a final "Target Allocation" list, for example:
[
  {"pair": "NEE/CWEN", "action": "OPEN_LONG", "allocation_amount": 16000},
  {"pair": "RUN/PBW", "action": "OPEN_SHORT", "allocation_amount": 8000}
]

Ensure the sum of allocation_amount does NOT exceed total_capital (100000).
If it does, scale them down proportionally and mention it in the comments.

Your output MUST be a clear, structured allocation plan.
        """

        expected_output = """
Target Allocation object, for example:
{
  "allocations": [
    {"pair": "NEE/CWEN", "action": "OPEN_LONG", "allocation_amount": 16000},
    {"pair": "RUN/PBW", "action": "OPEN_SHORT", "allocation_amount": 8000}
  ],
  "comment": "Total allocation = 24,000 < 100,000 capital. Within limits."
}
        """

        return Task(
            description=description,
            expected_output=expected_output,
            agent=agent,
            context=context_tasks
        )

    def execution_task(self, agent, context_tasks) -> Task:
        """
        Task per l'Execution Agent.
        Prende il piano di allocazione e simula le esecuzioni.
        """
        description = """
You are the Execution Trader.

You receive the Target Allocation from the Portfolio Coordinator as context.

STEP 1 – Read the allocation plan.
If there are no allocations or an explicit "NO_ALLOCATIONS" status:
- Output: "No Trades Executed" and stop.

STEP 2 – For each allocation entry:
You MUST call the tool "Execute Pairs Trade" with:
- ticker_leg1: the first ticker of the pair (e.g. "NEE")
- ticker_leg2: the second ticker of the pair (e.g. "CWEN")
- action: map
    - OPEN_LONG  -> "LONG_SPREAD"
    - OPEN_SHORT -> "SHORT_SPREAD"
- total_value: the allocation_amount from the plan
- hedge_ratio: use the known beta for that pair (e.g. 0.948 for NEE/CWEN)

STEP 3 – Collect the tool outputs and build an Execution Log:
- pair
- action
- leg1: ticker, side, shares, avg_fill
- leg2: ticker, side, shares, avg_fill
- total_value_executed

Return a structured execution report.
        """

        expected_output = """
Execution Log example:
{
  "executions": [
    {
      "pair": "NEE/CWEN",
      "action": "OPEN_LONG",
      "leg1": {"ticker": "NEE", "side": "BUY", "shares": 123.45, "avg_fill": 75.32},
      "leg2": {"ticker": "CWEN", "side": "SELL", "shares": 410.12, "avg_fill": 28.05},
      "total_value_executed": 16000
    }
  ],
  "comment": "All trades simulated with 10 bps slippage."
}
        """

        return Task(
            description=description,
            expected_output=expected_output,
            agent=agent,
            context=context_tasks
        )
