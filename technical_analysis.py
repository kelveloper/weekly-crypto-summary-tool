import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import os
import traceback
from dotenv import load_dotenv
import ta  # Technical Analysis library

class CryptoAnalyzer:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('COINGECKO_API_KEY')
        self.base_url = "https://api.coingecko.com/api/v3"
        self.cache_dir = "cache"
        self.cache_duration = 3600  # Cache duration in seconds (1 hour)
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        # Initialize empty cache
        self._cache = {}
    
    def _get_cache_path(self, symbol):
        return os.path.join(self.cache_dir, f"{symbol.lower()}_data.json")
    
    def _load_from_cache(self, symbol):
        """Load cached data for a symbol."""
        cache_file = self._get_cache_path(symbol)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                    # Check if cache is valid (has required keys and data)
                    if (isinstance(cache_data, dict) and 
                        'data' in cache_data and 
                        'timestamp' in cache_data and 
                        isinstance(cache_data['data'], list) and 
                        len(cache_data['data']) > 0):
                        return cache_data
                    else:
                        print(f"Invalid cache format for {symbol}, fetching fresh data")
                        return None
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading cache for {symbol}: {str(e)}")
                # Remove invalid cache file
                try:
                    os.remove(cache_file)
                except:
                    pass
                return None
        return None
    
    def _save_to_cache(self, symbol, data):
        cache_path = self._get_cache_path(symbol)
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        # Save to file cache
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f)
        # Update memory cache
        self._cache[symbol] = {
            'timestamp': datetime.now(),
            'data': data
        }
    
    def fetch_historical_data(self, symbol):
        """Fetch historical data for a symbol."""
        print(f"\nStarting data fetch for {symbol}...")
        
        # Try to load from cache first
        cached_data = self._load_from_cache(symbol)
        if cached_data:
            print(f"Using cached data for {symbol}")
            # Check if we have enough data points and if cache is recent
            cache_time = datetime.fromisoformat(cached_data['timestamp'])
            if len(cached_data['data']) >= 180 and (datetime.now() - cache_time).total_seconds() < 3600:  # Cache valid for 1 hour
                print(f"Cache valid with {len(cached_data['data'])} data points")
                return cached_data['data']
            else:
                print(f"Cache expired or not enough data points, fetching fresh data...")
                # Clear the cache file
                cache_file = self._get_cache_path(symbol)
                try:
                    if os.path.exists(cache_file):
                        os.remove(cache_file)
                except:
                    pass
        
        # If no valid cache or not enough data, fetch fresh data
        try:
            # Get coin ID from symbol
            coin_id = self._get_coin_id(symbol)
            if not coin_id:
                print(f"Could not find coin ID for {symbol}")
                return None
            
            # Calculate date range for live data - get more data to ensure we have enough Mondays
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)  # Get 1 year of data to ensure enough Mondays
            
            # Fetch historical data
            url = f"{self.base_url}/coins/{coin_id}/market_chart/range"
            params = {
                'vs_currency': 'usd',
                'from': int(start_date.timestamp()),
                'to': int(end_date.timestamp())
            }
            
            print(f"Fetching live data for {symbol} from {start_date.date()} to {end_date.date()}...")
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0'
            }
            
            # Add delay to avoid rate limiting
            time.sleep(2)  # 2 second delay between requests
            
            response = requests.get(url, params=params, headers=headers)
            print(f"API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"Successfully fetched data for {symbol}")
                    
                    if 'prices' in data and data['prices']:
                        # Convert the data to our format
                        daily_data = []
                        for timestamp, price in data['prices']:
                            date = datetime.fromtimestamp(timestamp/1000)
                            daily_data.append({
                                'date': date.strftime('%Y-%m-%d'),
                                'price': price
                            })
                        
                        # Sort by date ascending
                        daily_data.sort(key=lambda x: x['date'])
                        
                        print(f"Converted {len(daily_data)} price points to daily data")
                        
                        # Check if we have enough data
                        if len(daily_data) < 180:  # Need at least 180 days to ensure enough Mondays
                            print(f"Error: Not enough data points from API ({len(daily_data)}), need at least 180")
                            return None
                        
                        # Cache the data
                        self._save_to_cache(symbol, daily_data)
                        print(f"Successfully cached {len(daily_data)} data points for {symbol}")
                        return daily_data
                    else:
                        print(f"No price data found in response for {symbol}")
                        return None
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON response for {symbol}: {str(e)}")
                    print(f"Response content: {response.text[:200]}...")  # Print first 200 chars of response
                    return None
            elif response.status_code == 429:  # Rate limit
                print(f"Rate limit reached for {symbol}. Waiting before retry...")
                time.sleep(60)  # Wait 1 minute before retry
                return self.fetch_historical_data(symbol)  # Retry the request
            else:
                print(f"API request failed with status code: {response.status_code}")
                print(f"Response content: {response.text[:200]}...")  # Print first 200 chars of response
                return None
            
        except requests.exceptions.RequestException as e:
            print(f"Network error fetching data for {symbol}: {str(e)}")
            return None
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            print(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _get_coin_id(self, symbol):
        """Get CoinGecko coin ID from symbol."""
        try:
            # Special case for Bitcoin
            if symbol.upper() == 'BTC':
                return 'bitcoin'
            
            # Try to get from cache first
            cache_file = os.path.join(self.cache_dir, 'coin_ids.json')
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r') as f:
                        coin_ids = json.load(f)
                        if symbol.lower() in coin_ids:
                            return coin_ids[symbol.lower()]
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Error reading coin ID cache: {str(e)}")
                    # Remove invalid cache file
                    try:
                        os.remove(cache_file)
                    except:
                        pass
            
            # If not in cache, fetch from API
            url = f"{self.base_url}/coins/list"
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0'
            }
            
            # Add delay to avoid rate limiting
            time.sleep(2)
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                try:
                    coins = response.json()
                    coin_ids = {}
                    for coin in coins:
                        coin_ids[coin['symbol'].lower()] = coin['id']
                    
                    # Save to cache
                    try:
                        with open(cache_file, 'w') as f:
                            json.dump(coin_ids, f)
                    except IOError as e:
                        print(f"Error saving coin ID cache: {str(e)}")
                    
                    return coin_ids.get(symbol.lower())
                except json.JSONDecodeError as e:
                    print(f"Error decoding coin list JSON: {str(e)}")
                    return None
            elif response.status_code == 429:  # Rate limit
                print("Rate limit reached while fetching coin list. Waiting before retry...")
                time.sleep(60)  # Wait 1 minute before retry
                return self._get_coin_id(symbol)  # Retry
            else:
                print(f"Failed to fetch coin list. Status code: {response.status_code}")
                return None
            
        except requests.exceptions.RequestException as e:
            print(f"Network error fetching coin list: {str(e)}")
            return None
        except Exception as e:
            print(f"Error getting coin ID for {symbol}: {str(e)}")
            return None
    
    def analyze_crypto(self, symbol):
        """Analyze cryptocurrency using MACD that matches TradingView's implementation."""
        print(f"\nStarting analysis for {symbol}...")
        
        # Fetch historical data
        data = self.fetch_historical_data(symbol)
        
        if data is None or len(data) < 180:  # Need at least 180 days for proper MACD calculation
            print("Error: Not enough data points for analysis")
            return None
            
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Handle both cached and live data formats
        if 'timestamp' in df.columns:
            df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        else:
            df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Set start date to January 1, 2025
        start_date = pd.Timestamp('2025-01-01')
        
        # Filter data from 2025 onwards
        df = df[df.index >= start_date]
        
        if len(df) < 26:  # Need at least 26 weeks for MACD calculation
            print("Error: Not enough data points after filtering for 2025")
            return None
        
        # Resample to weekly data (Monday to Monday)
        weekly_data = df['price'].resample('W-MON', closed='left', label='left').last().to_frame()
        
        # Ensure we have enough data points for MACD calculation
        if len(weekly_data) < 26:  # Need at least 26 weeks for slow EMA
            print("Error: Not enough weekly data points for MACD calculation")
            return None
        
        # Calculate MACD using ta library
        macd_indicator = ta.trend.MACD(
            close=weekly_data['price'],
            window_fast=12,
            window_slow=26,
            window_sign=9
        )
        
        weekly_data['macd_line'] = macd_indicator.macd()
        weekly_data['signal_line'] = macd_indicator.macd_signal()
        weekly_data['distance'] = weekly_data['macd_line'] - weekly_data['signal_line']
        
        # Drop rows with NaN values (first 26 weeks due to slow EMA calculation)
        weekly_data = weekly_data.dropna()
        
        if len(weekly_data) < 2:  # Need at least 2 weeks for comparison
            print("Error: Not enough data points after MACD calculation")
            return None
        
        # Print weekly analysis
        print("\nWeekly MACD Analysis for 2025 (Monday to Monday):")
        print("=" * 100)
        print(f"{'Date':<15} {'Price':<15} {'MACD':<15} {'Signal':<15} {'Distance':<15} {'Trend':<10}")
        print("-" * 100)
        
        # Prepare historical data
        historical_data = []
        for i in range(len(weekly_data)):
            date = weekly_data.index[i]
            price = weekly_data['price'].iloc[i]
            macd_value = weekly_data['macd_line'].iloc[i]
            signal_value = weekly_data['signal_line'].iloc[i]
            distance = weekly_data['distance'].iloc[i]
            
            week_data = {
                'date': date.strftime('%Y-%m-%d'),
                'price': price,
                'macd': macd_value,
                'signal': signal_value,
                'distance': distance
            }
            historical_data.append(week_data)
            
            # Print to console
            trend = "Bullish" if distance > 0 else "Bearish"
            print(f"{date.strftime('%Y-%m-%d'):<15} ${price:>10.2f} {macd_value:>14.4f} {signal_value:>14.4f} {distance:>14.4f} {trend:>10}")
        
        print("=" * 100)
        
        if not historical_data:
            print("Error: No historical data generated")
            return None
            
        # Get current values
        current_week = historical_data[-1]
        current_macd = current_week['macd']
        current_signal = current_week['signal']
        current_distance = current_week['distance']
        
        # Determine trend and momentum
        trend = "bullish" if current_distance > 0 else "bearish"
        momentum = "increasing" if current_distance > historical_data[-2]['distance'] else "decreasing"
        
        # Generate recommendation
        recommendation = self._generate_recommendation(trend, momentum, current_distance)
        
        result = {
            'current_week_data': current_week,
            'current_macd': current_macd,
            'current_signal': current_signal,
            'current_distance': current_distance,
            'trend': trend,
            'momentum': momentum,
            'recommendation': recommendation,
            'historical_data': historical_data
        }
        
        return result
    
    def _generate_recommendation(self, trend, momentum, distance):
        """Generate a recommendation based on trend, momentum, and MACD distance."""
        if trend == "bullish":
            if momentum == "increasing":
                if abs(distance) > 100:  # Strong trend
                    return "Strong bullish momentum with significant MACD separation. Consider holding or adding to positions with proper risk management."
                else:
                    return "Bullish trend with increasing momentum. Consider holding positions and monitor for potential entry points."
            else:
                if abs(distance) > 100:  # Strong trend
                    return "Bullish trend but momentum weakening. Consider taking partial profits and monitor for potential reversal signals."
                else:
                    return "Bullish trend with decreasing momentum. Exercise caution and consider tightening stop losses."
        else:
            if momentum == "increasing":
                if abs(distance) > 100:  # Strong trend
                    return "Bearish trend but momentum improving. Monitor for potential reversal signals and consider scaling into positions."
                else:
                    return "Bearish trend with improving momentum. Consider waiting for confirmation of trend reversal before entering positions."
            else:
                if abs(distance) > 100:  # Strong trend
                    return "Strong bearish momentum. Consider reducing positions or waiting for clear reversal signals before entering."
                else:
                    return "Bearish trend with decreasing momentum. Exercise caution and wait for confirmation of trend reversal."
    
    def get_current_price(self, symbol):
        """Get the current price of a cryptocurrency."""
        try:
            # Try different symbol formats
            symbol_formats = [symbol, f"{symbol}USD", f"{symbol}-USD"]
            
            for sym in symbol_formats:
                try:
                    url = f"https://api.coingecko.com/api/v3/simple/price"
                    params = {
                        'ids': 'bitcoin',
                        'vs_currencies': 'usd'
                    }
                    
                    response = requests.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    
                    if 'bitcoin' in data and 'usd' in data['bitcoin']:
                        return data['bitcoin']['usd']
                    
                except Exception as e:
                    print(f"Error fetching price for {sym}: {str(e)}")
                    continue
                    
            raise Exception("Failed to fetch current price")
            
        except Exception as e:
            print(f"Error in get_current_price: {str(e)}")
            return None 