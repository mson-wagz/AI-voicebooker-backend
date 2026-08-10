"""
Test script for all admin endpoints
This script tests the complete admin dashboard functionality
"""
import asyncio
import httpx
import json
from datetime import datetime, timedelta
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

class AdminAPITester:
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=API_BASE)
        self.auth_token = None
        self.user_data = None
        
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def login(self, email: str = "test@example.com", password: str = "testpassword123"):
        """Login and store auth token"""
        print("🔐 Logging in...")
        
        login_data = {
            "email": email,
            "password": password
        }
        
        response = await self.client.post("/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("token")
            self.user_data = data.get("user")
            self.client.headers.update({"Authorization": f"Bearer {self.auth_token}"})
            print(f"✅ Login successful! User: {self.user_data.get('name')}")
            return True
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    
    async def test_overview_stats(self):
        """Test overview statistics endpoint"""
        print("\n📊 Testing overview stats...")
        
        response = await self.client.get("/owner/dashboard/overview-stats")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Overview stats retrieved successfully")
            print(f"   Total Calls: {data.get('totalCalls')}")
            print(f"   Successful Bookings: {data.get('successfulBookings')}")
            print(f"   Failed Bookings: {data.get('failedBookings')}")
            print(f"   Conversion Rate: {data.get('conversionRate')}%")
            return True
        else:
            print(f"❌ Overview stats failed: {response.status_code} - {response.text}")
            return False
    
    async def test_call_logs(self):
        """Test call logs endpoint"""
        print("\n📞 Testing call logs...")
        
        response = await self.client.get("/owner/dashboard/calls")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Call logs retrieved successfully")
            print(f"   Total calls: {data.get('total')}")
            print(f"   Page: {data.get('page')}")
            print(f"   Calls returned: {len(data.get('calls', []))}")
            return True
        else:
            print(f"❌ Call logs failed: {response.status_code} - {response.text}")
            return False
    
    async def test_bookings(self):
        """Test bookings endpoint"""
        print("\n📅 Testing bookings...")
        
        response = await self.client.get("/owner/dashboard/bookings")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Bookings retrieved successfully")
            print(f"   Total bookings: {data.get('total')}")
            print(f"   Page: {data.get('page')}")
            print(f"   Bookings returned: {len(data.get('bookings', []))}")
            return True
        else:
            print(f"❌ Bookings failed: {response.status_code} - {response.text}")
            return False
    
    async def test_restaurant_settings(self):
        """Test restaurant settings endpoint"""
        print("\n🏪 Testing restaurant settings...")
        
        response = await self.client.get("/user/restaurant-settings")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Restaurant settings retrieved successfully")
            print(f"   Restaurant: {data.get('name')}")
            print(f"   Phone: {data.get('phone_number')}")
            print(f"   Email: {data.get('email')}")
            print(f"   Opening hours: {len(data.get('opening_hours', []))} days")
            return True
        else:
            print(f"❌ Restaurant settings failed: {response.status_code} - {response.text}")
            return False
    
    async def test_policy_settings(self):
        """Test policy settings endpoint"""
        print("\n📋 Testing policy settings...")
        
        response = await self.client.get("/user/policy-settings")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Policy settings retrieved successfully")
            print(f"   Deposit Required: {data.get('deposit_required')}")
            print(f"   Max Party Size: {data.get('max_party_size')}")
            print(f"   Auto Confirm: {data.get('auto_confirm')}")
            return True
        else:
            print(f"❌ Policy settings failed: {response.status_code} - {response.text}")
            return False
    
    async def test_opening_hours(self):
        """Test opening hours endpoint"""
        print("\n⏰ Testing opening hours...")
        
        response = await self.client.get("/user/opening-hours")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Opening hours retrieved successfully")
            print(f"   Days configured: {len(data.get('opening_hours', []))}")
            for hours in data.get('opening_hours', [])[:3]:  # Show first 3 days
                print(f"   {hours.get('day_name')}: {hours.get('open_time')} - {hours.get('close_time')}")
            return True
        else:
            print(f"❌ Opening hours failed: {response.status_code} - {response.text}")
            return False
    
    async def test_calls_trend(self):
        """Test calls trend analytics"""
        print("\n📈 Testing calls trend analytics...")
        
        response = await self.client.get("/owner/dashboard/analytics/calls-trend")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Calls trend retrieved successfully")
            trend_data = data.get('trend', [])
            print(f"   Data points: {len(trend_data)}")
            if trend_data:
                latest = trend_data[0]
                print(f"   Latest date: {latest.get('date')}")
                print(f"   Calls on latest date: {latest.get('call_count')}")
            return True
        else:
            print(f"❌ Calls trend failed: {response.status_code} - {response.text}")
            return False
    
    async def test_performance_metrics(self):
        """Test performance metrics"""
        print("\n⚡ Testing performance metrics...")
        
        response = await self.client.get("/owner/dashboard/analytics/performance-metrics")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Performance metrics retrieved successfully")
            print(f"   Average call duration: {data.get('average_call_duration')} seconds")
            peak_hours = data.get('peak_call_hours', [])
            if peak_hours:
                print(f"   Peak hour: {peak_hours[0].get('hour')}:00 with {peak_hours[0].get('call_count')} calls")
            return True
        else:
            print(f"❌ Performance metrics failed: {response.status_code} - {response.text}")
            return False
    
    async def test_availability(self):
        """Test availability endpoint"""
        print("\n📆 Testing availability...")
        
        # Test with tomorrow's date
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = await self.client.get(f"/user/availability?date={tomorrow}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Availability retrieved successfully")
            print(f"   Date: {data.get('date')}")
            print(f"   Is closed: {data.get('is_closed')}")
            if not data.get('is_closed'):
                print(f"   Open: {data.get('open_time')} - {data.get('close_time')}")
                print(f"   Available slots: {len(data.get('available_slots', []))}")
            return True
        else:
            print(f"❌ Availability failed: {response.status_code} - {response.text}")
            return False
    
    async def run_all_tests(self):
        """Run all admin endpoint tests"""
        print("🚀 Starting Admin API Tests")
        print("=" * 50)
        
        # First login
        if not await self.login():
            print("❌ Cannot proceed with tests without authentication")
            return False
        
        # Run all tests
        tests = [
            self.test_overview_stats,
            self.test_call_logs,
            self.test_bookings,
            self.test_restaurant_settings,
            self.test_policy_settings,
            self.test_opening_hours,
            self.test_calls_trend,
            self.test_performance_metrics,
            self.test_availability,
        ]
        
        results = []
        for test in tests:
            try:
                result = await test()
                results.append(result)
            except Exception as e:
                print(f"❌ Test failed with exception: {str(e)}")
                results.append(False)
        
        # Summary
        print("\n" + "=" * 50)
        passed = sum(results)
        total = len(results)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All admin endpoints are working correctly!")
        else:
            print("⚠️  Some endpoints need attention")
        
        return passed == total

async def main():
    """Main test runner"""
    print("RestoVoice Admin API Test Suite")
    print("Make sure the backend is running on http://localhost:8000")
    print()
    
    async with AdminAPITester() as tester:
        success = await tester.run_all_tests()
        
    if success:
        print("\n✅ All tests completed successfully!")
    else:
        print("\n❌ Some tests failed. Check the logs above.")

if __name__ == "__main__":
    asyncio.run(main())
