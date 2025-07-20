#!/bin/bash

# CockroachDB Operations Script for Trip Planner

CONTAINER_NAME="trip-planner-cockroachdb"

function check_container() {
    if ! docker ps | grep -q $CONTAINER_NAME; then
        echo "Error: CockroachDB container is not running"
        echo "Start it with: docker-compose up -d cockroachdb"
        exit 1
    fi
}

function db_connect() {
    echo "Connecting to CockroachDB..."
    docker exec -it $CONTAINER_NAME ./cockroach sql --insecure
}

function db_status() {
    echo "Checking CockroachDB status..."
    docker exec $CONTAINER_NAME ./cockroach node status --insecure
}

function db_create_database() {
    echo "Creating trip_planner database..."
    docker exec $CONTAINER_NAME ./cockroach sql --insecure --execute="CREATE DATABASE IF NOT EXISTS trip_planner;"
    echo "Database created successfully"
}

function db_backup() {
    BACKUP_DIR="./backups"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    
    echo "Creating backup directory..."
    mkdir -p $BACKUP_DIR
    
    echo "Backing up trip_planner database..."
    docker exec $CONTAINER_NAME ./cockroach sql --insecure --execute="BACKUP DATABASE trip_planner TO 'nodelocal://1/backup_$TIMESTAMP';"
    
    # Copy backup from container
    docker cp $CONTAINER_NAME:/cockroach/cockroach-data/extern/backup_$TIMESTAMP $BACKUP_DIR/
    echo "Backup completed: $BACKUP_DIR/backup_$TIMESTAMP"
}

function db_restore() {
    if [ -z "$1" ]; then
        echo "Usage: $0 restore <backup_timestamp>"
        echo "Available backups:"
        ls -la ./backups/ 2>/dev/null || echo "No backups found"
        exit 1
    fi
    
    BACKUP_TIMESTAMP=$1
    BACKUP_PATH="./backups/backup_$BACKUP_TIMESTAMP"
    
    if [ ! -d "$BACKUP_PATH" ]; then
        echo "Error: Backup not found: $BACKUP_PATH"
        exit 1
    fi
    
    echo "Restoring from backup: $BACKUP_TIMESTAMP"
    
    # Copy backup to container
    docker cp $BACKUP_PATH $CONTAINER_NAME:/cockroach/cockroach-data/extern/
    
    # Restore database
    docker exec $CONTAINER_NAME ./cockroach sql --insecure --execute="DROP DATABASE IF EXISTS trip_planner CASCADE;"
    docker exec $CONTAINER_NAME ./cockroach sql --insecure --execute="RESTORE DATABASE trip_planner FROM 'nodelocal://1/backup_$BACKUP_TIMESTAMP';"
    
    echo "Restore completed"
}

function show_help() {
    echo "CockroachDB Operations for Trip Planner"
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  connect     - Connect to CockroachDB CLI"
    echo "  status      - Show cluster status"
    echo "  create-db   - Create trip_planner database"
    echo "  backup      - Create a backup of the database"
    echo "  restore     - Restore from a backup (requires timestamp)"
    echo "  help        - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 connect"
    echo "  $0 backup"
    echo "  $0 restore 20241201_143022"
}

# Main script logic
case "$1" in
    connect)
        check_container
        db_connect
        ;;
    status)
        check_container
        db_status
        ;;
    create-db)
        check_container
        db_create_database
        ;;
    backup)
        check_container
        db_backup
        ;;
    restore)
        check_container
        db_restore $2
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Error: Unknown command '$1'"
        echo ""
        show_help
        exit 1
        ;;
esac 