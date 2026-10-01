# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Image Metadata
# =============================================================================
# Description:
#   Tests for ImageMetadataManager - image metadata tracking, versioning, and deduplication.
#
# Usage Examples:
#   CLI:
#     python -m tests.test_image_metadata
#   Python API:
#     from tests.test_image_metadata import TestImageMetadataManager
#
#     service = TestImageMetadataManager()
#
# File: test_image_metadata.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Tests for ImageMetadataManager - image metadata tracking, versioning, and deduplication.

Tests:
- Metadata creation and retrieval
- Version tracking for image updates
- Perceptual hashing and duplicate detection
- Source type tracking
- EXIF data extraction
- Statistics and analysis"""

import json
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
import pytest
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

@pytest.mark.skipif(not PIL_AVAILABLE, reason='PIL not available')
class TestImageMetadataManager:
    """Test suite for ImageMetadataManager."""

    @pytest.fixture
    def temp_metadata_dir(self):
        """Create temporary metadata directory."""
        with TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def manager(self, temp_metadata_dir):
        """Create ImageMetadataManager instance."""
        from src.rag.pixel.image_metadata import ImageMetadataManager
        return ImageMetadataManager(metadata_dir=temp_metadata_dir)

    def create_test_image(self, path: Path, width: int=100, height: int=100) -> None:
        """Create a simple test image."""
        img = Image.new('RGB', (width, height), color='red')
        img.save(path)

    def test_add_image(self, manager, temp_metadata_dir):
        """Test adding an image."""
        image_path = temp_metadata_dir / 'test.png'
        self.create_test_image(image_path)
        metadata = manager.add_image(image_path=image_path, source_type='local_file', tags=['test', 'demo'])
        assert metadata.image_id
        assert metadata.filename == 'test.png'
        assert metadata.source.source_type == 'local_file'
        assert 'test' in metadata.tags

    def test_get_metadata(self, manager, temp_metadata_dir):
        """Test retrieving metadata."""
        image_path = temp_metadata_dir / 'test.png'
        self.create_test_image(image_path)
        added = manager.add_image(image_path)
        retrieved = manager.get_metadata(added.image_id)
        assert retrieved is not None
        assert retrieved.filename == added.filename

    def test_version_tracking(self, manager, temp_metadata_dir):
        """Test version tracking for image updates."""
        image_v1 = temp_metadata_dir / 'image_v1.png'
        self.create_test_image(image_v1, width=100, height=100)
        meta_v1 = manager.add_image(image_v1)
        assert len(meta_v1.versions) == 1
        assert meta_v1.versions[0].version == 1
        image_v2 = temp_metadata_dir / 'image_v2.png'
        self.create_test_image(image_v2, width=200, height=200)
        meta_v2 = manager.update_version(meta_v1.image_id, image_v2)
        assert len(meta_v2.versions) == 2
        assert meta_v2.versions[-1].version == 2

    def test_perceptual_hash_computation(self, manager, temp_metadata_dir):
        """Test perceptual hash computation."""
        image_path = temp_metadata_dir / 'test.png'
        self.create_test_image(image_path)
        metadata = manager.add_image(image_path)
        assert metadata.perceptual_hash is not None
        assert isinstance(metadata.perceptual_hash, str)
        assert len(metadata.perceptual_hash) > 0

    def test_duplicate_detection(self, manager, temp_metadata_dir):
        """Test finding duplicate/similar images."""
        img1_path = temp_metadata_dir / 'image1.png'
        img2_path = temp_metadata_dir / 'image2.png'
        self.create_test_image(img1_path)
        self.create_test_image(img2_path)
        meta1 = manager.add_image(img1_path)
        meta2 = manager.add_image(img2_path)
        similar = manager.find_similar(meta1.image_id, threshold=0.9)
        assert isinstance(similar, list)

    def test_source_type_tracking(self, manager, temp_metadata_dir):
        """Test tracking different source types."""
        image_path = temp_metadata_dir / 'test.png'
        self.create_test_image(image_path)
        for source_type in ['local_file', 'pdf_page', 'web_url', 'screenshot']:
            metadata = manager.add_image(image_path, source_type=source_type, source_metadata={'test': 'metadata'})
            assert metadata.source.source_type == source_type
            assert metadata.source.source_metadata.get('test') == 'metadata'

    def test_exif_extraction(self, manager, temp_metadata_dir):
        """Test EXIF data extraction."""
        image_path = temp_metadata_dir / 'test.png'
        self.create_test_image(image_path)
        metadata = manager.add_image(image_path)
        assert isinstance(metadata.exif_data, dict)

    def test_statistics(self, manager, temp_metadata_dir):
        """Test statistics calculation."""
        for i in range(3):
            img_path = temp_metadata_dir / f'image_{i}.png'
            self.create_test_image(img_path)
            manager.add_image(img_path)
        stats = manager.get_statistics()
        assert stats['total_images'] == 3
        assert stats['total_versions'] >= 3
        assert stats['total_size_bytes'] > 0

    def test_metadata_persistence(self, manager, temp_metadata_dir):
        """Test metadata persistence to disk."""
        image_path = temp_metadata_dir / 'test.png'
        self.create_test_image(image_path)
        meta = manager.add_image(image_path)
        manager._save_metadata()
        assert manager.metadata_file.exists()

    def test_hamming_similarity(self, manager):
        """Test Hamming similarity calculation."""
        hash1 = '1010101010101010'
        hash2 = '1010101010101010'
        similarity = manager._hamming_similarity(hash1, hash2)
        assert similarity == 1.0
        hash3 = '0000000000000000'
        similarity = manager._hamming_similarity(hash1, hash3)
        assert similarity == 0.0

    def test_deduplicate(self, manager, temp_metadata_dir):
        """Test deduplication analysis."""
        for i in range(3):
            img_path = temp_metadata_dir / f'image_{i}.png'
            self.create_test_image(img_path)
            manager.add_image(img_path)
        duplicates = manager.deduplicate(threshold=0.85)
        assert isinstance(duplicates, dict)

    def test_invalid_image_id(self, manager):
        """Test handling of invalid image IDs."""
        metadata = manager.get_metadata('nonexistent_image_id')
        assert metadata is None

    def test_singleton_pattern(self):
        """Test singleton pattern."""
        from src.rag.pixel.image_metadata import get_image_metadata_manager
        manager1 = get_image_metadata_manager()
        manager2 = get_image_metadata_manager()
        assert manager1 is manager2
if __name__ == '__main__':
    print('ImageMetadataManager Tests')
    print('=' * 50)
    try:
        from src.rag.pixel.image_metadata import ImageMetadataManager
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as temp_dir:
            manager = ImageMetadataManager(metadata_dir=Path(temp_dir))
            from PIL import Image
            img_path = Path(temp_dir) / 'test.png'
            img = Image.new('RGB', (100, 100), color='red')
            img.save(img_path)
            meta = manager.add_image(img_path)
            print(f'✓ Added image: {meta.image_id}')
            retrieved = manager.get_metadata(meta.image_id)
            print(f'✓ Retrieved metadata: {retrieved.filename}')
            stats = manager.get_statistics()
            print(f"✓ Statistics: {stats['total_images']} images")
            print('\n✓ All basic tests passed')
    except Exception as e:
        print(f'✗ Error: {e}')
        import traceback
        traceback.print_exc()