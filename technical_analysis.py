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

class CoinbaseAPI:
    def __init__(self):
        self.base_url = "https://api.exchange.coinbase.com"
        self.cache_dir = "cache"
        self.cache_duration = 0  # Temporarily disable caching to force fresh data fetch
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _get_cache_path(self, symbol):
        return os.path.join(self.cache_dir, f"{symbol.lower()}_coinbase_data.json")
    
    def _load_from_cache(self, symbol):
        """Load cached data for a symbol."""
        cache_file = self._get_cache_path(symbol)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                    if (isinstance(cache_data, dict) and 
                        'data' in cache_data and 
                        'timestamp' in cache_data and 
                        isinstance(cache_data['data'], list) and 
                        len(cache_data['data']) > 0):
                        return cache_data
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading cache for {symbol}: {str(e)}")
                try:
                    os.remove(cache_file)
                except:
                    pass
        return None
    
    def _save_to_cache(self, symbol, data):
        cache_path = self._get_cache_path(symbol)
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f)
    
    def fetch_historical_data(self, symbol):
        """Fetch historical data for a symbol using Coinbase API."""
        try:
            # Calculate date range - fetch 2 years of data for better EMA initialization
            end_date = datetime.now()
            start_date = end_date - timedelta(days=730)  # 2 years
            
            # Coinbase API endpoint for historical data
            url = f"{self.base_url}/products/BTC-USD/candles"
            
            # Calculate chunk size to stay under 300 data points
            # Each day is one data point, so we'll fetch 250 days at a time
            chunk_days = 250
            current_start = start_date
            all_data = []
            
            while current_start < end_date:
                current_end = min(current_start + timedelta(days=chunk_days), end_date)
                
                params = {
                    'start': current_start.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'end': current_end.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'granularity': 86400  # Daily data
                }
                
                response = requests.get(url, params=params)
                
                if response.status_code == 200:
                    chunk_data = response.json()
                    if chunk_data:
                        # Convert Coinbase format to our format
                        for candle in chunk_data:
                            timestamp, low, high, open_price, close_price, volume = candle
                            date = datetime.fromtimestamp(timestamp)
                            if date.weekday() == 5:  # Only keep Saturday data
                                all_data.append({
                                    'date': date.strftime('%Y-%m-%d'),
                                    'price': close_price
                                })
                
                # Move to next chunk
                current_start = current_end
                # Small delay to avoid rate limiting
                time.sleep(0.5)
            
            if all_data:
                # Sort by date ascending
                all_data.sort(key=lambda x: x['date'])
                return all_data
            
            return None
            
        except Exception as e:
            return None
    
    def get_current_price(self, symbol):
        """Get the current price from Coinbase API."""
        try:
            url = f"{self.base_url}/products/BTC-USD/ticker"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                return float(data['price'])
            else:
                print(f"Failed to get current price from Coinbase. Status code: {response.status_code}")
                print(f"Response content: {response.text}")
        except Exception as e:
            print(f"Error getting current price from Coinbase: {str(e)}")
        
        return None

class CryptoAnalyzer:
    def __init__(self):
        load_dotenv()
        self.coinbase_api = CoinbaseAPI()
        self.cache_dir = "cache"
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def fetch_historical_data(self, symbol):
        """Fetch historical data using Coinbase API."""
        return self.coinbase_api.fetch_historical_data(symbol)
    
    def get_current_price(self, symbol):
        """Get current price using Coinbase API."""
        return self.coinbase_api.get_current_price(symbol)
    
    def analyze_crypto(self, symbol):
        """Analyze cryptocurrency using MACD that matches TradingView's implementation."""
        print(f"\nStarting analysis for {symbol}...")
        
        # Fetch historical data
        data = self.fetch_historical_data(symbol)
        
        if data is None or len(data) < 180:
            print("Error: Not enough data points for analysis")
            return None
            
        # Convert to DataFrame
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Get current date and previous Monday
        current_date = datetime.now()
        last_monday = current_date - timedelta(days=current_date.weekday())
        
        # Set start date to 8 weeks before last Monday
        start_date = last_monday - timedelta(weeks=8)
        
        # Filter data for the analysis period
        df = df[df.index >= start_date]
        
        if len(df) < 26:
            print("Error: Not enough data points after filtering")
            return None
        
        # Get all Sundays in the range
        sunday_data = df[df.index.weekday == 6]
        
        # Print weekly analysis
        print("\nWeekly MACD Analysis:")
        print("=" * 100)
        print(f"{'Date':<15} {'Price':<15} {'MACD':<15} {'Signal':<15} {'Distance':<15} {'Trend':<10}")
        print("-" * 100)
        
        # Calculate MACD using ta library
        macd_indicator = ta.trend.MACD(
            close=sunday_data['price'],
            window_fast=12,
            window_slow=26,
            window_sign=9
        )
        
        sunday_data['macd_line'] = macd_indicator.macd()
        sunday_data['signal_line'] = macd_indicator.macd_signal()
        sunday_data['distance'] = sunday_data['macd_line'] - sunday_data['signal_line']
        
        # Drop rows with NaN values
        sunday_data = sunday_data.dropna()
        
        if len(sunday_data) < 2:
            print("Error: Not enough data points after MACD calculation")
            return None
        
        # Prepare historical data
        historical_data = []
        for i in range(len(sunday_data)):
            date = sunday_data.index[i]
            price = sunday_data['price'].iloc[i]
            macd_value = sunday_data['macd_line'].iloc[i]
            signal_value = sunday_data['signal_line'].iloc[i]
            distance = sunday_data['distance'].iloc[i]
            
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
                return "Strong Buy: Bullish trend with increasing momentum"
            else:
                return "Buy: Bullish trend but momentum may be slowing"
        else:
            if momentum == "increasing":
                return "Strong Sell: Bearish trend with increasing momentum"
            else:
                return "Sell: Bearish trend but momentum may be slowing" 