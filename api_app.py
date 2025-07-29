from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import re
import time
import random
import os
from technical_analysis import CryptoAnalyzer
import traceback
import jwt

app = Flask(__name__)

# Database configuration for deployment
if os.environ.get('DATABASE_URL'):
    # For production (PostgreSQL, MySQL, etc.)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
else:
    # For development (SQLite)
    db_path = os.environ.get('DB_PATH', '/data/crypto.db')  # Use persistent volume in production
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-string')
app.config['JWT_EXPIRATION_DELTA'] = timedelta(hours=24)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# CORS configuration
cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
CORS(app, origins=cors_origins, supports_credentials=True)

db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'purchase_date': self.purchase_date.isoformat(),
            'purchase_price': self.purchase_price,
            'quantity': self.quantity,
            'transaction_type': self.transaction_type,
            'transaction_total': self.transaction_total,
            'created_at': self.created_at.isoformat()
        }

def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + app.config['JWT_EXPIRATION_DELTA']
    }
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except:
        return None

def token_required(f):
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            token = token.split(' ')[1]
            user_id = verify_token(token)
            if user_id is None:
                return jsonify({'error': 'Token is invalid'}), 401
            current_user = User.query.get(user_id)
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
        except:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(current_user, *args, **kwargs)
    
    decorated.__name__ = f.__name__
    return decorated

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email') 
        password = data.get('password')
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        token = generate_token(user.id)
        return jsonify({
            'message': 'Registration successful!',
            'token': token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            token = generate_token(user.id)
            return jsonify({
                'message': 'Login successful!',
                'token': token,
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio', methods=['GET'])
@token_required
def get_portfolio(current_user):
    try:
        transactions = Portfolio.query.filter_by(user_id=current_user.id).order_by(Portfolio.created_at.desc()).all()
        return jsonify({
            'transactions': [t.to_dict() for t in transactions]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/add_holding', methods=['POST'])
@token_required
def add_holding(current_user):
    try:
        data = request.get_json()
        
        transaction_id = f"manual_{int(time.time())}_{random.randint(1000, 9999)}"
        
        holding = Portfolio(
            user_id=current_user.id,
            symbol=data.get('symbol').upper(),  # Standardize to uppercase
            purchase_date=datetime.strptime(data.get('purchase_date'), '%Y-%m-%d').date(),
            purchase_price=float(data.get('purchase_price')),
            quantity=float(data.get('quantity')),
            transaction_type='Buy',
            transaction_id=transaction_id,
            transaction_date=datetime.strptime(data.get('purchase_date'), '%Y-%m-%d').date(),
            transaction_price=float(data.get('purchase_price')),
            transaction_quantity=float(data.get('quantity')),
            transaction_fee=0.0,
            transaction_total=float(data.get('purchase_price')) * float(data.get('quantity'))
        )
        db.session.add(holding)
        db.session.commit()
        
        return jsonify({
            'message': 'Holding added successfully!',
            'holding': holding.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for deployment"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

def init_db():
    """Initialize database with proper error handling"""
    try:
        # Ensure the directory exists for SQLite
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///'):
            db_file = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            db_dir = os.path.dirname(db_file)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
        
        db.create_all()
        print(f"Database initialized successfully")
        
        # Check if there are any users
        user_count = User.query.count()
        print(f"Current user count: {user_count}")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

if __name__ == '__main__':
    with app.app_context():
        init_db()
    
    port = int(os.environ.get('PORT', 5001))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(debug=debug, host=host, port=port)
