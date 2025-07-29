#!/usr/bin/env python3
"""
Database backup and restore utility for CoinFolio Analytics
"""

import os
import shutil
import sqlite3
import argparse
from datetime import datetime
import json

def backup_sqlite_database(db_path, backup_dir):
    """Create a backup of SQLite database"""
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False
    
    # Create backup directory if it doesn't exist
    os.makedirs(backup_dir, exist_ok=True)
    
    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"crypto_backup_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        # Copy the database file
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up successfully to: {backup_path}")
        
        # Also create a JSON export for portability
        export_to_json(db_path, backup_dir, timestamp)
        
        return backup_path
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False

def export_to_json(db_path, backup_dir, timestamp):
    """Export database to JSON format"""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        cursor = conn.cursor()
        
        # Export all tables
        export_data = {}
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            export_data[table] = [dict(row) for row in rows]
        
        # Save to JSON file
        json_filename = f"crypto_export_{timestamp}.json"
        json_path = os.path.join(backup_dir, json_filename)
        
        with open(json_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"✅ Data exported to JSON: {json_path}")
        conn.close()
        
    except Exception as e:
        print(f"❌ JSON export failed: {e}")

def restore_database(backup_path, target_path):
    """Restore database from backup"""
    if not os.path.exists(backup_path):
        print(f"Backup file not found: {backup_path}")
        return False
    
    try:
        # Create target directory if it doesn't exist
        target_dir = os.path.dirname(target_path)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)
        
        # Copy backup to target location
        shutil.copy2(backup_path, target_path)
        print(f"✅ Database restored successfully to: {target_path}")
        return True
        
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return False

def list_backups(backup_dir):
    """List all available backups"""
    if not os.path.exists(backup_dir):
        print(f"Backup directory not found: {backup_dir}")
        return
    
    backups = []
    for file in os.listdir(backup_dir):
        if file.startswith('crypto_backup_') and file.endswith('.db'):
            file_path = os.path.join(backup_dir, file)
            size = os.path.getsize(file_path)
            mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            backups.append((file, size, mtime))
    
    if not backups:
        print("No backups found.")
        return
    
    print("\n📋 Available Backups:")
    print("-" * 60)
    for filename, size, mtime in sorted(backups, key=lambda x: x[2], reverse=True):
        size_mb = size / (1024 * 1024)
        print(f"{filename:<30} {size_mb:>8.2f} MB  {mtime.strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    parser = argparse.ArgumentParser(description='Database backup and restore utility')
    parser.add_argument('action', choices=['backup', 'restore', 'list'], 
                       help='Action to perform')
    parser.add_argument('--db-path', default='./data/crypto.db',
                       help='Path to database file')
    parser.add_argument('--backup-dir', default='./backups',
                       help='Directory to store backups')
    parser.add_argument('--backup-file', 
                       help='Specific backup file to restore from')
    
    args = parser.parse_args()
    
    if args.action == 'backup':
        backup_sqlite_database(args.db_path, args.backup_dir)
    
    elif args.action == 'restore':
        if not args.backup_file:
            print("❌ Please specify --backup-file for restore operation")
            return
        restore_database(args.backup_file, args.db_path)
    
    elif args.action == 'list':
        list_backups(args.backup_dir)

if __name__ == '__main__':
    main() 