from flask import Flask, render_template, redirect, url_for, flash, request
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
        # logic for updating threshold rules or user profile can go here
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings'))
    return render_template('settings.html', rules=rules)

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
