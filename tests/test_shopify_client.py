"""Tests for Shopify API client retry behavior."""
import unittest
from unittest.mock import Mock, patch

from shopify_client import ShopifyAPIError, ShopifyClient


def make_response(status_code, json_data=None, headers=None, text=''):
    response = Mock()
    response.status_code = status_code
    response.headers = headers or {}
    response.text = text
    response.json.return_value = json_data or {}
    response.raise_for_status.return_value = None
    return response


class TestShopifyClient(unittest.TestCase):
    def setUp(self):
        self.client = ShopifyClient(
            store_domain='example.myshopify.com',
            api_version='2024-04',
            access_token='test-token',
            timeout=5
        )

    @patch('shopify_client.time.sleep')
    @patch('shopify_client.requests.request')
    def test_rate_limit_uses_retry_after_then_succeeds(self, mock_request, mock_sleep):
        rate_limited = make_response(
            429,
            headers={'Retry-After': '3'},
            text='Rate Limit Exceeded'
        )
        success = make_response(200, json_data={'products': []})
        mock_request.side_effect = [rate_limited, success]

        data, next_page = self.client.request('GET', '/products.json')

        self.assertEqual(data, {'products': []})
        self.assertIsNone(next_page)
        self.assertEqual(mock_request.call_count, 2)
        mock_sleep.assert_called_once_with(3)

    @patch('shopify_client.time.sleep')
    @patch('shopify_client.requests.request')
    def test_server_errors_use_exponential_backoff_then_succeed(self, mock_request, mock_sleep):
        first_error = make_response(500, text='Server error')
        second_error = make_response(500, text='Server error')
        success = make_response(200, json_data={'products': [{'id': 1}]})
        mock_request.side_effect = [first_error, second_error, success]

        data, _ = self.client.request('GET', '/products.json')

        self.assertEqual(data, {'products': [{'id': 1}]})
        self.assertEqual(mock_request.call_count, 3)
        self.assertEqual([call.args[0] for call in mock_sleep.call_args_list], [1, 2])

    @patch('shopify_client.time.sleep')
    @patch('shopify_client.requests.request')
    def test_server_error_raises_after_retries(self, mock_request, mock_sleep):
        mock_request.return_value = make_response(500, text='Server error')

        with self.assertRaises(ShopifyAPIError):
            self.client.request('GET', '/products.json', max_retries=2)

        self.assertEqual(mock_request.call_count, 3)
        self.assertEqual([call.args[0] for call in mock_sleep.call_args_list], [1, 2])


if __name__ == '__main__':
    unittest.main()
