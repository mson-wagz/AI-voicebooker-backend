@echo off
REM RestoVoice AI Backend Docker Quick Start Script for Windows

echo 🚀 Starting RestoVoice AI Backend with Docker...

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.example .env >nul
    echo ⚠️  Please edit .env file with your actual API keys before running the services.
    echo    Required variables:
    echo    - VAPI_API_KEY
    echo    - AZURE_OPENAI_API_KEY
    echo    - ELEVENLABS_API_KEY
    echo.
    pause
)

REM Choose environment
echo 🌍 Choose environment:
echo 1) Development ^(with live reload^)
echo 2) Production ^(optimized^)
set /p choice="Enter choice (1 or 2): "

if "%choice%"=="1" (
    set COMPOSE_FILE=docker-compose.dev.yml
    echo 🔧 Starting development environment...
) else if "%choice%"=="2" (
    set COMPOSE_FILE=docker-compose.prod.yml
    echo 🚀 Starting production environment...
) else (
    echo ❌ Invalid choice. Defaulting to development.
    set COMPOSE_FILE=docker-compose.dev.yml
)

REM Build and start services
echo 🏗️  Building Docker images...
docker-compose -f %COMPOSE_FILE% build

echo 🚀 Starting services...
docker-compose -f %COMPOSE_FILE% up -d

REM Wait for services to be ready
echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Check service health
echo 🔍 Checking service health...

REM Check backend health
curl -f http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ AI Backend is healthy
) else (
    echo ⚠️  AI Backend might still be starting...
)

REM Check database health
docker-compose -f %COMPOSE_FILE% exec -T postgres pg_isready -U postgres >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ PostgreSQL is healthy
) else (
    echo ⚠️  PostgreSQL might still be starting...
)

echo.
echo 🎉 RestoVoice AI Backend is starting up!
echo.
echo 📍 Available endpoints:
echo    - API: http://localhost:8000
echo    - Health: http://localhost:8000/health
echo    - Documentation: http://localhost:8000/docs
echo    - Database: localhost:5439
echo.
echo 📋 Useful commands:
echo    - View logs: docker-compose -f %COMPOSE_FILE% logs -f
echo    - Stop services: docker-compose -f %COMPOSE_FILE% down
echo    - Restart services: docker-compose -f %COMPOSE_FILE% restart
echo.
echo 🔧 To test the integration:
echo    curl http://localhost:8000/v1/vapi/voices/elevenlabs
echo.
echo 📖 For more information, see DOCKER_SETUP.md
pause
