"""
Shopify Admin API client with retry logic and pagination support.
"""
import requests
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs


class ShopifyAPIError(Exception):
    """Exception raised for Shopify API errors."""
    pass


class ShopifyClient:
    """Client for interacting with Shopify Admin API."""

    def __init__(self, store_domain: str, api_version: str, access_token: str, timeout: int = 30):
        """
        Initialize Shopify API client.

        Args:
            store_domain: Shopify store domain (e.g., 'example.myshopify.com')
            api_version: API version (e.g., '2024-04')
            access_token: Admin API access token
            timeout: Request timeout in seconds
        """
        self.store_domain = store_domain.replace('https://', '').replace('http://', '')
        self.api_version = api_version
        self.access_token = access_token
        self.timeout = timeout
        self.base_url = f"https://{self.store_domain}/admin/api/{self.api_version}"

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        return {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json'
        }

    def _parse_link_header(self, link_header: Optional[str]) -> Optional[str]:
        """
        Parse Link header for pagination.

        Args:
            link_header: Link header value from response

        Returns:
            Next page URL if available, None otherwise
        """
        if not link_header:
            return None

        links = link_header.split(',')
        for link in links:
            parts = link.strip().split(';')
            if len(parts) == 2:
                url = parts[0].strip('<> ')
                rel = parts[1].strip()
                if 'rel="next"' in rel:
                    return url
        return None

    def request(self, method: str, endpoint: str, params: Optional[Dict] = None,
                max_retries: int = 3) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Make HTTP request with retry logic for rate limits and server errors.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            max_retries: Maximum number of retry attempts

        Returns:
            Tuple of (response_data, next_page_url)

        Raises:
            ShopifyAPIError: If request fails after retries
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        for attempt in range(max_retries + 1):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    timeout=self.timeout
                )

                # Handle rate limiting (429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 2))
                    if attempt < max_retries:
                        time.sleep(retry_after)
                        continue
                    raise ShopifyAPIError(f"Rate limit exceeded after {max_retries} retries")

                # Handle server errors (5xx)
                if 500 <= response.status_code < 600:
                    if attempt < max_retries:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    raise ShopifyAPIError(f"Server error {response.status_code}: {response.text}")

                # Handle client errors (4xx)
                if 400 <= response.status_code < 500:
                    raise ShopifyAPIError(f"Client error {response.status_code}: {response.text}")

                # Success
                response.raise_for_status()
                next_page_url = self._parse_link_header(response.headers.get('Link'))
                return response.json(), next_page_url

            except requests.exceptions.Timeout:
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                raise ShopifyAPIError(f"Request timeout after {max_retries} retries")

            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                raise ShopifyAPIError(f"Request failed: {str(e)}")

        raise ShopifyAPIError("Request failed after all retries")

    def get_products(self, limit: int = 250) -> List[Dict]:
        """
        Fetch products with pagination support.

        Args:
            limit: Maximum number of products to fetch

        Returns:
            List of product dictionaries
        """
        products = []
        params = {
            'limit': min(limit, 250),  # Shopify max is 250 per page
            'status': 'any'
        }

        endpoint = '/products.json'
        fetched = 0

        while fetched < limit:
            data, next_url = self.request('GET', endpoint, params)

            if data and 'products' in data:
                batch = data['products']
                remaining = limit - fetched
                products.extend(batch[:remaining])
                fetched += len(batch[:remaining])

                # Check if we have more pages and haven't hit limit
                if next_url and fetched < limit:
                    # Parse next URL to get page_info parameter
                    parsed = urlparse(next_url)
                    query_params = parse_qs(parsed.query)
                    if 'page_info' in query_params:
                        params = {'page_info': query_params['page_info'][0], 'limit': min(250, limit - fetched)}
                        endpoint = '/products.json'
                    else:
                        break
                else:
                    break
            else:
                break

        return products

    def get_locations(self) -> List[Dict]:
        """
        Fetch all store locations.

        Returns:
            List of location dictionaries
        """
        data, _ = self.request('GET', '/locations.json')
        return data.get('locations', []) if data else []

    def get_inventory_levels(self, inventory_item_ids: List[int],
                            location_ids: Optional[List[int]] = None) -> List[Dict]:
        """
        Fetch inventory levels for given inventory items.

        Args:
            inventory_item_ids: List of inventory item IDs
            location_ids: Optional list of location IDs to filter by

        Returns:
            List of inventory level dictionaries
        """
        if not inventory_item_ids:
            return []

        # Batch inventory item IDs (API has query length limits)
        batch_size = 50
        all_levels = []

        for i in range(0, len(inventory_item_ids), batch_size):
            batch = inventory_item_ids[i:i + batch_size]
            params = {
                'inventory_item_ids': ','.join(map(str, batch))
            }

            if location_ids:
                params['location_ids'] = ','.join(map(str, location_ids))

            data, _ = self.request('GET', '/inventory_levels.json', params)
            if data and 'inventory_levels' in data:
                all_levels.extend(data['inventory_levels'])

        return all_levels

    def get_product(self, product_id: int) -> Optional[Dict]:
        """
        Fetch a single product by ID.

        Args:
            product_id: Product ID

        Returns:
            Product dictionary or None if not found
        """
        try:
            data, _ = self.request('GET', f'/products/{product_id}.json')
            return data.get('product') if data else None
        except ShopifyAPIError:
            return None

    def search_products_by_query(self, query_string: str, limit: int = 250) -> List[Dict]:
        """
        Search products using Shopify query syntax.

        Args:
            query_string: Search query
            limit: Maximum results to return

        Returns:
            List of matching product dictionaries
        """
        products = []
        params = {
            'limit': min(limit, 250),
            'status': 'any'
        }

        # Add query parameter if provided
        if query_string:
            params['title'] = query_string

        endpoint = '/products.json'
        data, _ = self.request('GET', endpoint, params)

        if data and 'products' in data:
            products = data['products'][:limit]

        return products
