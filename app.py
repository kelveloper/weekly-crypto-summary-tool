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
import ta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Fixed secret key
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
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate username format
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            flash('Username must be 3-20 characters long and can only contain letters, numbers, and underscores', 'error')
            return redirect(url_for('register'))
        
        # Validate password strength
        if not re.match(r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}$', password):
            flash('Password must be at least 8 characters long and contain at least one number, one uppercase and one lowercase letter', 'error')
            return redirect(url_for('register'))
        
        # Check password confirmation
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
        
        # Check if username exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        # Check if email exists
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('register'))
        
        # Validate email format
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('Invalid email format', 'error')
            return redirect(url_for('register'))
        
        # Create new user
        user = User(username=username, email=email)
        user.password_hash = generate_password_hash(password)
        db.session.add(user)
        db.session.commit()
        
        # Log the user in automatically
        login_user(user)
        
        # Show success message and redirect to portfolio
        flash('Registration successful!', 'success')
        return redirect(url_for('portfolio'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        print(f"Login attempt for username: {username}")  # Debug log
        
        # Only show error if both fields are filled
        if username and password:
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                print(f"Login successful for user: {user.id}")  # Debug log
                login_user(user)
                return redirect(url_for('portfolio'))
            else:
                print("Login failed - invalid credentials")  # Debug log
                flash('Invalid username or password', 'error')
        else:
            print("Login failed - missing fields")  # Debug log
            flash('Please enter both username and password', 'error')
        return redirect(url_for('login'))
    return render_template('login.html')

@login_manager.unauthorized_handler
def unauthorized():
    flash('Please log in to access this page', 'error')
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/portfolio')
@login_required
def portfolio():
    try:
        print(f"Current user: {current_user.id}")  # Debug log
        
        # Get all transactions for the current user in reverse chronological order
        transactions = Portfolio.query.filter_by(user_id=current_user.id)\
            .order_by(Portfolio.transaction_date.desc())\
            .all()
        
        print(f"Total transactions found: {len(transactions)}")  # Debug log
        
        # Calculate current holdings
        holdings = {}
        # Calculate BTC total investment separately
        btc_total_investment = 0
        btc_quantity = 0.0  # Explicitly set to 0.0
        # Calculate total initial investment by summing all transaction totals
        total_initial_investment = sum(transaction.transaction_total for transaction in transactions)
        
        # Group transactions by symbol
        transactions_by_symbol = {}
        for transaction in transactions:
            symbol = transaction.symbol
            if symbol not in transactions_by_symbol:
                transactions_by_symbol[symbol] = []
            transactions_by_symbol[symbol].append(transaction)
        
        # Calculate quantities for each symbol
        for symbol, symbol_transactions in transactions_by_symbol.items():
            # Sort transactions by date (oldest first)
            symbol_transactions.sort(key=lambda x: x.transaction_date)
            
            running_quantity = 0.0
            for transaction in symbol_transactions:
                # Simply add the transaction quantity (negative for sells, positive for buys)
                running_quantity += transaction.transaction_quantity
            
            # Store the final quantity
            if running_quantity > 0:
                holdings[symbol] = {
                    'quantity': running_quantity,
                    'total_cost': sum(t.transaction_total for t in symbol_transactions),
                    'average_price': sum(t.transaction_total for t in symbol_transactions) / running_quantity
                }
        
        # Remove holdings with zero quantity
        holdings = {k: v for k, v in holdings.items() if v['quantity'] > 0}
        
        # Get BTC specific values
        if 'BTC' in holdings:
            btc_quantity = holdings['BTC']['quantity']
            btc_total_investment = holdings['BTC']['total_cost']
        
        return render_template('portfolio.html', 
                             transactions=transactions,
                             holdings=holdings,
                             total_initial_investment=total_initial_investment,
                             btc_total_investment=btc_total_investment,
                             btc_quantity=btc_quantity)
    except Exception as e:
        print(f"Error in portfolio route: {str(e)}")  # Debug log
        print(f"Error type: {type(e)}")  # Debug log
        traceback.print_exc()  # Print full traceback
        flash('Error loading portfolio. Please try again later.', 'error')
        return redirect(url_for('login'))

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
        
        # Print file information
        print("\n=== CSV File Information ===")
        print(f"Total lines in file: {len(lines)}")
        print("\nFirst 5 lines:")
        for i, line in enumerate(lines[:5], 1):
            print(f"Line {i}: {line.strip()}")
        print("=======================\n")
        
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
                    # Get the total from the "Total (inclusive of fees and/or spread)" column
                    total = float(parts[8].replace('$', '').replace(',', '').strip())
                    
                    # Check if transaction already exists
                    transaction_key = (transaction_id, symbol, quantity, price)
                    if transaction_key in existing_transactions:
                        duplicate_count += 1
                        continue
                    
                    # Parse the date properly
                    try:
                        transaction_date = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S UTC').date()
                    except ValueError:
                        # Try alternative format if the first one fails
                        transaction_date = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').date()
                    
                    # Create a new portfolio entry
                    holding = Portfolio(
                        user_id=current_user.id,
                        symbol=symbol,
                        purchase_date=transaction_date,
                        purchase_price=price,
                        quantity=quantity,
                        transaction_type=transaction_type,
                        transaction_id=transaction_id,
                        transaction_date=transaction_date,
                        transaction_price=price,
                        transaction_quantity=quantity,
                        transaction_fee=0.0,  # Default to 0 if not available
                        transaction_total=total
                    )
                    new_transactions.append(holding)
                    print(f"Found new transaction: {holding.symbol} - {holding.quantity} @ ${holding.purchase_price} on {holding.transaction_date}")
            except Exception as e:
                print(f"Error processing line: {str(e)}")
                print(f"Problematic line: {line}")
                continue
        
        if duplicate_count > 0:
            flash(f'Skipped {duplicate_count} duplicate transactions', 'warning')
        
        if new_transactions:
            for holding in new_transactions:
                db.session.add(holding)
            db.session.commit()
            print(f"Successfully imported {len(new_transactions)} new transactions")
            flash(f'Successfully imported {len(new_transactions)} new transactions!', 'success')
        else:
            print("No new transactions found in CSV file")
            flash('No new transactions to import', 'error')
            
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
        flash('All transactions have been cleared successfully', 'success')
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
    transaction = Portfolio.query.get_or_404(transaction_id)
    if transaction.user_id != current_user.id:
        abort(403)
    db.session.delete(transaction)
    db.session.commit()
    flash('Transaction deleted successfully', 'success')
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

@app.route('/weekly_summary')
@login_required
def weekly_summary():
    try:
        analyzer = CryptoAnalyzer()
        
        # Get analysis data
        result = analyzer.analyze_crypto('BTC')
        if result is None:
            return render_template('weekly_summary.html', error="No data available")
        
        # Prepare data for template
        weekly_data = result['historical_data']
        current_week = result['current_week_data']
        # Format the date as 'Mon DD, YYYY'
        current_week['date_formatted'] = datetime.strptime(current_week['date'], '%Y-%m-%d').strftime('%b %d, %Y')
        previous_week = weekly_data[-2] if len(weekly_data) > 1 else None
        
        # Generate recommendation based on current trend and momentum
        recommendation = result['recommendation']
        
        # Create analysis object for template
        analysis = {
            'current_week_data': current_week,
            'previous_week_data': previous_week,
            'recommendation': recommendation
        }

        # Create summary object for template
        summary = {
            'technical_analysis': {
                'rsi': 'Overbought' if current_week['distance'] > 1000 else 'Oversold' if current_week['distance'] < -1000 else 'Neutral',
                'macd': f"{current_week['macd']:.2f}",
                'moving_averages': 'Bullish' if current_week['distance'] > 0 else 'Bearish',
                'support_resistance': 'Breaking Resistance' if current_week['distance'] > 0 else 'Testing Support'
            },
            'sentiment_analysis': {
                'social_media': 'Bullish' if current_week['distance'] > 0 else 'Bearish',
                'news_sentiment': 'Positive' if current_week['distance'] > 0 else 'Negative',
                'market_sentiment': 'Optimistic' if current_week['distance'] > 0 else 'Pessimistic'
            },
            'on_chain_analysis': {
                'network_activity': 'High' if current_week['distance'] > 0 else 'Low',
                'wallet_activity': 'Increasing' if current_week['distance'] > previous_week['distance'] else 'Decreasing',
                'supply_metrics': 'Accumulation' if current_week['distance'] > 0 else 'Distribution'
            },
            'market_analysis': {
                'volume_analysis': 'High' if current_week['distance'] > 0 else 'Low',
                'liquidity': 'Strong' if current_week['distance'] > 0 else 'Weak',
                'market_structure': 'Bullish' if current_week['distance'] > 0 else 'Bearish'
            }
        }
        
        return render_template('weekly_summary.html',
                             analysis=analysis,
                             weekly_data=weekly_data,
                             summary=summary)
                             
    except Exception as e:
        print(f"Error in weekly_summary: {str(e)}")
        traceback.print_exc()
        return render_template('weekly_summary.html', error=str(e), weekly_data=[])

@app.route('/macd_analysis_copy')
@login_required
def macd_analysis_copy():
    try:
        analyzer = CryptoAnalyzer()
        
        # Get the selected coin from the request args, default to BTC
        selected_coin = request.args.get('coin', 'BTC')
        
        # Get analysis data for the selected coin
        result = analyzer.analyze_crypto(selected_coin)
        if result is None:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'No data available'}), 404
            return render_template('macd_analysis_copy.html', error="No data available")
        
        # Prepare data for template
        weekly_data = result['historical_data']
        current_week = result['current_week_data']
        # Format the date as 'Mon DD, YYYY'
        current_week['date_formatted'] = datetime.strptime(current_week['date'], '%Y-%m-%d').strftime('%b %d, %Y')
        previous_week = weekly_data[-2] if len(weekly_data) > 1 else None
        
        # Generate recommendation based on current trend and momentum
        recommendation = result['recommendation']
        
        # Create analysis object for template
        analysis = {
            'current_week_data': current_week,
            'previous_week_data': previous_week,
            'recommendation': recommendation
        }

        # Get all unique coins from the user's portfolio
        portfolio_coins = set()
        for transaction in Portfolio.query.filter_by(user_id=current_user.id).all():
            portfolio_coins.add(transaction.symbol)
        
        # If it's an AJAX request, return JSON data
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'analysis': analysis,
                'weekly_data': weekly_data,
                'portfolio_coins': list(portfolio_coins),
                'current_coin': selected_coin
            })
        
        # Otherwise, render the template
        return render_template('macd_analysis_copy.html',
                             analysis=analysis,
                             weekly_data=weekly_data,
                             portfolio_coins=list(portfolio_coins),
                             current_coin=selected_coin)
                             
    except Exception as e:
        print(f"Error in macd_analysis_copy: {str(e)}")
        traceback.print_exc()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': str(e)}), 500
        return render_template('macd_analysis_copy.html', error=str(e), weekly_data=[])

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