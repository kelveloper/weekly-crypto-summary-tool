#!/bin/bash

# Automated backup script for CoinFolio Analytics
# Add this to your crontab for regular backups
# Example: 0 2 * * * /path/to/your/app/cron_backup.sh

# Set the application directory
APP_DIR="/path/to/your/weekly-crypto-summary-tool"
cd "$APP_DIR"

# Create timestamp for logging
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Log file
LOG_FILE="logs/backup.log"

# Function to log messages
log_message() {
    echo "[$TIMESTAMP] $1" >> "$LOG_FILE"
}

log_message "Starting automated backup..."

# Run the backup
if python3 database_backup.py backup --db-path ./data/crypto.db --backup-dir ./backups; then
    log_message "✅ Backup completed successfully"
else
    log_message "❌ Backup failed"
    exit 1
fi

# Clean up old backups (keep last 30 days)
find ./backups -name "crypto_backup_*.db" -type f -mtime +30 -delete
find ./backups -name "crypto_export_*.json" -type f -mtime +30 -delete

log_message "🧹 Old backups cleaned up"
log_message "Backup process completed"

# Optional: Send backup status to a monitoring service or email
# curl -X POST "your-monitoring-endpoint" -d "Backup completed for CoinFolio Analytics" 