@echo off
cd /d "C:\Users\Shivam Tyagi\property_rental"
call "venv\Scripts\activate.bat"
python manage.py send_renewal_reminders >> renewal_reminders.log 2>&1
