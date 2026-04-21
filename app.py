from flask import Flask, render_template, redirect, url_for, flash, request, abort
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import os
import pandas as pd
import io
import csv
from flask import Response

from config import Config
from models import db, User, Resource, UsageData, ThresholdRule, Report, Recommendation

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists', 'warning')
            return redirect(url_for('register'))
            
        new_user = User(username=username, password_hash=generate_password_hash(password), role=role)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    reports = Report.query.filter_by(user_id=current_user.id).order_by(Report.date_generated.desc()).all()
    
    # Fetch a few recent usages to show in the "Resource Overview" grid
    recent_usages = UsageData.query.filter_by(user_id=current_user.id).order_by(UsageData.date.desc()).limit(4).all()
    
    return render_template('dashboard.html', reports=reports, recent_usages=recent_usages)

@app.route('/resources', methods=['GET', 'POST'])
@login_required
def resources():
    if request.method == 'POST':
        name = request.form.get('name')
        res_type = request.form.get('type')
        hourly_rate = request.form.get('hourly_rate', 0)
        
        new_resource = Resource(name=name, type=res_type, hourly_rate=float(hourly_rate))
        db.session.add(new_resource)
        db.session.commit()
        flash('Resource added successfully!', 'success')
        return redirect(url_for('resources'))
        
    all_resources = Resource.query.all()
    return render_template('resources.html', resources=all_resources)

@app.route('/edit_resource/<int:resource_id>', methods=['POST'])
@login_required
@admin_required
def edit_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    resource.name = request.form.get('name')
    resource.type = request.form.get('type')
    resource.hourly_rate = float(request.form.get('hourly_rate', 0))
    db.session.commit()
    flash('Resource updated successfully!', 'success')
    return redirect(url_for('resources'))

@app.route('/delete_resource/<int:resource_id>', methods=['POST'])
@login_required
@admin_required
def delete_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    db.session.delete(resource)
    db.session.commit()
    flash('Resource deleted successfully!', 'success')
    return redirect(url_for('resources'))

@app.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.all()
    return render_template('users.html', users=all_users)

@app.route('/add_user', methods=['POST'])
@login_required
@admin_required
def add_user():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role', 'user')
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists', 'danger')
        return redirect(url_for('users'))
        
    new_user = User(username=username, password_hash=generate_password_hash(password), role=role)
    db.session.add(new_user)
    db.session.commit()
    flash('User added successfully!', 'success')
    return redirect(url_for('users'))

@app.route('/edit_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    user.username = request.form.get('username')
    user.role = request.form.get('role')
    
    password = request.form.get('password')
    if password:
        user.password_hash = generate_password_hash(password)
        
    db.session.commit()
    flash('User updated successfully!', 'success')
    return redirect(url_for('users'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('You cannot delete your own account!', 'danger')
        return redirect(url_for('users'))
        
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('users'))

@app.route('/analytics')
@login_required
def analytics():
    reports = Report.query.filter_by(user_id=current_user.id).all()
    return render_template('analytics.html', reports=reports)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    rules = ThresholdRule.query.all()
    if request.method == 'POST':
        action = request.form.get('action', '')
        if action == 'update_profile':
            current_user.email = request.form.get('email', '').strip()
            current_user.display_name = request.form.get('display_name', '').strip()
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        elif action == 'update_notifications':
            current_user.cost_alerts = 'cost_alerts' in request.form
            current_user.weekly_reports = 'weekly_reports' in request.form
            current_user.opt_tips = 'opt_tips' in request.form
            current_user.sec_alerts = 'sec_alerts' in request.form
            db.session.commit()
            flash('Notification preferences saved!', 'success')
        return redirect(url_for('settings'))
    return render_template('settings.html', rules=rules)

@app.route('/security', methods=['GET', 'POST'])
@login_required
def security():
    if request.method == 'POST':
        action = request.form.get('action', '')
        if action == 'change_password':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            if not check_password_hash(current_user.password_hash, current_password):
                flash('Current password is incorrect.', 'danger')
            elif new_password != confirm_password:
                flash('New passwords do not match.', 'danger')
            elif len(new_password) < 6:
                flash('New password must be at least 6 characters.', 'warning')
            else:
                current_user.password_hash = generate_password_hash(new_password)
                db.session.commit()
                flash('Password updated successfully!', 'success')
        elif action == 'update_security':
            current_user.enable_2fa = 'enable_2fa' in request.form
            current_user.login_notify = 'login_notify' in request.form
            current_user.session_timeout = request.form.get('session_timeout', '1 hour')
            db.session.commit()
            flash('Security settings updated!', 'success')
        return redirect(url_for('security'))
    return render_template('security.html')

@app.route('/add_rule', methods=['POST'])
@login_required
@admin_required
def add_rule():
    res_type = request.form.get('resource_type')
    op = request.form.get('operator')
    val = float(request.form.get('value', 0))
    rec = request.form.get('recommendation')
    
    new_rule = ThresholdRule(
        resource_type=res_type,
        condition_operator=op,
        threshold_value=val,
        recommendation_text=rec
    )
    db.session.add(new_rule)
    db.session.commit()
    flash('Threshold rule added!', 'success')
    return redirect(url_for('settings'))

@app.route('/edit_rule/<int:rule_id>', methods=['POST'])
@login_required
@admin_required
def edit_rule(rule_id):
    rule = ThresholdRule.query.get_or_404(rule_id)
    rule.resource_type = request.form.get('resource_type')
    rule.condition_operator = request.form.get('operator')
    rule.threshold_value = float(request.form.get('value', 0))
    rule.recommendation_text = request.form.get('recommendation')
    db.session.commit()
    flash('Rule updated successfully!', 'success')
    return redirect(url_for('settings'))

@app.route('/delete_rule/<int:rule_id>', methods=['POST'])
@login_required
@admin_required
def delete_rule(rule_id):
    rule = ThresholdRule.query.get_or_404(rule_id)
    db.session.delete(rule)
    db.session.commit()
    flash('Rule removed!', 'success')
    return redirect(url_for('settings'))

@app.route('/sync-data', methods=['POST'])
@login_required
def sync_data():
    # Simulate a data synchronization process
    flash('Data synchronized with cloud provider successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/export-report/<int:report_id>')
@login_required
def export_report(report_id):
    report = Report.query.get(report_id)
    if not report or report.user_id != current_user.id:
        flash('Report not found', 'danger')
        return redirect(url_for('dashboard'))
        
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Resource', 'Utilization %', 'Usage Hours', 'Estimated Savings', 'Recommendation'])
    
    for rec in report.recommendations:
        usage = rec.usage_data
        writer.writerow([
            usage.resource.name,
            usage.avg_utilization_percent,
            usage.usage_hours,
            rec.estimated_savings,
            rec.suggestion_text
        ])
    
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=report_{report_id}.csv"}
    )

@app.route('/report/<int:report_id>')
@login_required
def report_detail(report_id):
    report = Report.query.get(report_id)
    if not report or report.user_id != current_user.id:
        flash('Report not found or unauthorized.', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('report_detail.html', report=report)

@app.route('/delete_report/<int:report_id>', methods=['POST'])
@login_required
def delete_report(report_id):
    report = Report.query.get(report_id)
    
    if not report or report.user_id != current_user.id:
        flash('Unauthorized action', 'danger')
        return redirect(url_for('dashboard'))
    
    # 🔥 delete usage data also
    UsageData.query.filter_by(user_id=current_user.id).delete()
    
    # delete report
    db.session.delete(report)
    db.session.commit()
    
    flash('Report deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
            
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
            
        if file and file.filename.endswith('.csv'):
            try:
                df = pd.read_csv(file)
                # expected columns: resource_name, resource_type, utilization_percent, usage_hours
                for _, row in df.iterrows():
                    res_name = row.get('resource_name')
                    resource = Resource.query.filter_by(name=res_name).first()
                    
                    if resource:
                        usage = UsageData(
                            user_id=current_user.id,
                            resource_id=resource.id,
                            avg_utilization_percent=float(row.get('utilization_percent', 0)),
                            usage_hours=float(row.get('usage_hours', 0))
                        )
                        db.session.add(usage)
                        
                db.session.commit()
                # STEP 1: Get all user usage data
                user_usages = UsageData.query.filter_by(user_id=current_user.id).all()

                total_cost = 0
                report = Report(user_id=current_user.id, total_cost=0)
                db.session.add(report)
                db.session.commit()  # commit to get report.id

                for usage in user_usages:
                    resource = usage.resource
                    
                    # STEP 2: cost calculation
                    cost = resource.hourly_rate * usage.usage_hours
                    total_cost += cost
                    
                    # STEP 3: apply rules
                    rules = ThresholdRule.query.filter_by(resource_type=resource.type).all()
                    
                    for rule in rules:
                        condition_met = False
                        
                        if rule.condition_operator == '<':
                            condition_met = usage.avg_utilization_percent < rule.threshold_value
                        elif rule.condition_operator == '>':
                            condition_met = usage.avg_utilization_percent > rule.threshold_value
                        
                        if condition_met:
                            rec = Recommendation(
                                report_id=report.id,
                                usage_data_id=usage.id,
                                suggestion_text=rule.recommendation_text,
                                estimated_savings=cost * 0.2  # simple assumption
                            )
                            db.session.add(rec)

                # STEP 4: update total cost
                report.total_cost = total_cost
                db.session.commit() 
                flash('Data uploaded successfully!', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error processing file: {str(e)}', 'danger')
                return redirect(request.url)
        else:
            flash('Please upload a CSV file.', 'danger')
            return redirect(request.url)
            
    return render_template('upload.html')

def init_db():
    with app.app_context():
        db.create_all()
        # Seed dummy resources and rules if database is empty
        if not Resource.query.first():
            resources = [
                Resource(name='EC2-Micro', type='Compute', hourly_rate=0.0116),
                Resource(name='EC2-Large', type='Compute', hourly_rate=0.0928),
                Resource(name='S3-Standard', type='Storage', hourly_rate=0.00003),
                Resource(name='RDS-pg-small', type='Database', hourly_rate=0.036)
            ]
            db.session.bulk_save_objects(resources)
            
            rules = [
                ThresholdRule(resource_type='Compute', condition_operator='<', threshold_value=20.0, recommendation_text='Instance underutilized, downgrade recommended'),
                ThresholdRule(resource_type='Compute', condition_operator='>', threshold_value=85.0, recommendation_text='High instance utilization detected, consider upgrading'),
                ThresholdRule(resource_type='Storage', condition_operator='<', threshold_value=10.0, recommendation_text='Unused storage detected, consider deletion')
            ]
            db.session.bulk_save_objects(rules)
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
