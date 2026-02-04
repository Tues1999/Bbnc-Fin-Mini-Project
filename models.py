from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=True) # NEW: Thai name
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'teacher', 'director', 'finance'

class ExpenseRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(500), nullable=True)  # NEW: รายละเอียดคำขอ
    account_type = db.Column(db.String(50), nullable=False) # 'Subsidy', 'Income', 'Lunch'
    status = db.Column(db.String(20), default='PENDING') # 'PENDING', 'APPROVED' (requires both)
    
    # Dual Approval System
    finance_approver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    finance_approved_at = db.Column(db.DateTime, nullable=True)
    
    director_approver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    director_approved_at = db.Column(db.DateTime, nullable=True)

    requester = db.relationship('User', foreign_keys=[requester_id], backref='requests_made')
    finance_approver = db.relationship('User', foreign_keys=[finance_approver_id], backref='finance_approvals')
    director_approver = db.relationship('User', foreign_keys=[director_approver_id], backref='director_approvals')

class LedgerEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    note = db.Column(db.String(255), nullable=True)
    ledger_type = db.Column(db.String(50), nullable=False) # 'Subsidy', 'Income', 'Lunch'
    category = db.Column(db.String(100), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False) # 'Income', 'Expense'
    
    # NEW: Link to originating expense request (optional)
    expense_request_id = db.Column(db.Integer, db.ForeignKey('expense_request.id'), nullable=True)
    
    # NEW: Track creation
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    expense_request = db.relationship('ExpenseRequest', backref=db.backref('ledger_entry', uselist=False))
    created_by = db.relationship('User', foreign_keys=[created_by_id])

# NEW: Audit history table for ledger entries
class LedgerEntryHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ledger_entry_id = db.Column(db.Integer, db.ForeignKey('ledger_entry.id'), nullable=False)
    edited_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    edited_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Store what changed
    field_name = db.Column(db.String(50), nullable=False)  # e.g., 'amount', 'description'
    old_value = db.Column(db.String(500))
    new_value = db.Column(db.String(500))
    
    # Relationships
    ledger_entry = db.relationship('LedgerEntry', backref='history')
    edited_by = db.relationship('User', foreign_keys=[edited_by_id])
