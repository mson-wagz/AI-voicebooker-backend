# Docker Setup Guide for RestoVoice AI Backend

## Overview

This guide covers setting up the RestoVoice AI Backend with Docker, including Vapi AI integration with Eleven Labs voice synthesis and PostgreSQL database.

## Prerequisites

- Docker and Docker Compose installed
- Environment variables configured (see `.env.example`)
- Sufficient system resources (minimum 2GB RAM, 2 CPU cores)

## Environment Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Required environment variables:

```bash
# Database Configuration
POSTGRES_PASSWORD=your_secure_password

# Vapi AI Configuration
VAPI_API_KEY=your_vapi_api_key
VAPI_PHONE_NUMBER_ID=your_vapi_phone_number_id

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_DEPLOYMENT=your_deployment_name
AZURE_RESOURCE_ID=your_azure_resource_id

# Eleven Labs Voice Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key

# Security
SECRET_KEY=your_secret_key_here
```

## Development Setup

### Start Development Environment

```bash
# Build and start all services
docker-compose -f docker-compose.dev.yml up --build

# Run in background
docker-compose -f docker-compose.dev.yml up -d --build
```

### Development Services

- **AI Backend**: `http://localhost:8000`
- **PostgreSQL**: `localhost:5439`
- **API Documentation**: `http://localhost:8000/docs`

### Development Features

- Live code reloading
- Volume mounts for source code
- Detailed logging
- Database persistence

### Stop Development Environment

```bash
docker-compose -f docker-compose.dev.yml down
```

## Production Setup

### Environment Variables for Production

Create a production `.env` file with all required variables:

```bash
# Required for production
POSTGRES_PASSWORD=your_production_password
VAPI_API_KEY=your_production_vapi_key
AZURE_OPENAI_API_KEY=your_production_azure_key
ELEVENLABS_API_KEY=your_production_elevenlabs_key
SECRET_KEY=your_production_secret_key
```

### Start Production Environment

```bash
# Build and start production services
docker-compose -f docker-compose.prod.yml up --build -d

# Check service status
docker-compose -f docker-compose.prod.yml ps
```

### Production Features

- Multi-worker deployment
- Resource limits
- Health checks
- Optimized Docker layers
- No development dependencies

### Stop Production Environment

```bash
docker-compose -f docker-compose.prod.yml down
```

## Service Health Checks

### Check Backend Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "availability": "operational",
    "tools": "operational",
    "vapi_integration": "operational",
    "database": "operational"
  }
}
```

### Check Database Health

```bash
docker-compose exec postgres pg_isready -U postgres
```

## API Endpoints

Once running, the following endpoints are available:

### Core Services
- `GET /` - Service overview
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

### Vapi Integration
- `POST /v1/vapi/calls/initiate` - Initiate outbound calls
- `POST /v1/vapi/assistants/create` - Create AI assistants
- `GET /v1/vapi/voices/elevenlabs` - List available voices
- `POST /v1/vapi/webhooks/vapi` - Handle Vapi webhooks

### Database Operations
- `POST /v1/db/restaurants` - Create restaurants
- `GET /v1/db/restaurants/{id}` - Get restaurant details
- `POST /v1/db/bookings` - Create bookings
- `GET /v1/db/restaurants/{id}/bookings` - Get restaurant bookings

## Monitoring and Logs

### View Logs

```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f ai-backend
docker-compose logs -f postgres
```

### Monitor Resource Usage

```bash
# Check container resource usage
docker stats

# Check disk usage
docker system df
```

## Database Management

### Connect to Database

```bash
# Connect using psql
docker-compose exec postgres psql -U postgres -d restovoice

# Connect using external tool
# Host: localhost
# Port: 5432
# Database: restovoice
# User: postgres
# Password: (from POSTGRES_PASSWORD)
```

### Database Migrations

The application automatically creates tables on startup using SQLAlchemy. For manual migrations:

```bash
# Access the application container
docker-compose exec ai-backend bash

# Run Python commands for database operations
python -c "
from src.core.database.connection import init_db
import asyncio
asyncio.run(init_db())
"
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check what's using port 8000
   netstat -tulpn | grep :8000
   # Stop conflicting services or change port in docker-compose.yml
   ```

2. **Database Connection Issues**
   ```bash
   # Check database logs
   docker-compose logs postgres
   
   # Test database connection
   docker-compose exec postgres psql -U postgres -d restovoice -c "SELECT version();"
   ```

3. **Environment Variable Issues**
   ```bash
   # Verify environment variables are loaded
   docker-compose exec ai-backend env | grep -E "(VAPI|ELEVENLABS|DATABASE)"
   ```

4. **Build Failures**
   ```bash
   # Clean build cache
   docker-compose down
   docker system prune -f
   docker-compose build --no-cache
   ```

### Performance Optimization

1. **Increase Worker Count**
   ```yaml
   # In docker-compose.prod.yml
   command: ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "8"]
   ```

2. **Database Connection Pooling**
   ```yaml
   # Add to environment variables
   - DATABASE_POOL_SIZE=20
   - DATABASE_MAX_OVERFLOW=30
   ```

3. **Resource Limits**
   ```yaml
   # Adjust in docker-compose.prod.yml
   deploy:
     resources:
       limits:
         cpus: '2.0'
         memory: 2G
   ```

## Security Considerations

1. **Use Production Secrets**
   - Never commit actual API keys to version control
   - Use Docker secrets or environment files in production

2. **Network Security**
   - Use HTTPS in production
   - Configure firewall rules
   - Limit database access to application container only

3. **Container Security**
   - Run as non-root user (configured)
   - Use minimal base images
   - Regular security updates

## Scaling

### Horizontal Scaling

```yaml
# In docker-compose.prod.yml
services:
  ai-backend:
    deploy:
      replicas: 3
```

### Load Balancing

Use a reverse proxy (nginx/traefik) in front of multiple instances:

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - ai-backend
```

## Backup and Recovery

### Database Backup

```bash
# Create backup
docker-compose exec postgres pg_dump -U postgres restovoice > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U postgres restovoice < backup.sql
```

### Volume Backup

```bash
# Backup volumes
docker run --rm -v restovoice_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# Restore volumes
docker run --rm -v restovoice_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

## Next Steps

1. **Configure Environment Variables**: Set up all required API keys and secrets
2. **Test Development Setup**: Start with docker-compose.dev.yml
3. **Verify Integration**: Test Vapi and Eleven Labs functionality
4. **Deploy to Production**: Use docker-compose.prod.yml
5. **Set up Monitoring**: Configure logging and monitoring tools
6. **Configure Backups**: Set up automated database backups

## Support

For issues:
1. Check logs: `docker-compose logs`
2. Verify environment variables
3. Test individual services
4. Check network connectivity
5. Review API documentation at `http://localhost:8000/docs`
