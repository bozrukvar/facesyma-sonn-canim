#!/usr/bin/env python
"""
create_admin.py
===============
Admin kullanıcı oluştur (seed script).

Usage:
    python manage.py shell
    >>> exec(open('create_admin.py').read())

Veya:
    python create_admin.py
"""

import os
import django

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facesyma_project.settings')
django.setup()

from admin_api.utils.auth import create_default_admin

if __name__ == '__main__':
    print("Creating default admin user...")
    result = create_default_admin()
    if result:
        print("✓ Admin kullanıcısı başarıyla oluşturuldu!")
        print("  E-posta: admin@facesyma.com")
        print("  Şifre: Yukarıdaki '[create_default_admin] Temporary password:' satırına bakın.")
        print("  UYARI: Giriş yaptıktan sonra şifrenizi mutlaka değiştirin!")
    else:
        print("✓ Admin kullanıcısı zaten mevcut.")
