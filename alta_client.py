"""
Alta/Avigilon API Client
Handles authentication, HTTP requests, and response parsing for Alta Cloud APIs
"""

import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AltaAPIError(Exception):
    """Custom exception for Alta API errors"""
    pass


class AltaClient:
    """
    Client for interacting with Alta/Avigilon Cloud APIs
    
    Handles:
    - Authentication via API token
    - HTTP requests with proper headers
    - Error handling and retries
    - Response parsing
    """
    
    def __init__(self, base_url: str, api_token: str):
        """
        Initialize Alta API client
        
        Args:
            base_url: Organization base URL (e.g., https://ifss-kenya-office.eu2.alta.avigilon.com)
            api_token: API authentication token
        """
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.session = requests.Session()
        self._cached_events = None  # Cache for access events
        
        # Set default headers
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        logger.info(f"Initialized AltaClient for: {base_url}")
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        retry_count: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request to Alta API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., /api/v1/accessEvents)
            params: Query parameters
            data: Request body data
            retry_count: Number of retries on failure
            
        Returns:
            Parsed JSON response or None
            
        Raises:
            AltaAPIError: On API errors or network issues
        """
        url = f"{self.base_url}{endpoint}"
        
        logger.info(f"Making {method} request to: {endpoint}")
        
        for attempt in range(retry_count):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    timeout=30
                )
                
                # Handle HTTP errors
                if response.status_code == 401:
                    logger.error("Authentication failed - invalid token")
                    raise AltaAPIError("Authentication failed. Please check your API token.")
                
                elif response.status_code == 403:
                    logger.error("Access forbidden - insufficient permissions")
                    raise AltaAPIError("Access forbidden. You don't have permission for this resource.")
                
                elif response.status_code == 404:
                    logger.error(f"Resource not found: {endpoint}")
                    raise AltaAPIError(f"Resource not found: {endpoint}")
                
                elif response.status_code == 204:
                    # No content - return empty dict
                    return {}
                
                elif response.status_code == 429:
                    logger.warning("Rate limit exceeded, waiting before retry...")
                    time.sleep(2 ** attempt)
                    continue
                
                elif response.status_code >= 500:
                    logger.error(f"Server error: {response.status_code}")
                    if attempt < retry_count - 1:
                        time.sleep(1)
                        continue
                    raise AltaAPIError(f"Server error: {response.status_code}")
                
                # Raise for other bad status codes
                response.raise_for_status()
                
                # Check if response is JSON
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' not in content_type:
                    logger.warning(f"Non-JSON response: {content_type}")
                    return {}
                
                # Parse and return JSON response
                try:
                    return response.json()
                except ValueError:
                    logger.error("Failed to parse JSON response")
                    return {}
                
            except requests.exceptions.Timeout:
                logger.error(f"Request timeout (attempt {attempt + 1}/{retry_count})")
                if attempt < retry_count - 1:
                    time.sleep(1)
                    continue
                raise AltaAPIError("Request timeout. Please try again.")
            
            except requests.exceptions.ConnectionError:
                logger.error(f"Connection error (attempt {attempt + 1}/{retry_count})")
                if attempt < retry_count - 1:
                    time.sleep(1)
                    continue
                raise AltaAPIError("Unable to connect to Alta API. Please check your network.")
            
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                raise AltaAPIError(f"Request failed: {str(e)}")
        
        raise AltaAPIError("Maximum retries exceeded")
    
    # ========== USER IDENTITY ==========
    
    def get_current_user(self) -> Optional[Dict]:
        """
        Get the current authenticated user
        
        Returns:
            Current user dictionary or None
        """
        endpoint = "/api/v1/me"
        
        try:
            response = self._make_request('GET', endpoint)
            if response:
                logger.info(f"Retrieved current user")
                return response
            return None
        except AltaAPIError as e:
            logger.error(f"Failed to get current user: {str(e)}")
            return None
    
    # ========== ACCESS EVENTS ==========
    
    def get_access_events(self) -> List[Dict]:
        """
        Get access events (cached after first call)
        
        Returns:
            List of access event dictionaries
        """
        # Return cached events if available
        if self._cached_events is not None:
            logger.info(f"Returning {len(self._cached_events)} cached access events")
            return self._cached_events
        
        endpoint = "/api/v1/accessEvents"
        
        try:
            logger.info(f"Calling {endpoint} with no parameters")
            response = self._make_request('GET', endpoint)
            if not response:
                logger.info("No response returned from accessEvents")
                return []
            
            # Handle both direct list and wrapped response
            events = response if isinstance(response, list) else response.get('data', response.get('events', []))
            
            # Cache the events
            self._cached_events = events
            
            logger.info(f"Retrieved and cached {len(events)} access events")
            return events
        except AltaAPIError as e:
            logger.error(f"Failed to get access events: {str(e)}")
            raise
    
    # ========== NEW: GET SINGLE ACCESS EVENT BY GUID ==========
    
    def get_access_event_by_guid(self, guid: str) -> Optional[Dict]:
        """
        Get a single access event by its GUID
        
        Args:
            guid: The unique identifier of the access event
            
        Returns:
            Access event dictionary or None if not found
            
        Raises:
            AltaAPIError: On API errors or network issues
        """
        endpoint = f"/api/v1/accessEvents/{guid}"
        
        try:
            logger.info(f"Fetching access event with GUID: {guid}")
            response = self._make_request('GET', endpoint)
            
            if response:
                logger.info(f"Retrieved access event: {guid}")
                return response
            
            logger.warning(f"Access event not found: {guid}")
            return None
            
        except AltaAPIError as e:
            if "not found" in str(e).lower():
                logger.warning(f"Access event not found: {guid}")
                return None
            logger.error(f"Failed to get access event {guid}: {str(e)}")
            raise
    
    def get_entries_today(self) -> List[Dict]:
        """
        Get today's access events
        
        Returns:
            List of today's access events
        """
        all_events = self.get_access_events()
        
        # Calculate today's start in UTC (00:00 UTC today)
        today_start_utc = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_ms = int(today_start_utc.timestamp() * 1000)
        
        # Filter events from 00:00 UTC today to now
        today_events = [
            event for event in all_events
            if isinstance(event.get('time'), (int, float)) and event.get('time', 0) >= today_start_ms
        ]
        
        logger.info(f"[TODAY] Filtered {len(today_events)} events from today out of {len(all_events)} total (UTC boundary: {today_start_utc.isoformat()})")
        return today_events
    
    def get_entries_yesterday(self) -> List[Dict]:
        """
        Get yesterday's access events
        
        Returns:
            List of yesterday's access events
        """
        all_events = self.get_access_events()
        
        # Calculate yesterday's time range in UTC
        # Yesterday: 00:00 UTC yesterday to 00:00 UTC today
        today_start_utc = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start_utc = today_start_utc - timedelta(days=1)
        
        yesterday_start_ms = int(yesterday_start_utc.timestamp() * 1000)
        yesterday_end_ms = int(today_start_utc.timestamp() * 1000)
        
        yesterday_events = [
            event for event in all_events
            if isinstance(event.get('time'), (int, float)) and yesterday_start_ms <= event.get('time', 0) < yesterday_end_ms
        ]
        
        logger.info(f"[YESTERDAY] Filtered {len(yesterday_events)} events from yesterday out of {len(all_events)} total (UTC range: {yesterday_start_utc.isoformat()} to {today_start_utc.isoformat()})")
        return yesterday_events
    
    def get_entries_last_n_days(self, days: int = 7) -> List[Dict]:
        """
        Get access events for the last N days
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of access events
        """
        all_events = self.get_access_events()
        
        # Calculate start time in epoch milliseconds (using current time, not UTC midnight)
        start_time = datetime.utcnow() - timedelta(days=days)
        start_time_ms = int(start_time.timestamp() * 1000)
        
        filtered_events = [
            event for event in all_events
            if isinstance(event.get('time'), (int, float)) and event.get('time', 0) >= start_time_ms
        ]
        
        logger.info(f"[LAST_{days}_DAYS] Filtered {len(filtered_events)} events from last {days} days out of {len(all_events)} total")
        return filtered_events
    
    def get_last_entry(self) -> Optional[Dict]:
        """
        Get the most recent access event
        
        Returns:
            Most recent event or None
        """
        events = self.get_access_events()
        if not events:
            logger.info("No access events available")
            return None
        
        # Sort by time descending and return first
        sorted_events = sorted(
            events,
            key=lambda x: x.get('time', 0),
            reverse=True
        )
        
        logger.info("Retrieved most recent access event")
        return sorted_events[0]
    
    # ========== ACCESS POINTS (DOORS/READERS) ==========
    
    def get_access_points(self) -> List[Dict]:
        """
        Get all access control points (doors/readers)
        
        Returns:
            List of access point dictionaries
        """
        endpoint = "/api/v1/accessControlPoints"
        
        try:
            response = self._make_request('GET', endpoint)
            if not response:
                return []
            
            # Handle both direct list and wrapped response
            points = response if isinstance(response, list) else response.get('data', response.get('accessControlPoints', []))
            logger.info(f"Retrieved {len(points)} access control points")
            return points
        except AltaAPIError as e:
            logger.error(f"Failed to get access points: {str(e)}")
            raise
    
    def get_available_access_points(self) -> List[Dict]:
        """
        Get available access points
        
        Returns:
            List of available access point dictionaries
        """
        endpoint = "/api/v1/availableAccessPoints"
        
        try:
            response = self._make_request('GET', endpoint)
            if not response:
                return []
            
            # Handle both direct list and wrapped response
            points = response if isinstance(response, list) else response.get('data', response.get('availableAccessPoints', []))
            logger.info(f"Retrieved {len(points)} available access points")
            return points
        except AltaAPIError as e:
            logger.error(f"Failed to get available access points: {str(e)}")
            raise
    
    # ========== NEW: UNLOCK ACCESS POINT ==========
    
    def unlock_access_point(self, access_point_id: str) -> Dict:
        """
        Unlock an access control point (door)
        
        Args:
            access_point_id: The ID of the access point to unlock
            
        Returns:
            Empty dict if successful (204 response) or response JSON if present
            
        Raises:
            AltaAPIError: On invalid ID, insufficient permissions, or other API errors
        """
        endpoint = f"/api/v1/accessControlPoints/{access_point_id}/unlock"
        
        try:
            logger.info(f"Attempting to unlock access point: {access_point_id}")
            response = self._make_request('POST', endpoint)
            
            logger.info(f"Successfully unlocked access point: {access_point_id}")
            return response if response else {}
            
        except AltaAPIError as e:
            logger.error(f"Failed to unlock access point {access_point_id}: {str(e)}")
            raise
    
    # ========== FILTERING HELPERS ==========
    
    def filter_denied_entries(self, events: List[Dict]) -> List[Dict]:
        """
        Filter events to only show denied access attempts
        
        Args:
            events: List of event dictionaries
            
        Returns:
            List of denied events
        """
        denied_events = []
        
        for event in events:
            event_type = event.get('event_type', '')
            event_name = event.get('event_name', '').lower()
            
            # Exclude HELD_OPEN events completely
            if event_type in ['HELD_OPEN', 'HELD_OPEN_ENDED']:
                continue
            
            # Include if ACCESS_DENIED or event_name contains "failed" or "denied"
            if (event_type == 'ACCESS_DENIED' or 
                'failed' in event_name or 
                'denied' in event_name):
                denied_events.append(event)
        
        logger.info(f"[DENIED] Filtered {len(denied_events)} denied events from {len(events)} total")
        return denied_events
    
    def filter_granted_entries(self, events: List[Dict]) -> List[Dict]:
        """
        Filter events to only show granted access
        
        Args:
            events: List of event dictionaries
            
        Returns:
            List of granted events
        """
        granted_events = [
            event for event in events
            if event.get('event_type') == 'ACCESS_GRANTED'
        ]
        
        logger.info(f"[GRANTED] Filtered {len(granted_events)} granted events from {len(events)} total")
        return granted_events
