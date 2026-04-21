from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), default='user') # 'user' or 'admin'
    email = db.Column(db.String(150), nullable=True)
    display_name = db.Column(db.String(150), nullable=True)
    
    # Preferences
    cost_alerts = db.Column(db.Boolean, default=True)
    weekly_reports = db.Column(db.Boolean, default=True)
    opt_tips = db.Column(db.Boolean, default=False)
    sec_alerts = db.Column(db.Boolean, default=True)
    
    # Security
    enable_2fa = db.Column(db.Boolean, default=False)
    login_notify = db.Column(db.Boolean, default=True)
    session_timeout = db.Column(db.String(50), default='1 hour')

    usage_data = db.relationship('UsageData', backref='user', lazy=True)
    reports = db.relationship('Report', backref='user', lazy=True)

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False) # e.g. Compute, Storage
    hourly_rate = db.Column(db.Float, nullable=False)
    
class UsageData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'), nullable=False)
    resource = db.relationship('Resource', backref='usages')
    avg_utilization_percent = db.Column(db.Float, nullable=False)
    allocated_amount = db.Column(db.Float, nullable=True) # e.g., 100GB or cores
    usage_hours = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class ThresholdRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resource_type = db.Column(db.String(50), nullable=False)
    condition_operator = db.Column(db.String(10), nullable=False) # '<', '>', etc.
    threshold_value = db.Column(db.Float, nullable=False)
    recommendation_text = db.Column(db.String(255), nullable=False)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_generated = db.Column(db.DateTime, default=datetime.utcnow)
    total_cost = db.Column(db.Float, nullable=False, default=0.0)
    recommendations = db.relationship('Recommendation', backref='report', lazy=True, cascade="all, delete-orphan")

class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('report.id'), nullable=False)
    usage_data_id = db.Column(db.Integer, db.ForeignKey('usage_data.id'), nullable=False)
    usage_data = db.relationship('UsageData')
    suggestion_text = db.Column(db.String(500), nullable=False)
    estimated_savings = db.Column(db.Float, nullable=True)
