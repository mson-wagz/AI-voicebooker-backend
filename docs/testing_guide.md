# Browser-Use Testing Guide

## Quick Testing Options

### Option 1: Simple Flow Test (No Browser Required)

Test the AI processing and metadata storage without browser automation:

```bash
# 1. Set up Azure OpenAI environment variables
export AZURE_OPENAI_API_KEY="your_key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT="gpt-4-turbo-preview"

# 2. Run the simple test
uv run python test_booking_flow_simple.py
```

**What this tests:**
- Azure OpenAI call processing
- Booking details extraction
- JSON metadata storage
- Flow simulation

### Option 2: Full Browser Automation Test

Test the complete flow including browser automation:

```bash
# 1. Install browser-use (if not already installed)
uv add browser-use

# 2. Install browser dependencies (if needed)
# On Ubuntu/Debian:
sudo apt-get install -y google-chrome-stable

# On macOS with Homebrew:
brew install --cask google-chrome

# 3. Set environment variables
export AZURE_OPENAI_API_KEY="your_key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT="gpt-4-turbo-preview"
export VAPI_API_KEY="your_vapi_key"

# 4. Run the browser test
uv run python test_browser_automation.py
```

**What this tests:**
- Everything from Option 1
- Browser initialization
- Web navigation
- Form filling automation
- Real booking attempt (on demo site)

### Option 3: Configuration Test Only

Just verify your setup is correct:

```bash
uv run python test_azure_config.py
```

## Test Results

### Successful Simple Test Output:
```
🎯 Testing Simple Booking Flow
==================================================

📞 Step 1: Processing call with Azure OpenAI...
✅ Call processed! Call ID: uuid-generated-id

📄 Step 2: Checking extracted metadata...
✅ Metadata found:
   - Customer: John Smith
   - Phone: +1-555-123-4567
   - Date: 2024-03-18
   - Time: 19:00
   - Party Size: 4
   - Occasion: birthday
   - Priority: normal
   - Status: pending

🤖 Step 3: Simulating automation...
✅ Booking marked as completed!
   Reference: BK202403171234
   Steps: 5

📊 Step 4: Final verification...
✅ Flow completed successfully!
   Final Status: completed
   Booking Ref: BK202403171234

✨ All tests completed successfully!
```

### Browser Automation Test:
The browser test will:
1. Show sample booking data
2. Initialize browser in headless mode
3. Navigate to example restaurant website
4. Attempt booking process
5. Show results and screenshots taken

## Troubleshooting

### Azure OpenAI Issues:
```
❌ Missing Azure OpenAI environment variables
```
**Solution:** Set the required environment variables:
```bash
export AZURE_OPENAI_API_KEY="your_key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT="gpt-4-turbo-preview"
```

### Browser-Use Not Installed:
```
❌ browser-use not installed
```
**Solution:** Install it:
```bash
uv add browser-use
```

### Browser Issues:
```
❌ Failed to initialize browser
```
**Solution:** Install Chrome/Chromium:
```bash
# Ubuntu/Debian
sudo apt-get install -y google-chrome-stable

# macOS
brew install --cask google-chrome

# Windows
# Download and install Chrome from google.com/chrome
```

### Permission Issues:
```
❌ Permission denied creating metadata files
```
**Solution:** Create metadata directory:
```bash
mkdir -p call_metadata/{pending,processing,completed,failed}
chmod 755 call_metadata
```

## Testing with Real Data

### Test with Your Own Restaurant:

1. **Create Restaurant Configuration:**
```python
# In browser_use.py, add your restaurant:
"my_restaurant": RestaurantBookingSite(
    name="My Restaurant",
    url="https://my-restaurant.com",
    booking_path="/reservations",
    selectors={
        "date_field": "#reservation-date",
        "time_field": "#reservation-time", 
        "party_size": "#party-size",
        "name_field": "#customer-name",
        "phone_field": "#customer-phone",
        "submit_button": "#submit-reservation"
    }
)
```

2. **Update Test Data:**
```python
# In test script, use:
call_data = {
    "restaurant_id": "my_restaurant",
    "customer_phone": "+1-your-phone",
    "transcript": "Your actual call transcript...",
    "status": "completed"
}
```

3. **Run Test:**
```bash
uv run python test_browser_automation.py
```

### Test with Vapi Webhook:

1. **Start the Server:**
```bash
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

2. **Send Test Webhook:**
```bash
curl -X POST http://localhost:8000/v1/vapi/webhooks/vapi \
  -H "Content-Type: application/json" \
  -d '{
    "type": "call.end",
    "call": {
      "id": "test-call-123",
      "status": "completed",
      "transcript": "I need a table for 4 people tomorrow at 7 PM",
      "customer": {"number": "+1-555-123-4567"},
      "restaurantId": "restaurant_1"
    }
  }'
```

3. **Check Results:**
```bash
curl http://localhost:8000/health
```

## Production Testing

### Load Testing:
```bash
# Test multiple concurrent calls
uv run python test_booking_flow_simple.py
```

### End-to-End Testing:
1. Set up real restaurant configurations
2. Configure Vapi webhook URL
3. Make actual test calls
4. Monitor automation results

### Monitoring:
- Check `/health` endpoint for service status
- Monitor `call_metadata/` directories for processing status
- Review logs for automation results

## Next Steps

After successful testing:

1. **Deploy to Production:**
   - Set up environment variables in production
   - Configure real restaurant sites
   - Set up Vapi webhook endpoint

2. **Monitor Performance:**
   - Track booking success rates
   - Monitor processing times
   - Set up alerts for failures

3. **Scale Up:**
   - Add more restaurant configurations
   - Increase concurrent processing limits
   - Set up load balancing
