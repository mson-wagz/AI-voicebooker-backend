"""
Database configuration and connection management using Prisma
"""
import logging
from prisma import Prisma

logger = logging.getLogger(__name__)

prisma = Prisma()


async def get_db():
    """Yield the shared Prisma client"""
    yield prisma


async def init_db():
    """Connect Prisma client"""
    await prisma.connect()
    logger.info("Prisma connected to database")


async def close_db():
    """Disconnect Prisma client"""
    if prisma.is_connected():
        await prisma.disconnect()
        logger.info("Prisma disconnected from database")
