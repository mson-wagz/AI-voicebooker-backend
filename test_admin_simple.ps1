# Simple Admin API Test Script - PowerShell Version
# Avoids ampersand issues by using simpler approach

param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$RestaurantId = "test-restaurant-1"
)

$ApiBase = "$BaseUrl/admin"

Write-Host "=====================================" -ForegroundColor Blue
Write-Host "RestoVoice Admin Backend API Tests" -ForegroundColor Blue  
Write-Host "=====================================" -ForegroundColor Blue
Write-Host "Base URL: $BaseUrl"
Write-Host "Restaurant ID: $RestaurantId"
Write-Host ""

# Test 1: Health Check
Write-Host "Test 1: Admin Health Check" -ForegroundColor Yellow
curl -s -w "Status: %{http_code}`n" -X GET "$ApiBase/health"
Write-Host ""

# Test 2: Dashboard Stats  
Write-Host "Test 2: Dashboard Statistics" -ForegroundColor Yellow
curl -s -w "Status: %{http_code}`n" -X GET "$ApiBase/dashboard/stats/$RestaurantId"
Write-Host ""

# Test 3: Get Policy
Write-Host "Test 3: Get Restaurant Policy" -ForegroundColor Yellow
curl -s -w "Status: %{http_code}`n" -X GET "$ApiBase/policies/$RestaurantId"
Write-Host ""

# Test 4: Create Policy
Write-Host "Test 4: Create Policy" -ForegroundColor Yellow
$policyData = '{"deposit_required":true,"deposit_amount":500,"max_party_size":12,"opening_hours":[{"day_of_week":0,"open_time":"09:00","close_time":"22:00","is_closed":true},{"day_of_week":1,"open_time":"09:00","close_time":"22:00","is_closed":false}],"deposit_rules":[{"day_of_week":5,"min_party":6,"start_time":"18:00","end_time":"22:00"}]}'
curl -s -w "Status: %{http_code}`n" -X POST -H "Content-Type: application/json" -d "$policyData" "$ApiBase/policies/$RestaurantId"
Write-Host ""

# Test 5: Update Policy
Write-Host "Test 5: Update Policy" -ForegroundColor Yellow
$updateData = '{"deposit_required":false,"max_party_size":15}'
curl -s -w "Status: %{http_code}`n" -X PUT -H "Content-Type: application/json" -d "$updateData" "$ApiBase/policies/$RestaurantId"
Write-Host ""

# Test 6: Call Logs (simple URL without query params)
Write-Host "Test 6: Call Logs" -ForegroundColor Yellow
curl -s -w "Status: %{http_code}`n" -X GET "$ApiBase/calls/$RestaurantId"
Write-Host ""

# Test 7: Booking Logs (simple URL without query params)
Write-Host "Test 7: Booking Logs" -ForegroundColor Yellow
curl -s -w "Status: %{http_code}`n" -X GET "$ApiBase/bookings/$RestaurantId"
Write-Host ""

# Test 8: Error Case - Non-existent Restaurant
Write-Host "Test 8: Error Case - Non-existent Restaurant" -ForegroundColor Yellow
curl -s -w "Status: %{http_code}`n" -X GET "$ApiBase/dashboard/stats/non-existent-restaurant"
Write-Host ""

Write-Host "=====================================" -ForegroundColor Blue
Write-Host "Tests Completed!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Blue
Write-Host "Quick Reference:" -ForegroundColor Blue
Write-Host "- Dashboard Stats: GET $ApiBase/dashboard/stats/$RestaurantId"
Write-Host "- Policy Management: GET/POST/PUT $ApiBase/policies/$RestaurantId"  
Write-Host "- Call Logs: GET $ApiBase/calls/$RestaurantId"
Write-Host "- Booking Logs: GET $ApiBase/bookings/$RestaurantId"
Write-Host "- Health Check: GET $ApiBase/health"
Write-Host ""
