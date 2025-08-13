#!/bin/bash

# Kortekstream Deployment Management Script

show_help() {
    echo "Kortekstream Deployment Manager"
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start       Start production deployment (with Nginx)"
    echo "  dev         Start development deployment (without Nginx)"
    echo "  stop        Stop all containers"
    echo "  restart     Restart all containers"
    echo "  status      Show container status"
    echo "  logs        Show application logs"
    echo "  backup      Backup database"
    echo "  clean       Clean up old containers and volumes"
    echo "  update      Update and rebuild containers"
    echo "  test        Test application endpoints"
    echo "  help        Show this help message"
}

start_production() {
    echo "🚀 Starting production deployment with Nginx..."
    docker compose -f docker-compose.prod.yml up -d --build
    echo "⏳ Waiting for services to be ready..."
    sleep 30
    check_health
}

start_development() {
    echo "🔧 Starting development deployment..."
    docker compose up -d --build
    echo "⏳ Waiting for services to be ready..."
    sleep 30
    check_health
}

stop_deployment() {
    echo "🛑 Stopping deployment..."
    docker compose -f docker-compose.prod.yml down 2>/dev/null || true
    docker compose down 2>/dev/null || true
    echo "✅ Deployment stopped"
}

restart_deployment() {
    echo "🔄 Restarting deployment..."
    stop_deployment
    start_production
}

show_status() {
    echo "📊 Container Status:"
    docker compose -f docker-compose.prod.yml ps 2>/dev/null || docker compose ps
}

show_logs() {
    echo "📋 Application Logs (last 50 lines):"
    docker compose -f docker-compose.prod.yml logs --tail=50 web 2>/dev/null || docker compose logs --tail=50 web
}

backup_database() {
    echo "💾 Creating database backup..."
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    docker compose -f docker-compose.prod.yml exec -T db pg_dump -U postgres kortekstream > "$BACKUP_FILE" 2>/dev/null || \
    docker compose exec -T db pg_dump -U postgres kortekstream > "$BACKUP_FILE"
    echo "✅ Database backup created: $BACKUP_FILE"
}

clean_deployment() {
    echo "🧹 Cleaning up old containers and volumes..."
    stop_deployment
    docker system prune -f
    echo "✅ Cleanup completed"
}

update_deployment() {
    echo "📦 Updating deployment..."
    stop_deployment
    docker compose -f docker-compose.prod.yml build --no-cache
    start_production
}

test_endpoints() {
    echo "🧪 Testing application endpoints..."
    
    # Test port 9111 only
    if curl -f -s http://localhost:9111/health/ > /dev/null 2>&1; then
        echo "✅ Application HTTP (port 9111): OK"
    else
        echo "❌ Application HTTP (port 9111): FAILED"
    fi
    
    # Test Redis port 7363
    if nc -z localhost 7363 2>/dev/null; then
        echo "✅ Redis (port 7363): OK"
    else
        echo "❌ Redis (port 7363): FAILED"
    fi
}

check_health() {
    echo "🔍 Checking application health..."
    show_status
    echo ""
    test_endpoints
    echo ""
    echo "🌐 Access URLs:"
    echo "   - Application: http://localhost:9111"
    echo "   - Health Check: http://localhost:9111/health/"
    echo "   - Redis: localhost:7363"
}

case "$1" in
    start)
        start_production
        ;;
    dev)
        start_development
        ;;
    stop)
        stop_deployment
        ;;
    restart)
        restart_deployment
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    backup)
        backup_database
        ;;
    clean)
        clean_deployment
        ;;
    update)
        update_deployment
        ;;
    test)
        test_endpoints
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac