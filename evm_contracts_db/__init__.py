import sys

if not(sys.argv[0] == 'manage.py'):
    import os
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "evm_contracts_db.settings")
    django.setup()