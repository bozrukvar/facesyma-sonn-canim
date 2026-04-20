"""
Facesyma Test Module — Google Cloud Storage Integration
=======================================================
Handle PDF storage and signed URL generation for test reports.

Features:
- Upload PDF to Google Cloud Storage
- Generate signed URLs (1 hour validity)
- Cleanup old PDFs
- Error handling and logging
"""

import os
import logging
from io import BytesIO
from datetime import timedelta
from typing import Optional

try:
    from google.cloud import storage
    from google.oauth2 import service_account
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False

log = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────
GCS_BUCKET = os.environ.get("GCS_BUCKET", "facesyma-test-reports")
GCS_PROJECT = os.environ.get("GCS_PROJECT", "facesyma-project")
GCS_CREDENTIALS = os.environ.get("GCS_CREDENTIALS")  # Path to JSON credentials file


class GCSStorageManager:
    """Manage PDF storage in Google Cloud Storage"""

    def __init__(self):
        self.bucket_name = GCS_BUCKET
        self.project = GCS_PROJECT
        self.client = None
        self.bucket = None
        self._initialize()

    def _initialize(self):
        """Initialize GCS client"""
        if not GOOGLE_CLOUD_AVAILABLE:
            log.warning("Google Cloud Storage library not installed")
            return

        try:
            if GCS_CREDENTIALS and os.path.exists(GCS_CREDENTIALS):
                # Use service account credentials
                credentials = service_account.Credentials.from_service_account_file(
                    GCS_CREDENTIALS
                )
                self.client = storage.Client(
                    project=self.project,
                    credentials=credentials
                )
            else:
                # Use default credentials (e.g., gcloud auth or environment)
                self.client = storage.Client(project=self.project)

            self.bucket = self.client.bucket(self.bucket_name)
            log.info(f"✓ GCS initialized: bucket={self.bucket_name}")
        except Exception as e:
            log.warning(f"GCS initialization failed: {e}")
            self.client = None
            self.bucket = None

    def upload_pdf(self, result_id: str, pdf_buffer: BytesIO) -> Optional[str]:
        """
        Upload PDF to GCS and return public URL or None if disabled

        Args:
            result_id: Unique result identifier
            pdf_buffer: BytesIO buffer containing PDF content

        Returns:
            Public URL or signed URL, or None if GCS not available
        """
        if not self.client or not self.bucket:
            log.info("GCS not configured - returning None")
            return None

        try:
            filename = f"test-reports/{result_id}.pdf"
            blob = self.bucket.blob(filename)

            # Upload PDF
            pdf_buffer.seek(0)
            blob.upload_from_file(
                pdf_buffer,
                content_type="application/pdf",
                rewind=True
            )

            log.info(f"✓ PDF uploaded: {filename}")

            # Return signed URL
            url = self.generate_signed_url(result_id)
            return url

        except Exception as e:
            log.error(f"PDF upload failed: {e}")
            return None

    def generate_signed_url(self, result_id: str, expiration_hours: int = 24) -> str:
        """
        Generate signed URL for PDF download

        Args:
            result_id: Unique result identifier
            expiration_hours: URL validity in hours (default 24)

        Returns:
            Signed URL string
        """
        if not self.client or not self.bucket:
            return None

        try:
            filename = f"test-reports/{result_id}.pdf"
            blob = self.bucket.blob(filename)

            # Generate signed URL
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=expiration_hours),
                method="GET"
            )

            log.info(f"✓ Signed URL generated for {filename}")
            return url

        except Exception as e:
            log.error(f"Failed to generate signed URL: {e}")
            return None

    def delete_pdf(self, result_id: str) -> bool:
        """
        Delete PDF from GCS

        Args:
            result_id: Unique result identifier

        Returns:
            True if successful, False otherwise
        """
        if not self.client or not self.bucket:
            return False

        try:
            filename = f"test-reports/{result_id}.pdf"
            blob = self.bucket.blob(filename)
            blob.delete()
            log.info(f"✓ PDF deleted: {filename}")
            return True
        except Exception as e:
            log.error(f"PDF deletion failed: {e}")
            return False

    def list_pdfs(self, limit: int = 100) -> list:
        """
        List all test report PDFs

        Args:
            limit: Maximum number to return

        Returns:
            List of blob names
        """
        if not self.client or not self.bucket:
            return []

        try:
            blobs = self.bucket.list_blobs(prefix="test-reports/", max_results=limit)
            return [blob.name for blob in blobs]
        except Exception as e:
            log.error(f"Failed to list PDFs: {e}")
            return []

    def get_pdf(self, result_id: str) -> Optional[BytesIO]:
        """
        Download PDF from GCS

        Args:
            result_id: Unique result identifier

        Returns:
            BytesIO buffer or None if not found
        """
        if not self.client or not self.bucket:
            return None

        try:
            filename = f"test-reports/{result_id}.pdf"
            blob = self.bucket.blob(filename)

            pdf_buffer = BytesIO()
            blob.download_to_file(pdf_buffer)
            pdf_buffer.seek(0)

            log.info(f"✓ PDF downloaded: {filename}")
            return pdf_buffer

        except Exception as e:
            log.error(f"PDF download failed: {e}")
            return None

    def cleanup_old_pdfs(self, days: int = 30) -> int:
        """
        Delete PDFs older than N days

        Args:
            days: Age threshold in days

        Returns:
            Number of PDFs deleted
        """
        if not self.client or not self.bucket:
            return 0

        try:
            from datetime import datetime, timezone

            deleted_count = 0
            threshold = datetime.now(timezone.utc) - timedelta(days=days)

            blobs = self.bucket.list_blobs(prefix="test-reports/")
            for blob in blobs:
                if blob.time_created < threshold:
                    blob.delete()
                    deleted_count += 1

            log.info(f"✓ Cleaned up {deleted_count} old PDFs")
            return deleted_count

        except Exception as e:
            log.error(f"Cleanup failed: {e}")
            return 0


# Singleton instance
_gcs_manager = None


def get_gcs_manager() -> GCSStorageManager:
    """Get or create GCS manager instance"""
    global _gcs_manager
    if _gcs_manager is None:
        _gcs_manager = GCSStorageManager()
    return _gcs_manager


def test_gcs_integration():
    """Test GCS integration"""
    print("\n" + "=" * 70)
    print("TESTING GCS INTEGRATION")
    print("=" * 70)

    manager = get_gcs_manager()

    if not manager.client:
        print("⚠ GCS not configured (credentials not found)")
        print("  Set GCS_CREDENTIALS environment variable to use GCS")
        print("  Without GCS, PDFs will be generated but not stored")
        return

    print("✓ GCS initialized successfully")

    # Test signed URL generation
    test_id = "test-pdf-123"
    url = manager.generate_signed_url(test_id)
    if url:
        print(f"✓ Signed URL generated: {url[:50]}...")
    else:
        print("✗ Failed to generate signed URL")

    print()


if __name__ == "__main__":
    test_gcs_integration()
