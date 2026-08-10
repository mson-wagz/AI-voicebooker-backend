@echo off
setlocal enabledelayedexpansion

REM RestoVoice Admin Backend API Test Script (Batch)
REM Tests all admin endpoints with curl commands

set BASE_URL=%BASE_URL%
if "%BASE_URL%"=="" set BASE_URL=http://localhost:8000
set RESTAURANT_ID=%RESTAURANT_ID%
if "%RESTAURANT_ID%"=="" set RESTAURANT_ID=test-restaurant-1
set API_BASE=%BASE_URL%/admin

echo =====================================
echo RestoVoice Admin Backend API Tests
echo =====================================
echo Base URL: %BASE_URL%
echo Restaurant ID: %RESTAURANT_ID%
echo API Base: %API_BASE%
echo.

REM Check if curl is available
curl --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: curl is required but not available
    exit /b 1
)

REM Check if server is running
echo Checking Server Connection...
curl -s "%BASE_URL%/health" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Server is not running at %BASE_URL%
    echo Please start the server first:
    echo python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
    exit /b 1
)
echo SUCCESS: Server is running at %BASE_URL%
echo.

REM Test 1: Admin Health Check
echo Test 1: Admin Health Check
echo Method: GET
echo URL: %API_BASE%/health
echo Expected Status: 200
curl -s -w "HTTP_STATUS:%%{http_code}" -X GET "%API_BASE%/health"
echo.
echo.

REM Test 2: Get Dashboard Stats
echo Test 2: Get Dashboard Statistics
echo Method: GET
echo URL: %API_BASE%/dashboard/stats/%RESTAURANT_ID%
echo Expected Status: 200
curl -s -w "HTTP_STATUS:%%{http_code}" -X GET "%API_BASE%/dashboard/stats/%RESTAURANT_ID%"
echo.
echo.

REM Test 3: Get Policy
echo Test 3: Get Restaurant Policy
echo Method: GET
echo URL: %API_BASE%/policies/%RESTAURANT_ID%
echo Expected Status: 200
curl -s -w "HTTP_STATUS:%%{http_code}" -X GET "%API_BASE%/policies/%RESTAURANT_ID%"
echo.
echo.

REM Test 4: Create Policy
echo Test 4: Create/Update Policy
echo Method: POST
echo URL: %API_BASE%/policies/%RESTAURANT_ID%
echo Expected Status: 200
set "policy_data={\"deposit_required\":true,\"deposit_amount\":500,\"max_party_size\":12,\"opening_hours\":[{\"day_of_week\":0,\"open_time\":\"09:00\",\"close_time\":\"22:00\",\"is_closed\":true},{\"day_of_week\":1,\"open_time\":\"09:00\",\"close_time\":\"22:00\",\"is_closed\":false},{\"day_of_week\":2,\"open_time\":\"09:00\",\"close_time\":\"22:00\",\"is_closed\":false},{\"day_of_week\":3,\"open_time\":\"09:00\",\"close_time\":\"22:00\",\"is_closed\":false},{\"day_of_week\":4,\"open_time\":\"09:00\",\"close_time\":\"22:00\",\"is_closed\":false},{\"day_of_week\":5,\"open_time\":\"09:00\",\"close_time\":\"23:00\",\"is_closed\":false},{\"day_of_week\":6,\"open_time\":\"09:00\",\"close_time\":\"23:00\",\"is_closed\":false}],\"deposit_rules\":[{\"day_of_week\":5,\"min_party\":6,\"start_time\":\"18:00\",\"end_time\":\"22:00\"},{\"day_of_week\":6,\"min_party\":8,\"start_time\":\"17:00\",\"end_time\":\"21:00\"}]}"
curl -s -w "HTTP_STATUS:%%{http_code}" -X POST -H "Content-Type: application/json" -d "!policy_data!" "%API_BASE%/policies/%RESTAURANT_ID%"
echo.
echo.

REM Test 5: Update Policy
echo Test 5: Update Policy (Partial)
echo Method: PUT
echo URL: %API_BASE%/policies/%RESTAURANT_ID%
echo Expected Status: 200
set "update_data={\"deposit_required\":false,\"max_party_size\":15}"
curl -s -w "HTTP_STATUS:%%{http_code}" -X PUT -H "Content-Type: application/json" -d "!update_data!" "%API_BASE%/policies/%RESTAURANT_ID%"
echo.
echo.

REM Test 6: Get Call Logs
echo Test 6: Get Call Logs (Pagination)
echo Method: GET
echo URL: %API_BASE%/calls/%RESTAURANT_ID%?limit=5&offset=0
echo Expected Status: 200
curl -s -w "HTTP_STATUS:%%{http_code}" -X GET "%API_BASE%/calls/%RESTAURANT_ID%?limit=5&offset=0"
echo.
echo.

REM Test 7: Get Booking Logs
echo Test 7: Get Booking Logs
echo Method: GET
echo URL: %API_BASE%/bookings/%RESTAURANT_ID%?limit=5&offset=0
echo Expected Status: 200
curl -s -w "HTTP_STATUS:%%{http_code}" -X GET "%API_BASE%/bookings/%RESTAURANT_ID%?limit=5&offset=0"
echo.
echo.

REM Test 8: Get Booking Logs with Status Filter
echo Test 8: Get Booking Logs (Status Filter)
echo Method: GET
echo URL: %API_BASE%/bookings/%RESTAURANT_ID%?status=CONFIRMED&limit=5&offset=0
echo Expected Status: 200
curl -s -w "HTTP_STATUS:%%{http_code}" -X GET "%API_BASE%/bookings/%RESTAURANT_ID%?status=CONFIRMED&limit=5&offset=0"
echo.
echo.

REM Test 9: Error Case - Non-existent Restaurant
echo Test 9: Error Case - Non-existent Restaurant
echo Method: GET
echo URL: %API_BASE%/dashboard/stats/non-existent-restaurant
echo Expected Status: 404
curl -s -w "HTTP_STATUS:%%{http_code}" -X GET "%API_BASE%/dashboard/stats/non-existent-restaurant"
echo.
echo.

REM Test 10: Error Case - Limit Too High
echo Test 10: Error Case - Limit Too High
echo Method: GET
echo URL: %API_BASE%/calls/%RESTAURANT_ID%?limit=150
echo Expected Status: 422
curl -s -w "HTTP_STATUS:%%{http_code}" -X GET "%API_BASE%/calls/%RESTAURANT_ID%?limit=150"
echo.
echo.

echo =====================================
echo Test Summary
echo =====================================
echo All admin endpoint tests completed!
echo Check the responses above to verify functionality
echo Any errors indicate issues that need to be addressed
echo.
echo Quick Reference:
echo - Dashboard Stats: GET %API_BASE%/dashboard/stats/%RESTAURANT_ID%
echo - Policy Management: GET/POST/PUT %API_BASE%/policies/%RESTAURANT_ID%
echo - Call Logs: GET %API_BASE%/calls/%RESTAURANT_ID%
echo - Booking Logs: GET %API_BASE%/bookings/%RESTAURANT_ID%
echo - Health Check: GET %API_BASE%/health
echo.

pause
