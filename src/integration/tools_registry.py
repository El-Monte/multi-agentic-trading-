"""
Central registry mapping Team B's tools to Team A's agents.
Maps only the tools that Team B actually implemented.
"""
import sys
import os
from src.tools.sentiment_tools import analyze_social_sentiment

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.signal_tools import (
    calculate_spread_and_zscore,
    generate_trade_signal
)

from tools.risk_tools import (
    check_correlation,
    check_volatility_regime
)

from tools.allocation_tools import (
    calculate_position_size,
    calculate_kelly_allocation
)

from tools.execution_tools import (
    execute_pairs_trade
)


# TOOL

# Pair Monitor Agents 
PAIR_MONITOR_TOOLS = [
    calculate_spread_and_zscore, 
    generate_trade_signal, 
    analyze_social_sentiment       
]

# Risk Manager Agent
RISK_MANAGER_TOOLS = [
    check_correlation,           
    check_volatility_regime       
]

# Portfolio Coordinator Agent 
PORTFOLIO_COORDINATOR_TOOLS = [
    calculate_kelly_allocation,    
    calculate_position_size,       
    check_correlation              
]

# Execution Agent
EXECUTION_AGENT_TOOLS = [
    execute_pairs_trade            
]


TOOLS_REGISTRY = {
    'pair_monitor': PAIR_MONITOR_TOOLS,
    'risk_manager': RISK_MANAGER_TOOLS,
    'portfolio_coordinator': PORTFOLIO_COORDINATOR_TOOLS,
    'execution': EXECUTION_AGENT_TOOLS
}



def get_tool_name(tool):
    """
    Get the name of a tool regardless of whether it's a function or CrewAI Tool object.
    
    Args:
        tool: Either a regular function or a CrewAI Tool object
    
    Returns:
        String name of the tool
    """
    if hasattr(tool, 'name'):
        return tool.name
    elif hasattr(tool, '__name__'):
        return tool.__name__
    else:
        return str(tool)


# Validation function

def validate_tools_available() -> bool:
    """
    Test that all tools are importable and callable.
    
    Returns:
        True if all tools work, False if any fail
    """
    print("\n" + "="*70)
    print("🔍 VALIDATING TEAM B TOOLS")
    print("="*70 + "\n")
    
    all_tools = (
        PAIR_MONITOR_TOOLS +
        RISK_MANAGER_TOOLS +
        PORTFOLIO_COORDINATOR_TOOLS +
        EXECUTION_AGENT_TOOLS
    )
    
    all_valid = True
    tool_count = 0
    
    for tool in all_tools:
        tool_count += 1
        tool_name = get_tool_name(tool)
        
        try:
            if hasattr(tool, 'name'):
                print(f"{tool_name} (CrewAI Tool)")
            elif callable(tool):
                print(f" {tool_name} (Python function)")
            else:
                print(f" {tool_name}: Not callable")
                all_valid = False
            
        except Exception as e:
            print(f"{tool_name}: Error - {e}")
            all_valid = False
    
    print("\n" + "="*70)
    print(f" VALIDATION RESULTS")
    print("="*70)
    print(f"Total tools checked: {tool_count}")
    print(f"Status: {' ALL PASSED' if all_valid else ' SOME FAILED'}")
    print("="*70 + "\n")
    
    return all_valid


def print_tool_summary():
    """Print summary of available tools for each agent."""
    print("\n" + "="*70)
    print(" TOOL ASSIGNMENTS SUMMARY")
    print("="*70 + "\n")
    
    for agent_type, tools in TOOLS_REGISTRY.items():
        agent_name = agent_type.upper().replace('_', ' ')
        print(f"🤖 {agent_name}:")
        for tool in tools:
            tool_name = get_tool_name(tool)
            print(f"   • {tool_name}")
        print()
    
    print("="*70 + "\n")



if __name__ == "__main__":
    print_tool_summary()
    
    if validate_tools_available():
        print(" Integration ready!")
        print(" All Team B tools are available for Team A agents")
        print(f"\n Tool count by agent:")
        print(f"   Pair Monitors: {len(PAIR_MONITOR_TOOLS)} tools")
        print(f"   Risk Manager: {len(RISK_MANAGER_TOOLS)} tools")
        print(f"   Portfolio Coordinator: {len(PORTFOLIO_COORDINATOR_TOOLS)} tools")
        print(f"   Execution Agent: {len(EXECUTION_AGENT_TOOLS)} tools")
        print(f"   Total: {len(PAIR_MONITOR_TOOLS + RISK_MANAGER_TOOLS + PORTFOLIO_COORDINATOR_TOOLS + EXECUTION_AGENT_TOOLS)} tools")
        print("\n Next step: Update src/agents/crew_setup.py")
        print("   Import: from src.integration.tools_registry import TOOLS_REGISTRY\n")
    else:
        print(" Some tools failed validation")
        print("Fix the issues above before proceeding\n")