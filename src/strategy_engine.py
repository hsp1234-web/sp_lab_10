# -*- coding: utf-8 -*-
from src.strategy import SupertrendBNFStrategy

# In the future, this module can be expanded to dynamically load different strategies.
# For now, it simply exposes the existing strategy class to be used by the backtest engine.

def get_strategy_class(strategy_name: str):
    """
    Retrieve the strategy class based on the name.
    Currently defaults to SupertrendBNFStrategy.
    """
    if strategy_name == 'SupertrendBNF':
        return SupertrendBNFStrategy
    else:
        # Default or raise error
        print(f"[Strategy] Warning: Unknown strategy '{strategy_name}'. Defaulting to SupertrendBNFStrategy.")
        return SupertrendBNFStrategy
