# RestoVoice Admin Backend API Test Script (PowerShell) - Fixed Version
# Tests all admin endpoints with curl commands

param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$RestaurantId = "test-restaurant-1",
    [switch]$Help
)

# Show help
if ($Help) {
    Write-Host @"
RestoVoice Admin Backend API Test Script (PowerShell)

Usage: .\test_admin_api_fixed.ps1 [OPTIONS]

Options:
  -Help                   Show this help message
  -BaseUrl URL            Base URL (default: http://localhost:8000)
  -RestaurantId ID        Restaurant ID (default: test-restaurant-1)

Examples:
  .\test_admin_api_fixed.ps1                                    # Use defaults
  .\test_admin_api_fixed.ps1 -BaseUrl "http://localhost:3000"   # Different port
  .\test_admin_api_fixed.ps1 -RestaurantId "my-restaurant-123"  # Specific restaurant
  .\test_admin_api_fixed.ps1 -BaseUrl "https://api.restovoice.com"  # Production API

Environment Variables:
  BASE_URL        Base URL for the API
  RESTAURANT_ID   Restaurant ID to test with
"@
    exit 0
}

# Configuration
$ApiBase = "$BaseUrl/admin"

# Helper functions
function Write-Header {
    param([string]$Title)
    Write-Host "`n=====================================" -ForegroundColor Blue
    Write-Host $Title -ForegroundColor Blue
    Write-Host "=====================================" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Yellow
}

# Test endpoint function
function Test-Endpoint {
    param(
        [string]$Method,
        [string]$Endpoint,
        [string]$Data,
        [string]$Description,
        [int]$ExpectedStatus = 200
    )
    
    Write-Header $Description
    Write-Host "Method: $Method"
    Write-Host "URL: $ApiBase$Endpoint"
    if ($Data) {
        Write-Host "Data: $Data"
    }
    Write-Host "Expected Status: $ExpectedStatus"
    Write-Host ""
    
    try {
        # Build curl command - escape URLs properly
        $fullUrl = "$ApiBase$Endpoint"
        $curlCmd = @(
            "curl", "-s", "-w", "`nHTTP_STATUS:%%{http_code}", "-X", $Method
        )
        
        if ($Data) {
            $curlCmd += @("-H", "Content-Type: application/json", "-d", $Data)
        }
        
        $curlCmd += $fullUrl
        
        # Execute and capture response
        $response = & $curlCmd 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "curl command failed"
        }
        
        # Parse response
        $lines = $response -split "`n"
        $statusLine = $lines | Where-Object { $_ -match "HTTP_STATUS:" }
        $status = [int]($statusLine -replace "HTTP_STATUS:", "")
        $body = $lines -join "`n" -replace "HTTP_STATUS:.*$", ""
        
        # Check status
        if ($status -eq $ExpectedStatus) {
            Write-Success "Status: $status (Expected: $ExpectedStatus)"
            Write-Host "Response:"
            
            # Try to format JSON if available
            try {
                $body | ConvertFrom-Json | ConvertTo-Json -Depth 10
            } catch {
                $body
            }
        } else {
            Write-Error "Status: $status (Expected: $ExpectedStatus)"
            Write-Host "Response:"
            $body
            return $false
        }
    } catch {
        Write-Error "Request failed: $($_.Exception.Message)"
        return $false
    }
    
    return $true
}

# Check if server is running
function Test-Server {
    Write-Header "Checking Server Connection"
    try {
        $response = curl -s "$BaseUrl/health" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Server is running at $BaseUrl"
            return $true
        }
    } catch {
        # Continue to error message
    }
    
    Write-Error "Server is not running at $BaseUrl"
    Write-Host "Please start the server first:"
    Write-Host "python -m uvicorn src.main:app --host 0.0.0.0 --port 8000"
    return $false
}

# Main test execution
function Main {
    Write-Header "RestoVoice Admin Backend API Tests"
    Write-Host "Base URL: $BaseUrl"
    Write-Host "Restaurant ID: $RestaurantId"
    Write-Host "API Base: $ApiBase"
    
    # Check server
    if (-not (Test-Server)) {
        exit 1
    }
    
    $testResults = @()
    
    # Test 1: Admin Health Check
    $result = Test-Endpoint "GET" "/health" "" "Admin Health Check" 200
    $testResults += @{ Test = "Admin Health Check"; Passed = $result }
    
    # Test 2: Get Dashboard Stats
    $result = Test-Endpoint "GET" "/dashboard/stats/$RestaurantId" "" "Get Dashboard Statistics" 200
    $testResults += @{ Test = "Dashboard Statistics"; Passed = $result }
    
    # Test 3: Get Policy (should create default if not exists)
    $result = Test-Endpoint "GET" "/policies/$RestaurantId" "" "Get Restaurant Policy" 200
    $testResults += @{ Test = "Get Policy"; Passed = $result }
    
    # Test 4: Create Policy
    $policyData = @{
        deposit_required = $true
        deposit_amount = 500
        max_party_size = 12
        opening_hours = @(
            @{ day_of_week = 0; open_time = "09:00"; close_time = "22:00"; is_closed = $true }
            @{ day_of_week = 1; open_time = "09:00"; close_time = "22:00"; is_closed = $false }
            @{ day_of_week = 2; open_time = "09:00"; close_time = "22:00"; is_closed = $false }
            @{ day_of_week = 3; open_time = "09:00"; close_time = "22:00"; is_closed = $false }
            @{ day_of_week = 4; open_time = "09:00"; close_time = "22:00"; is_closed = $false }
            @{ day_of_week = 5; open_time = "09:00"; close_time = "23:00"; is_closed = $false }
            @{ day_of_week = 6; open_time = "09:00"; close_time = "23:00"; is_closed = $false }
        )
        deposit_rules = @(
            @{ day_of_week = 5; min_party = 6; start_time = "18:00"; end_time = "22:00" }
            @{ day_of_week = 6; min_party = 8; start_time = "17:00"; end_time = "21:00" }
        )
    } | ConvertTo-Json -Depth 10
    
    $result = Test-Endpoint "POST" "/policies/$RestaurantId" $policyData "Create/Update Policy" 200
    $testResults += @{ Test = "Create Policy"; Passed = $result }
    
    # Test 5: Update Policy (partial update)
    $updateData = @{
        deposit_required = $false
        max_party_size = 15
    } | ConvertTo-Json
    
    $result = Test-Endpoint "PUT" "/policies/$RestaurantId" $updateData "Update Policy (Partial)" 200
    $testResults += @{ Test = "Update Policy"; Passed = $result }
    
    # Test 6: Get Call Logs - Fix URL encoding
    $callEndpoint = "/calls/$RestaurantId?limit=5&offset=0"
    $result = Test-Endpoint "GET" $callEndpoint "" "Get Call Logs (Pagination)" 200
    $testResults += @{ Test = "Call Logs"; Passed = $result }
    
    # Test 7: Get Call Logs with different pagination
    $callEndpoint2 = "/calls/$RestaurantId?limit=10&offset=5"
    $result = Test-Endpoint "GET" $callEndpoint2 "" "Get Call Logs (Different Page)" 200
    $testResults += @{ Test = "Call Logs (Page 2)"; Passed = $result }
    
    # Test 8: Get Booking Logs
    $bookingEndpoint = "/bookings/$RestaurantId?limit=5&offset=0"
    $result = Test-Endpoint "GET" $bookingEndpoint "" "Get Booking Logs" 200
    $testResults += @{ Test = "Booking Logs"; Passed = $result }
    
    # Test 9: Get Booking Logs with Status Filter
    $bookingEndpoint2 = "/bookings/$RestaurantId?status=CONFIRMED&limit=5&offset=0"
    $result = Test-Endpoint "GET" $bookingEndpoint2 "" "Get Booking Logs (Status Filter)" 200
    $testResults += @{ Test = "Booking Logs (Confirmed)"; Passed = $result }
    
    # Test 10: Get Booking Logs with Failed Status
    $bookingEndpoint3 = "/bookings/$RestaurantId?status=FAILED&limit=5&offset=0"
    $result = Test-Endpoint "GET" $bookingEndpoint3 "" "Get Booking Logs (Failed Status)" 200
    $testResults += @{ Test = "Booking Logs (Failed)"; Passed = $result }
    
    # Test 11: Error Cases - Non-existent Restaurant
    $result = Test-Endpoint "GET" "/dashboard/stats/non-existent-restaurant" "" "Get Dashboard Stats (Non-existent Restaurant)" 404
    $testResults += @{ Test = "Error - Non-existent Restaurant"; Passed = $result }
    
    # Test 12: Error Cases - Invalid Policy Data
    $invalidPolicy = @{
        deposit_required = "not_boolean"
        max_party_size = -5
        opening_hours = "not_array"
    } | ConvertTo-Json
    
    $result = Test-Endpoint "POST" "/policies/$RestaurantId" $invalidPolicy "Create Policy (Invalid Data)" 422
    $testResults += @{ Test = "Error - Invalid Policy Data"; Passed = $result }
    
    # Test 13: Error Cases - Limit Too High
    $limitEndpoint = "/calls/$RestaurantId?limit=150"
    $result = Test-Endpoint "GET" $limitEndpoint "" "Get Call Logs (Limit Too High)" 422
    $testResults += @{ Test = "Error - Limit Too High"; Passed = $result }
    
    # Test 14: Error Cases - Negative Offset
    $offsetEndpoint = "/bookings/$RestaurantId?offset=-5"
    $result = Test-Endpoint "GET" $offsetEndpoint "" "Get Booking Logs (Negative Offset)" 422
    $testResults += @{ Test = "Error - Negative Offset"; Passed = $result }
    
    # Test 15: Error Cases - Wrong HTTP Method
    $result = Test-Endpoint "POST" "/calls/$RestaurantId" "" "Wrong HTTP Method" 405
    $testResults += @{ Test = "Error - Wrong HTTP Method"; Passed = $result }
    
    # Summary
    Write-Header "Test Summary"
    
    $passedCount = ($testResults | Where-Object { $_.Passed -eq $true }).Count
    $totalCount = $testResults.Count
    
    Write-Host "Tests Passed: $passedCount/$totalCount" -ForegroundColor $(if ($passedCount -eq $totalCount) { "Green" } else { "Yellow" })
    
    Write-Host "`nTest Results:"
    foreach ($test in $testResults) {
        $status = if ($test.Passed) { "✅" } else { "❌" }
        Write-Host "$status $($test.Test)" -ForegroundColor $(if ($test.Passed) { "Green" } else { "Red" })
    }
    
    if ($passedCount -eq $totalCount) {
        Write-Success "All admin endpoint tests passed!"
    } else {
        Write-Error "Some tests failed. Check the responses above."
    }
    
    Write-Info "Check the responses above to verify functionality"
    
    Write-Host "`nQuick Reference:" -ForegroundColor Blue
    Write-Host "- Dashboard Stats: GET $ApiBase/dashboard/stats/$RestaurantId"
    Write-Host "- Policy Management: GET/POST/PUT $ApiBase/policies/$RestaurantId"
    Write-Host "- Call Logs: GET $ApiBase/calls/$RestaurantId"
    Write-Host "- Booking Logs: GET $ApiBase/bookings/$RestaurantId"
    Write-Host "- Health Check: GET $ApiBase/health"
}

# Check dependencies
try {
    $null = Get-Command curl -ErrorAction Stop
} catch {
    Write-Error "curl is required but not available"
    exit 1
}

# Run main function
Main
