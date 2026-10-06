"""
email_config.py
Fill this in with YOUR email account's SMTP details to make the
automated reminder emails actually send. Until you do, ENABLED stays
False and the app safely runs in DRY-RUN mode: it writes each email it
*would have* sent into sent_emails_log.txt instead of sending it, so
the Admin > Email Center screen still works for a demo.

---------------------------------------------------------------------
HOW TO SET THIS UP WITH A GMAIL ACCOUNT (most common for students):
1. Use a Gmail account you don't mind using for this project.
2. Turn on 2-Step Verification: myaccount.google.com/security
3. Create an "App Password": myaccount.google.com/apppasswords
   (Gmail will not let you use your normal login password for SMTP.)
4. Paste that 16-character app password below as SMTP_PASSWORD.
5. Set SMTP_USERNAME to your full Gmail address.
6. Set ENABLED = True.

Any other provider (Outlook, Yahoo, your college's mail, etc.) works
the same way -- just change SMTP_HOST/SMTP_PORT to match that provider.
---------------------------------------------------------------------
"""

ENABLED = False  # flip to True once the fields below are filled in

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587  # 587 = STARTTLS (used here). 465 = SSL.

SMTP_USERNAME = ""   # e.g. "yourprojectaccount@gmail.com"
SMTP_PASSWORD = ""   # the App Password, NOT your normal Gmail password

SENDER_NAME = "Bajaj & TVS Service Reminder Manager"
