"""Tests for SSH key normalization functionality."""

import unittest
import logging

from tap_toast_sftp.client import SFTPClient


class TestSSHKeyNormalization(unittest.TestCase):
    """Test class for SSH key normalization."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a minimal config for testing
        self.config = {
            "sftp_host": "test-host",
            "sftp_username": "test-user",
            "sftp_private_key": None,  # Will be set in individual tests
        }
        # Disable logging during tests
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        """Tear down test fixtures."""
        # Re-enable logging
        logging.disable(logging.NOTSET)

    def test_already_normalized_key(self):
        """Test that an already normalized key remains unchanged."""
        normalized_key = """-----BEGIN RSA PRIVATE KEY-----
-----END RSA PRIVATE KEY-----"""
        
        self.config["sftp_private_key"] = normalized_key
        client = SFTPClient(self.config)
        
        # The key should remain unchanged
        self.assertEqual(client.private_key.strip(), normalized_key.strip())

    def test_key_with_escaped_newlines(self):
        """Test that a key with escaped newlines is properly normalized."""
        escaped_key = "-----BEGIN RSA PRIVATE KEY-----\\nMIIEpAIBAAKCAQEAn6MKnmtLvdNd1fEO\\nKEY_CONTENT\\n-----END RSA PRIVATE KEY-----"
        
        expected_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAn6MKnmtLvdNd1fEO
KEY_CONTENT
-----END RSA PRIVATE KEY-----"""
        
        self.config["sftp_private_key"] = escaped_key
        client = SFTPClient(self.config)
        
        # The key should be normalized with actual newlines
        self.assertEqual(client.private_key.strip(), expected_key.strip())

    def test_key_without_newlines(self):
        """Test that a key without newlines is properly normalized."""
        key_without_newlines = "-----BEGIN RSA PRIVATE KEY----- MIIEpAIBAAKCAQEAn6MKnmtLvdNd1fEO KEY_CONTENT -----END RSA PRIVATE KEY-----"
        
        expected_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAn6MKnmtLvdNd1fEO KEY_CONTENT
-----END RSA PRIVATE KEY-----"""
        
        self.config["sftp_private_key"] = key_without_newlines
        client = SFTPClient(self.config)
        
        # The key should be normalized with newlines in the right places
        self.assertTrue("-----BEGIN RSA PRIVATE KEY-----\n" in client.private_key)
        self.assertTrue("\n-----END RSA PRIVATE KEY-----" in client.private_key)

    def test_key_with_extra_whitespace(self):
        """Test that a key with extra whitespace is properly normalized."""
        key_with_whitespace = """
        
        -----BEGIN RSA PRIVATE KEY-----
            MIIEpAIBAAKCAQEAn6MKnmtLvdNd1fEO
            KEY_CONTENT
        -----END RSA PRIVATE KEY-----
        
        """
        
        expected_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAn6MKnmtLvdNd1fEO
KEY_CONTENT
-----END RSA PRIVATE KEY-----"""
        
        self.config["sftp_private_key"] = key_with_whitespace
        client = SFTPClient(self.config)
        
        # The key should be normalized with extra whitespace removed
        self.assertEqual(client.private_key.strip(), expected_key.strip())

    def test_malformed_key(self):
        """Test handling of a malformed key without proper markers."""
        malformed_key = "This is not a valid SSH key"
        
        self.config["sftp_private_key"] = malformed_key
        client = SFTPClient(self.config)
        
        # The key should be returned as is with a warning logged
        self.assertEqual(client.private_key.strip(), malformed_key.strip())


if __name__ == "__main__":
    unittest.main()
