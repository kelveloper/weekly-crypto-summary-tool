from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import pandas as pd
from io import StringIO
import re
import time
import random
from technical_analysis import CryptoAnalyzer
import requests
import traceback

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crypto.db'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    portfolio = db.relationship('Portfolio', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Portfolio model
class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    purchase_date = db.Column(db.Date, nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)
    transaction_id = db.Column(db.String(50), nullable=False)
    transaction_date = db.Column(db.Date, nullable=False)
    transaction_price = db.Column(db.Float, nullable=False)
    transaction_quantity = db.Column(db.Float, nullable=False)
    transaction_fee = db.Column(db.Float, nullable=False)
    transaction_total = db.Column(db.Float, nullable=False)

class WeeklyMACD(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    date = db.Column(db.Date, nullable=False)
    price = db.Column(db.Float, nullable=False)
    macd = db.Column(db.Float, nullable=False)
    signal = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<WeeklyMACD {self.symbol} {self.date}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('portfolio'))
    return redirect(url_for('register'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate username format
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            flash('Username must be 3-20 characters long and can only contain letters, numbers, and underscores')
            return redirect(url_for('register'))
        
        # Validate password strength
        if not re.match(r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}$', password):
            flash('Password must be at least 8 characters long and contain at least one number, one uppercase and one lowercase letter')
            return redirect(url_for('register'))
        
        # Check password confirmation
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register'))
        
        # Check if username exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        # Check if email exists
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return redirect(url_for('register'))
        
        # Validate email format
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('Invalid email format')
            return redirect(url_for('register'))
        
        # Create new user
        user = User(username=username, email=email)
        user.password_hash = generate_password_hash(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            # Always redirect to portfolio page after login
            return redirect(url_for('portfolio'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/portfolio')
@login_required
def portfolio():
    try:
        # Get page number from request args, default to 1
        page = request.args.get('page', 1, type=int)
        per_page = 20  # Increased to 20 transactions per page
        
        # Get paginated transactions for the current user
        transactions = Portfolio.query.filter_by(user_id=current_user.id)\
            .order_by(Portfolio.transaction_date.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        # Calculate current holdings
        holdings = {}
        for transaction in transactions.items:
            symbol = transaction.symbol
            if symbol not in holdings:
                holdings[symbol] = {
                    'quantity': 0,
                    'total_cost': 0,
                    'average_price': 0,
                    'current_price': 0,
                    'total_value': 0,
                    'profit_loss': 0,
                    'profit_loss_percentage': 0
                }
            
            if transaction.transaction_type == 'buy':
                holdings[symbol]['quantity'] += transaction.quantity
                holdings[symbol]['total_cost'] += transaction.quantity * transaction.purchase_price
            else:  # sell
                holdings[symbol]['quantity'] -= transaction.quantity
                holdings[symbol]['total_cost'] -= transaction.quantity * transaction.purchase_price
        
        # Remove holdings with zero quantity
        holdings = {k: v for k, v in holdings.items() if v['quantity'] > 0}
        
        # Calculate current values and profit/loss
        total_portfolio_value = 0
        total_profit_loss = 0
        for symbol, data in holdings.items():
            try:
                # Get current price from Alpha Vantage
                url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}USD&apikey={ALPHA_VANTAGE_API_KEY}"
                response = requests.get(url)
                if response.status_code == 200:
                    quote = response.json().get('Global Quote', {})
                    current_price = float(quote.get('05. price', 0))
                    data['current_price'] = current_price
                    data['total_value'] = data['quantity'] * current_price
                    data['average_price'] = data['total_cost'] / data['quantity']
                    data['profit_loss'] = data['total_value'] - data['total_cost']
                    data['profit_loss_percentage'] = (data['profit_loss'] / data['total_cost']) * 100
                    
                    total_portfolio_value += data['total_value']
                    total_profit_loss += data['profit_loss']
            except Exception as e:
                print(f"Error getting price for {symbol}: {str(e)}")
                continue
        
        # Sort holdings by total value (descending)
        holdings = dict(sorted(holdings.items(), key=lambda x: x[1]['total_value'], reverse=True))
        
        return render_template('portfolio.html', 
                             transactions=transactions,
                             holdings=holdings,
                             total_portfolio_value=total_portfolio_value,
                             total_profit_loss=total_profit_loss)
    except Exception as e:
        print(f"Error loading portfolio: {str(e)}")
        flash('Error loading portfolio. Please try again later.', 'error')
        return redirect(url_for('index'))

@app.route('/import_csv', methods=['POST'])
@login_required
def import_csv():
    if 'csv_file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('portfolio'))
    
    file = request.files['csv_file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('portfolio'))
    
    if not file.filename.endswith('.csv'):
        flash('Please upload a CSV file', 'error')
        return redirect(url_for('portfolio'))
    
    try:
        # Read the file content
        content = file.read().decode('utf-8')
        lines = content.split('\n')
        
        # Check for existing transactions
        existing_transactions = set()
        for transaction in Portfolio.query.filter_by(user_id=current_user.id).all():
            existing_transactions.add((transaction.transaction_id, transaction.symbol, transaction.quantity, transaction.purchase_price))
        
        new_transactions = []
        duplicate_count = 0
        
        # Skip the first two lines (headers)
        for line in lines[2:]:
            try:
                if not line.strip():
                    continue
                    
                # Split the line by commas
                parts = line.strip().split(',')
                if len(parts) >= 8:
                    transaction_id = parts[0].strip()
                    timestamp = parts[1].strip()
                    transaction_type = parts[2].strip()
                    symbol = parts[3].strip()
                    quantity = float(parts[4].strip())
                    price = float(parts[6].replace('$', '').replace(',', '').strip())
                    
                    # Check if transaction already exists
                    transaction_key = (transaction_id, symbol, quantity, price)
                    if transaction_key in existing_transactions:
                        duplicate_count += 1
                        continue
                    
                    # Create a new portfolio entry
                    holding = Portfolio(
                        user_id=current_user.id,
                        symbol=symbol,
                        purchase_date=datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S UTC').date(),
                        purchase_price=price,
                        quantity=quantity,
                        transaction_type=transaction_type,
                        transaction_id=transaction_id,
                        transaction_date=datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S UTC').date(),
                        transaction_price=price,
                        transaction_quantity=quantity,
                        transaction_fee=0.0,  # Default to 0 if not available
                        transaction_total=price * quantity
                    )
                    new_transactions.append(holding)
                    print(f"Preparing to add transaction: {holding.symbol} - {holding.quantity}")
            except Exception as e:
                print(f"Error processing line: {line}")
                print(f"Error details: {str(e)}")
                continue
        
        if duplicate_count > 0:
            flash(f'Skipped {duplicate_count} duplicate transactions', 'warning')
        
        if new_transactions:
            for holding in new_transactions:
                db.session.add(holding)
            db.session.commit()
            flash(f'Successfully imported {len(new_transactions)} new transactions!', 'success')
        else:
            flash('No new transactions to import', 'info')
            
    except Exception as e:
        db.session.rollback()
        print(f"Error importing CSV: {str(e)}")
        flash(f'Error importing CSV: {str(e)}', 'error')
    
    return redirect(url_for('portfolio'))

@app.route('/clear_all_transactions', methods=['POST'])
@login_required
def clear_all_transactions():
    try:
        # Delete all transactions for the current user
        Portfolio.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        flash('All transactions have been cleared successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error clearing transactions: {str(e)}', 'error')
    
    return redirect(url_for('portfolio'))

@app.route('/add_holding', methods=['GET', 'POST'])
@login_required
def add_holding():
    if request.method == 'POST':
        try:
            # Generate a unique transaction ID for manual entries
            transaction_id = f"manual_{int(time.time())}_{random.randint(1000, 9999)}"
            
            holding = Portfolio(
                user_id=current_user.id,
                symbol=request.form.get('symbol'),
                purchase_date=datetime.strptime(request.form.get('purchase_date'), '%Y-%m-%d').date(),
                purchase_price=float(request.form.get('purchase_price')),
                quantity=float(request.form.get('quantity')),
                transaction_type='Buy',  # Default to Buy for manual entries
                transaction_id=transaction_id,
                transaction_date=datetime.strptime(request.form.get('purchase_date'), '%Y-%m-%d').date(),
                transaction_price=float(request.form.get('purchase_price')),
                transaction_quantity=float(request.form.get('quantity')),
                transaction_fee=0.0,  # Default to 0 for manual entries
                transaction_total=float(request.form.get('purchase_price')) * float(request.form.get('quantity'))
            )
            db.session.add(holding)
            db.session.commit()
            flash('Holding added successfully!')
            return redirect(url_for('portfolio'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding holding: {str(e)}')
            return redirect(url_for('add_holding'))
    
    return render_template('add_holding.html')

@app.route('/delete_transaction/<int:transaction_id>', methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    try:
        transaction = Portfolio.query.get_or_404(transaction_id)
        # Ensure the transaction belongs to the current user
        if transaction.user_id != current_user.id:
            flash('Unauthorized action')
            return redirect(url_for('portfolio'))
        
        db.session.delete(transaction)
        db.session.commit()
        flash('Transaction deleted successfully!')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting transaction: {str(e)}')
    
    return redirect(url_for('portfolio'))

@app.route('/edit_holding/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_holding(id):
    holding = Portfolio.query.get_or_404(id)
    # Ensure the holding belongs to the current user and is a manual input
    if holding.user_id != current_user.id or holding.transaction_id:
        flash('Unauthorized action')
        return redirect(url_for('portfolio'))
    
    if request.method == 'POST':
        try:
            holding.symbol = request.form.get('symbol')
            holding.quantity = float(request.form.get('quantity'))
            holding.purchase_price = float(request.form.get('purchase_price'))
            holding.transaction_price = holding.purchase_price
            holding.transaction_quantity = holding.quantity
            holding.transaction_total = holding.quantity * holding.purchase_price
            
            db.session.commit()
            flash('Holding updated successfully!')
            return redirect(url_for('portfolio'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating holding: {str(e)}')
    
    return render_template('edit_holding.html', holding=holding)

@app.route('/get_realtime_data')
@login_required
def get_realtime_data():
    try:
        analyzer = CryptoAnalyzer()
        # Get current price
        current_price = analyzer.get_current_price('BTC')
        
        if current_price is None:
            return jsonify({'error': 'Unable to fetch current price'})
            
        # Get historical data for MACD calculation
        data = analyzer.fetch_historical_data('BTC')
        if data is None or len(data) < 180:  # Need at least 180 days of data
            return jsonify({'error': 'Not enough historical data for analysis'})
            
        # Convert to DataFrame
        df = pd.DataFrame(data)
        if 'timestamp' in df.columns:
            df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        else:
            df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Set start date to January 1, 2025
        start_date = pd.Timestamp('2025-01-01')
        df = df[df.index >= start_date]
        
        # Get all Mondays
        mondays = pd.date_range(start=start_date, end=pd.Timestamp.now(), freq='W-MON')
        if len(mondays) < 35:  # Need at least 35 weeks for full MACD calculation
            return jsonify({'error': 'Not enough weekly data points for MACD calculation'})
        
        # Create a new DataFrame with only Monday data
        weekly_data = pd.DataFrame(index=mondays)
        weekly_data['close'] = df['price'].resample('W-MON').last()
        
        # Calculate EMAs using TradingView's formula
        def calculate_ema(data, length):
            alpha = 2 / (length + 1)
            ema = pd.Series(index=data.index, dtype=float)
            
            # Initialize with first value
            ema.iloc[0] = data.iloc[0]
            
            # Calculate EMA for remaining periods
            for i in range(1, len(data)):
                ema.iloc[i] = data.iloc[i] * alpha + ema.iloc[i-1] * (1 - alpha)
            
            return ema
        
        # Calculate MACD using TradingView's method
        # First calculate the 12 and 26 period EMAs
        fast_ema = calculate_ema(weekly_data, 12)
        slow_ema = calculate_ema(weekly_data, 26)
        
        # Calculate MACD line (difference between EMAs)
        macd = fast_ema - slow_ema
        
        # Calculate Signal line (9-period EMA of MACD)
        signal = calculate_ema(macd, 9)
        
        # Get current values (safely)
        if len(macd) > 0 and len(signal) > 0:
            current_macd = macd.iloc[-1]
            current_signal = signal.iloc[-1]
            current_distance = current_macd - current_signal
            
            # Print current values for debugging
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n[{current_time}] Current Values:")
            print(f"Bitcoin Price: ${current_price:.2f}")
            print(f"MACD: {current_macd:.4f}")
            print(f"Signal: {current_signal:.4f}")
            print(f"Distance: {current_distance:.4f}")
            
            return jsonify({
                'price': current_price,
                'macd': float(current_macd),
                'signal': float(current_signal),
                'distance': float(current_distance),
                'timestamp': current_time
            })
        else:
            return jsonify({'error': 'Unable to calculate current MACD values'})
            
    except Exception as e:
        print(f"Error getting real-time data: {str(e)}")
        traceback.print_exc()  # Print full traceback for debugging
        return jsonify({'error': str(e)})

@app.route('/weekly_summary')
@login_required
def weekly_summary():
    try:
        analyzer = CryptoAnalyzer()
        
        # Get historical data
        data = analyzer.fetch_historical_data('BTC')
        if data is None:
            return render_template('weekly_summary.html', error="No data available")
            
        # Convert to DataFrame
        df = pd.DataFrame(data)
        if 'timestamp' in df.columns:
            df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['price'] = df['price'].astype(float)
        else:
            df['date'] = pd.to_datetime(df['date'])
            df['price'] = df['price'].astype(float)
        df.set_index('date', inplace=True)
        
        # Get the closing price of each week (Sunday)
        weekly_data = df['price'].resample('W-SUN').last()
        
        # Convert Sunday dates to Monday dates
        weekly_data.index = weekly_data.index - pd.Timedelta(days=6)
        
        # Calculate EMAs using TradingView's formula
        def calculate_ema(data, length):
            alpha = 2 / (length + 1)
            ema = pd.Series(index=data.index, dtype=float)
            
            # Initialize with first value
            ema.iloc[0] = data.iloc[0]
            
            # Calculate EMA for remaining periods
            for i in range(1, len(data)):
                ema.iloc[i] = data.iloc[i] * alpha + ema.iloc[i-1] * (1 - alpha)
            
            return ema
        
        # Calculate MACD using TradingView's method
        # First calculate the 12 and 26 period EMAs
        fast_ema = calculate_ema(weekly_data, 12)
        slow_ema = calculate_ema(weekly_data, 26)
        
        # Calculate MACD line (difference between EMAs)
        macd = fast_ema - slow_ema
        
        # Calculate Signal line (9-period EMA of MACD)
        signal = calculate_ema(macd, 9)
        
        # Print weekly analysis
        print("\nWeekly MACD Analysis:")
        print("=" * 100)
        print(f"{'Date':<15} {'Price':<15} {'MACD':<15} {'Signal':<15} {'Distance':<15} {'Trend':<10}")
        print("-" * 100)
        
        for i in range(len(weekly_data)):
            date = weekly_data.index[i]
            price = weekly_data.iloc[i]
            macd_value = macd.iloc[i]
            signal_value = signal.iloc[i]
            distance = macd_value - signal_value
            trend = "Bullish" if distance > 0 else "Bearish"
            
            print(f"{date.strftime('%Y-%m-%d'):<15} ${price:>10.2f} {macd_value:>14.4f} {signal_value:>14.4f} {distance:>14.4f} {trend:>10}")
        
        print("=" * 100)
        
        # Create weekly data list for template
        weekly_data_list = []
        previous_distance = None
        
        for i in range(len(weekly_data)):
            date = weekly_data.index[i]
            price = weekly_data.iloc[i]
            macd_value = macd.iloc[i]
            signal_value = signal.iloc[i]
            distance = macd_value - signal_value
            
            weekly_data_list.append({
                'date': date,
                'price': price,
                'macd': macd_value,
                'signal': signal_value,
                'distance': distance,
                'previous_distance': previous_distance
            })
            previous_distance = distance

        # Get current week's data
        current_week = weekly_data_list[-1]
        previous_week = weekly_data_list[-2] if len(weekly_data_list) > 1 else None
        
        # Generate recommendation based on current trend and momentum
        recommendation = ""
        if current_week['distance'] > 0:
            if previous_week and previous_week['distance'] <= 0:
                recommendation = "Strong Buy Signal: Golden Cross detected. MACD has crossed above the signal line, indicating a potential upward trend."
            elif current_week['distance'] > previous_week['distance']:
                recommendation = "Buy/Hold: Bullish trend strengthening. MACD distance from signal line is increasing."
            else:
                recommendation = "Hold: Bullish trend continuing but momentum may be slowing. Monitor for potential trend reversal."
        else:
            if previous_week and previous_week['distance'] > 0:
                recommendation = "Strong Sell Signal: Death Cross detected. MACD has crossed below the signal line, indicating a potential downward trend."
            elif current_week['distance'] < previous_week['distance']:
                recommendation = "Sell/Hold: Bearish trend strengthening. MACD distance from signal line is increasing."
            else:
                recommendation = "Hold: Bearish trend continuing but momentum may be slowing. Monitor for potential trend reversal."

        # Create analysis object for template
        analysis = {
            'current_week_data': current_week,
            'previous_week_data': previous_week,
            'recommendation': recommendation
        }
        
        return render_template('weekly_summary.html',
                             analysis=analysis,
                             weekly_data=weekly_data_list)
                             
    except Exception as e:
        print(f"Error in weekly_summary: {str(e)}")
        traceback.print_exc()
        return render_template('weekly_summary.html', error=str(e))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Check for existing users
        users = User.query.all()
        if not users:
            print("No users found in the database. Please register a new user.")
        else:
            print(f"Found {len(users)} users in the database.")
    app.run(debug=True, host='0.0.0.0', port=5001) 