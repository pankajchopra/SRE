"""
Stock Information Tool
Fetches stock ticker information from Yahoo Finance API.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

import yfinance as yf
import pandas as pd
from langchain.tools import BaseTool

# Configure logging
logger = logging.getLogger(__name__)

class StockInfoTool(BaseTool):
    """Tool for fetching stock information from Yahoo Finance."""
    
    name = "stock_info"
    description = """
    Fetches financial information about stocks using ticker symbols.
    Use this tool when users ask about stock prices, historical performance,
    company financials, or any stock market related information.
    """
    
    def _extract_ticker_symbols(self, text: str) -> List[str]:
        """
        Extract potential stock ticker symbols from the query.
        
        Args:
            text: The user query text
            
        Returns:
            List of potential ticker symbols
        """
        # Common ticker symbol patterns (uppercase 1-5 letters)
        ticker_pattern = r'\b[A-Z]{1,5}\b'
        potential_tickers = re.findall(ticker_pattern, text)
        
        # Filter out common non-ticker words
        common_words = {'I', 'A', 'THE', 'FOR', 'TO', 'IN', 'AND', 'OR', 'OF', 'AT', 'BY'}
        filtered_tickers = [ticker for ticker in potential_tickers if ticker not in common_words]
        
        return filtered_tickers
    
    def _get_stock_info(self, ticker: str) -> Dict[str, Any]:
        """
        Get basic stock information for a ticker.
        
        Args:
            ticker: The stock ticker symbol
            
        Returns:
            Dictionary with stock information
        """
        try:
            # Fetch stock data
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Extract relevant information
            basic_info = {
                'symbol': ticker,
                'name': info.get('shortName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'current_price': info.get('currentPrice', info.get('regularMarketPrice', 'N/A')),
                'currency': info.get('currency', 'USD'),
                'market_cap': info.get('marketCap', 'N/A'),
                'pe_ratio': info.get('trailingPE', 'N/A'),
                'dividend_yield': info.get('dividendYield', 'N/A'),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 'N/A'),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', 'N/A'),
            }
            
            # Format numerical values for readability
            for key, value in basic_info.items():
                if isinstance(value, (int, float)):
                    if key == 'market_cap' and value > 1_000_000:
                        basic_info[key] = f"${value / 1_000_000_000:.2f} billion"
                    elif key == 'dividend_yield' and value is not None:
                        basic_info[key] = f"{value * 100:.2f}%"
                    elif isinstance(value, float):
                        basic_info[key] = f"{value:.2f}"
            
            return basic_info
            
        except Exception as e:
            logger.error(f"Error getting stock info for {ticker}: {e}")
            return {'symbol': ticker, 'error': str(e)}
    
    def _get_historical_data(self, ticker: str, period: str = '1mo') -> Dict[str, Any]:
        """
        Get historical stock data.
        
        Args:
            ticker: The stock ticker symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            
        Returns:
            Dictionary with historical data summary
        """
        try:
            # Fetch historical data
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            
            if hist.empty:
                return {'error': f"No historical data available for {ticker}"}
            
            # Calculate summary statistics
            summary = {
                'start_date': hist.index[0].strftime('%Y-%m-%d'),
                'end_date': hist.index[-1].strftime('%Y-%m-%d'),
                'start_price': round(hist['Close'][0], 2),
                'end_price': round(hist['Close'][-1], 2),
                'percent_change': round((hist['Close'][-1] / hist['Close'][0] - 1) * 100, 2),
                'highest_price': round(hist['High'].max(), 2),
                'lowest_price': round(hist['Low'].min(), 2),
                'average_volume': f"{int(hist['Volume'].mean()):,}",
            }
            
            # Add formatted percent change
            if summary['percent_change'] > 0:
                summary['change_formatted'] = f"↑ {summary['percent_change']}%"
            else:
                summary['change_formatted'] = f"↓ {abs(summary['percent_change'])}%"
                
            return summary
            
        except Exception as e:
            logger.error(f"Error getting historical data for {ticker}: {e}")
            return {'symbol': ticker, 'error': str(e)}
    
    def _run(self, query: str) -> str:
        """
        Run the stock information tool based on the query.
        
        Args:
            query: The user query string
            
        Returns:
            Formatted stock information
        """
        try:
            logger.info(f"Processing stock query: {query}")
            
            # Extract potential ticker symbols
            potential_tickers = self._extract_ticker_symbols(query)
            
            if not potential_tickers:
                return "No stock ticker symbols identified in your query. Please specify a valid stock symbol (e.g., AAPL for Apple)."
            
            # Determine if we need historical data based on query keywords
            historical_keywords = ['historical', 'history', 'trend', 'performance', 'past', 'previous', 'changed']
            need_historical = any(keyword in query.lower() for keyword in historical_keywords)
            
            # Determine the period for historical data
            period = '1mo'  # Default to 1 month
            if 'year' in query.lower() or '12 month' in query.lower():
                period = '1y'
            elif '6 month' in query.lower():
                period = '6mo'
            elif '3 month' in query.lower() or 'quarter' in query.lower():
                period = '3mo'
            elif 'week' in query.lower():
                period = '5d'
            elif 'day' in query.lower():
                period = '1d'
                
            # Process each potential ticker and build the response
            results = []
            
            for ticker in potential_tickers[:3]:  # Limit to first 3 tickers to avoid too much output
                info = self._get_stock_info(ticker)
                
                if 'error' in info:
                    results.append(f"Could not retrieve information for {ticker}: {info['error']}")
                    continue
                    
                # Format basic information
                ticker_result = f"""
                📊 {info['name']} ({info['symbol']})
                
                Current Price: ${info['current_price']} {info['currency']}
                Sector: {info['sector']}
                Industry: {info['industry']}
                Market Cap: {info['market_cap']}
                P/E Ratio: {info['pe_ratio']}
                Dividend Yield: {info['dividend_yield']}
                52-Week Range: ${info['fifty_two_week_low']} - ${info['fifty_two_week_high']}
                """
                
                # Add historical data if needed
                if need_historical:
                    hist_data = self._get_historical_data(ticker, period)
                    
                    if 'error' in hist_data:
                        ticker_result += f"\nHistorical Data: {hist_data['error']}"
                    else:
                        ticker_result += f"""
                        
                        📈 Historical Performance ({period}):
                        Period: {hist_data['start_date']} to {hist_data['end_date']}
                        Starting Price: ${hist_data['start_price']}
                        Current Price: ${hist_data['end_price']}
                        Change: {hist_data['change_formatted']}
                        Highest: ${hist_data['highest_price']}
                        Lowest: ${hist_data['lowest_price']}
                        Average Daily Volume: {hist_data['average_volume']}
                        """
                
                results.append(ticker_result.strip())
            
            # Combine results with separators
            response = "\n\n" + "\n\n---\n\n".join(results)
            
            # Add disclaimer
            response += "\n\n⚠️ Disclaimer: Stock information is for informational purposes only and may be delayed. Do not make investment decisions based solely on this data."
            
            return response
            
        except Exception as e:
            logger.error(f"Error in stock info tool: {e}")
            return f"Error retrieving stock information: {str(e)}"
