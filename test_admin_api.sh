#!/bin/bash

# RestoVoice Admin Backend API Test Script
# Tests all admin endpoints with curl commands

set -e  # Exit on any error

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
RESTAURANT_ID="${RESTAURANT_ID:-test-restaurant-1}"
API_BASE="${BASE_URL}/admin"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}=====================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=====================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    local expected_status=${5:-200}
    
    print_header "$description"
    echo "Method: $method"
    echo "URL: ${API_BASE}${endpoint}"
    if [ -n "$data" ]; then
        echo "Data: $data"
    fi
    echo "Expected Status: $expected_status"
    echo ""
    
    # Build curl command
    local curl_cmd="curl -s -w '\nHTTP_STATUS:%{http_code}' -X $method"
    
    if [ -n "$data" ]; then
        curl_cmd="$curl_cmd -H 'Content-Type: application/json' -d '$data'"
    fi
    
    curl_cmd="$curl_cmd '${API_BASE}${endpoint}'"
    
    # Execute and capture response
    local response=$(eval "$curl_cmd")
    local body=$(echo "$response" | sed -e 's/HTTP_STATUS:.*$//')
    local status=$(echo "$response" | tail -c 4)
    
    # Check status
    if [ "$status" -eq "$expected_status" ]; then
        print_success "Status: $status (Expected: $expected_status)"
        echo "Response:"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
    else
        print_error "Status: $status (Expected: $expected_status)"
        echo "Response:"
        echo "$body"
        return 1
    fi
}

# Check if server is running
check_server() {
    print_header "Checking Server Connection"
    if curl -s "$BASE_URL/health" > /dev/null; then
        print_success "Server is running at $BASE_URL"
    else
        print_error "Server is not running at $BASE_URL"
        echo "Please start the server first:"
        echo "python -m uvicorn src.main:app --host 0.0.0.0 --port 8000"
        exit 1
    fi
}

# Main test execution
main() {
    print_header "RestoVoice Admin Backend API Tests"
    echo "Base URL: $BASE_URL"
    echo "Restaurant ID: $RESTAURANT_ID"
    echo "API Base: $API_BASE"
    
    # Check server
    check_server
    
    # Test 1: Admin Health Check
    test_endpoint "GET" "/health" "" "Admin Health Check" 200
    
    # Test 2: Get Dashboard Stats
    test_endpoint "GET" "/dashboard/stats/$RESTAURANT_ID" "" "Get Dashboard Statistics" 200
    
    # Test 3: Get Policy (should create default if not exists)
    test_endpoint "GET" "/policies/$RESTAURANT_ID" "" "Get Restaurant Policy" 200
    
    # Test 4: Create Policy
    policy_data='{
        "deposit_required": true,
        "deposit_amount": 500,
        "max_party_size": 12,
        "opening_hours": [
            {
                "day_of_week": 0,
                "open_time": "09:00",
                "close_time": "22:00",
                "is_closed": true
            },
            {
                "day_of_week": 1,
                "open_time": "09:00",
                "close_time": "22:00",
                "is_closed": false
            },
            {
                "day_of_week": 2,
                "open_time": "09:00",
                "close_time": "22:00",
                "is_closed": false
            },
            {
                "day_of_week": 3,
                "open_time": "09:00",
                "close_time": "22:00",
                "is_closed": false
            },
            {
                "day_of_week": 4,
                "open_time": "09:00",
                "close_time": "22:00",
                "is_closed": false
            },
            {
                "day_of_week": 5,
                "open_time": "09:00",
                "close_time": "23:00",
                "is_closed": false
            },
            {
                "day_of_week": 6,
                "open_time": "09:00",
                "close_time": "23:00",
                "is_closed": false
            }
        ],
        "deposit_rules": [
            {
                "day_of_week": 5,
                "min_party": 6,
                "start_time": "18:00",
                "end_time": "22:00"
            },
            {
                "day_of_week": 6,
                "min_party": 8,
                "start_time": "17:00",
                "end_time": "21:00"
            }
        ]
    }'
    test_endpoint "POST" "/policies/$RESTAURANT_ID" "$policy_data" "Create/Update Policy" 200
    
    # Test 5: Update Policy (partial update)
    update_data='{
        "deposit_required": false,
        "max_party_size": 15
    }'
    test_endpoint "PUT" "/policies/$RESTAURANT_ID" "$update_data" "Update Policy (Partial)" 200
    
    # Test 6: Get Call Logs
    test_endpoint "GET" "/calls/$RESTAURANT_ID?limit=5&offset=0" "" "Get Call Logs (Pagination)" 200
    
    # Test 7: Get Call Logs with different pagination
    test_endpoint "GET" "/calls/$RESTAURANT_ID?limit=10&offset=5" "" "Get Call Logs (Different Page)" 200
    
    # Test 8: Get Booking Logs
    test_endpoint "GET" "/bookings/$RESTAURANT_ID?limit=5&offset=0" "" "Get Booking Logs" 200
    
    # Test 9: Get Booking Logs with Status Filter
    test_endpoint "GET" "/bookings/$RESTAURANT_ID?status=CONFIRMED&limit=5&offset=0" "" "Get Booking Logs (Status Filter)" 200
    
    # Test 10: Get Booking Logs with Failed Status
    test_endpoint "GET" "/bookings/$RESTAURANT_ID?status=FAILED&limit=5&offset=0" "" "Get Booking Logs (Failed Status)" 200
    
    # Test 11: Error Cases - Non-existent Restaurant
    test_endpoint "GET" "/dashboard/stats/non-existent-restaurant" "" "Get Dashboard Stats (Non-existent Restaurant)" 404
    
    # Test 12: Error Cases - Invalid Policy Data
    invalid_policy='{
        "deposit_required": "not_boolean",
        "max_party_size": -5,
        "opening_hours": "not_array"
    }'
    test_endpoint "POST" "/policies/$RESTAURANT_ID" "$invalid_policy" "Create Policy (Invalid Data)" 422
    
    # Test 13: Error Cases - Limit Too High
    test_endpoint "GET" "/calls/$RESTAURANT_ID?limit=150" "" "Get Call Logs (Limit Too High)" 422
    
    # Test 14: Error Cases - Negative Offset
    test_endpoint "GET" "/bookings/$RESTAURANT_ID?offset=-5" "" "Get Booking Logs (Negative Offset)" 422
    
    # Test 15: Error Cases - Wrong HTTP Method
    test_endpoint "POST" "/policies/$RESTAURANT_ID" "" "POST to GET-only Endpoint" 405
    
    print_header "Test Summary"
    print_success "All admin endpoint tests completed!"
    print_info "Check the responses above to verify functionality"
    print_info "Any errors indicate issues that need to be addressed"
    
    echo -e "\n${BLUE}Quick Reference:${NC}"
    echo "- Dashboard Stats: GET ${API_BASE}/dashboard/stats/$RESTAURANT_ID"
    echo "- Policy Management: GET/POST/PUT ${API_BASE}/policies/$RESTAURANT_ID"
    echo "- Call Logs: GET ${API_BASE}/calls/$RESTAURANT_ID"
    echo "- Booking Logs: GET ${API_BASE}/bookings/$RESTAURANT_ID"
    echo "- Health Check: GET ${API_BASE}/health"
}

# Help function
show_help() {
    echo "RestoVoice Admin Backend API Test Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -u, --url URL           Base URL (default: http://localhost:8000)"
    echo "  -r, --restaurant ID     Restaurant ID (default: test-restaurant-1)"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Use defaults"
    echo "  $0 -u http://localhost:3000           # Different port"
    echo "  $0 -r my-restaurant-123              # Specific restaurant"
    echo "  $0 -u https://api.restovoice.com    # Production API"
    echo ""
    echo "Environment Variables:"
    echo "  BASE_URL        Base URL for the API"
    echo "  RESTAURANT_ID   Restaurant ID to test with"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -u|--url)
            BASE_URL="$2"
            shift 2
            ;;
        -r|--restaurant)
            RESTAURANT_ID="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check dependencies
if ! command -v curl &> /dev/null; then
    print_error "curl is required but not installed"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    print_info "jq is not installed. JSON responses will not be formatted"
fi

# Run main function
main
