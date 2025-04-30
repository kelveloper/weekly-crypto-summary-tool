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
        self.cache_duration = 3600  # 1 hour cache duration
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        print(f"CoinbaseAPI initialized with base_url: {self.base_url}")
        
        # Add test data for development
        self.test_data = {
            'BTC': [
                {'date': '2024-01-01', 'price': 45000.0},
                {'date': '2024-01-08', 'price': 46000.0},
                {'date': '2024-01-15', 'price': 47000.0},
                {'date': '2024-01-22', 'price': 48000.0},
                {'date': '2024-01-29', 'price': 49000.0},
                {'date': '2024-02-05', 'price': 50000.0},
                {'date': '2024-02-12', 'price': 51000.0},
                {'date': '2024-02-19', 'price': 52000.0},
                {'date': '2024-02-26', 'price': 53000.0},
                {'date': '2024-03-04', 'price': 54000.0},
                {'date': '2024-03-11', 'price': 55000.0},
                {'date': '2024-03-18', 'price': 56000.0},
                {'date': '2024-03-25', 'price': 57000.0},
                {'date': '2024-04-01', 'price': 58000.0},
                {'date': '2024-04-08', 'price': 59000.0},
                {'date': '2024-04-15', 'price': 60000.0},
                {'date': '2024-04-22', 'price': 61000.0},
                {'date': '2024-04-29', 'price': 62000.0}
            ]
        }
    
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
            # For development, use test data
            if symbol in self.test_data:
                print(f"Using test data for {symbol}")
                return self.test_data[symbol]
            
            # Calculate date range - fetch 2 years of data for better EMA initialization
            end_date = datetime.now()
            start_date = end_date - timedelta(days=730)  # 2 years
            
            # Coinbase API endpoint for historical data
            url = f"{self.base_url}/products/{symbol}-USD/candles"
            print(f"Fetching data from: {url}")
            
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
                
                print(f"Requesting data from {current_start} to {current_end}")
                response = requests.get(url, params=params)
                
                if response.status_code == 200:
                    chunk_data = response.json()
                    print(f"Received {len(chunk_data)} data points")
                    if chunk_data:
                        # Convert Coinbase format to our format
                        for candle in chunk_data:
                            timestamp, open_price, high, low, close_price, volume = candle
                            date = datetime.fromtimestamp(timestamp)
                            # Keep all daily data
                            all_data.append({
                                'date': date.strftime('%Y-%m-%d'),
                                'price': float(close_price)  # Ensure price is float
                            })
                else:
                    print(f"Error response from Coinbase API: Status {response.status_code}")
                    print(f"Response: {response.text}")
                
                current_start = current_end + timedelta(days=1)
            
            return all_data
            
        except Exception as e:
            print(f"Error fetching historical data: {str(e)}")
            traceback.print_exc()
            return None
    
    def get_current_price(self, symbol):
        """Get the current price from Coinbase API."""
        try:
            url = f"{self.base_url}/products/{symbol}-USD/ticker"
            print(f"Fetching current price from: {url}")
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                price = float(data['price'])
                print(f"Current price for {symbol}: ${price:,.2f}")
                return price
            else:
                print(f"Failed to get current price from Coinbase. Status code: {response.status_code}")
                print(f"Response content: {response.text}")
        except Exception as e:
            print(f"Error getting current price from Coinbase: {str(e)}")
            traceback.print_exc()
        
        return None

class CryptoAnalyzer:
    def __init__(self):
        print("Initializing CryptoAnalyzer...")
        self.coinbase_api = CoinbaseAPI()
        self.cache_dir = "cache"
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        print("CryptoAnalyzer initialized successfully")
    
    def fetch_historical_data(self, symbol):
        """Fetch historical data for a symbol using Coinbase API."""
        try:
            # Calculate date range - fetch 2 years of data for better EMA initialization
            end_date = datetime.now()
            start_date = end_date - timedelta(days=730)  # 2 years
            
            # Coinbase API endpoint for historical data
            url = f"{self.coinbase_api.base_url}/products/{symbol}-USD/candles"
            print(f"Fetching data from: {url}")
            
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
                
                print(f"Requesting data from {current_start} to {current_end}")
                response = requests.get(url, params=params)
                
                if response.status_code == 200:
                    chunk_data = response.json()
                    print(f"Received {len(chunk_data)} data points")
                    if chunk_data:
                        # Convert Coinbase format to our format
                        for candle in chunk_data:
                            timestamp, open_price, high, low, close_price, volume = candle
                            date = datetime.fromtimestamp(timestamp)
                            # Keep all daily data
                            all_data.append({
                                'date': date.strftime('%Y-%m-%d'),
                                'price': float(close_price)  # Ensure price is float
                            })
                else:
                    print(f"Error response from Coinbase API: Status {response.status_code}")
                    print(f"Response: {response.text}")
                    return None
                
                # Move to next chunk
                current_start = current_end
                # Small delay to avoid rate limiting
                time.sleep(0.5)
            
            if all_data:
                print(f"Total data points collected: {len(all_data)}")
                # Sort by date ascending
                all_data.sort(key=lambda x: x['date'])
                return all_data
            
            print("No data points collected")
            return None
            
        except Exception as e:
            print(f"Error fetching historical data: {str(e)}")
            traceback.print_exc()
            return None
    
    def get_current_price(self, symbol):
        """Get current price using Coinbase API."""
        return self.coinbase_api.get_current_price(symbol)
    
    def analyze_crypto(self, symbol):
        """Analyze cryptocurrency using MACD that matches TradingView's implementation."""
        try:
            # Fetch historical data
            data = self.fetch_historical_data(symbol)
            
            if data is None:
                return None
                
            if len(data) < 180:
                return None
                
            # Convert to DataFrame
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # Resample to weekly data (using Saturday as the end of week)
            weekly_df = df.resample('W-SAT').last()
            
            # Calculate EMAs using TradingView's formula
            def calculate_tv_ema(data, length):
                alpha = 2 / (length + 1)
                ema = pd.Series(index=data.index, dtype=float)
                # Initialize with first value
                ema.iloc[0] = data.iloc[0]
                # Calculate EMA
                for i in range(1, len(data)):
                    ema.iloc[i] = data.iloc[i] * alpha + ema.iloc[i-1] * (1 - alpha)
                return ema
            
            # Calculate MACD using TradingView's method
            fast_ema = calculate_tv_ema(weekly_df['price'], 12)  # 12-period EMA
            slow_ema = calculate_tv_ema(weekly_df['price'], 26)  # 26-period EMA
            macd = fast_ema - slow_ema  # MACD Line
            signal = calculate_tv_ema(macd, 9)  # Signal Line (9-period EMA of MACD)
            
            # Add to DataFrame
            weekly_df['macd_line'] = macd
            weekly_df['signal_line'] = signal
            weekly_df['distance'] = macd - signal
            
            # Drop rows with NaN values
            weekly_df = weekly_df.dropna()
            
            if len(weekly_df) < 2:
                return None
            
            # Get current date and previous Monday
            current_date = datetime.now()
            last_monday = current_date - timedelta(days=current_date.weekday())
            
            # Set start date to 8 weeks before last Monday
            start_date = last_monday - timedelta(weeks=8)
            
            # Filter data for display (last 8 weeks)
            display_df = weekly_df[weekly_df.index >= start_date]
            
            # Prepare historical data
            historical_data = []
            previous_distance = None
            previous_trend = None
            current_market = None  # Track current market state
            previous_macd = None
            previous_macd_trend = None
            
            for i in range(len(weekly_df)):
                date = weekly_df.index[i]
                monday_date = date - pd.Timedelta(days=date.weekday())  # Get Monday of the week
                price = weekly_df['price'].iloc[i]
                macd_value = weekly_df['macd_line'].iloc[i]
                signal_value = weekly_df['signal_line'].iloc[i]
                distance = weekly_df['distance'].iloc[i]
                
                # Determine if this is a reversal point in distance
                is_reversal = False
                highlight_color = None
                market_message = None
                special_recommendation = None
                
                # Check for market transitions (crosses)
                if previous_distance is not None:
                    current_trend = 'increasing' if distance > previous_distance else 'decreasing'
                    
                    if (previous_distance <= 0 and distance > 0) or (previous_distance >= 0 and distance < 0):
                        if distance > 0:
                            market_message = "🚀 WELCOME TO THE BULL MARKET! 🚀"
                            current_market = 'bull'
                        else:
                            market_message = "😢 WELCOME TO THE BEAR MARKET! 😢"
                            current_market = 'bear'
                
                # Check for reversals in MACD
                is_macd_reversal = False
                if previous_macd is not None:
                    current_macd_trend = 'increasing' if macd_value > previous_macd else 'decreasing'
                    if previous_macd_trend is not None and current_macd_trend != previous_macd_trend:
                        is_macd_reversal = True
                
                if current_market == 'bear':
                    if is_macd_reversal and current_macd_trend == 'increasing':
                        is_reversal = True
                        highlight_color = 'lightgreen'
                        special_recommendation = "🚀 BUY ALERT: MACD reversal in Bear Market! MACD has started increasing, indicating potential bottom formation."
                        print(f"[Partial Buy] {monday_date.strftime('%Y-%m-%d')} - MACD reversal in Bear Market")
                    else:
                        highlight_color = 'lightyellow'
                        special_recommendation = "📊 HOLD/ACCUMULATE: In Bear Market, consider accumulating on dips while waiting for stronger reversal signals."
                elif current_market == 'bull':
                    if is_macd_reversal and current_macd_trend == 'decreasing':
                        is_reversal = True
                        highlight_color = 'lightred'
                        special_recommendation = "🚨 SELL ALERT: MACD reversal in Bull Market! MACD has started decreasing, indicating potential top formation."
                        print(f"[Partial Sell] {monday_date.strftime('%Y-%m-%d')} - MACD reversal in Bull Market")
                    else:
                        highlight_color = 'lightyellow'
                        special_recommendation = "📊 HOLD/SELL PARTIAL: In Bull Market, consider taking some profits while maintaining core position."
                
                # Update previous values for next iteration
                previous_macd_trend = current_macd_trend if 'current_macd_trend' in locals() else None
                previous_macd = macd_value
                previous_distance = distance
                previous_trend = 'increasing' if distance > previous_distance else 'decreasing' if previous_distance is not None else None
                
                week_data = {
                    'date': monday_date.strftime('%Y-%m-%d'),
                    'monday_date': monday_date.strftime('%Y-%m-%d'),
                    'date_formatted': monday_date.strftime('%b %d, %Y'),
                    'price': float(price),
                    'macd': float(macd_value),
                    'signal': float(signal_value),
                    'distance': float(distance),
                    'trend': 'Bullish' if distance > 0 else 'Bearish',
                    'is_reversal': is_reversal,
                    'highlight_color': highlight_color,
                    'market_message': market_message,
                    'special_recommendation': special_recommendation
                }
                historical_data.append(week_data)
            
            if not historical_data:
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
            
        except Exception as e:
            return None
    
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