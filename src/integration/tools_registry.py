"""
Central registry mapping Team B's tools to Team A's agents.
Maps only the tools that Team B actually implemented.
"""
import sys
import os

# Path Setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ============================================================================
# IMPORT TEAM B'S TOOLS (Only what actually exists)
# ============================================================================

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


# ============================================================================
# TOOL ASSIGNMENTS FOR EACH AGENT
# ============================================================================

# Pair Monitor Agents (NEE/CWEN, RUN/PBW, PLUG/RUN)
# Job: Analyze pairs and generate trade signals
PAIR_MONITOR_TOOLS = [
    calculate_spread_and_zscore,  # Calculate spread Z-score
    generate_trade_signal          # Generate LONG/SHORT/FLAT signal
]

# Risk Manager Agent
# Job: Check portfolio-level risk constraints
RISK_MANAGER_TOOLS = [
    check_correlation,             # Check if positions are too correlated
    check_volatility_regime        # Check if market volatility is too high
]

# Portfolio Coordinator Agent (Manager)
# Job: Allocate capital across multiple signals
PORTFOLIO_COORDINATOR_TOOLS = [
    calculate_kelly_allocation,    # Kelly Criterion sizing
    calculate_position_size,       # Convert to dollar amounts
    check_correlation              # Check correlation for allocation decisions
]

# Execution Agent
# Job: Execute trades with slippage modeling
EXECUTION_AGENT_TOOLS = [
    execute_pairs_trade            # Execute both legs of spread trade
]


# ============================================================================
# MASTER REGISTRY
# ============================================================================

TOOLS_REGISTRY = {
    'pair_monitor': PAIR_MONITOR_TOOLS,
    'risk_manager': RISK_MANAGER_TOOLS,
    'portfolio_coordinator': PORTFOLIO_COORDINATOR_TOOLS,
    'execution': EXECUTION_AGENT_TOOLS
}


# ============================================================================
# HELPER FUNCTION: Get tool name (handles both regular functions and @tool decorated)
# ============================================================================

def get_tool_name(tool):
    """
    Get the name of a tool regardless of whether it's a function or CrewAI Tool object.
    
    Args:
        tool: Either a regular function or a CrewAI Tool object
    
    Returns:
        String name of the tool
    """
    # Try to get name from CrewAI Tool object first
    if hasattr(tool, 'name'):
        return tool.name
    # Fall back to function __name__
    elif hasattr(tool, '__name__'):
        return tool.__name__
    # Last resort: convert to string
    else:
        return str(tool)


# ============================================================================
# VALIDATION FUNCTION
# ============================================================================

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
            # Check if it's a CrewAI Tool object or regular function
            if hasattr(tool, 'name'):
                # It's a CrewAI Tool (has @tool decorator)
                print(f"✅ {tool_name} (CrewAI Tool)")
            elif callable(tool):
                # It's a regular Python function
                print(f"✅ {tool_name} (Python function)")
            else:
                # Something's wrong
                print(f"❌ {tool_name}: Not callable")
                all_valid = False
            
        except Exception as e:
            print(f"❌ {tool_name}: Error - {e}")
            all_valid = False
    
    print("\n" + "="*70)
    print(f"📊 VALIDATION RESULTS")
    print("="*70)
    print(f"Total tools checked: {tool_count}")
    print(f"Status: {'✅ ALL PASSED' if all_valid else '❌ SOME FAILED'}")
    print("="*70 + "\n")
    
    return all_valid


def print_tool_summary():
    """Print summary of available tools for each agent."""
    print("\n" + "="*70)
    print("📋 TOOL ASSIGNMENTS SUMMARY")
    print("="*70 + "\n")
    
    for agent_type, tools in TOOLS_REGISTRY.items():
        agent_name = agent_type.upper().replace('_', ' ')
        print(f"🤖 {agent_name}:")
        for tool in tools:
            tool_name = get_tool_name(tool)
            print(f"   • {tool_name}")
        print()
    
    print("="*70 + "\n")


# ============================================================================
# RUN VALIDATION
# ============================================================================

if __name__ == "__main__":
    # Show what tools we have
    print_tool_summary()
    
    # Validate they all work
    if validate_tools_available():
        print("🎉 Integration ready!")
        print("✅ All Team B tools are available for Team A agents")
        print(f"\n📊 Tool count by agent:")
        print(f"   Pair Monitors: {len(PAIR_MONITOR_TOOLS)} tools")
        print(f"   Risk Manager: {len(RISK_MANAGER_TOOLS)} tools")
        print(f"   Portfolio Coordinator: {len(PORTFOLIO_COORDINATOR_TOOLS)} tools")
        print(f"   Execution Agent: {len(EXECUTION_AGENT_TOOLS)} tools")
        print(f"   Total: {len(PAIR_MONITOR_TOOLS + RISK_MANAGER_TOOLS + PORTFOLIO_COORDINATOR_TOOLS + EXECUTION_AGENT_TOOLS)} tools")
        print("\n📍 Next step: Update src/agents/crew_setup.py")
        print("   Import: from src.integration.tools_registry import TOOLS_REGISTRY\n")
    else:
        print("⚠️  Some tools failed validation")
        print("🔧 Fix the issues above before proceeding\n")