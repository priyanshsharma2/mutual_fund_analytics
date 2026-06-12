"""
Bluestock Mutual Fund Analytics - Quantitative Risk Modeling Layer.

This module houses vector processing algorithms to compute rolling returns,
geometric compounding curves, systemic exposure thresholds, and maximum drawdowns.

Author: Priyansh Sharma
Date: June 12, 2026
"""

import pandas as pd
import numpy as np
from scipy import stats
import logging

logger = logging.getLogger(__name__)

def calculate_daily_returns(nav_series: pd.Series) -> pd.Series:
    """
    Computes daily percentage returns from an array of consecutive NAVs.
    
    Formula:
        daily_return = (NAV_t / NAV_t-1) - 1

    Args:
        nav_series (pd.Series): Historical timeline vector of a fund's NAV.

    Returns:
        pd.Series: Staged daily return percentage distribution.
    """
    if nav_series.empty or len(nav_series) < 2:
        logger.warning("Empty or insufficient asset pricing vector received.")
        return pd.Series(dtype=float)
    return nav_series.pct_change().dropna()

def calculate_cagr(start_nav: float, end_nav: float, years: float) -> float:
    """
    Computes the Compound Annual Growth Rate (CAGR) over an explicit timeline window.

    Formula:
        CAGR = (NAV_end / NAV_start) ** (1 / n) - 1

    Args:
        start_nav (float): Net Asset Value at the beginning of holding window.
        end_nav (float): Net Asset Value at the closing date of validation frame.
        years (float): Total fractional calendar year duration (n).

    Returns:
        float: Smoothed geometric mean compounding growth rate.
    """
    if start_nav <= 0 or end_nav <= 0 or years <= 0:
        logger.error("Invalid parameters provided for geometric compounding.")
        return 0.0
    return (end_nav / start_nav) ** (1.0 / years) - 1.0

def calculate_maximum_drawdown(nav_series: pd.Series) -> float:
    """
    Isolates the worst peak-to-trough capital erosion percentage drop.

    Formula:
        Drawdown = (NAV / Running Maximum) - 1

    Args:
        nav_series (pd.Series): Historical time-series asset pricing vector.

    Returns:
        float: The absolute minimum percentage value indicating maximum historical risk.
    """
    if nav_series.empty:
        return 0.0
    running_max = nav_series.cummax()
    drawdown_series = (nav_series / running_max) - 1.0
    return float(drawdown_series.min())
