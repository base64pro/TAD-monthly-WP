# --- ملف: models.py ---
# تعريف هياكل جداول قاعدة البيانات (مع حقل الحالة المدمج)

from extensions import db
from datetime import datetime, date

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activity_date = db.Column(db.Date, nullable=False, index=True)
    activity_desc = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(250), nullable=True)
    # --- الحقول المحذوفة ---
    # confirmed = db.Column(db.Boolean, default=True, nullable=False) # تم الحذف
    # execution_status = db.Column(db.Boolean, default=False, nullable=False) # تم الحذف
    # --- الحقل الجديد ---
    # 0: غير مؤكد, 1: مؤكد, 2: منفذ
    status = db.Column(db.Integer, default=0, nullable=False, index=True)
    # --------------------
    team_programs = db.Column(db.String(250), nullable=True)
    team_logistics = db.Column(db.String(250), nullable=True)
    team_finance = db.Column(db.String(250), nullable=True)
    team_media = db.Column(db.String(250), nullable=True)
    team_cars = db.Column(db.String(250), nullable=True)
    link1 = db.Column(db.String(500), nullable=True)
    link2 = db.Column(db.String(500), nullable=True)
    link3 = db.Column(db.String(500), nullable=True)
    admin_suggestions = db.Column(db.Text, nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    project = db.relationship('Project', backref=db.backref('activities', lazy='dynamic'))
    last_updated_by_id = db.Column(db.Integer, db.ForeignKey('editor.id'), nullable=True)
    last_updated_by = db.relationship('Editor', backref=db.backref('edited_activities', lazy='dynamic'))
    last_updated_on = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        # تم تحديث repr ليشمل الحالة الجديدة (اختياري)
        status_map = {0: 'Unconfirmed', 1: 'Confirmed', 2: 'Executed'}
        return f'<Activity id={self.id} date={self.activity_date} status={status_map.get(self.status, self.status)} desc={self.activity_desc[:20]}>'

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)

    def __repr__(self):
        return f'<Project id={self.id} name={self.name}>'

class Editor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f'<Editor id={self.id} name={self.name}>'
