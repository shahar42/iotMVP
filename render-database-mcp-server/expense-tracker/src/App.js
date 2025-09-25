import React, { useState, useEffect } from 'react';
import './App.css';

const categories = ['Food', 'Transport', 'Shopping', 'Entertainment', 'Bills', 'Other'];

function App() {
  const [expenses, setExpenses] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    description: '',
    amount: '',
    category: 'Food',
    date: new Date().toISOString().split('T')[0]
  });

  useEffect(() => {
    const saved = localStorage.getItem('expenses');
    if (saved) {
      setExpenses(JSON.parse(saved));
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('expenses', JSON.stringify(expenses));
  }, [expenses]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (editingId) {
      setExpenses(expenses.map(exp =>
        exp.id === editingId ? { ...formData, id: editingId } : exp
      ));
      setEditingId(null);
    } else {
      const newExpense = { ...formData, id: Date.now() };
      setExpenses([...expenses, newExpense]);
    }
    setFormData({ description: '', amount: '', category: 'Food', date: new Date().toISOString().split('T')[0] });
    setShowForm(false);
  };

  const handleEdit = (expense) => {
    setFormData(expense);
    setEditingId(expense.id);
    setShowForm(true);
  };

  const handleDelete = (id) => {
    setExpenses(expenses.filter(exp => exp.id !== id));
  };

  const totalAmount = expenses.reduce((sum, exp) => sum + parseFloat(exp.amount || 0), 0);

  return (
    <div className="app">
      <header className="header">
        <h1>💰 Expense Tracker</h1>
        <div className="total">Total: ${totalAmount.toFixed(2)}</div>
      </header>

      <div className="container">
        <button
          className="add-btn"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? 'Cancel' : '+ Add Expense'}
        </button>

        {showForm && (
          <form className="expense-form" onSubmit={handleSubmit}>
            <div className="form-row">
              <input
                type="text"
                placeholder="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                required
              />
              <input
                type="number"
                step="0.01"
                placeholder="Amount"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                required
              />
            </div>
            <div className="form-row">
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              >
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
              <input
                type="date"
                value={formData.date}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                required
              />
            </div>
            <button type="submit" className="submit-btn">
              {editingId ? 'Update' : 'Add'} Expense
            </button>
          </form>
        )}

        <div className="expenses-list">
          {expenses.length === 0 ? (
            <div className="empty-state">
              <p>No expenses yet. Add your first expense!</p>
            </div>
          ) : (
            expenses
              .sort((a, b) => new Date(b.date) - new Date(a.date))
              .map(expense => (
                <div key={expense.id} className="expense-item">
                  <div className="expense-info">
                    <div className="expense-desc">{expense.description}</div>
                    <div className="expense-meta">
                      <span className={`category category-${expense.category.toLowerCase()}`}>
                        {expense.category}
                      </span>
                      <span className="date">{expense.date}</span>
                    </div>
                  </div>
                  <div className="expense-amount">${parseFloat(expense.amount).toFixed(2)}</div>
                  <div className="expense-actions">
                    <button onClick={() => handleEdit(expense)}>Edit</button>
                    <button onClick={() => handleDelete(expense.id)}>Delete</button>
                  </div>
                </div>
              ))
          )}
        </div>
      </div>
    </div>
  );
}

export default App;