import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

const Portfolio = ({ token }) => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const fetchPortfolio = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/portfolio', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setTransactions(response.data.transactions);
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to fetch portfolio');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center">
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-danger" role="alert">
        {error}
      </div>
    );
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Portfolio</h2>
        <Link to="/add-holding" className="btn btn-primary">
          <i className="fas fa-plus me-2"></i>Add Holding
        </Link>
      </div>

      {transactions.length === 0 ? (
        <div className="card">
          <div className="card-body text-center">
            <h5>No holdings yet</h5>
            <p>Start building your crypto portfolio by adding your first holding.</p>
            <Link to="/add-holding" className="btn btn-primary">
              Add Your First Holding
            </Link>
          </div>
        </div>
      ) : (
        <div className="card">
          <div className="card-header">
            <h5>Your Transactions</h5>
          </div>
          <div className="card-body">
            <div className="table-responsive">
              <table className="table table-striped">
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>Type</th>
                    <th>Date</th>
                    <th>Price</th>
                    <th>Quantity</th>
                    <th>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((transaction) => (
                    <tr key={transaction.id}>
                      <td>
                        <strong>{transaction.symbol}</strong>
                      </td>
                      <td>
                        <span className={`badge ${transaction.transaction_type === 'Buy' ? 'bg-success' : 'bg-danger'}`}>
                          {transaction.transaction_type}
                        </span>
                      </td>
                      <td>{new Date(transaction.transaction_date).toLocaleDateString()}</td>
                      <td>${transaction.transaction_price.toFixed(2)}</td>
                      <td>{transaction.transaction_quantity.toFixed(8)}</td>
                      <td>${transaction.transaction_total.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Portfolio; 