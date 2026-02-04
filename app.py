from flask import Flask, render_template, redirect, url_for, request, flash, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import pandas as pd
import io
import os

from models import db, User, ExpenseRequest, LedgerEntry, LedgerEntryHistory

app = Flask(__name__)
app.config['SECRET_KEY'] = 'banbangnamchuet_secret_key_123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///financial_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Thai role name mapping
ROLE_NAMES_TH = {
    'teacher': 'คุณครู',
    'director': 'ผู้อำนวยการโรงเรียน',
    'finance': 'ครูการเงิน'
}

@app.context_processor
def utility_processor():
    return dict(role_names_th=ROLE_NAMES_TH)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Initialization ---
def init_db():
    with app.app_context():
        db.create_all()
        # Create default users if they don't exist
        # Create default users if they don't exist
        if not User.query.filter_by(username='teacher').first():
            db.session.add(User(username='teacher', name='ครู 01', password_hash=generate_password_hash('pass1234'), role='teacher'))
            db.session.add(User(username='director', name='ผอ.โรงเรียนบ้านบางน้ำจืด', password_hash=generate_password_hash('pass1234'), role='director'))
            db.session.add(User(username='finance', name='ครูการเงิน', password_hash=generate_password_hash('pass1234'), role='finance'))
            db.session.commit()
            print("Database initialized and default users created.")

# --- Routes ---

@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('dashboard.html')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        role = request.form.get('role')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('รหัสผ่านไม่ตรงกัน', 'danger')
            return redirect(url_for('register'))
            
        if User.query.filter_by(username=username).first():
            flash('ชื่อผู้ใช้นี้ถูกใช้งานแล้ว', 'danger')
            return redirect(url_for('register'))
            
        new_user = User(
            username=username,
            name=name,
            role=role,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('สมัครสมาชิกสำเร็จ! กรุณาเข้าสู่ระบบ', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง', 'danger')
    return render_template('login.html')

def redirect_role_based(user):
    if user.role == 'teacher':
        return redirect(url_for('request_page'))
    elif user.role == 'director':
        return redirect(url_for('approve_page'))
    elif user.role == 'finance':
        return redirect(url_for('ledger_view', type='subsidy'))
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Page 2: Expense Request ---
@app.route('/request', methods=['GET', 'POST'])
@login_required
def request_page():
    if current_user.role not in ['teacher', 'finance']:
        flash('คุณไม่มีสิทธ์เข้าถึงหน้านี้', 'danger')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        date_str = request.form.get('date')
        amount = float(request.form.get('amount'))
        description = request.form.get('description', '')  # NEW
        account_type = request.form.get('account_type')
        
        new_request = ExpenseRequest(
            requester_id=current_user.id,
            date=datetime.strptime(date_str, '%Y-%m-%d').date(),
            amount=amount,
            description=description,  # NEW
            account_type=account_type
        )
        db.session.add(new_request)
        db.session.commit()
        db.session.add(new_request)
        db.session.commit()
        flash('บันทึกคำขอเบิกเงินเรียบร้อยแล้ว', 'success')
        
    return render_template('page2_request.html')

# --- Page 3: My Requests Status (Teacher & Finance) ---
@app.route('/my-requests')
@login_required
def my_requests():
    if current_user.role not in ['teacher', 'finance']:
        flash('คุณไม่มีสิทธ์เข้าถึงหน้านี้', 'danger')
        return redirect(url_for('index'))
    
    # Get all requests submitted by current user
    my_requests = ExpenseRequest.query.filter_by(requester_id=current_user.id).order_by(ExpenseRequest.date.desc()).all()
    return render_template('page3_status.html', requests=my_requests)

# --- Page 4: Approval ---
@app.route('/approve')
@login_required
def approve_page():
    if current_user.role not in ['director', 'finance']:
        flash('คุณไม่มีสิทธิ์เข้าถึงหน้านี้', 'danger')
        return redirect(url_for('index'))
    
    # Show all pending or partially approved requests
    # Filter: Status is PENDING or PARTIALLY_APPROVED (essentially not 'APPROVED')
    # Or just show everything that isn't fully approved
    pending_requests = ExpenseRequest.query.filter(ExpenseRequest.status != 'APPROVED').all()
    return render_template('page4_approve.html', requests=pending_requests)

@app.route('/approve/<int:req_id>')
@login_required
def approve_action(req_id):
    req = ExpenseRequest.query.get_or_404(req_id)
    
    if current_user.role == 'finance':
        if not req.finance_approved_at:
            req.finance_approver_id = current_user.id
            req.finance_approved_at = datetime.utcnow()
            flash('เจ้าหน้าที่การเงินอนุมัติแล้ว', 'success')
    elif current_user.role == 'director':
        if not req.director_approved_at:
            req.director_approver_id = current_user.id
            req.director_approved_at = datetime.utcnow()
            flash('ผู้อำนวยการอนุมัติแล้ว', 'success')
    else:
        return redirect(url_for('index'))

    # Check if both have approved
    if req.finance_approved_at and req.director_approved_at:
        req.status = 'APPROVED'
        
        try:
            # AUTO-CREATE LEDGER ENTRY
            ledger_type_map = {
                'เงินอุดหนุนอื่น': 'Subsidy',
                'เงินรายได้สถานศึกษา': 'Income',
                'เงินอาหารกลางวัน': 'Lunch'
            }
            
            new_ledger = LedgerEntry(
                date=req.date,
                amount=req.amount,
                description=f'อนุมัติจากคำขอ #{req.id}',
                ledger_type=ledger_type_map.get(req.account_type, 'subsidy'),
                category='รายจ่าย',
                transaction_type='Expense',
                expense_request_id=req.id,
                created_by_id=current_user.id
            )
            db.session.add(new_ledger)
            db.session.commit()
            flash(f'✅ อนุมัติคำขอและบันทึกลงทะเบียน {ledger_type_map.get(req.account_type, "Subsidy")} เรียบร้อยแล้ว! (รหัสรายการ: {new_ledger.id})', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'⚠️ อนุมัติเรียบร้อยแต่เกิดข้อผิดพลาดในการสร้างรายการทะเบียน: {str(e)}', 'warning')
            print(f"ERROR creating ledger: {e}")
            import traceback
            traceback.print_exc()
    
    db.session.commit()
    return redirect(url_for('approve_page'))

# --- Edit Ledger Entry ---
@app.route('/ledger/<type>/edit/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def edit_ledger_entry(type, entry_id):
    if current_user.role not in ['finance', 'director']:
        flash('คุณไม่มีสิทธ์เข้าถึงหน้านี้', 'danger')
        return redirect(url_for('index'))
    
    entry = LedgerEntry.query.get_or_404(entry_id)
    
    if request.method == 'POST':
        # Track changes
        old_amount = entry.amount
        new_amount = float(request.form.get('amount'))
        if old_amount != new_amount:
            history = LedgerEntryHistory(
                ledger_entry_id=entry.id,
                edited_by_id=current_user.id,
                field_name='amount',
                old_value=str(old_amount),
                new_value=str(new_amount)
            )
            db.session.add(history)
            entry.amount = new_amount
        
        old_desc = entry.description or ''
        new_desc = request.form.get('description') or ''
        if old_desc != new_desc:
            history = LedgerEntryHistory(
                ledger_entry_id=entry.id,
                edited_by_id=current_user.id,
                field_name='description',
                old_value=old_desc,
                new_value=new_desc
            )
            db.session.add(history)
            entry.description = new_desc
        
        old_note = entry.note or ''
        new_note = request.form.get('note') or ''
        if old_note != new_note:
            history = LedgerEntryHistory(
                ledger_entry_id=entry.id,
                edited_by_id=current_user.id,
                field_name='note',
                old_value=old_note,
                new_value=new_note
            )
            db.session.add(history)
            entry.note = new_note
        
        db.session.commit()
        flash('บันทึกการแก้ไขเรียบร้อยแล้ว', 'success')
        return redirect(url_for('ledger_view', type=type))
    
    return render_template('edit_ledger.html', entry=entry, type=type)

# --- View Ledger History ---
@app.route('/ledger/history/<int:entry_id>')
@login_required
def ledger_history(entry_id):
    if current_user.role not in ['finance', 'director']:
        flash('คุณไม่มีสิทธ์เข้าถึงหน้านี้', 'danger')
        return redirect(url_for('index'))
    
    entry = LedgerEntry.query.get_or_404(entry_id)
    history = LedgerEntryHistory.query.filter_by(
        ledger_entry_id=entry_id
    ).order_by(LedgerEntryHistory.edited_at.desc()).all()
    
    # Map ledger_type to URL type
    type_map = {
        'Subsidy': 'subsidy',
        'Income': 'income',
        'Lunch': 'lunch'
    }
    ledger_type_url = type_map.get(entry.ledger_type, 'subsidy')
    
    return render_template('ledger_history.html', entry=entry, history=history, ledger_type_url=ledger_type_url)

# --- Page 6, 7, 8: Ledgers ---
@app.route('/ledger/<type>', methods=['GET', 'POST'])
@login_required
def ledger_view(type):
    # Mapping URL type to DB Ledger Type and Template
    type_map = {
        'subsidy': {'db_type': 'Subsidy', 'template': 'page6_subsidy.html', 'header': 'ทะเบียนคุมเงินอุดหนุน'},
        'income': {'db_type': 'Income', 'template': 'page7_income.html', 'header': 'ทะเบียนคุมเงินรายได้'},
        'lunch': {'db_type': 'Lunch', 'template': 'page8_lunch.html', 'header': 'ทะเบียนคุมเงินอาหารกลางวัน'}
    }
    
    if type not in type_map:
        return "Invalid ledger type", 404
        
    if current_user.role not in ['finance', 'director']:
        flash('คุณไม่มีสิทธ์เข้าถึงหน้านี้', 'danger')
        return redirect(url_for('index'))

    config = type_map[type]

    if request.method == 'POST':
        date_str = request.form.get('date')
        amount = float(request.form.get('amount'))
        description = request.form.get('description')
        note = request.form.get('note')  # NEW
        category = request.form.get('category')
        transaction_type = request.form.get('transaction_type')
        
        entry = LedgerEntry(
            date=datetime.strptime(date_str, '%Y-%m-%d').date(),
            amount=amount,
            description=description,
            note=note,  # NEW
            category=category,
            transaction_type=transaction_type,
            ledger_type=config['db_type'],
            created_by_id=current_user.id # NEW: Track manual creator
        )
        db.session.add(entry)
        db.session.commit()
        flash('บันทึกรายการเรียบร้อยแล้ว', 'success')
    
    # Fetch entries (Optimized with Eager Loading)
    from sqlalchemy.orm import joinedload
    entries = LedgerEntry.query.filter_by(ledger_type=config['db_type']).options(
        joinedload(LedgerEntry.created_by),
        joinedload(LedgerEntry.expense_request).joinedload(ExpenseRequest.requester)
    ).order_by(LedgerEntry.date).all()
    
    # Categories for dropdowns
    categories = []
    if type == 'subsidy':
        categories = ['ค่าจัดการเรียนการสอน', 'ค่ากิจกรรมพัฒนาผู้เรียน', 'ค่าเครื่องแบบ', 'ค่าอุปกรณ์การเรียน', 'ค่าหนังสือเรียน', 'อื่นๆ']
    elif type == 'income':
        categories = ['เงินบริจาค', 'ทุนการศึกษา', 'ค่าจ้างครู', 'อื่นๆ']
    
    # Calculate summary statistics (Optimized using SQL queries)
    from sqlalchemy import func
    
    today = date.today()
    current_month_start = today.replace(day=1)
    current_month_end = (current_month_start + relativedelta(months=1)) - relativedelta(days=1)
    
    # Get date range from query params or use defaults
    balance_start = request.args.get('balance_start')
    balance_end = request.args.get('balance_end')
    
    if balance_start and balance_end:
        balance_start_date = datetime.strptime(balance_start, '%Y-%m-%d').date()
        balance_end_date = datetime.strptime(balance_end, '%Y-%m-%d').date()
    else:
        # Default: start of current year to today
        balance_start_date = today.replace(month=1, day=1)
        balance_end_date = today
    
    # Helper to calculate sum
    def get_sum(transaction_type, start_date, end_date):
        result = db.session.query(func.sum(LedgerEntry.amount)).filter(
            LedgerEntry.ledger_type == config['db_type'],
            LedgerEntry.transaction_type == transaction_type,
            LedgerEntry.date >= start_date,
            LedgerEntry.date <= end_date
        ).scalar()
        return result or 0.0

    # Calculate monthly income (current month)
    monthly_income = get_sum('Income', current_month_start, current_month_end)
    
    # Calculate monthly expenses (current month)
    monthly_expense = get_sum('Expense', current_month_start, current_month_end)
    
    # Calculate balance for selected range
    balance_income = get_sum('Income', balance_start_date, balance_end_date)
    balance_expense = get_sum('Expense', balance_start_date, balance_end_date)
    current_balance = balance_income - balance_expense
    
    return render_template(
        config['template'], 
        entries=entries, 
        categories=categories,
        header=config['header'],
        ledger_type=type,
        monthly_income=monthly_income,
        monthly_expense=monthly_expense,
        current_balance=current_balance,
        balance_start=balance_start_date.strftime('%Y-%m-%d'),
        balance_end=balance_end_date.strftime('%Y-%m-%d'),
        current_month=today.strftime('%B %Y')
    )

# --- Export Logic ---
@app.route('/export/<type>')
@login_required
def export_ledger(type):
    if current_user.role not in ['finance', 'director']:
        return "Access denied", 403

    type_map = {
        'subsidy': 'Subsidy',
        'income': 'Income',
        'lunch': 'Lunch'
    }
    
    header_map = {
        'subsidy': 'ทะเบียนคุมเงินอุดหนุน',
        'income': 'ทะเบียนคุมเงินรายได้',
        'lunch': 'ทะเบียนคุมเงินอาหารกลางวัน'
    }
    
    if type not in type_map:
        return "Invalid type", 404
        
    from sqlalchemy.orm import joinedload
    
    entries = LedgerEntry.query.filter_by(ledger_type=type_map[type]).options(
        joinedload(LedgerEntry.created_by),
        joinedload(LedgerEntry.expense_request).joinedload(ExpenseRequest.requester)
    ).order_by(LedgerEntry.date).all()
    
    data = []
    balance = 0.0
    
    # For Monthly Stats
    today = date.today()
    current_month_start = today.replace(day=1)
    current_month_end = (current_month_start + relativedelta(months=1)) - relativedelta(days=1)
    
    monthly_income = 0.0
    monthly_expense = 0.0
    
    for e in entries:
        # Resolve Creator
        creator = "-"
        if e.expense_request:
            creator = e.expense_request.requester.name or e.expense_request.requester.username
        elif e.created_by:
            creator = e.created_by.name or e.created_by.username
            
        # Amounts
        income = 0.0
        expense = 0.0
        if e.transaction_type == 'Income':
            income = e.amount
            balance += e.amount
            # Monthly Stat Update
            if current_month_start <= e.date <= current_month_end:
                monthly_income += e.amount
        else:
            expense = e.amount
            balance -= e.amount
            # Monthly Stat Update
            if current_month_start <= e.date <= current_month_end:
                monthly_expense += e.amount
                
        data.append({
            'วันที่': e.date.strftime('%d/%m/%Y'),
            'หมวดหมู่': e.category,
            'ผู้ทำรายการ': creator,
            'รายละเอียด': e.description,
            'รายรับ': income if income > 0 else None,
            'รายจ่าย': expense if expense > 0 else None,
            'คงเหลือ': balance,
            'หมายเหตุ': e.note
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel with Summary
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1', startrow=1)
        
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']
        
        # Add Title and Date
        worksheet.cell(row=1, column=1, value=f"{header_map.get(type, type)} - ข้อมูล ณ วันที่ {today.strftime('%d/%m/%Y')}")
        
        # Add Summary at the bottom
        last_row = len(data) + 4
        
        worksheet.cell(row=last_row, column=1, value="สรุปยอด")
        worksheet.cell(row=last_row+1, column=1, value="รายรับของเดือนนี้")
        worksheet.cell(row=last_row+1, column=2, value=monthly_income)
        
        worksheet.cell(row=last_row+2, column=1, value="รายจ่ายของเดือนนี้")
        worksheet.cell(row=last_row+2, column=2, value=monthly_expense)
        
        worksheet.cell(row=last_row+3, column=1, value="เงินคงเหลือสุทธิ")
        worksheet.cell(row=last_row+3, column=2, value=balance) # Current Balance is the final running balance

    output.seek(0)
    
    return send_file(output, download_name=f'{type}_ledger_{today.strftime("%Y%m%d")}.xlsx', as_attachment=True)

if __name__ == '__main__':
    if not os.path.exists('instance/financial_system.db'):
        init_db()
    else:
        # Also run init_db to check for missing tables/users in case of partial setup
        init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
