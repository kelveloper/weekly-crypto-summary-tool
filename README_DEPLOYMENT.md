# 🚀 CoinFolio Analytics - Database Persistence & Deployment Guide

This guide explains how to ensure your database persists when deploying your crypto portfolio application.

## 📊 Database Persistence Solutions

### Option 1: SQLite with Persistent Storage (Recommended for Small-Medium Apps)

✅ **Pros:**
- Simple setup, no external database server needed
- Perfect for personal use or small teams
- Easy backup and restore
- Low resource usage

❌ **Cons:**
- Not suitable for high-concurrency applications
- Single file can be a limitation for scaling

**Setup:**
```bash
# The app now uses environment variables for database path
export DB_PATH=/data/crypto.db  # Persistent volume mount point
python3 api_app.py
```

### Option 2: PostgreSQL/MySQL (Recommended for Production)

✅ **Pros:**
- Robust, production-ready
- Supports multiple concurrent users
- Better performance for complex queries
- Built-in replication and backup features

❌ **Cons:**
- Requires separate database server
- More complex setup and maintenance

**Setup:**
```bash
# Set environment variable for production database
export DATABASE_URL=postgresql://user:password@host:5432/crypto_db
python3 api_app.py
```

## 🐳 Docker Deployment (Recommended)

### Quick Start
```bash
# 1. Clone and navigate to your project
cd weekly-crypto-summary-tool

# 2. Run the deployment script
./deploy.sh

# 3. Access your application
# Frontend: http://localhost:3000
# API: http://localhost:5001
```

### Manual Docker Deployment
```bash
# 1. Create persistent directories
mkdir -p data backups logs

# 2. Copy environment template
cp .env.example .env
# Edit .env file with your secure keys

# 3. Build and run with Docker Compose
docker-compose up --build -d

# 4. Check status
docker-compose ps
```

## 💾 Database Backup & Restore

### Automated Backups
```bash
# Manual backup
python3 database_backup.py backup

# List all backups
python3 database_backup.py list

# Restore from backup
python3 database_backup.py restore --backup-file backups/crypto_backup_20241226_120000.db
```

### Setup Automated Backups
```bash
# 1. Make scripts executable
chmod +x cron_backup.sh

# 2. Edit the script path
nano cron_backup.sh
# Change APP_DIR to your actual path

# 3. Add to crontab for daily backups at 2 AM
crontab -e
# Add: 0 2 * * * /path/to/your/app/cron_backup.sh
```

## 🌐 Production Deployment Options

### 1. VPS/Cloud Server (DigitalOcean, Linode, AWS EC2)

**Setup Steps:**
```bash
# 1. SSH into your server
ssh user@your-server-ip

# 2. Clone your repository
git clone https://github.com/yourusername/weekly-crypto-summary-tool.git
cd weekly-crypto-summary-tool

# 3. Run deployment script
./deploy.sh

# 4. Configure reverse proxy (nginx)
sudo apt install nginx
# Configure nginx to proxy to your app
```

**Nginx Configuration Example:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. Platform as a Service (Heroku, Railway, Render)

**For Heroku:**
```bash
# 1. Install Heroku CLI
# 2. Create Heroku apps
heroku create your-app-api
heroku create your-app-frontend

# 3. Set environment variables
heroku config:set DATABASE_URL=postgres://... --app your-app-api
heroku config:set SECRET_KEY=your-secret-key --app your-app-api

# 4. Deploy
git push heroku main
```

### 3. Container Platforms (Docker Hub, AWS ECS, Google Cloud Run)

**Deploy to Cloud Run:**
```bash
# 1. Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/crypto-api

# 2. Deploy to Cloud Run
gcloud run deploy --image gcr.io/PROJECT_ID/crypto-api --platform managed
```

## 🗄️ Database Migration

### From Development to Production

**Option A: Backup & Restore (SQLite)**
```bash
# 1. Backup development database
python3 database_backup.py backup --db-path crypto.db

# 2. Copy backup to production server
scp backups/crypto_backup_*.db user@server:/app/data/

# 3. Restore on production
python3 database_backup.py restore --backup-file crypto_backup_*.db --db-path /data/crypto.db
```

**Option B: Export/Import via JSON**
```bash
# 1. Export from development (included in backup script)
python3 database_backup.py backup

# 2. Use the JSON file to import to PostgreSQL/MySQL
# (Custom import script needed for different database types)
```

## 🔒 Security Considerations

### Environment Variables
```bash
# Always use strong, unique keys in production
SECRET_KEY=your-super-secure-32-character-key
JWT_SECRET_KEY=another-super-secure-32-character-key

# Generate secure keys
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### File Permissions
```bash
# Secure your database and config files
chmod 600 .env
chmod 700 data/
chmod 755 backups/
```

### SSL/HTTPS
```bash
# Use Let's Encrypt for free SSL certificates
sudo certbot --nginx -d your-domain.com
```

## 📊 Monitoring & Maintenance

### Health Checks
```bash
# API health check
curl http://localhost:5001/api/health

# Check database size
ls -lah data/crypto.db
```

### Log Management
```bash
# View application logs
docker-compose logs -f api

# Backup logs rotation
logrotate /etc/logrotate.d/crypto-app
```

### Performance Monitoring
```bash
# Monitor resource usage
docker stats

# Database performance
sqlite3 data/crypto.db "PRAGMA optimize;"
```

## 🆘 Troubleshooting

### Common Issues

**Database locked error:**
```bash
# Check for zombie processes
ps aux | grep python
kill -9 <process_id>
```

**Permission denied:**
```bash
# Fix permissions
sudo chown -R $USER:$USER data/
chmod 755 data/
```

**Port already in use:**
```bash
# Find and kill process using port
lsof -i :5001
kill -9 <process_id>
```

### Recovery Procedures

**Corrupted database:**
```bash
# 1. Stop application
docker-compose down

# 2. Restore from latest backup
python3 database_backup.py restore --backup-file backups/crypto_backup_latest.db

# 3. Restart application
docker-compose up -d
```

## 📋 Deployment Checklist

- [ ] Environment variables configured
- [ ] Secure keys generated
- [ ] Database path configured for persistence
- [ ] Backup strategy implemented
- [ ] SSL/HTTPS configured
- [ ] Monitoring setup
- [ ] Regular maintenance scheduled
- [ ] Recovery procedures tested

## 🔗 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Deployment Guide](https://www.postgresql.org/docs/)
- [nginx Configuration](https://nginx.org/en/docs/)
- [Let's Encrypt SSL](https://letsencrypt.org/)

---

💡 **Need Help?** Check the logs first, then review this guide, or open an issue in the repository. 