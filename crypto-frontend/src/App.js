import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import '@fortawesome/fontawesome-free/css/all.min.css';
import './App.css';

import Navbar from './components/Navbar';
import Login from './components/Login';
import Register from './components/Register';
import Portfolio from './components/Portfolio';
import AddHolding from './components/AddHolding';
import WeeklySummary from './components/WeeklySummary';
import MacdAnalysis from './components/MacdAnalysis';

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
    }
  }, []);

  const login = (userData, userToken) => {
    setUser(userData);
    setToken(userToken);
    localStorage.setItem('token', userToken);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  return (
    <div className="App">
      <Router>
        <Navbar user={user} logout={logout} />
        <div className="container mt-4">
          <Routes>
            <Route 
              path="/login" 
              element={!user ? <Login onLogin={login} /> : <Navigate to="/portfolio" />} 
            />
            <Route 
              path="/register" 
              element={!user ? <Register onLogin={login} /> : <Navigate to="/portfolio" />} 
            />
            <Route 
              path="/portfolio" 
              element={user ? <Portfolio token={token} /> : <Navigate to="/login" />} 
            />
            <Route 
              path="/add-holding" 
              element={user ? <AddHolding token={token} /> : <Navigate to="/login" />} 
            />
            <Route 
              path="/weekly-summary" 
              element={user ? <WeeklySummary token={token} /> : <Navigate to="/login" />} 
            />
            <Route 
              path="/macd-analysis" 
              element={user ? <MacdAnalysis token={token} /> : <Navigate to="/login" />} 
            />
            <Route 
              path="/" 
              element={<Navigate to={user ? "/portfolio" : "/login"} />} 
            />
          </Routes>
        </div>
      </Router>
    </div>
  );
}

export default App;
