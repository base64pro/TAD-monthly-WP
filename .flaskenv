# --- ملف: .flaskenv ---
# ملف لتحديد متغيرات البيئة لـ Flask (يجب حفظه بنفس اسم .flaskenv)
# Flask سيقرأ هذا الملف تلقائيًا عند استخدام أمر 'flask run'

# يخبر Flask بمكان العثور على كائن التطبيق الرئيسي (في ملف app.py، المتغير اسمه app)
FLASK_APP=app.py

# يضبط Flask ليعمل في وضع التطوير (development)
# هذا يتيح ميزات مثل وضع التصحيح (debugger) وإعادة التحميل التلقائي (reloader)
# وهو مفيد جدًا أثناء كتابة الكود
FLASK_ENV=development
# ملاحظة: في إصدارات Flask الأحدث، قد يُفضل استخدام FLASK_DEBUG=1 بدلاً من FLASK_ENV
# FLASK_DEBUG=1

