"""
Automation service for continuous booking processing
Production-ready service that runs in the background
"""

import asyncio
import logging
import signal
import sys
from typing import Optional
from ..automation.browser_use import get_booking_processor
from ..metadata.storage import metadata_storage

logger = logging.getLogger(__name__)

class AutomationService:
    """Production-ready automation service"""
    
    def __init__(self):
        self.booking_processor = get_booking_processor()
        self.is_running = False
        self.processing_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    async def start(self):
        """Start the automation service"""
        if self.is_running:
            logger.warning("Automation service is already running")
            return
        
        logger.info("Starting automation service...")
        self.is_running = True
        
        # Start the main processing loop
        self.processing_task = asyncio.create_task(self.booking_processor.start_processing_loop())
        
        # Start periodic cleanup task
        self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        logger.info("Automation service started successfully")
    
    async def stop(self):
        """Stop the automation service gracefully"""
        if not self.is_running:
            return
        
        logger.info("Stopping automation service...")
        self.is_running = False
        
        # Cancel tasks
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Cleanup resources
        await self.booking_processor.cleanup()
        
        logger.info("Automation service stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(self.stop())
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of old files"""
        while self.is_running:
            try:
                # Clean up files older than 30 days
                cleaned_count = await metadata_storage.cleanup_old_files(days=30)
                if cleaned_count > 0:
                    logger.info(f"Cleaned up {cleaned_count} old metadata files")
                
                # Retry failed calls
                retried_count = await metadata_storage.retry_failed_calls(max_retries=3)
                if retried_count > 0:
                    logger.info(f"Retried {retried_count} failed calls")
                
                # Wait 1 hour before next cleanup
                await asyncio.sleep(3600)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def get_status(self) -> dict:
        """Get service status"""
        pending_calls = await metadata_storage.get_pending_calls(limit=100)
        
        return {
            "is_running": self.is_running,
            "pending_calls": len(pending_calls),
            "service_uptime": "running" if self.is_running else "stopped"
        }

# Global service instance
automation_service: Optional[AutomationService] = None

def get_automation_service() -> AutomationService:
    """Get global automation service instance"""
    global automation_service
    if automation_service is None:
        automation_service = AutomationService()
    return automation_service

async def run_automation_service():
    """Run the automation service (for standalone execution)"""
    service = get_automation_service()
    try:
        await service.start()
        # Keep the service running
        while service.is_running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        await service.stop()

if __name__ == "__main__":
    # Run the service standalone
    asyncio.run(run_automation_service())
