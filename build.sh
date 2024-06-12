# Exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate --run-syncdb

python manage.py shell <<EOF
from django.contrib.auth.models import User

username = 'amannick2'
email = 'amannick2@gmail.com'
password = 'kibtypen'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print("Superuser created successfully.")
else:
    print("Superuser already exists. Skipping creation.")
EOF