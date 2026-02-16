"""
WSGI configuration for PythonAnywhere deployment.

Instructions:
1. Upload all project files to /home/YOURUSERNAME/carnaval_saas/
2. Copy the content of this file into the PythonAnywhere WSGI config file at:
   /var/www/YOURUSERNAME_pythonanywhere_com_wsgi.py
3. Replace YOURUSERNAME with your actual username.
"""

import sys
import os

# Replace YOURUSERNAME with your PythonAnywhere username
project_home = '/home/g3v3r/carnaval_saas'

if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.chdir(project_home)

from app import app as application
