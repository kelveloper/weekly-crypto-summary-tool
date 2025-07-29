import React from 'react';
import { Link, useNavigate } from 'react-router-dom';

const Navbar = ({ user, logout }) => {
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="navbar navbar-expand-lg navbar-dark" style={{
      background: 'linear-gradient(135deg, #0052FF, #0038B3)',
      boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)'
    }}>
      <div className="container">
        <Link className="navbar-brand" to="/">
          <i className="fas fa-coins me-2"></i>
          CoinFolio Analytics
        </Link>
        
        {user && (
          <>
            <button 
              className="navbar-toggler" 
              type="button" 
              data-bs-toggle="collapse" 
              data-bs-target="#navbarNav"
            >
              <span className="navbar-toggler-icon"></span>
            </button>
            
            <div className="collapse navbar-collapse" id="navbarNav">
              <ul className="navbar-nav me-auto">
                <li className="nav-item">
                  <Link className="nav-link" to="/portfolio">
                    <i className="fas fa-wallet me-1"></i> Portfolio
                  </Link>
                </li>
                <li className="nav-item">
                  <Link className="nav-link" to="/add-holding">
                    <i className="fas fa-plus me-1"></i> Add Holding
                  </Link>
                </li>
                <li className="nav-item">
                  <Link className="nav-link" to="/weekly-summary">
                    <i className="fas fa-chart-line me-1"></i> Weekly Summary
                  </Link>
                </li>
                <li className="nav-item">
                  <Link className="nav-link" to="/macd-analysis">
                    <i className="fas fa-chart-area me-1"></i> MACD Analysis
                  </Link>
                </li>
              </ul>
              
              <div className="navbar-nav">
                <span className="navbar-text me-3">
                  Welcome, {user.username}!
                </span>
                <button 
                  className="btn btn-outline-light btn-sm" 
                  onClick={handleLogout}
                >
                  <i className="fas fa-sign-out-alt me-1"></i> Logout
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </nav>
  );
};

export default Navbar; 