from flask import Flask, render_template, request, redirect, url_for, flash
import os
from datetime import datetime, date
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

if not DATABASE_URL:
    DATABASE_URL = 'sqlite:///app.db'

engine = create_engine(DATABASE_URL)
Base = declarative_base()

class Expense(Base):
    __tablename__ = 'expenses'
    
    id = Column(Integer, primary_key=True)
    description = Column(String(200), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    expense_date = Column(Date, nullable=False, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Expense {self.description}: ${self.amount}>'

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Categories for expenses
CATEGORIES = [
    'Food & Dining',
    'Transportation',
    'Shopping',
    'Entertainment',
    'Bills & Utilities',
    'Healthcare',
    'Travel',
    'Education',
    'Other'
]

@app.route('/')
def index():
    session = Session()
    try:
        # Get recent expenses
        recent_expenses = session.query(Expense).order_by(Expense.created_at.desc()).limit(10).all()
        
        # Calculate total for current month
        current_month = date.today().replace(day=1)
        monthly_total = session.query(Expense).filter(
            Expense.expense_date >= current_month
        ).with_entities(Expense.amount).all()
        
        total_this_month = sum(expense.amount for expense in monthly_total) if monthly_total else 0
        
        return render_template('index.html', 
                             expenses=recent_expenses, 
                             monthly_total=total_this_month,
                             current_month=current_month.strftime('%B %Y'))
    finally:
        session.close()

@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        amount = request.form.get('amount', '').strip()
        category = request.form.get('category', '')
        expense_date_str = request.form.get('expense_date', '')
        
        # Validation
        if not description:
            flash('Description is required!', 'error')
            return render_template('add_expense.html', categories=CATEGORIES)
        
        try:
            amount = float(amount)
            if amount <= 0:
                flash('Amount must be greater than 0!', 'error')
                return render_template('add_expense.html', categories=CATEGORIES)
        except ValueError:
            flash('Invalid amount format!', 'error')
            return render_template('add_expense.html', categories=CATEGORIES)
        
        if category not in CATEGORIES:
            flash('Invalid category!', 'error')
            return render_template('add_expense.html', categories=CATEGORIES)
        
        # Parse date
        if expense_date_str:
            try:
                expense_date = datetime.strptime(expense_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format!', 'error')
                return render_template('add_expense.html', categories=CATEGORIES)
        else:
            expense_date = date.today()
        
        session = Session()
        try:
            new_expense = Expense(
                description=description,
                amount=amount,
                category=category,
                expense_date=expense_date
            )
            session.add(new_expense)
            session.commit()
            flash('Expense added successfully!', 'success')
            return redirect(url_for('index'))
        except SQLAlchemyError as e:
            session.rollback()
            flash('Error adding expense. Please try again.', 'error')
            return render_template('add_expense.html', categories=CATEGORIES)
        finally:
            session.close()
    
    return render_template('add_expense.html', categories=CATEGORIES)

@app.route('/monthly_summary')
def monthly_summary():
    session = Session()
    try:
        # Get current month expenses
        current_month = date.today().replace(day=1)
        expenses = session.query(Expense).filter(
            Expense.expense_date >= current_month
        ).order_by(Expense.expense_date.desc()).all()
        
        # Calculate category totals
        category_totals = {}
        for expense in expenses:
            if expense.category in category_totals:
                category_totals[expense.category] += expense.amount
            else:
                category_totals[expense.category] = expense.amount
        
        total_amount = sum(category_totals.values())
        
        return render_template('monthly_summary.html', 
                             expenses=expenses,
                             category_totals=category_totals,
                             total_amount=total_amount,
                             current_month=current_month.strftime('%B %Y'))
    finally:
        session.close()

@app.route('/delete_expense/<int:expense_id>')
def delete_expense(expense_id):
    session = Session()
    try:
        expense = session.query(Expense).get(expense_id)
        if expense:
            session.delete(expense)
            session.commit()
            flash('Expense deleted successfully!', 'success')
        else:
            flash('Expense not found!', 'error')
    except SQLAlchemyError as e:
        session.rollback()
        flash('Error deleting expense. Please try again.', 'error')
    finally:
        session.close()
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)