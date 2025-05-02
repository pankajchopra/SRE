"""
Account API Tool
Interfaces with the local account API endpoint.
"""

import logging
import json
import requests
from typing import Dict, Any, Optional
from urllib.parse import urljoin

from langchain.tools import BaseTool

# Configure logging
logger = logging.getLogger(__name__)

class AccountAPITool(BaseTool):
    """Tool for interacting with the account API."""
    
    name = "account_api"
    description = """
    Interfaces with the account API to retrieve and manage user account information.
    Use this tool when the user wants to check account details, balances, transactions,
    or other account-related information.
    """
    
    base_url = "http://localhost:8080/api/account/v1"
    timeout = 10  # seconds
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Account API tool.
        
        Args:
            api_key: Optional API key for authentication
        """
        super().__init__()
        self.api_key = api_key
        
    def _get_headers(self) -> Dict[str, str]:
        """Get the headers for API requests."""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
            
        return headers
    
    def _make_request(self, endpoint: str, method: str = 'GET', 
                     params: Optional[Dict[str, Any]] = None, 
                     data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the API.
        
        Args:
            endpoint: API endpoint to call
            method: HTTP method to use
            params: Query parameters
            data: Request body data
            
        Returns:
            API response as a dictionary
        """
        url = urljoin(self.base_url, endpoint)
        headers = self._get_headers()
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=self.timeout
            )
            
            # Handle response
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            
            # Try to get error details from response
            error_detail = "Unknown error"
            try:
                error_json = e.response.json()
                error_detail = error_json.get('message', error_json.get('error', str(e)))
            except:
                error_detail = str(e)
                
            return {'error': f"HTTP error: {error_detail}", 'status_code': e.response.status_code}
            
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error to {url}")
            return {'error': f"Could not connect to the account API. Please ensure the API server is running at {self.base_url}"}
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout connecting to {url}")
            return {'error': f"Request timed out after {self.timeout} seconds"}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return {'error': f"Request error: {str(e)}"}
            
        except ValueError as e:
            logger.error(f"JSON parsing error: {e}")
            return {'error': f"Invalid response format from API: {str(e)}"}
    
    def get_account_info(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get account information.
        
        Args:
            account_id: Optional account ID. If not provided, returns all accounts.
            
        Returns:
            Account information
        """
        endpoint = f"accounts/{account_id}" if account_id else "accounts"
        return self._make_request(endpoint)
    
    def get_transactions(self, account_id: str, 
                        start_date: Optional[str] = None, 
                        end_date: Optional[str] = None,
                        limit: int = 50) -> Dict[str, Any]:
        """
        Get account transactions.
        
        Args:
            account_id: Account ID
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            limit: Maximum number of transactions to return
            
        Returns:
            Transaction data
        """
        endpoint = f"accounts/{account_id}/transactions"
        params = {'limit': limit}
        
        if start_date:
            params['start_date'] = start_date
            
        if end_date:
            params['end_date'] = end_date
            
        return self._make_request(endpoint, params=params)
    
    def get_balance(self, account_id: str) -> Dict[str, Any]:
        """
        Get account balance.
        
        Args:
            account_id: Account ID
            
        Returns:
            Balance information
        """
        endpoint = f"accounts/{account_id}/balance"
        return self._make_request(endpoint)
    
    def _extract_account_id(self, query: str) -> Optional[str]:
        """
        Try to extract an account ID from the query.
        
        Args:
            query: User query string
            
        Returns:
            Extracted account ID or None
        """
        # This is a simplified implementation
        # In a real system, you would use a more sophisticated approach
        # such as entity extraction with an LLM or regex patterns
        
        import re
        
        # Look for patterns like "account 12345" or "account #12345" or "account id 12345"
        patterns = [
            r'account\s+#?(\d+)',
            r'account\s+id\s+#?(\d+)',
            r'acc\s+#?(\d+)',
            r'acct\s+#?(\d+)',
            r'account\s+number\s+#?(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                return match.group(1)
                
        return None
    
    def _run(self, query: str) -> str:
        """
        Process the account API query.
        
        Args:
            query: User query string
            
        Returns:
            Formatted response with account information
        """
        try:
            logger.info(f"Processing account query: {query}")
            
            # Determine the type of account query
            query_lower = query.lower()
            
            # Extract account ID if present
            account_id = self._extract_account_id(query)
            
            # Handle different query types
            if 'transactions' in query_lower or 'activity' in query_lower:
                if not account_id:
                    return "Please specify an account ID to retrieve transactions."
                
                # Determine date range if present
                start_date = None
                end_date = None
                
                # Very basic date extraction - would be more sophisticated in production
                if 'last month' in query_lower:
                    from datetime import datetime, timedelta
                    today = datetime.now()
                    first_of_month = datetime(today.year, today.month, 1)
                    last_month = first_of_month - timedelta(days=1)
                    start_date = datetime(last_month.year, last_month.month, 1).strftime('%Y-%m-%d')
                    end_date = first_of_month.strftime('%Y-%m-%d')
                elif 'last week' in query_lower:
                    from datetime import datetime, timedelta
                    today = datetime.now()
                    start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
                    end_date = today.strftime('%Y-%m-%d')
                    
                # Get transactions
                result = self.get_transactions(account_id, start_date, end_date)
                
                if 'error' in result:
                    return f"Error retrieving transactions: {result['error']}"
                
                # Format transactions
                transactions = result.get('transactions', [])
                if not transactions:
                    return f"No transactions found for account {account_id} in the specified period."
                
                # Format the response
                response = f"Transactions for Account #{account_id}:\n\n"
                
                if start_date and end_date:
                    response += f"Period: {start_date} to {end_date}\n\n"
                
                for i, tx in enumerate(transactions[:10], 1):  # Limit to 10 transactions
                    date = tx.get('date', 'Unknown date')
                    description = tx.get('description', 'Unknown transaction')
                    amount = tx.get('amount', 0)
                    
                    # Format amount with sign
                    if amount < 0:
                        amount_str = f"-${abs(amount):.2f}"
                    else:
                        amount_str = f"${amount:.2f}"
                    
                    response += f"{i}. {date} | {description} | {amount_str}\n"
                
                if len(transactions) > 10:
                    response += f"\n... and {len(transactions) - 10} more transactions."
                
                return response
                
            elif 'balance' in query_lower:
                if not account_id:
                    # Get all accounts if no specific account requested
                    accounts_result = self.get_account_info()
                    
                    if 'error' in accounts_result:
                        return f"Error retrieving accounts: {accounts_result['error']}"
                    
                    accounts = accounts_result.get('accounts', [])
                    if not accounts:
                        return "No accounts found."
                    
                    response = "Account Balances:\n\n"
                    for account in accounts:
                        acc_id = account.get('id', 'Unknown')
                        acc_name = account.get('name', 'Unknown')
                        acc_type = account.get('type', 'Unknown')
                        balance = account.get('balance', 0)
                        currency = account.get('currency', 'USD')
                        
                        response += f"Account #{acc_id} ({acc_type}): {acc_name}\n"
                        response += f"Balance: ${balance:.2f} {currency}\n\n"
                    
                    return response
                else:
                    # Get specific account balance
                    result = self.get_balance(account_id)
                    
                    if 'error' in result:
                        return f"Error retrieving balance: {result['error']}"
                    
                    balance = result.get('balance', 0)
                    available = result.get('available', balance)
                    currency = result.get('currency', 'USD')
                    
                    response = f"Balance for Account #{account_id}:\n\n"
                    response += f"Current Balance: ${balance:.2f} {currency}\n"
                    response += f"Available Balance: ${available:.2f} {currency}\n"
                    
                    return response
            
            else:
                # Default to account information
                if not account_id:
                    # Get all accounts if no specific account requested
                    accounts_result = self.get_account_info()
                    
                    if 'error' in accounts_result:
                        return f"Error retrieving accounts: {accounts_result['error']}"
                    
                    accounts = accounts_result.get('accounts', [])
                    if not accounts:
                        return "No accounts found."
                    
                    response = "Your Accounts:\n\n"
                    for account in accounts:
                        acc_id = account.get('id', 'Unknown')
                        acc_name = account.get('name', 'Unknown')
                        acc_type = account.get('type', 'Unknown')
                        acc_status = account.get('status', 'Unknown')
                        
                        response += f"Account #{acc_id}\n"
                        response += f"Name: {acc_name}\n"
                        response += f"Type: {acc_type}\n"
                        response += f"Status: {acc_status}\n\n"
                    
                    return response
                else:
                    # Get specific account information
                    result = self.get_account_info(account_id)
                    
                    if 'error' in result:
                        return f"Error retrieving account information: {result['error']}"
                    
                    account = result.get('account', {})
                    
                    if not account:
                        return f"No information found for account {account_id}."
                    
                    response = f"Account #{account_id} Details:\n\n"
                    response += f"Name: {account.get('name', 'Unknown')}\n"
                    response += f"Type: {account.get('type', 'Unknown')}\n"
                    response += f"Status: {account.get('status', 'Unknown')}\n"
                    response += f"Balance: ${account.get('balance', 0):.2f} {account.get('currency', 'USD')}\n"
                    response += f"Open Date: {account.get('open_date', 'Unknown')}\n"
                    
                    return response
        
        except Exception as e:
            logger.error(f"Error in account API tool: {e}")
            return f"Error processing account request: {str(e)}"
                