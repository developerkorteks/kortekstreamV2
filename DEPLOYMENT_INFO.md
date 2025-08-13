# KortekStream Deployment Information

## 🚀 Deployment Status: **READY**

### 📍 Access Information
- **Main Application**: http://localhost:9111
- **Health Check**: http://localhost:9111/health/
- **Database**: PostgreSQL on localhost:5432 (internal)
- **Cache**: Redis on localhost:7363

### 🔧 Configuration Details

#### Ports Used
- **9111**: Django Application (Gunicorn)
- **7363**: Redis Cache Server
- **5432**: PostgreSQL Database (internal only)

#### Services Running
- **Web Container**: Django app with Gunicorn (3 workers)
- **Redis Container**: Redis 7 Alpine with custom port
- **Database Container**: PostgreSQL 14 Alpine

### 🛠 Management Commands

#### Using Docker Compose
```bash
# Start production deployment
docker compose -f docker-compose.prod.yml up -d

# Start development deployment
docker compose up -d

# Stop deployment
docker compose -f docker-compose.prod.yml down

# View logs
docker compose -f docker-compose.prod.yml logs web

# View all container status
docker compose -f docker-compose.prod.yml ps
```

#### Using Management Script
```bash
# Start production
./manage-deployment.sh start

# Start development
./manage-deployment.sh dev

# Stop deployment
./manage-deployment.sh stop

# View status
./manage-deployment.sh status

# View logs
./manage-deployment.sh logs

# Test endpoints
./manage-deployment.sh test

# Backup database
./manage-deployment.sh backup

# Clean up
./manage-deployment.sh clean

# Update deployment
./manage-deployment.sh update

# Show help
./manage-deployment.sh help
```

### 🗄 Environment Configuration

#### Database
- **Type**: PostgreSQL 14
- **Database**: kortekstream
- **User**: postgres
- **Password**: password123 (change in production)

#### Redis
- **Port**: 7363
- **Memory Policy**: allkeys-lru
- **Persistence**: RDB snapshots every 20 seconds if 1+ changes

#### Django
- **Port**: 9111
- **Workers**: 3 Gunicorn workers
- **Debug**: False (production)
- **Static Files**: Collected to `/app/staticfiles`
- **Media Files**: Stored in `/app/media`

### 📊 Health Checks
- **Web**: HTTP GET to `/health/` endpoint
- **Redis**: Redis PING command on port 7363
- **Database**: PostgreSQL connection check

### 🔐 Security Features
- CORS headers configured
- CSP headers enabled
- X-Frame-Options protection
- XSS protection enabled
- Content type sniffing protection

### 📁 Volume Mounts
- **postgres_data**: PostgreSQL data persistence
- **redis_data**: Redis data persistence  
- **media_volume**: User uploaded media files
- **logs_volume**: Application logs

### 🚦 Container Restart Policies
- **Production**: `restart: unless-stopped`
- **Development**: No automatic restart

### 📝 Log Locations
- **Gunicorn Access**: `/app/logs/gunicorn_access.log`
- **Gunicorn Error**: `/app/logs/gunicorn_error.log`
- **Django**: Application logs in container

### ⚡ Performance Optimizations
- Gunicorn with multiple workers
- Redis for caching and sessions
- Static files served efficiently
- Connection pooling enabled
- Request/response compression

---

**Last Updated**: $(date)
**Deployment Method**: Docker Compose
**Environment**: Production Ready