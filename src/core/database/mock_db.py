"""
Mock database for testing purposes
Simple in-memory database that mimics Prisma operations
"""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import asyncio

class MockPrismaClient:
    """Mock Prisma client for testing"""
    
    def __init__(self):
        self._users: Dict[str, Any] = {}
        self._restaurants: Dict[str, Any] = {}
        self._policies: Dict[str, Any] = {}
        self.user = self._UserTable(self)
        self.restaurant = self._RestaurantTable(self)
        self.policy = self._PolicyTable(self)

    class _UserTable:
        def __init__(self, client: "MockPrismaClient"):
            self._client = client

        async def find_unique(self, *, where: Dict[str, Any]):
            if "email" in where:
                for user in self._client._users.values():
                    if user.email == where["email"]:
                        return user
            elif "id" in where:
                return self._client._users.get(where["id"])
            return None

        async def create(self, *, data: Dict[str, Any]):
            user_id = data.get("id", str(uuid.uuid4()))
            user = MockUser(
                id=user_id,
                email=data["email"],
                name=data["name"],
                role=data["role"],
                onboarding_complete=data.get("onboarding_complete", False),
                restaurant_id=data.get("restaurant_id"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self._client._users[user_id] = user
            return user

        async def update(self, *, where: Dict[str, Any], data: Dict[str, Any]):
            user = self._client._users.get(where["id"])
            if user:
                for key, value in data.items():
                    setattr(user, key, value)
                user.updated_at = datetime.utcnow()
            return user

    class _RestaurantTable:
        def __init__(self, client: "MockPrismaClient"):
            self._client = client

        async def find_unique(self, *, where: Dict[str, Any]):
            if "id" in where:
                return self._client._restaurants.get(where["id"])
            return None

        async def create(self, *, data: Dict[str, Any]):
            restaurant_id = data.get("id", str(uuid.uuid4()))
            restaurant = MockRestaurant(
                id=restaurant_id,
                name=data["name"],
                phone_number=data["phone_number"],
                timezone=data.get("timezone", "UTC"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self._client._restaurants[restaurant_id] = restaurant
            return restaurant

        async def update(self, *, where: Dict[str, Any], data: Dict[str, Any]):
            restaurant = self._client._restaurants.get(where["id"])
            if restaurant:
                for key, value in data.items():
                    setattr(restaurant, key, value)
                restaurant.updated_at = datetime.utcnow()
            return restaurant

    class _PolicyTable:
        def __init__(self, client: "MockPrismaClient"):
            self._client = client

        async def create(self, *, data: Dict[str, Any]):
            policy_id = data.get("id", str(uuid.uuid4()))
            policy = MockPolicy(
                id=policy_id,
                restaurant_id=data["restaurant_id"],
                deposit_required=data.get("deposit_required", False),
                max_party_size=data.get("max_party_size", 10),
                deposit_amount=data.get("deposit_amount")
            )
            self._client._policies[policy_id] = policy
            return policy

        async def update_many(self, *, where: Dict[str, Any], data: Dict[str, Any]):
            updated_count = 0
            for policy in self._client._policies.values():
                if policy.restaurant_id == where.get("restaurant_id"):
                    for key, value in data.items():
                        setattr(policy, key, value)
                    updated_count += 1
            return {"count": updated_count}

class MockUser:
    """Mock User model"""
    def __init__(self, id: str, email: str, name: str, role: str, 
                 onboarding_complete: bool, restaurant_id: Optional[str],
                 created_at: datetime, updated_at: datetime):
        self.id = id
        self.email = email
        self.name = name
        self.role = role
        self.onboarding_complete = onboarding_complete
        self.restaurant_id = restaurant_id
        self.created_at = created_at
        self.updated_at = updated_at

class MockRestaurant:
    """Mock Restaurant model"""
    def __init__(self, id: str, name: str, phone_number: str, timezone: str,
                 created_at: datetime, updated_at: datetime):
        self.id = id
        self.name = name
        self.phone_number = phone_number
        self.timezone = timezone
        self.created_at = created_at
        self.updated_at = updated_at

class MockPolicy:
    """Mock Policy model"""
    def __init__(self, id: str, restaurant_id: str, deposit_required: bool,
                 max_party_size: int, deposit_amount: Optional[int] = None):
        self.id = id
        self.restaurant_id = restaurant_id
        self.deposit_required = deposit_required
        self.max_party_size = max_party_size
        self.deposit_amount = deposit_amount

# Create mock client instance
mock_prisma = MockPrismaClient()
