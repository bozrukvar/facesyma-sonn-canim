#!/usr/bin/env python
"""manage.py"""
import os, sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facesyma_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Django yüklü değil.") from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
