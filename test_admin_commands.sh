# RestoVoice Admin API - Quick Test Commands
# Use these commands to test admin endpoints once the server is running properly

# Configuration
BASE_URL="http://localhost:8000"
RESTAURANT_ID="test-restaurant-1"
API_BASE="$BASE_URL/admin"

echo "=== RestoVoice Admin API Test Commands ==="
echo "Base URL: $BASE_URL"
echo "Restaurant ID: $RESTAURANT_ID"
echo ""

# 1. Check Server Health
echo "1. Server Health Check:"
curl -s -w "Status: %{http_code}\n" -X GET "$BASE_URL/health"
echo ""

# 2. Admin Health Check
echo "2. Admin Health Check:"
curl -s -w "Status: %{http_code}\n" -X GET "$API_BASE/health"
echo ""

# 3. Dashboard Statistics
echo "3. Dashboard Statistics:"
curl -s -w "Status: %{http_code}\n" -X GET "$API_BASE/dashboard/stats/$RESTAURANT_ID"
echo ""

# 4. Get Policy
echo "4. Get Restaurant Policy:"
curl -s -w "Status: %{http_code}\n" -X GET "$API_BASE/policies/$RESTAURANT_ID"
echo ""

# 5. Create Policy
echo "5. Create Policy:"
curl -s -w "Status: %{http_code}\n" -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "deposit_required": true,
    "deposit_amount": 500,
    "max_party_size": 12,
    "opening_hours": [
      {"day_of_week": 0, "open_time": "09:00", "close_time": "22:00", "is_closed": true},
      {"day_of_week": 1, "open_time": "09:00", "close_time": "22:00", "is_closed": false}
    ],
    "deposit_rules": [
      {"day_of_week": 5, "min_party": 6, "start_time": "18:00", "end_time": "22:00"}
    ]
  }' \
  "$API_BASE/policies/$RESTAURANT_ID"
echo ""

# 6. Update Policy
echo "6. Update Policy:"
curl -s -w "Status: %{http_code}\n" -X PUT \
  -H "Content-Type: application/json" \
  -d '{
    "deposit_required": false,
    "max_party_size": 15
  }' \
  "$API_BASE/policies/$RESTAURANT_ID"
echo ""

# 7. Get Call Logs
echo "7. Get Call Logs:"
curl -s -w "Status: %{http_code}\n" -X GET "$API_BASE/calls/$RESTAURANT_ID?limit=5&offset=0"
echo ""

# 8. Get Booking Logs
echo "8. Get Booking Logs:"
curl -s -w "Status: %{http_code}\n" -X GET "$API_BASE/bookings/$RESTAURANT_ID?limit=5&offset=0"
echo ""

# 9. Get Booking Logs (Status Filter)
echo "9. Get Booking Logs (Confirmed):"
curl -s -w "Status: %{http_code}\n" -X GET "$API_BASE/bookings/$RESTAURANT_ID?status=CONFIRMED&limit=5&offset=0"
echo ""

# 10. Error Test - Non-existent Restaurant
echo "10. Error Test (Non-existent Restaurant):"
curl -s -w "Status: %{http_code}\n" -X GET "$API_BASE/dashboard/stats/non-existent-restaurant"
echo ""

echo "=== Test Complete ==="
echo ""
echo "Expected Results:"
echo "- Health checks: 200"
echo "- Dashboard/Policy/Logs: 200 (if data exists) or 404 (if no data)"
echo "- Error tests: 404 or 422"
echo ""
echo "If all endpoints return 404, the admin service is not properly initialized."
echo "Check server logs for import errors."
