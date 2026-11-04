#!/usr/bin/env bash
set -e

echo "============================================================"
echo "🚀 KirayaSaathi — Google Cloud VM Automated Setup"
echo "============================================================"

# 1. Setup 2GB Swap Memory (Prevents memory crash on e2-micro 1GB RAM)
echo "[1/7] Configuring 2GB Swap space (Prevents memory crash)..."
if [ ! -f /swapfile ]; then
    sudo fallocate -l 2G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    sudo sysctl vm.swappiness=10
    echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
    echo "✅ Swap memory enabled!"
else
    echo "ℹ️ Swap file already exists."
fi

# 2. Update and Install Python 3.12 + System Dependencies
echo "[2/7] Installing Python 3.12, MySQL, Nginx, and Git..."
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y software-properties-common curl git
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3.12 python3.12-venv python3.12-dev \
    mysql-server nginx

# 3. Configure MySQL Database
echo "[3/7] Setting up MySQL database (kiraya_db)..."
sudo systemctl enable --now mysql
sudo mysql -e "CREATE DATABASE IF NOT EXISTS kiraya_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'kiraya_user'@'localhost' IDENTIFIED BY 'KirayaSaathi#2026!Db';"
sudo mysql -e "ALTER USER 'kiraya_user'@'localhost' IDENTIFIED BY 'KirayaSaathi#2026!Db';"
sudo mysql -e "GRANT ALL PRIVILEGES ON kiraya_db.* TO 'kiraya_user'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"
echo "✅ MySQL ready!"

# 4. Clone or Pull KirayaSaathi Backend Repository
echo "[4/7] Downloading KirayaSaathi Backend..."
sudo mkdir -p /var/www/kirayasaathi
sudo chown -R $USER:$USER /var/www/kirayasaathi
cd /var/www/kirayasaathi

if [ ! -d "backend/.git" ]; then
    rm -rf backend
    git clone https://github.com/GouravBerwal/KirayaSaathi_Backend.git backend
else
    cd backend
    git pull origin main
    cd ..
fi

cd /var/www/kirayasaathi/backend

# 5. Create Python 3.12 Virtual Environment & Install Dependencies
echo "[5/7] Installing Python 3.12 dependencies & migrating database..."
rm -rf /var/www/kirayasaathi/venv
python3.12 -m venv /var/www/kirayasaathi/venv

/var/www/kirayasaathi/venv/bin/pip install --upgrade pip
/var/www/kirayasaathi/venv/bin/pip install -r requirements.txt

cat << 'ENVEOF' > /var/www/kirayasaathi/backend/.env
DEBUG=False
SECRET_KEY=kirayasaathi-vm-gcp-2026-production-key-9a8b7c6d5e4f
DJANGO_ALLOWED_HOSTS=*
CORS_ALLOWED_ORIGINS=https://kirayasaathi.app,https://www.kirayasaathi.app,https://kiraya-saathi-frontend.vercel.app,http://localhost:5173
CSRF_TRUSTED_ORIGINS=https://kirayasaathi.app,https://www.kirayasaathi.app,https://kiraya-saathi-frontend.vercel.app
FRONTEND_URL=https://kirayasaathi.app

DB_ENGINE=mysql
DB_NAME=kiraya_db
DB_USER=kiraya_user
DB_PASSWORD=KirayaSaathi#2026!Db
DB_HOST=127.0.0.1
DB_PORT=3306

EMAIL_HOST_USER=kirayasaathi.support@gmail.com
EMAIL_HOST_PASSWORD=tvlybnzksxcbxbdf
DEFAULT_FROM_EMAIL=KirayaSaathi <kirayasaathi.support@gmail.com>
ALLOW_OTP_FALLBACK=True
ENVEOF

mkdir -p /var/www/kirayasaathi/media /var/www/kirayasaathi/static
if [ -f "/var/www/kirayasaathi/backend/kiraya_clean_for_cloud.sql" ]; then
    echo "Importing original MySQL database..."
    sudo mysql kiraya_db < /var/www/kirayasaathi/backend/kiraya_clean_for_cloud.sql
fi
/var/www/kirayasaathi/venv/bin/python manage.py migrate --noinput
/var/www/kirayasaathi/venv/bin/python manage.py collectstatic --noinput

# 6. Configure Systemd Service for Gunicorn (Runs 24x7)
echo "[6/7] Setting up Gunicorn 24x7 service..."
sudo tee /etc/systemd/system/kirayasaathi.service > /dev/null << 'SERVICEEOF'
[Unit]
Description=KirayaSaathi Gunicorn Application Daemon
After=network.target mysql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/kirayasaathi/backend
EnvironmentFile=/var/www/kirayasaathi/backend/.env
ExecStart=/var/www/kirayasaathi/venv/bin/gunicorn --workers 2 --threads 2 --bind 127.0.0.1:8000 --timeout 120 config.wsgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICEEOF

sudo chown -R www-data:www-data /var/www/kirayasaathi
sudo chmod -R 775 /var/www/kirayasaathi/media
sudo systemctl daemon-reload
sudo systemctl enable --now kirayasaathi
sudo systemctl restart kirayasaathi

# 7. Configure Nginx Web Server
echo "[7/7] Configuring Nginx Web Server..."
sudo tee /etc/nginx/sites-available/kirayasaathi > /dev/null << 'NGINXEOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 50M;

    location /static/ {
        alias /var/www/kirayasaathi/static/;
        expires 30d;
    }

    location /media/ {
        alias /var/www/kirayasaathi/media/;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
    }
}
NGINXEOF

sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/kirayasaathi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

echo "============================================================"
echo "🎉 SUCCESS! KirayaSaathi Backend & MySQL are now LIVE on VM!"
echo "Server IP: $(curl -s ifconfig.me)"
echo "Test API: http://$(curl -s ifconfig.me)/api/auth/csrf/"
echo "============================================================"
