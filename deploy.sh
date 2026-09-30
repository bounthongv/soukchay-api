#!/bin/bash

# Soukchay API Deployment Script
# Uploads and deploys the API to apis.com.la

set -e

# Configuration
API_DIR="/home/apis/soukchay_api"
SERVICE_FILE="/etc/systemd/system/soukchay-api.service"
VHOST_FILE="/etc/apache2/sites-available/soukchay-api.conf"

echo "🚀 Starting Soukchay API deployment..."

# Create tar package
echo "📦 Creating tar package..."
cd api
tar -czf ../soukchay_api.tar.gz .
cd ..

# Upload to server
echo "📤 Uploading to apis.com.la..."
ssh apis@apis.com.la "mkdir -p $API_DIR"
scp soukchay_api.tar.gz apis@apis.com.la:$API_DIR/
ssh apis@apis.com.la "cd $API_DIR && tar -xzf soukchay_api.tar.gz && rm soukchay_api.tar.gz"

# Install dependencies
echo "📦 Installing dependencies..."
ssh apis@apis.com.la "cd $API_DIR && python3 -m pip install -r requirements.txt"

# Create systemd service
echo "🔧 Creating systemd service..."
ssh apis@apis.com.la "cat > $SERVICE_FILE << 'EOF'
[Unit]
Description=Soukchay API
After=network.target

[Service]
Type=simple
User=apis
WorkingDirectory=$API_DIR
Environment=PATH=$API_DIR/venv/bin
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 127.0.0.1 --port 5005 --reload
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF"

# Enable and start service
echo "🚀 Starting service..."
ssh apis@apis.com.la "sudo systemctl daemon-reload && sudo systemctl enable soukchay-api && sudo systemctl start soukchay-api"

# Create Apache vhost
echo "🌐 Creating Apache vhost..."
ssh apis@apis.com.la "cat > $VHOST_FILE << 'EOF'
<VirtualHost *:80>
    ServerName soukchay-api.apis.com.la
    ProxyPass / http://127.0.0.1:5005/
    ProxyPassReverse / http://127.0.0.1:5005/
    ErrorLog \${APACHE_LOG_DIR}/soukchay-api_error.log
    CustomLog \${APACHE_LOG_DIR}/soukchay-api_access.log combined
</VirtualHost>
EOF"

# Enable vhost
echo "🌐 Enabling vhost..."
ssh apis@apis.com.la "sudo a2ensite soukchay-api && sudo systemctl reload apache2"

# Add DNS record
echo "🌐 Adding DNS record..."
echo "Please add the following DNS record manually:"
echo "  Name: soukchay-api"
echo "  Type: A"
echo "  Value: 202.137.147.5"
echo "  Zone: apis.com.la"

# Get SSL certificate
echo "🔒 Getting SSL certificate..."
ssh apis@apis.com.la "sudo certbot --apache -d soukchay-api.apis.com.la -n --agree-tos --email admin@apis.com.la"

# Check service status
echo "✅ Checking service status..."
ssh apis@apis@apis.com.la "sudo systemctl status soukchay-api"

echo "🎉 Deployment complete!"
echo "🌐 Visit: https://soukchay-api.apis.com.la"
echo "📖 Docs: https://soukchay-api.apis.com.la/docs"