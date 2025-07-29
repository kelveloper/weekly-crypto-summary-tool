# 📈 CoinFolio Analytics - Crypto Portfolio & Technical Analysis Tool

![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.2-green.svg)
![React](https://img.shields.io/badge/react-19.1.0-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A comprehensive cryptocurrency portfolio management and technical analysis application that helps you track your investments, analyze market trends, and make informed trading decisions using MACD (Moving Average Convergence Divergence) indicators.

## ✨ Features

### 📊 Portfolio Management
- **User Authentication**: Secure registration and login system
- **Portfolio Tracking**: Add, edit, and manage crypto holdings
- **Transaction History**: Detailed transaction logs with dates and amounts
- **Real-time Prices**: Live price tracking from Coinbase API
- **Multi-cryptocurrency Support**: Track Bitcoin, Ethereum, and other major cryptocurrencies

### 📈 Technical Analysis
- **MACD Analysis**: Advanced MACD (12, 26, 9) analysis matching TradingView's implementation
- **Weekly Data Processing**: Analyzes weekly price movements for better trend identification
- **Interactive Charts**: Dynamic charts using Chart.js with clickable data points
- **Trend Detection**: Automatic bullish/bearish trend identification
- **Golden/Death Cross Alerts**: Real-time alerts for MACD signal crossovers
- **Historical Analysis**: Review past performance and trends

### 🎯 Trading Signals
- **Buy/Sell Recommendations**: AI-powered trading recommendations based on MACD analysis
- **Market Reversal Detection**: Identifies potential market tops and bottoms
- **Momentum Analysis**: Tracks momentum changes and trend strength
- **Special Alerts**: Market transition notifications (Bull/Bear market entries)

### 🔧 Advanced Features
- **Responsive Design**: Mobile-friendly interface
- **Data Caching**: Intelligent caching system for improved performance
- **Backup & Restore**: Automated database backup and restore functionality
- **Deployment Ready**: Docker containerization and production deployment scripts
- **API Support**: RESTful API for frontend integration

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+ (for frontend)
- Docker (optional, for containerized deployment)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/kelveloper/weekly-crypto-summary-tool.git
   cd weekly-crypto-summary-tool
   ```

2. **Set up Python environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Initialize the database**
   ```bash
   python3 init_db.py
   ```

4. **Run the application**
   ```bash
   python3 app.py
   ```

5. **Access the application**
   - Web Interface: http://127.0.0.1:5001
   - API Endpoint: http://127.0.0.1:5001/api

### Docker Deployment (Recommended)

1. **Quick deployment with script**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

2. **Manual Docker deployment**
   ```bash
   # Create persistent directories
   mkdir -p data backups logs

   # Build and run with Docker Compose
   docker-compose up --build -d

   # Check status
   docker-compose ps
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - API: http://localhost:5001

## 📋 Usage Guide

### Getting Started
1. **Register a new account** or log in with existing credentials
2. **Add your crypto holdings** with purchase dates and amounts
3. **Navigate to Technical Analysis** to view MACD charts and recommendations
4. **Monitor weekly summaries** for market insights

### Technical Analysis Features

#### MACD Analysis
- **Basic Mode**: Pre-configured settings for quick analysis
- **Advanced Mode**: Customize all parameters and thresholds
- **Multiple Timeframes**: Weekly analysis for better trend identification
- **Interactive Charts**: Click on chart points to see detailed analysis

#### Understanding the Signals
- **Golden Cross** 🟢: MACD crosses above signal line (Bullish)
- **Death Cross** 🔴: MACD crosses below signal line (Bearish)
- **Distance**: Measures the strength of the current trend
- **Momentum**: Indicates if the trend is strengthening or weakening

### Portfolio Management
- **Add Holdings**: Enter cryptocurrency, amount, and purchase details
- **Track Performance**: View real-time portfolio value and gains/losses
- **Transaction History**: Detailed log of all trading activities
- **Export Data**: Backup your portfolio data

## 🏗️ Architecture

### Backend (Flask)
- **app.py**: Main Flask application with web interface
- **api_app.py**: RESTful API server for frontend integration
- **technical_analysis.py**: MACD calculation and analysis engine
- **Database**: SQLite with automatic migrations

### Frontend (React)
- **crypto-frontend/**: Modern React application
- **Components**: Modular components for portfolio, analysis, and authentication
- **Bootstrap**: Responsive UI framework

### Data Processing
- **Coinbase API**: Real-time price data
- **MACD Calculation**: TradingView-compatible implementation
- **Weekly Aggregation**: Saturday-based weekly data processing
- **Caching System**: Intelligent data caching for performance

## 🛠️ Technology Stack

### Backend
- **Flask 3.0.2**: Web framework
- **SQLAlchemy**: Database ORM
- **Flask-Login**: User authentication
- **pandas**: Data processing
- **ta**: Technical analysis library
- **requests**: API communication

### Frontend
- **React 19.1.0**: UI framework
- **Bootstrap 5.3.7**: CSS framework
- **Chart.js**: Interactive charts
- **Axios**: HTTP client
- **React Router**: Navigation

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-service orchestration
- **SQLite/PostgreSQL**: Database options
- **nginx**: Reverse proxy (production)

## 📊 API Documentation

### Authentication Endpoints
```
POST /api/register    - Register new user
POST /api/login       - User login
POST /api/logout      - User logout
```

### Portfolio Endpoints
```
GET  /api/portfolio           - Get user portfolio
POST /api/portfolio           - Add new holding
PUT  /api/portfolio/{id}      - Update holding
DELETE /api/portfolio/{id}    - Delete holding
```

### Analysis Endpoints
```
GET /api/analysis/{symbol}    - Get MACD analysis for symbol
GET /api/prices/{symbol}      - Get current price
GET /api/historical/{symbol}  - Get historical data
```

## 🔒 Security Features

- **Password Hashing**: Werkzeug security for password protection
- **Session Management**: Secure session handling
- **CORS Protection**: Configurable CORS policies
- **Environment Variables**: Secure configuration management
- **JWT Tokens**: API authentication (in api_app.py)

## 🗄️ Database Schema

### User Table
- id, username, email, password_hash, created_at

### Portfolio Table
- id, user_id, symbol, purchase_date, purchase_price, quantity, transaction_type, transaction_id, transaction_date

### WeeklyMACD Table
- id, symbol, date, price, macd, signal, created_at

## 🚀 Deployment Options

### 1. Local Development
Perfect for testing and development work.

### 2. Docker Containers
Recommended for most deployments with persistent data volumes.

### 3. Cloud Platforms
- **Heroku**: PaaS deployment
- **AWS ECS**: Container orchestration
- **Google Cloud Run**: Serverless containers
- **DigitalOcean**: VPS deployment

### 4. Traditional VPS
Deploy on any Linux server with Docker support.

For detailed deployment instructions, see [README_DEPLOYMENT.md](./README_DEPLOYMENT.md).

## 🛡️ Backup & Recovery

### Automated Backups
```bash
# Manual backup
python3 database_backup.py backup

# List backups
python3 database_backup.py list

# Restore from backup
python3 database_backup.py restore --backup-file backups/crypto_backup_20241226_120000.db
```

### Scheduled Backups
Set up automated daily backups using the included cron script:
```bash
chmod +x cron_backup.sh
# Add to crontab: 0 2 * * * /path/to/your/app/cron_backup.sh
```

## 🎨 Screenshots

### Portfolio Dashboard
Track your cryptocurrency holdings with real-time value updates and performance metrics.

### MACD Analysis
Interactive MACD charts with detailed technical analysis and trading recommendations.

### Trading Signals
Get actionable buy/sell signals based on MACD crossovers and momentum analysis.

## 🔧 Configuration

### Environment Variables
```bash
# Database
DB_PATH=/data/crypto.db
DATABASE_URL=postgresql://user:pass@host:5432/db

# Security
SECRET_KEY=your-super-secure-32-character-key
JWT_SECRET_KEY=your-jwt-secret-key

# API
CORS_ORIGINS=http://localhost:3000
FLASK_ENV=production
```

### Customization
- **MACD Parameters**: Modify fast (12), slow (26), and signal (9) periods
- **Update Frequency**: Configure data refresh intervals
- **Supported Coins**: Add new cryptocurrencies to the analysis
- **UI Themes**: Customize colors and styling

## 📚 Educational Content

### MACD Explained
The Moving Average Convergence Divergence (MACD) is a trend-following momentum indicator that shows the relationship between two moving averages of a security's price.

### Trading Strategy
- **Golden Cross**: When MACD crosses above the signal line, it's often considered a bullish signal
- **Death Cross**: When MACD crosses below the signal line, it's often considered a bearish signal
- **Divergence**: When price moves in the opposite direction of MACD, it may signal a trend reversal

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **TradingView**: MACD calculation methodology
- **Coinbase**: Real-time price data API
- **Chart.js**: Interactive charting library
- **Bootstrap**: UI component framework

## 📞 Support

- **Documentation**: Check [README_DEPLOYMENT.md](./README_DEPLOYMENT.md) for deployment help
- **Issues**: Open an issue on GitHub for bug reports
- **Discussions**: Use GitHub Discussions for questions and feature requests

## 🔮 Roadmap

### Upcoming Features
- **Multiple Indicators**: RSI, Bollinger Bands, Moving Averages
- **Portfolio Analytics**: Advanced performance metrics
- **Price Alerts**: Custom price and indicator alerts
- **Mobile App**: Native mobile application
- **Social Features**: Share analysis and follow other traders
- **AI Predictions**: Machine learning-based price predictions

---

<div align="center">

**Built with ❤️ for the crypto community**

[⭐ Star this repo](https://github.com/kelveloper/weekly-crypto-summary-tool) | [🐛 Report Bug](https://github.com/kelveloper/weekly-crypto-summary-tool/issues) | [💡 Request Feature](https://github.com/kelveloper/weekly-crypto-summary-tool/issues)

</div>
