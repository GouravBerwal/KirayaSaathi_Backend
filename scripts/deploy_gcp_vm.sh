#!/usr/bin/env bash
set -e

echo "============================================================"
echo "🚀 KirayaSaathi — Google Cloud VM Automated Deployment Setup"
echo "============================================================"

# 1. Setup 2GB Swap Memory (Prevents Out-Of-Memory crashes on e2-micro 1GB RAM)
echo "[1/7] Configuring 2GB Swap space..."
if [ ! -f /swapfile ]; then
    sudo fallocate -l 2G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    sudo sysctl vm.swappiness=10
    echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
    echo "✅ Swap memory enabled successfully!"
else
    echo "ℹ️ Swap file already exists, skipping."
fi

# 2. Update and Install System Dependencies
echo "[2/7] Installing system packages (Python, MySQL, Nginx, Git)..."
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3-pip python3-venv python3-dev \
    mysql-server nginx git curl

# 3. Configure MySQL Database
echo "[3/7] Setting up local MySQL database (kiraya_db)..."
sudo systemctl enable --now mysql
sudo mysql -e "CREATE DATABASE IF NOT EXISTS kiraya_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'kiraya_user'@'localhost' IDENTIFIED BY 'KirayaSaathi#2026!Db';"
sudo mysql -e "ALTER USER 'kiraya_user'@'localhost' IDENTIFIED BY 'KirayaSaathi#2026!Db';"
sudo mysql -e "GRANT ALL PRIVILEGES ON kiraya_db.* TO 'kiraya_user'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"
echo "✅ MySQL database kiraya_db and user kiraya_user ready!"

# 4. Clone or Pull KirayaSaathi Backend Repository
echo "[4/7] Setting up KirayaSaathi Backend code..."
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

# 5. Create Python Virtual Environment & Install Dependencies
echo "[5/7] Setting up Python virtual environment and dependencies..."
if [ ! -d "/var/www/kirayasaathi/venv" ]; then
    python3 -m venv /var/www/kirayasaathi/venv
fi

/var/www/kirayasaathi/venv/bin/pip install --upgrade pip
/var/www/kirayasaathi/venv/bin/pip install -r requirements.txt

# Create .env configuration
cat << 'EOF' > /var/www/kirayasaathi/backend/.env
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

EMAIL_HOST_USER=gouravberwal003@gmail.com
DEFAULT_FROM_EMAIL=KirayaSaathi <gouravberwal003@gmail.com>
BREVO_API_KEY=cM5tXVn5lhBKXX35QhNiaqfWq6ca2f6g9ADD3H7w3irVkQ9qjkyJufhdiRn2twnNI1Og1VemYSUAcm3P
ALLOW_OTP_FALLBACK=True
EOF

mkdir -p /var/www/kirayasaathi/media /var/www/kirayasaathi/static
/var/www/kirayasaathi/venv/bin/python manage.py migrate --noinput
/var/www/kirayasaathi/venv/bin/python manage.py collectstatic --noinput

# 6. Configure Systemd Service for Gunicorn (Runs 24x7)
echo "[6/7] Setting up Gunicorn 24x7 systemd daemon..."
sudo tee /etc/systemd/system/kirayasaathi.service > /dev/null << 'EOF'
[Unit]
Description=KirayaSaathi Gunicorn Application Daemon
After=network.target mysql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/kirayasaathi/backend
EnvironmentFile=/var/www/kirayasaathi/backend/.env
ExecStart=/var/www/kirayasaathi/venv/bin/gunicorn \
    --workers 2 \
    --threads 2 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    config.wsgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo chown -R www-data:www-data /var/www/kirayasaathi
sudo chmod -R 775 /var/www/kirayasaathi/media
sudo systemctl daemon-reload
sudo systemctl enable --now kirayasaathi
sudo systemctl restart kirayasaathi

# 7. Configure Nginx Reverse Proxy
echo "[7/7] Configuring Nginx web server and media storage..."
sudo tee /etc/nginx/sites-available/kirayasaathi > /dev/null << 'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 50M;

    location /static/ {
        alias /var/www/kirayasaathi/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location /media/ {
        alias /var/www/kirayasaathi/media/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
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
EOF

sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/kirayasaathi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

echo "============================================================"
echo "🎉 SUCCESS! KirayaSaathi Backend & MySQL are now LIVE on VM!"
echo "Server IP: $(curl -s ifconfig.me)"
echo "Test URL: http://$(curl -s ifconfig.me)/api/auth/csrf/"
echo "============================================================"
