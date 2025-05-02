# -*- coding: utf-8 -*-
# --- ملف: app.py ---
# النسخة المصححة + تصحيح منطق تحديد DATABASE_URL

import os
import sys
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import calendar
from functools import wraps
import traceback # لاستيراد traceback لطباعة تفاصيل الخطأ
from urllib.parse import quote
from flask import (
    Flask, render_template, url_for, request,
    redirect, session, flash, jsonify, Response, make_response
)
# ===> لا نستورد SQLAlchemy هنا مباشرة <===
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError # لاستيراد IntegrityError للتحقق من التفرد

# ===> استيراد db من الملف الجديد أولاً <===
from extensions import db
# ===> ثم استيراد النماذج <===
from models import Activity, Project, Editor # تأكد من وجود Editor هنا

# ===> محاولة استيراد WeasyPrint وتحديد حالته <===
# تم نقل هذا البلوك إلى هنا ليكون بعد استيراد النماذج وقبل استخدامه
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
    print("--- INFO: WeasyPrint found and enabled.")
except ImportError:
    WEASYPRINT_AVAILABLE = False
    print("--- WARNING: WeasyPrint not found. PDF export will be disabled.")
# ===> نهاية بلوك WeasyPrint <===


# تحميل المتغيرات من ملف .env
load_dotenv()

# --- دعم اللغات والنصوص ---
LANGUAGES = {'ar': {'name': 'العربية', 'dir': 'rtl'}, 'en': {'name': 'English', 'dir': 'ltr'}}
DEFAULT_LANGUAGE = 'ar'
MONTHS = {
    'ar': ["يناير", "فبراير", "مارس", "إبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"],
    'en': ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
}
DAYS_OF_WEEK = {
    'ar': ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"],
    'en': ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
}
# --- قاموس النصوص (UI_TEXTS) ---
# (يبقى كما هو بدون تغيير - تم إخفاؤه هنا للاختصار فقط، لكنه موجود في الكود الفعلي)
UI_TEXTS = {
    'ar': {
        # --- *** نصوص جديدة *** ---
        'th_admin_suggestions': "مقترحات/توصيات ادارية",
        'label_admin_suggestions': "مقترحات/توصيات ادارية (للأدمن):",
        'upcoming_activities_title': "أنشطة خلال الثلاث أيام القادمة",
        'no_upcoming_activities': "لا توجد أنشطة مجدولة خلال الأيام الثلاثة القادمة.",
        # -------------------------
        'monthly_plan': "خطة العمل الشهرية", 'org_name': "جمعية التحرير للتنمية",
        'plan_for': "خطة عمل شهر", 'prev_month': "الشهر السابق", 'next_month': "الشهر التالي",
        'login_editor': "الدخول كـ محرر", 'verify_code_placeholder': "أدخل رمز المحرر",
        'verify_btn': "تحقق", 'editor_mode_active': "وضع التحرير", 'editor_label': "المحرر",
        'logout_btn': "خروج", 'code_correct': "الرمز صحيح! يرجى اختيار اسم المحرر.",
        'select_editor_prompt': "-- اختر اسم المحرر --", 'confirm_editor_btn': "تأكيد",
        'cancel_btn': "إلغاء", 'code_incorrect': "الرمز المدخل غير صحيح.",
        'editor_selected_msg': "تم اختيار المحرر", 'invalid_editor': "المحرر المختار غير صالح.",
        'invalid_editor_id': "معرف المحرر غير صالح.", 'select_editor_warning': "الرجاء اختيار اسم المحرر.",
        'editor_mode_logout_msg': "تم الخروج من وضع التحرير.", 'add_activity_btn': "إضافة نشاط جديد +",
        'edit_btn': "تعديل", 'delete_btn': "حذف", 'confirm_delete_msg': "هل أنت متأكد من حذف هذا النشاط؟",
        'activity_deleted_success': "تم حذف النشاط بنجاح.", 'activity_deleted_error': "حدث خطأ أثناء حذف النشاط.",
        'modal_title_add': "إضافة نشاط جديد", 'modal_title_edit': "تعديل النشاط رقم",
        'save_changes_btn': "حفظ التغييرات", 'activity_added_success': "تم إضافة النشاط بنجاح!",
        'date_format_error': "تنسيق التاريخ غير صحيح. الرجاء استخدام YYYY-MM-DD.",
        'activity_added_error': "حدث خطأ أثناء إضافة النشاط.", 'activity_updated_success': "تم تحديث النشاط بنجاح!",
        'activity_updated_error': "حدث خطأ أثناء تحديث النشاط.", 'fetch_error': "حدث خطأ أثناء جلب البيانات.",
        'fetch_activity_error': "حدث خطأ أثناء جلب بيانات النشاط للتعديل.",
        'editor_required_warning': "يجب الدخول كـ محرر أو Admin واختيار اسمك للوصول لهذه الوظيفة.", # تم التعديل
        'no_activities_msg': "لا توجد أنشطة لعرضها لشهر",
        'th_id': "ت", 'th_date': "التاريخ", 'th_project': "المشروع والمانح", 'th_activity': "النشاط",
        'th_location': "موقع التنفيذ", 'th_confirmed': "مؤكد/غير مؤكد", 'th_programs': "البرامج",
        'th_logistics': "اللوجستيين", 'th_finance': "المالية", 'th_media': "الميديا", 'th_cars': "السيارات",
        'th_execution_status': "حالة التنفيذ", 'th_publication_links': "روابط النشر",
        'th_last_update': "آخر تحديث", 'th_actions': "إجراءات", 'confirmed': "مؤكد", 'unconfirmed': "غير مؤكد",
        'label_date': "التاريخ:", 'label_project': "المشروع والمانح:", 'label_activity': "النشاط:",
        'label_location': "موقع التنفيذ:", 'label_confirmed': "مؤكد؟", 'label_teams': "تفاصيل الفرق:",
        'label_programs': "البرامج:", 'label_logistics': "اللوجستيين:", 'label_finance': "المالية:",
        'label_media': "الميديا:", 'label_cars': "السيارات:",
        'label_execution_status': "تم التنفيذ؟", 'label_publication_links': "روابط النشر (اختياري):",
        'label_link1': "الرابط 1:", 'label_link2': "الرابط 2:", 'label_link3': "الرابط 3:",
        'project_none': "-- لا يوجد --", 'updated_by': "بواسطة",
        'export_pdf_btn': "تصدير PDF", 'pdf_export_error': "حدث خطأ أثناء تصدير PDF.",
        'weasyprint_not_found': "مكتبة WeasyPrint غير موجودة. لا يمكن تصدير PDF.",
        'executed': "منفذ", 'not_executed': "غير منفذ",
        'required_field': 'هذا الحقل مطلوب.',
        'login_admin': "الدخول كـ Admin",
        'verify_admin_code_placeholder': "أدخل رمز الـ Admin",
        'admin_mode_active': "وضع Admin",
        'settings_btn': "الإعدادات",
        'admin_settings_title': "إعدادات النظام",
        'manage_editors': "إدارة المحررين",
        'manage_projects': "إدارة المشاريع",
        'add_editor_btn': "إضافة محرر جديد +",
        'add_project_btn': "إضافة مشروع جديد +",
        'label_editor_name': "اسم المحرر:",
        'label_project_name': "اسم المشروع:",
        'modal_title_add_editor': "إضافة محرر جديد",
        'modal_title_edit_editor': "تعديل محرر",
        'modal_title_add_project': "إضافة مشروع جديد",
        'modal_title_edit_project': "تعديل مشروع",
        'editor_added_success': "تم إضافة المحرر بنجاح.",
        'editor_updated_success': "تم تحديث المحرر بنجاح.",
        'editor_deleted_success': "تم حذف المحرر بنجاح.",
        'editor_add_error': "خطأ في إضافة المحرر.",
        'editor_update_error': "خطأ في تحديث المحرر.",
        'editor_delete_error': "خطأ في حذف المحرر.",
        'editor_delete_confirm': "هل أنت متأكد من حذف هذا المحرر؟ ({name})",
        'editor_delete_prevented': "لا يمكن حذف المحرر لوجود أنشطة مرتبطة به.",
        'editor_delete_current_error': "لا يمكنك حذف المحرر المحدد حالياً.",
        'project_added_success': "تم إضافة المشروع بنجاح.",
        'project_updated_success': "تم تحديث المشروع بنجاح.",
        'project_deleted_success': "تم حذف المشروع بنجاح.",
        'project_add_error': "خطأ في إضافة المشروع.",
        'project_update_error': "خطأ في تحديث المشروع.",
        'project_delete_error': "خطأ في حذف المشروع.",
        'project_delete_confirm': "هل أنت متأكد من حذف هذا المشروع؟ ({name})",
        'project_delete_prevented': "لا يمكن حذف المشروع لوجود أنشطة مرتبطة به.",
        'admin_logout_msg': "تم الخروج من وضع Admin.",
        'admin_required_warning': "يجب الدخول كـ Admin للوصول لهذه الصفحة.",
        'name_required': 'الاسم مطلوب.',
        'name_unique': 'هذا الاسم مستخدم بالفعل.',
        'fetch_editors_error': 'خطأ في جلب قائمة المحررين.',
        'fetch_projects_error': 'خطأ في جلب قائمة المشاريع.',
        'get_editor_error': 'خطأ في جلب بيانات المحرر للتعديل.',
        'get_project_error': 'خطأ في جلب بيانات المشروع للتعديل.',
    },
    'en': {
        # --- *** New Texts *** ---
        'th_admin_suggestions': "Admin Suggestions/Recommendations",
        'label_admin_suggestions': "Admin Suggestions/Recommendations (Admin Only):",
        'upcoming_activities_title': "Activities Within Next 3 Days",
        'no_upcoming_activities': "No activities scheduled within the next 3 days.",
        # -------------------------
        'monthly_plan': "Monthly Work Plan", 'org_name': "Al-Tahrir Association for Development",
        'plan_for': "Work Plan for", 'prev_month': "Previous Month", 'next_month': "Next Month",
        'login_editor': "Login as Editor", 'verify_code_placeholder': "Enter Editor Code",
        'verify_btn': "Verify", 'editor_mode_active': "Editor Mode", 'editor_label': "Editor",
        'logout_btn': "Logout", 'code_correct': "Code correct! Please select editor name.",
        'select_editor_prompt': "-- Select Editor Name --", 'confirm_editor_btn': "Confirm",
        'cancel_btn': "Cancel", 'code_incorrect': "Incorrect code entered.",
        'editor_selected_msg': "Editor selected", 'invalid_editor': "Selected editor is invalid.",
        'invalid_editor_id': "Invalid editor ID.", 'select_editor_warning': "Please select editor name.",
        'editor_mode_logout_msg': "Logged out from editor mode.", 'add_activity_btn': "Add New Activity +",
        'edit_btn': "Edit", 'delete_btn': "Delete", 'confirm_delete_msg': "Are you sure you want to delete this activity?",
        'activity_deleted_success': "Activity deleted successfully.", 'activity_deleted_error': "Error deleting activity.",
        'modal_title_add': "Add New Activity", 'modal_title_edit': "Edit Activity ID",
        'save_changes_btn': "Save Changes", 'activity_added_success': "Activity added successfully!",
        'date_format_error': "Invalid date format. Please use YYYY-MM-DD.",
        'activity_added_error': "Error adding activity.", 'activity_updated_success': "Activity updated successfully!",
        'activity_updated_error': "Error updating activity.", 'fetch_error': "Error fetching data.",
        'fetch_activity_error': "Error fetching activity data for editing.",
        'editor_required_warning': "You must be logged in as an Editor or Admin and select your name to access this function.", # Updated
        'no_activities_msg': "No activities to display for",
        'th_id': "ID", 'th_date': "Date", 'th_project': "Project & Donor", 'th_activity': "Activity",
        'th_location': "Location", 'th_confirmed': "Confirmed/Unconfirmed", 'th_programs': "Programs",
        'th_logistics': "Logistics", 'th_finance': "Finance", 'th_media': "Media", 'th_cars': "Cars",
        'th_execution_status': "Exec. Status", 'th_publication_links': "Publ. Links",
        'th_last_update': "Last Update", 'th_actions': "Actions", 'confirmed': "Confirmed", 'unconfirmed': "Unconfirmed",
        'label_date': "Date:", 'label_project': "Project & Donor:", 'label_activity': "Activity:",
        'label_location': "Location:", 'label_confirmed': "Confirmed?", 'label_teams': "Team Details:",
        'label_programs': "Programs:", 'label_logistics': "Logistics:", 'label_finance': "Finance:",
        'label_media': "Media:", 'label_cars': "Cars:",
        'label_execution_status': "Executed?", 'label_publication_links': "Publication Links (Optional):",
        'label_link1': "Link 1:", 'label_link2': "Link 2:", 'label_link3': "Link 3:",
        'project_none': "-- None --", 'updated_by': "By",
        'export_pdf_btn': "Export PDF", 'pdf_export_error': "Error exporting PDF.",
        'weasyprint_not_found': "WeasyPrint library not found. PDF export disabled.",
        'executed': "Executed", 'not_executed': "Not Executed",
        'required_field': 'This field is required.',
        'login_admin': "Login as Admin",
        'verify_admin_code_placeholder': "Enter Admin Code",
        'admin_mode_active': "Admin Mode",
        'settings_btn': "Settings",
        'admin_settings_title': "System Settings",
        'manage_editors': "Manage Editors",
        'manage_projects': "Manage Projects",
        'add_editor_btn': "Add New Editor +",
        'add_project_btn': "Add New Project +",
        'label_editor_name': "Editor Name:",
        'label_project_name': "Project Name:",
        'modal_title_add_editor': "Add New Editor",
        'modal_title_edit_editor': "Edit Editor",
        'modal_title_add_project': "Add New Project",
        'modal_title_edit_project': "Edit Project",
        'editor_added_success': "Editor added successfully.",
        'editor_updated_success': "Editor updated successfully.",
        'editor_deleted_success': "Editor deleted successfully.",
        'editor_add_error': "Error adding editor.",
        'editor_update_error': "Error updating editor.",
        'editor_delete_error': "Error deleting editor.",
        'editor_delete_confirm': "Are you sure you want to delete this editor? ({name})",
        'editor_delete_prevented': "Cannot delete editor with associated activities.",
        'editor_delete_current_error': "You cannot delete the currently selected editor.",
        'project_added_success': "Project added successfully.",
        'project_updated_success': "Project updated successfully.",
        'project_deleted_success': "Project deleted successfully.",
        'project_add_error': "Error adding project.",
        'project_update_error': "Error updating project.",
        'project_delete_error': "Error deleting project.",
        'project_delete_confirm': "Are you sure you want to delete this project? ({name})",
        'project_delete_prevented': "Cannot delete project with associated activities.",
        'admin_logout_msg': "Logged out from Admin mode.",
        'admin_required_warning': "You must be logged in as an Admin to access this page.",
        'name_required': 'Name is required.',
        'name_unique': 'This name is already in use.',
        'fetch_editors_error': 'Error fetching editor list.',
        'fetch_projects_error': 'Error fetching project list.',
        'get_editor_error': 'Error fetching editor data for editing.',
        'get_project_error': 'Error fetching project data for editing.',
    }
}


# --- إعدادات التطبيق وقاعدة البيانات ---
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)

# --- تحديد رابط قاعدة البيانات (DATABASE_URL) ---
# ===> هذا هو الجزء الذي تم تعديله <===
DATABASE_URL = os.environ.get('DATABASE_URL')
using_postgres = False # متغير لتتبع ما إذا كنا نستخدم PostgreSQL

if DATABASE_URL:
    if DATABASE_URL.startswith('postgresql://'):
        # يتعرف على الرابط الجديد مباشرة
        print("--- INFO: Using PostgreSQL database (postgresql://) from Environment Variable.")
        using_postgres = True
    elif DATABASE_URL.startswith('postgres://'):
        # يتعرف على الرابط القديم ويقوم بالتعديل
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        print("--- INFO: Using PostgreSQL database (postgres:// converted) from Environment Variable.")
        using_postgres = True

# Fallback to SQLite only if DATABASE_URL is not set or not recognized as PostgreSQL
if not using_postgres:
    print("--- INFO: DATABASE_URL not set or not recognized as PostgreSQL. Using local SQLite database (database.db).")
    DATABASE_URL = 'sqlite:///' + os.path.join(basedir, 'database.db')

# تعيين الرابط النهائي للتطبيق
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
print(f"--- INFO: Final SQLALCHEMY_DATABASE_URI set.") # طباعة للتأكيد
# ===> نهاية الجزء المعدل <===

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-fallback-secret-key-change-it')
EDITOR_CODE = os.environ.get('EDITOR_CODE', '0000')
ADMIN_CODE = os.environ.get('ADMIN_CODE', 'admin0000')

# ===> لا يوجد بلوك try...except حول استيراد النماذج هنا لأنه تم في الأعلى <===

# --- دوال مساعدة ووظائف دعم اللغات ---

def editor_required(f):
    """Decorator to ensure user is logged in as Editor or Admin AND has selected an editor name."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        lang = get_locale()
        is_editor_session = session.get('is_editor', False)
        is_admin_session = session.get('is_admin', False)
        has_editor_id = session.get('editor_id') is not None

        if not ((is_editor_session or is_admin_session) and has_editor_id):
            if not (is_editor_session or is_admin_session):
                flash(get_text('editor_required_warning'), 'warning')
            elif not has_editor_id:
                 flash(get_text('select_editor_warning'), 'warning')

            referrer = request.referrer
            target_url = url_for('monthly_plan', lang=lang)
            # (الكود الخاص بمحاولة تحديد الشهر والسنة من الرابط المرجعي يبقى كما هو)
            if referrer:
                 parts = referrer.split('/')
                 try:
                     if len(parts) >= 6 and parts[-3] == 'plan' and parts[-2].isdigit() and parts[-1].isdigit():
                         target_url = url_for('monthly_plan', year=int(parts[-2]), month=int(parts[-1]), lang=lang)
                     elif len(parts) >= 7 and parts[-4] == 'plan' and parts[-2].isdigit() and parts[-1].isdigit():
                         target_url = url_for('monthly_plan', year=int(parts[-2]), month=int(parts[-1]), lang=parts[-3])
                 except (ValueError, IndexError):
                     pass
            return redirect(target_url)
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to ensure user is logged in as Admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        lang = get_locale()
        if not session.get('is_admin'):
            flash(get_text('admin_required_warning'), 'danger')
            # (الكود الخاص بتحديد الرابط المرجعي يبقى كما هو)
            referrer = request.referrer
            target_url = url_for('monthly_plan', lang=lang)
            if referrer:
                 parts = referrer.split('/')
                 try:
                     if len(parts) >= 6 and parts[-3] == 'plan' and parts[-2].isdigit() and parts[-1].isdigit():
                         target_url = url_for('monthly_plan', year=int(parts[-2]), month=int(parts[-1]), lang=lang)
                     elif len(parts) >= 7 and parts[-4] == 'plan' and parts[-2].isdigit() and parts[-1].isdigit():
                         target_url = url_for('monthly_plan', year=int(parts[-2]), month=int(parts[-1]), lang=parts[-3])
                 except (ValueError, IndexError):
                     pass
            return redirect(target_url)
        return f(*args, **kwargs)
    return decorated_function

def get_locale():
    return session.get('lang', DEFAULT_LANGUAGE)

def get_text(key, **kwargs):
    """Gets translated text for a key, allowing keyword arguments for formatting."""
    lang = get_locale()
    text = UI_TEXTS.get(lang, UI_TEXTS[DEFAULT_LANGUAGE]).get(key, key)
    try:
        return text.format(**kwargs)
    except (KeyError, TypeError, IndexError):
        return text

def get_day_name(date_obj, lang):
    """Returns the localized name of the day of the week."""
    if not date_obj:
        return ""
    day_index = date_obj.weekday()
    lang_days = DAYS_OF_WEEK.get(lang, DAYS_OF_WEEK[DEFAULT_LANGUAGE])
    if 0 <= day_index < len(lang_days):
        return lang_days[day_index]
    return ""

@app.context_processor
def inject_language_vars():
    """Injects language settings, user status, and helper functions into templates."""
    lang = get_locale()
    is_admin = session.get('is_admin', False)
    is_editor = session.get('is_editor', False) # True if editor OR admin logged in
    editor_id = session.get('editor_id')
    editor_name = session.get('editor_name')
    return dict(
        lang=lang,
        lang_dir=LANGUAGES.get(lang, {}).get('dir', 'rtl'),
        UI=UI_TEXTS.get(lang, UI_TEXTS[DEFAULT_LANGUAGE]),
        WEASYPRINT_AVAILABLE=WEASYPRINT_AVAILABLE, # تم نقل تعريفه للأعلى
        is_admin=is_admin,
        is_editor=is_editor,
        selected_editor_id=editor_id,
        selected_editor_name=editor_name,
        get_text=get_text,
        get_day_name=get_day_name
    )

# --- إنشاء الجداول وإضافة البيانات الأولية ---
# ===> تم نقل هذا البلوك إلى هنا ليكون بعد تعريف التطبيق وقبل تشغيل المسارات <===
with app.app_context():
    print("--- INFO: Initializing DB within app context...")
    try:
        # ===> ربط قاعدة البيانات بالتطبيق هنا <===
        db.init_app(app)
        print("--- INFO: DB initialized with app.")
        # ===> إنشاء الجداول <===
        db.create_all()
        print("--- INFO: DB tables created (if not exist).")

        # ===> إضافة البيانات الأولية فقط إذا كانت الجداول فارغة <===
        if not Project.query.first():
            print("--- INFO: Adding initial projects...")
            p1 = Project(name="مشروع ألفا")
            p2 = Project(name="مشروع بيتا")
            p3 = Project(name="مشروع جاما")
            db.session.add_all([p1, p2, p3])
            db.session.commit()
            print("--- INFO: Initial projects added.")
        else:
            print("--- INFO: Projects table not empty, skipping initial project data.")

        if not Editor.query.first():
            print("--- INFO: Adding initial editors...")
            e1=Editor(name="أحمد علي")
            e2=Editor(name="فاطمة حسن")
            e3=Editor(name="يوسف خالد")
            e4=Editor(name="مريم سعيد")
            e5=Editor(name="عمر محمود")
            e6=Editor(name="ليلى إبراهيم")
            e7=Editor(name="خالد عبدالله")
            db.session.add_all([e1,e2,e3,e4,e5,e6,e7])
            db.session.commit()
            print("--- INFO: Initial editors added.")
        else:
             print("--- INFO: Editors table not empty, skipping initial editor data.")

        if not Activity.query.first():
            print("--- INFO: Adding initial activities...")
            default_project = Project.query.first()
            default_editor = Editor.query.first()
            project_beta = Project.query.filter_by(name="مشروع بيتا").first()
            editor_fatima = Editor.query.filter_by(name="فاطمة حسن").first()

            if default_project and default_editor and project_beta and editor_fatima:
                today = date.today()
                next_month_date = today + relativedelta(months=1)
                tomorrow = today + timedelta(days=1)
                day_after_tomorrow = today + timedelta(days=2)

                a1 = Activity(activity_date=today, project_id=default_project.id, activity_desc="نشاط تجريبي للشهر الحالي.", location="المكتب الرئيسي", confirmed=True, team_programs="فريق أ", last_updated_by_id=default_editor.id, execution_status=False)
                a2 = Activity(activity_date=next_month_date.replace(day=15), project_id=default_project.id, activity_desc="نشاط تجريبي للشهر القادم.", location="الموقع الميداني", confirmed=False, team_programs="فريق ب", last_updated_by_id=default_editor.id, execution_status=True, link1="https://example.com/report1")
                a3 = Activity(activity_date=tomorrow, project_id=project_beta.id, activity_desc="نشاط تجريبي للغد.", location="القاعة الكبرى", confirmed=True, team_programs="فريق ج", last_updated_by_id=editor_fatima.id, execution_status=False, admin_suggestions="تأكد من جاهزية العرض التقديمي.")
                a4 = Activity(activity_date=day_after_tomorrow, project_id=default_project.id, activity_desc="نشاط تجريبي لبعد غد.", location="المكتب الرئيسي", confirmed=True, team_programs="فريق أ", last_updated_by_id=default_editor.id, execution_status=False)

                db.session.add_all([a1, a2, a3, a4])
                db.session.commit()
                print("--- INFO: Initial activities added.")
            else:
                print("--- WARNING: Skipping initial activity creation because default project/editor not found.")
        else:
            print("--- INFO: Activities table not empty, skipping initial activity data.")

        print("--- INFO: DB Initialization block finished.")

    except Exception as e:
        print(f"--- CRITICAL ERROR during DB initialization: {e}")
        traceback.print_exc()
        # لا يمكن استخدام flash هنا لأننا خارج سياق الطلب
        # يمكن الخروج من البرنامج إذا كانت قاعدة البيانات ضرورية للبدء
        # sys.exit("Failed to initialize database.")


# --- المسارات الرئيسية (Routes) ---
# (بقية المسارات تبقى كما هي بدون تغيير)
@app.route('/')
@app.route('/<lang>/')
@app.route('/plan/')
@app.route('/<lang>/plan/')
@app.route('/plan/<int:year>/<int:month>')
@app.route('/<lang>/plan/<int:year>/<int:month>')
def monthly_plan(lang=None, year=None, month=None):
    """Displays the monthly activity plan and upcoming activities."""
    if lang and lang in LANGUAGES:
        session['lang'] = lang
    current_lang = get_locale()

    current_time = datetime.now()
    if year is None: year = current_time.year
    if month is None: month = current_time.month

    if not 1 <= month <= 12:
        month = current_time.month
        year = current_time.year

    try:
        start_date = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = date(year, month, last_day)
    except ValueError:
        year = current_time.year
        month = current_time.month
        start_date = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = date(year, month, last_day)

    activities = []
    editors = []
    projects = []
    upcoming_activities = []
    try:
        activities = Activity.query.options(
            db.joinedload(Activity.project),
            db.joinedload(Activity.last_updated_by)
        ).filter(
            Activity.activity_date >= start_date,
            Activity.activity_date <= end_date
        ).order_by(Activity.activity_date).all()

        editors = Editor.query.order_by(Editor.name).all()
        projects = Project.query.order_by(Project.name).all()

        today = date.today()
        three_days_later = today + timedelta(days=2)
        upcoming_activities = Activity.query.options(
            db.joinedload(Activity.project)
        ).filter(
            Activity.activity_date >= today,
            Activity.activity_date <= three_days_later
        ).order_by(Activity.activity_date).all()

    except Exception as e:
        print(f"--- ERROR fetching data for {year}-{month}: {e}")
        traceback.print_exc()
        flash(get_text('fetch_error'), "danger")

    next_month_date = start_date + relativedelta(months=1)
    next_month_url = url_for('monthly_plan', year=next_month_date.year, month=next_month_date.month, lang=current_lang)
    prev_month_date = start_date - relativedelta(months=1)
    prev_month_url = url_for('monthly_plan', year=prev_month_date.year, month=prev_month_date.month, lang=current_lang)

    month_name = MONTHS[current_lang][month - 1] if 0 <= month - 1 < 12 else f"Month {month}"
    page_title = f"{get_text('plan_for')} {month_name} {year} - {get_text('org_name')}"

    return render_template('index.html',
                           title=page_title,
                           activities=activities,
                           current_year=year,
                           current_month=month,
                           month_name=month_name,
                           next_month_url=next_month_url,
                           prev_month_url=prev_month_url,
                           editors=editors,
                           projects=projects,
                           LANGUAGES=LANGUAGES,
                           upcoming_activities=upcoming_activities
                           )

# --- مسارات التحقق وتسجيل الخروج ---
@app.route('/verify-code', methods=['POST'])
def verify_code():
    """Verifies the Editor code."""
    entered_code = request.form.get('editor_code')
    lang = get_locale()
    redirect_url = request.referrer or url_for('monthly_plan', lang=lang)

    if entered_code == EDITOR_CODE:
        session['is_editor'] = True
        session.pop('is_admin', None)
        flash(get_text('code_correct'), 'success')
    else:
        session.pop('is_editor', None)
        session.pop('editor_id', None)
        session.pop('editor_name', None)
        flash(get_text('code_incorrect'), 'danger')
    return redirect(redirect_url)

@app.route('/verify-admin-code', methods=['POST'])
def verify_admin_code():
    """Verifies the Admin code."""
    entered_code = request.form.get('admin_code')
    lang = get_locale()
    redirect_url = request.referrer or url_for('monthly_plan', lang=lang)

    if entered_code == ADMIN_CODE:
        session['is_admin'] = True
        session['is_editor'] = True # Admin has editor privileges too
        flash(get_text('code_correct'), 'success')
    else:
        session.pop('is_admin', None)
        flash(get_text('code_incorrect'), 'danger')
    return redirect(redirect_url)

@app.route('/select-editor', methods=['POST'])
def select_editor():
    """Handles editor selection after login (for both Editor and Admin)."""
    lang = get_locale()
    redirect_url = request.referrer or url_for('monthly_plan', lang=lang)

    if not (session.get('is_editor') or session.get('is_admin')):
        return redirect(url_for('monthly_plan', lang=lang))

    editor_id_str = request.form.get('selected_editor')

    if editor_id_str and editor_id_str.isdigit():
        editor_id = int(editor_id_str)
        try:
            selected_editor = Editor.query.get(editor_id)
            if selected_editor:
                session['editor_id'] = selected_editor.id
                session['editor_name'] = selected_editor.name
                flash(f"{get_text('editor_selected_msg')}: {selected_editor.name}", 'info')
            else:
                flash(get_text('invalid_editor'), 'danger')
                session.pop('editor_id', None); session.pop('editor_name', None)
        except Exception as e:
            print(f"--- ERROR selecting editor {editor_id}: {e}"); traceback.print_exc()
            flash(get_text('invalid_editor_id'), 'danger')
            session.pop('editor_id', None); session.pop('editor_name', None)
    else:
        session.pop('editor_id', None); session.pop('editor_name', None)
        if editor_id_str: flash(get_text('invalid_editor_id'), 'danger')
        else: flash(get_text('select_editor_warning'), 'warning')

    return redirect(redirect_url)

@app.route('/logout')
def logout():
    """Logs out the user (Editor or Admin)."""
    lang = get_locale()
    was_admin = session.get('is_admin', False)
    session.pop('is_editor', None); session.pop('editor_id', None)
    session.pop('editor_name', None); session.pop('is_admin', None)
    if was_admin: flash(get_text('admin_logout_msg'), 'info')
    else: flash(get_text('editor_mode_logout_msg'), 'info')
    return redirect(url_for('monthly_plan', lang=lang))


# --- مسارات CRUD للأنشطة (Activity CRUD Routes) ---

@app.route('/add', methods=['POST'])
@editor_required
def add_activity():
    """Adds a new activity, including admin suggestions if applicable."""
    lang = get_locale()
    # (الكود لتحديد رابط إعادة التوجيه يبقى كما هو)
    activity_date_str = request.form.get('activity_date')
    redirect_year = datetime.now().year; redirect_month = datetime.now().month
    if activity_date_str:
        try: activity_date_obj = datetime.strptime(activity_date_str, '%Y-%m-%d').date(); redirect_year = activity_date_obj.year; redirect_month = activity_date_obj.month
        except ValueError: pass
    elif request.referrer:
        parts = request.referrer.split('/')
        try:
            if len(parts) >= 6 and parts[-3] == 'plan' and parts[-2].isdigit() and parts[-1].isdigit(): redirect_year = int(parts[-2]); redirect_month = int(parts[-1])
            elif len(parts) >= 7 and parts[-4] == 'plan' and parts[-2].isdigit() and parts[-1].isdigit(): redirect_year = int(parts[-2]); redirect_month = int(parts[-1])
        except (ValueError, IndexError): pass
    redirect_url = url_for('monthly_plan', year=redirect_year, month=redirect_month, lang=lang)

    print("--- ADD: Received form data:", request.form)
    try:
        # (الكود لاستخراج الحقول القياسية يبقى كما هو)
        activity_desc = request.form.get('activity_desc', '').strip()
        location = request.form.get('location', '').strip()
        team_programs = request.form.get('team_programs', '').strip()
        team_logistics = request.form.get('team_logistics', '').strip()
        team_finance = request.form.get('team_finance', '').strip()
        team_media = request.form.get('team_media', '').strip()
        team_cars = request.form.get('team_cars', '').strip()
        link1 = request.form.get('link1', '').strip()
        link2 = request.form.get('link2', '').strip()
        link3 = request.form.get('link3', '').strip()
        confirmed = request.form.get('confirmed') == 'on'
        execution_status = request.form.get('execution_status') == 'on'
        project_id_str = request.form.get('project_id')
        project_id = int(project_id_str) if project_id_str and project_id_str.isdigit() else None

        admin_suggestions = None
        if session.get('is_admin'):
            admin_suggestions = request.form.get('admin_suggestions', '').strip() or None

        errors = False
        if not activity_date_str: flash(get_text('required_field') + f" ({get_text('label_date')})", 'danger'); errors = True
        if not activity_desc: flash(get_text('required_field') + f" ({get_text('label_activity')})", 'danger'); errors = True
        if errors: print("--- ADD: Validation errors found."); return redirect(redirect_url)

        try:
            activity_date = datetime.strptime(activity_date_str, '%Y-%m-%d').date()
            redirect_url = url_for('monthly_plan', year=activity_date.year, month=activity_date.month, lang=lang)
        except ValueError:
            flash(get_text('date_format_error'), 'danger'); print("--- ADD: Date format error.")
            # (الكود لتحديد رابط إعادة التوجيه الأصلي يبقى كما هو)
            original_redirect_url = url_for('monthly_plan', year=datetime.now().year, month=datetime.now().month, lang=lang)
            if request.referrer:
                 parts = request.referrer.split('/')
                 try:
                     if len(parts) >= 6 and parts[-3] == 'plan' and parts[-2].isdigit() and parts[-1].isdigit(): original_redirect_url = url_for('monthly_plan', year=int(parts[-2]), month=int(parts[-1]), lang=lang)
                     elif len(parts) >= 7 and parts[-4] == 'plan' and parts[-2].isdigit() and parts[-1].isdigit(): original_redirect_url = url_for('monthly_plan', year=int(parts[-2]), month=int(parts[-1]), lang=parts[-3])
                 except (ValueError, IndexError): pass
            return redirect(original_redirect_url)

        new_activity = Activity(
            activity_date=activity_date, project_id=project_id, activity_desc=activity_desc,
            location=location or None, confirmed=confirmed, team_programs=team_programs or None,
            team_logistics=team_logistics or None, team_finance=team_finance or None,
            team_media=team_media or None, team_cars=team_cars or None,
            execution_status=execution_status, link1=link1 or None, link2=link2 or None, link3=link3 or None,
            last_updated_by_id=session.get('editor_id'),
            admin_suggestions=admin_suggestions
        )
        print("--- ADD: New Activity object:", {c.name: getattr(new_activity, c.name) for c in new_activity.__table__.columns})
        db.session.add(new_activity); db.session.commit()
        flash(get_text('activity_added_success'), 'success')
        print(f"--- INFO: Activity added successfully by editor ID {session.get('editor_id')}")
    except Exception as e:
        db.session.rollback(); flash(get_text('activity_added_error'), 'danger')
        print(f"--- ERROR adding activity: {e}"); traceback.print_exc()
    return redirect(redirect_url)

@app.route('/edit/<int:activity_id>', methods=['POST'])
@editor_required
def edit_activity(activity_id):
    """Edits an existing activity, including admin suggestions if applicable."""
    lang = get_locale()
    activity_to_edit = Activity.query.get_or_404(activity_id)
    original_date = activity_to_edit.activity_date
    redirect_url = url_for('monthly_plan', year=original_date.year, month=original_date.month, lang=lang)
    print(f"--- EDIT: Received form data for ID {activity_id}:", request.form)
    try:
        # (الكود لاستخراج الحقول القياسية يبقى كما هو)
        activity_date_str = request.form.get('activity_date')
        activity_desc = request.form.get('activity_desc', '').strip()
        location = request.form.get('location', '').strip()
        team_programs = request.form.get('team_programs', '').strip()
        team_logistics = request.form.get('team_logistics', '').strip()
        team_finance = request.form.get('team_finance', '').strip()
        team_media = request.form.get('team_media', '').strip()
        team_cars = request.form.get('team_cars', '').strip()
        link1 = request.form.get('link1', '').strip()
        link2 = request.form.get('link2', '').strip()
        link3 = request.form.get('link3', '').strip()
        confirmed = request.form.get('confirmed') == 'on'
        execution_status = request.form.get('execution_status') == 'on'
        project_id_str = request.form.get('project_id')
        project_id = int(project_id_str) if project_id_str and project_id_str.isdigit() else None

        admin_suggestions = None
        if session.get('is_admin'):
            submitted_suggestions = request.form.get('admin_suggestions', '__DEFAULT__')
            if submitted_suggestions != '__DEFAULT__':
                admin_suggestions = submitted_suggestions.strip() or None
            else:
                admin_suggestions = activity_to_edit.admin_suggestions

        errors = False
        if not activity_date_str: flash(get_text('required_field') + f" ({get_text('label_date')})", 'danger'); errors = True
        if not activity_desc: flash(get_text('required_field') + f" ({get_text('label_activity')})", 'danger'); errors = True
        if errors: print("--- EDIT: Validation errors found."); return redirect(redirect_url)

        try:
            new_date = datetime.strptime(activity_date_str, '%Y-%m-%d').date()
            if new_date.year != original_date.year or new_date.month != original_date.month:
                redirect_url = url_for('monthly_plan', year=new_date.year, month=new_date.month, lang=lang)
        except ValueError:
            flash(get_text('date_format_error'), 'danger'); print("--- EDIT: Date format error.")
            return redirect(redirect_url)

        # (الكود لتحديث الحقول القياسية يبقى كما هو)
        activity_to_edit.activity_date = new_date; activity_to_edit.project_id = project_id
        activity_to_edit.activity_desc = activity_desc; activity_to_edit.location = location or None
        activity_to_edit.confirmed = confirmed; activity_to_edit.team_programs = team_programs or None
        activity_to_edit.team_logistics = team_logistics or None; activity_to_edit.team_finance = team_finance or None
        activity_to_edit.team_media = team_media or None; activity_to_edit.team_cars = team_cars or None
        activity_to_edit.execution_status = execution_status; activity_to_edit.link1 = link1 or None
        activity_to_edit.link2 = link2 or None; activity_to_edit.link3 = link3 or None
        activity_to_edit.last_updated_by_id = session.get('editor_id')

        if session.get('is_admin'):
            activity_to_edit.admin_suggestions = admin_suggestions

        print("--- EDIT: Activity object before commit:", {c.name: getattr(activity_to_edit, c.name) for c in activity_to_edit.__table__.columns})
        db.session.commit(); flash(get_text('activity_updated_success'), 'success')
        print(f"--- INFO: Activity {activity_id} updated successfully by editor ID {session.get('editor_id')}")
    except Exception as e:
        db.session.rollback(); flash(get_text('activity_updated_error'), 'danger')
        print(f"--- ERROR updating activity {activity_id}: {e}"); traceback.print_exc()
    return redirect(redirect_url)

@app.route('/delete/<int:activity_id>', methods=['POST'])
@editor_required
def delete_activity_route(activity_id):
    """Deletes an activity."""
    lang = get_locale()
    activity_to_delete = Activity.query.get_or_404(activity_id)
    redirect_year = activity_to_delete.activity_date.year
    redirect_month = activity_to_delete.activity_date.month
    redirect_url = url_for('monthly_plan', year=redirect_year, month=redirect_month, lang=lang)
    desc_short = activity_to_delete.activity_desc[:20]
    try:
        db.session.delete(activity_to_delete)
        db.session.commit()
        flash(f"{get_text('activity_deleted_success')} ({desc_short}...)", 'success')
        print(f"--- INFO: Activity {activity_id} deleted by editor ID {session.get('editor_id')}")
    except Exception as e:
        db.session.rollback(); flash(get_text('activity_deleted_error'), 'danger'); print(f"--- ERROR deleting activity {activity_id}: {e}"); traceback.print_exc()
    return redirect(redirect_url)

@app.route('/get_activity/<int:activity_id>')
@editor_required
def get_activity_data(activity_id):
    """Returns activity data as JSON for the edit modal, including admin suggestions."""
    try:
        activity = Activity.query.get_or_404(activity_id)
        activity_data = {
            'id': activity.id,
            'activity_date': activity.activity_date.strftime('%Y-%m-%d') if activity.activity_date else '',
            'project_id': activity.project_id,
            'activity_desc': activity.activity_desc,
            'location': activity.location,
            'confirmed': activity.confirmed,
            'team_programs': activity.team_programs,
            'team_logistics': activity.team_logistics,
            'team_finance': activity.team_finance,
            'team_media': activity.team_media,
            'team_cars': activity.team_cars,
            'execution_status': activity.execution_status,
            'link1': activity.link1,
            'link2': activity.link2,
            'link3': activity.link3,
            'admin_suggestions': activity.admin_suggestions # تم تضمين المقترحات
        }
        return jsonify(activity_data)
    except Exception as e:
        print(f"--- ERROR fetching activity data for edit {activity_id}: {e}"); traceback.print_exc()
        return jsonify({'error': get_text('fetch_activity_error')}), 500

@app.route('/toggle_execution/<int:activity_id>', methods=['POST'])
@editor_required
def toggle_execution_status(activity_id):
    """Toggles the execution status of an activity via AJAX."""
    activity = Activity.query.get_or_404(activity_id)
    try:
        new_status = not activity.execution_status
        activity.execution_status = new_status
        activity.last_updated_by_id = session.get('editor_id')
        db.session.commit()
        print(f"--- INFO: Activity {activity_id} execution status toggled to {new_status} by editor ID {session.get('editor_id')}")
        return jsonify({'success': True, 'new_status': new_status})
    except Exception as e:
        db.session.rollback(); print(f"--- ERROR toggling execution status for activity {activity_id}: {e}"); traceback.print_exc()
        return jsonify({'success': False, 'message': get_text('activity_updated_error')}), 500


# --- مسارات إدارة الإعدادات (Admin Settings Routes) ---
# (الكود الخاص بمسارات /admin/... يبقى كما هو بدون تغيير)
@app.route('/admin/settings')
@admin_required
def admin_settings():
    """Displays the admin settings page."""
    lang = get_locale()
    editors = []
    projects = []
    try: editors = Editor.query.order_by(Editor.name).all()
    except Exception as e: print(f"--- ERROR fetching editors for admin settings: {e}"); traceback.print_exc(); flash(get_text('fetch_editors_error'), 'danger')
    try: projects = Project.query.order_by(Project.name).all()
    except Exception as e: print(f"--- ERROR fetching projects for admin settings: {e}"); traceback.print_exc(); flash(get_text('fetch_projects_error'), 'danger')
    return render_template('admin_settings.html', title=get_text('admin_settings_title'), editors=editors, projects=projects)

@app.route('/admin/editors/add', methods=['POST'])
@admin_required
def add_editor():
    """Adds a new editor."""
    name = request.form.get('editor_name', '').strip()
    lang = get_locale(); redirect_url = url_for('admin_settings', lang=lang)
    if not name: flash(get_text('name_required'), 'danger'); return redirect(redirect_url)
    try:
        new_editor = Editor(name=name); db.session.add(new_editor); db.session.commit()
        flash(get_text('editor_added_success'), 'success'); print(f"--- ADMIN: Editor '{name}' added.")
    except IntegrityError: db.session.rollback(); flash(get_text('name_unique'), 'warning'); print(f"--- ADMIN WARN: Attempted to add duplicate editor name '{name}'.")
    except Exception as e: db.session.rollback(); print(f"--- ERROR adding editor: {e}"); traceback.print_exc(); flash(get_text('editor_add_error'), 'danger')
    return redirect(redirect_url)

@app.route('/admin/editors/edit/<int:editor_id>', methods=['POST'])
@admin_required
def edit_editor(editor_id):
    """Edits an existing editor's name."""
    lang = get_locale(); redirect_url = url_for('admin_settings', lang=lang); editor_to_edit = Editor.query.get_or_404(editor_id)
    original_name = editor_to_edit.name; new_name = request.form.get('editor_name', '').strip()
    if not new_name: flash(get_text('name_required'), 'danger'); return redirect(redirect_url)
    if new_name == original_name: return redirect(redirect_url)
    try:
        existing = Editor.query.filter(Editor.name == new_name, Editor.id != editor_id).first()
        if existing: flash(get_text('name_unique'), 'warning'); print(f"--- ADMIN WARN: Attempted to rename editor {editor_id} to duplicate name '{new_name}'."); return redirect(redirect_url)
        editor_to_edit.name = new_name; db.session.commit()
        if session.get('editor_id') == editor_id: session['editor_name'] = new_name; print(f"--- ADMIN: Updated session name for editor {editor_id}.")
        flash(get_text('editor_updated_success'), 'success'); print(f"--- ADMIN: Editor {editor_id} ('{original_name}') renamed to '{new_name}'.")
    except IntegrityError: db.session.rollback(); flash(get_text('name_unique'), 'warning'); print(f"--- ADMIN ERROR: IntegrityError renaming editor {editor_id} to '{new_name}'.")
    except Exception as e: db.session.rollback(); print(f"--- ERROR updating editor {editor_id}: {e}"); traceback.print_exc(); flash(get_text('editor_update_error'), 'danger')
    return redirect(redirect_url)

@app.route('/admin/editors/delete/<int:editor_id>', methods=['POST'])
@admin_required
def delete_editor(editor_id):
    """Deletes an editor."""
    lang = get_locale(); redirect_url = url_for('admin_settings', lang=lang); editor_to_delete = Editor.query.get_or_404(editor_id)
    if session.get('editor_id') == editor_id: flash(get_text('editor_delete_current_error'), 'danger'); print(f"--- ADMIN WARN: Attempted to delete currently selected editor {editor_id}."); return redirect(redirect_url)
    if Activity.query.filter_by(last_updated_by_id=editor_id).first(): flash(get_text('editor_delete_prevented'), 'warning'); print(f"--- ADMIN WARN: Attempted to delete editor {editor_id} with associated activities."); return redirect(redirect_url)
    try:
        editor_name = editor_to_delete.name; db.session.delete(editor_to_delete); db.session.commit()
        flash(get_text('editor_deleted_success', name=editor_name), 'success'); print(f"--- ADMIN: Editor {editor_id} ('{editor_name}') deleted.")
    except Exception as e: db.session.rollback(); print(f"--- ERROR deleting editor {editor_id}: {e}"); traceback.print_exc(); flash(get_text('editor_delete_error'), 'danger')
    return redirect(redirect_url)

@app.route('/admin/get_editor/<int:editor_id>')
@admin_required
def get_editor_data(editor_id):
    """Returns editor data as JSON for the edit modal."""
    try: editor = Editor.query.get_or_404(editor_id); return jsonify({'id': editor.id, 'name': editor.name})
    except Exception as e: print(f"--- ERROR fetching editor data for admin edit {editor_id}: {e}"); traceback.print_exc(); return jsonify({'error': get_text('get_editor_error')}), 500

@app.route('/admin/projects/add', methods=['POST'])
@admin_required
def add_project():
    """Adds a new project."""
    name = request.form.get('project_name', '').strip(); lang = get_locale(); redirect_url = url_for('admin_settings', lang=lang)
    if not name: flash(get_text('name_required'), 'danger'); return redirect(redirect_url)
    try:
        new_project = Project(name=name); db.session.add(new_project); db.session.commit()
        flash(get_text('project_added_success'), 'success'); print(f"--- ADMIN: Project '{name}' added.")
    except IntegrityError: db.session.rollback(); flash(get_text('name_unique'), 'warning'); print(f"--- ADMIN WARN: Attempted to add duplicate project name '{name}'.")
    except Exception as e: db.session.rollback(); print(f"--- ERROR adding project: {e}"); traceback.print_exc(); flash(get_text('project_add_error'), 'danger')
    return redirect(redirect_url)

@app.route('/admin/projects/edit/<int:project_id>', methods=['POST'])
@admin_required
def edit_project(project_id):
    """Edits an existing project's name."""
    lang = get_locale(); redirect_url = url_for('admin_settings', lang=lang); project_to_edit = Project.query.get_or_404(project_id)
    original_name = project_to_edit.name; new_name = request.form.get('project_name', '').strip()
    if not new_name: flash(get_text('name_required'), 'danger'); return redirect(redirect_url)
    if new_name == original_name: return redirect(redirect_url)
    try:
        existing = Project.query.filter(Project.name == new_name, Project.id != project_id).first()
        if existing: flash(get_text('name_unique'), 'warning'); print(f"--- ADMIN WARN: Attempted to rename project {project_id} to duplicate name '{new_name}'."); return redirect(redirect_url)
        project_to_edit.name = new_name; db.session.commit()
        flash(get_text('project_updated_success'), 'success'); print(f"--- ADMIN: Project {project_id} ('{original_name}') renamed to '{new_name}'.")
    except IntegrityError: db.session.rollback(); flash(get_text('name_unique'), 'warning'); print(f"--- ADMIN ERROR: IntegrityError renaming project {project_id} to '{new_name}'.")
    except Exception as e: db.session.rollback(); print(f"--- ERROR updating project {project_id}: {e}"); traceback.print_exc(); flash(get_text('project_update_error'), 'danger')
    return redirect(redirect_url)

@app.route('/admin/projects/delete/<int:project_id>', methods=['POST'])
@admin_required
def delete_project(project_id):
    """Deletes a project."""
    lang = get_locale(); redirect_url = url_for('admin_settings', lang=lang); project_to_delete = Project.query.get_or_404(project_id)
    if Activity.query.filter_by(project_id=project_id).first(): flash(get_text('project_delete_prevented'), 'warning'); print(f"--- ADMIN WARN: Attempted to delete project {project_id} with associated activities."); return redirect(redirect_url)
    try:
        project_name = project_to_delete.name; db.session.delete(project_to_delete); db.session.commit()
        flash(get_text('project_deleted_success', name=project_name), 'success'); print(f"--- ADMIN: Project {project_id} ('{project_name}') deleted.")
    except Exception as e: db.session.rollback(); print(f"--- ERROR deleting project {project_id}: {e}"); traceback.print_exc(); flash(get_text('project_delete_error'), 'danger')
    return redirect(redirect_url)

@app.route('/admin/get_project/<int:project_id>')
@admin_required
def get_project_data(project_id):
    """Returns project data as JSON for the edit modal."""
    try: project = Project.query.get_or_404(project_id); return jsonify({'id': project.id, 'name': project.name})
    except Exception as e: print(f"--- ERROR fetching project data for admin edit {project_id}: {e}"); traceback.print_exc(); return jsonify({'error': get_text('get_project_error')}), 500


# --- مسار تصدير PDF (PDF Export Route) ---
@app.route('/export_pdf/<int:year>/<int:month>')
def export_pdf(year, month):
    """Exports the plan for the specified month as a PDF file."""
    lang = get_locale()
    # ===> التحقق من WeasyPrint يتم هنا قبل محاولة الاستخدام <===
    if not WEASYPRINT_AVAILABLE:
        flash(get_text('weasyprint_not_found'), 'danger')
        return redirect(url_for('monthly_plan', year=year, month=month, lang=lang))

    try:
        start_date = date(year, month, 1); last_day = calendar.monthrange(year, month)[1]; end_date = date(year, month, last_day)
        activities = Activity.query.options(
            db.joinedload(Activity.project),
            db.joinedload(Activity.last_updated_by)
        ).filter(
            Activity.activity_date >= start_date, Activity.activity_date <= end_date
        ).order_by(Activity.activity_date).all()

        month_name = MONTHS[lang][month - 1] if 0 <= month - 1 < 12 else f"Month {month}"
        pdf_title = f"{get_text('plan_for')} {month_name} {year} - {get_text('org_name')}"
        template_path = os.path.join(app.template_folder, 'pdf_template.html')
        if not os.path.exists(template_path):
             print(f"--- ERROR: PDF template not found at {template_path}"); flash(get_text('pdf_export_error') + " (Template missing)", 'danger')
             return redirect(url_for('monthly_plan', year=year, month=month, lang=lang))

        html_content = render_template(
            'pdf_template.html', title=pdf_title, activities=activities, lang=lang,
            lang_dir=LANGUAGES.get(lang, {}).get('dir', 'rtl'),
            UI=UI_TEXTS.get(lang, UI_TEXTS[DEFAULT_LANGUAGE]),
            month_name=month_name, current_year=year
        )

        # (الكود الخاص بـ CSS يبقى كما هو)
        current_direction = LANGUAGES.get(lang, {}).get('dir', 'rtl')
        current_text_align = 'right' if current_direction == 'rtl' else 'left'
        css_string = f"""
            @page {{ size: A4 landscape; margin: 0.8cm; @bottom-center {{ content: "Page " counter(page) " of " counter(pages); font-size: 8pt; color: #666; }} }}
            body {{ font-family: 'DejaVu Sans', Arial, sans-serif; font-size: 7.5pt; line-height: 1.3; direction: {current_direction}; }}
            .header {{ text-align: center; margin-bottom: 8px; padding: 5px; background-color: #3f51b5; color: white; border-radius: 3px; }}
            .title {{ font-size: 11pt; font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 6px; border: 1px solid #999; }}
            th, td {{ border: 1px solid #ccc; padding: 2px 4px; text-align: {current_text_align}; vertical-align: top; word-wrap: break-word; hyphens: auto; }}
            th {{ background-color: #e0e0e0; color: #333; font-weight: bold; text-align: center; vertical-align: middle; white-space: nowrap; font-size: 7pt;}}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            td:first-child, td:nth-child(2), td:nth-child(6), td:nth-child(12) {{ text-align: center; vertical-align: middle; }}
            .confirmed-true {{ background-color: #e8f5e9; }} .confirmed-false {{ background-color: #ffebee; }}
            .exec-true {{ background-color: #e3f2fd; }}
            .last-update {{ font-size: 0.8em; color: #666; text-align: center; white-space: nowrap; }}
            .links a {{ display: block; margin-bottom: 1px; color: #007bff; text-decoration: none; font-size: 0.8em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width:90px; }}
            .links a:hover {{ text-decoration: underline; }}
            td.admin-suggestions {{ font-size: 0.9em; color: #444; }}
            tr {{ page-break-inside: avoid; }} table {{ page-break-inside: auto; }}
        """

        print("--- PDF EXPORT: Generating PDF...")
        # ===> لا نحتاج للتحقق من WEASYPRINT_AVAILABLE مرة أخرى هنا <===
        html = HTML(string=html_content, base_url=basedir); pdf_file = html.write_pdf(stylesheets=[CSS(string=css_string)])
        print("--- PDF EXPORT: PDF generated successfully.")

        response = make_response(pdf_file); response.headers['Content-Type'] = 'application/pdf'
        raw_filename = f"Plan_{month_name}_{year}.pdf"; url_encoded_filename = quote(raw_filename)
        response.headers['Content-Disposition'] = f"inline; filename*=UTF-8''{url_encoded_filename}"
        return response

    except ImportError: # هذا الـ except سيلتقط الخطأ إذا فشل الاستيراد الأصلي لـ WeasyPrint
        print(f"--- ERROR: WeasyPrint components not loaded correctly during PDF generation."); flash(get_text('weasyprint_not_found'), 'danger')
        return redirect(url_for('monthly_plan', year=year, month=month, lang=lang))
    except Exception as e:
        print(f"--- ERROR exporting PDF for {year}-{month}: {e}"); traceback.print_exc(); flash(get_text('pdf_export_error'), 'danger')
        return redirect(url_for('monthly_plan', year=year, month=month, lang=lang))

# --- تشغيل التطبيق (App Runner) ---
if __name__ == '__main__':
    # (الكود الخاص بالتحقق من الحزم الاختيارية وتشغيل التطبيق يبقى كما هو)
    missing_packages = []
    try: import dateutil
    except ImportError: missing_packages.append('python-dateutil')
    try: import dotenv
    except ImportError: missing_packages.append('python-dotenv')
    if not WEASYPRINT_AVAILABLE: print("--- WARNING: WeasyPrint check at startup: PDF export disabled.")

    if missing_packages:
        print(f"--- WARNING: Missing optional packages: {', '.join(missing_packages)}. Install them for full functionality.")

    port = int(os.environ.get('PORT', 5000))
    # Set debug=True for development, False for production (using environment variable)
    is_debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    print(f"--- INFO: Running Flask app with debug mode: {is_debug_mode}")
    app.run(host='0.0.0.0', port=port, debug=is_debug_mode)
