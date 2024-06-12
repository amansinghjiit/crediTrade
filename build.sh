# Exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate --run-syncdb

echo "from django.contrib.auth.models import User; User.objects.create_superuser('amannick2', 'amannick2@gmail.com', 'kibtypen')" | python manage.py shell