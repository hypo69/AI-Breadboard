# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Image Metadata Manager for PixelRAG
# =============================================================================
# Description:
#   Comprehensive metadata management for indexed images including:
#   - Version tracking (similar images)
#   - Source tracking (origin of image)
#   - Deduplication (remove similar images)
#   - EXIF data extraction
#   - Perceptual hashing for duplicate detection
#
# File: image_metadata.py
# Project: ai-breadboard
# Package: src.rag.pixel
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

try:
    from PIL import Image
    from PIL.Image import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ImageSource:
    """
    ## hypo69 docblock
    Source information for an image.

    Attributes:
        source_type: 'local_file', 'pdf_page', 'web_url', 'screenshot'
        source_path: Path or URL to original source
        source_metadata: Additional source-specific metadata
    """
    source_type: str  # local_file, pdf_page, web_url, screenshot
    source_path: str
    source_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImageVersion:
    """
    ## hypo69 docblock
    Version information for an image.

    Attributes:
        version: Version number (1-based)
        created_at: Timestamp when version was indexed
        content_hash: SHA-256 hash of image content
        size_bytes: Image file size
        dimensions: (width, height) in pixels
        format: Image format (PNG, JPG, etc)
    """
    version: int
    created_at: float
    content_hash: str
    size_bytes: int
    dimensions: Tuple[int, int]
    format: str


@dataclass
class ImageMetadata:
    """
    ## hypo69 docblock
    Complete metadata for an indexed image.

    Attributes:
        image_id: Unique identifier for image
        filename: Original filename
        source: Source information
        versions: List of versions (for duplicate tracking)
        embedding_id: Reference to CLIP embedding
        perceptual_hash: Perceptual hash for duplicate detection
        exif_data: EXIF metadata (if available)
        tags: User-assigned tags
        created_at: When first indexed
        updated_at: When last updated
        is_latest: Whether this is latest version
    """
    image_id: str
    filename: str
    source: ImageSource
    versions: List[ImageVersion] = field(default_factory=list)
    embedding_id: Optional[str] = None
    perceptual_hash: Optional[str] = None
    exif_data: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = field(default_factory=lambda: datetime.now().timestamp())
    is_latest: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['source'] = asdict(self.source)
        data['versions'] = [asdict(v) for v in self.versions]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ImageMetadata:
        """Create from dictionary."""
        source_data = data.pop('source', {})
        source = ImageSource(**source_data)
        
        versions_data = data.pop('versions', [])
        versions = [ImageVersion(**v) for v in versions_data]
        
        return cls(source=source, versions=versions, **data)


class ImageMetadataManager:
    """
    ## hypo69 docblock
    Manages metadata for indexed images.

    Features:
    - Version tracking (similar images)
    - Source tracking (origin of image)
    - Deduplication (remove similar images)
    - Perceptual hashing for duplicate detection
    - EXIF data extraction
    """

    def __init__(self, metadata_dir: Path = Path("data/image_metadata")):
        """
        ## hypo69 docblock
        Initialize metadata manager.

        Args:
            metadata_dir: Directory for storing metadata
        """
        self.metadata_dir = Path(metadata_dir)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        self.metadata_file = self.metadata_dir / "images_metadata.jsonl"
        self.index_file = self.metadata_dir / "index.json"
        
        self._metadata: Dict[str, ImageMetadata] = {}
        self._load_metadata()

    def _load_metadata(self) -> None:
        """Load metadata from disk."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            meta = ImageMetadata.from_dict(data)
                            self._metadata[meta.image_id] = meta
                logger.info(f"Loaded metadata for {len(self._metadata)} images")
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")

    def _save_metadata(self) -> None:
        """Save metadata to disk."""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                for meta in self._metadata.values():
                    f.write(json.dumps(meta.to_dict(), ensure_ascii=False) + '\n')
            logger.info(f"Saved metadata for {len(self._metadata)} images")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    def add_image(
        self,
        image_path: str | Path,
        source_type: str = "local_file",
        source_metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> ImageMetadata:
        """
        ## hypo69 docblock
        Add image metadata.

        Args:
            image_path: Path to image file
            source_type: Type of source
            source_metadata: Additional source info
            tags: User tags for image

        Returns:
            ImageMetadata: Created metadata record
        """
        image_path = Path(image_path)
        
        # Read image to get properties
        if not PIL_AVAILABLE:
            raise ImportError("PIL required for image metadata")
        
        img = Image.open(image_path)
        width, height = img.size
        format_name = img.format or 'UNKNOWN'
        
        # Compute hashes
        image_bytes = image_path.read_bytes()
        content_hash = hashlib.sha256(image_bytes).hexdigest()
        perceptual_hash = self._compute_perceptual_hash(image_path)
        
        # Check for duplicates
        duplicate_ids = self._find_duplicates(perceptual_hash)
        
        # Extract EXIF data
        exif_data = self._extract_exif(img)
        
        # Generate ID
        image_id = f"{image_path.stem}_{content_hash[:8]}"
        
        # Check if already exists
        if image_id in self._metadata:
            existing = self._metadata[image_id]
            existing.updated_at = datetime.now().timestamp()
            return existing
        
        # Create new metadata
        source = ImageSource(
            source_type=source_type,
            source_path=str(image_path),
            source_metadata=source_metadata or {}
        )
        
        version = ImageVersion(
            version=1,
            created_at=datetime.now().timestamp(),
            content_hash=content_hash,
            size_bytes=len(image_bytes),
            dimensions=(width, height),
            format=format_name
        )
        
        metadata = ImageMetadata(
            image_id=image_id,
            filename=image_path.name,
            source=source,
            versions=[version],
            perceptual_hash=perceptual_hash,
            exif_data=exif_data,
            tags=tags or [],
            is_latest=True
        )
        
        # Store duplicates info
        if duplicate_ids:
            metadata.tags.extend([f"duplicate_of:{did}" for did in duplicate_ids])
        
        self._metadata[image_id] = metadata
        self._save_metadata()
        
        logger.info(f"Added metadata for {image_path.name} (id={image_id})")
        return metadata

    def get_metadata(self, image_id: str) -> Optional[ImageMetadata]:
        """
        ## hypo69 docblock
        Get metadata for image.

        Args:
            image_id: Image identifier

        Returns:
            ImageMetadata or None if not found
        """
        return self._metadata.get(image_id)

    def update_version(
        self,
        image_id: str,
        image_path: str | Path,
        source_metadata: Optional[Dict[str, Any]] = None
    ) -> ImageMetadata:
        """
        ## hypo69 docblock
        Update image to new version (for changed images).

        Args:
            image_id: Image identifier
            image_path: New image file path
            source_metadata: New source metadata

        Returns:
            Updated ImageMetadata
        """
        if image_id not in self._metadata:
            raise ValueError(f"Image {image_id} not found")
        
        metadata = self._metadata[image_id]
        
        # Mark old versions as not latest
        for v in metadata.versions:
            # Keep version info but track latest
            pass
        
        # Read new image
        image_path = Path(image_path)
        if not PIL_AVAILABLE:
            raise ImportError("PIL required for image metadata")
        
        img = Image.open(image_path)
        image_bytes = image_path.read_bytes()
        
        # Create new version
        content_hash = hashlib.sha256(image_bytes).hexdigest()
        new_version = ImageVersion(
            version=len(metadata.versions) + 1,
            created_at=datetime.now().timestamp(),
            content_hash=content_hash,
            size_bytes=len(image_bytes),
            dimensions=img.size,
            format=img.format or 'UNKNOWN'
        )
        
        metadata.versions.append(new_version)
        metadata.updated_at = datetime.now().timestamp()
        metadata.is_latest = True
        
        if source_metadata:
            metadata.source.source_metadata.update(source_metadata)
        
        self._save_metadata()
        logger.info(f"Updated {image_id} to version {new_version.version}")
        
        return metadata

    def _compute_perceptual_hash(self, image_path: Path) -> str:
        """
        ## hypo69 docblock
        Compute perceptual hash for image (for duplicate detection).

        Uses simple approach: resize to 8x8, convert to grayscale, compare to average.

        Args:
            image_path: Path to image

        Returns:
            Hex string of perceptual hash
        """
        if not PIL_AVAILABLE:
            return ""
        
        try:
            img = Image.open(image_path)
            
            # Resize to 8x8 grayscale
            img = img.convert('L').resize((8, 8))
            pixels = np.array(img).flatten()
            
            # Compare to average
            avg = np.mean(pixels)
            hash_bits = (pixels > avg).astype(int)
            
            # Convert to hex
            hash_int = int(''.join(map(str, hash_bits)), 2)
            return f"{hash_int:016x}"
        except Exception as e:
            logger.warning(f"Failed to compute perceptual hash: {e}")
            return ""

    def _find_duplicates(self, perceptual_hash: str, threshold: float = 0.95) -> List[str]:
        """
        ## hypo69 docblock
        Find duplicate images using perceptual hash similarity.

        Args:
            perceptual_hash: Hash to compare
            threshold: Similarity threshold (0-1)

        Returns:
            List of duplicate image IDs
        """
        if not perceptual_hash:
            return []
        
        duplicates: List[str] = []
        
        for image_id, meta in self._metadata.items():
            if not meta.perceptual_hash:
                continue
            
            # Hamming distance
            similarity = self._hamming_similarity(
                perceptual_hash,
                meta.perceptual_hash
            )
            
            if similarity >= threshold:
                duplicates.append(image_id)
        
        return duplicates

    @staticmethod
    def _hamming_similarity(hash1: str, hash2: str) -> float:
        """
        ## hypo69 docblock
        Compute similarity between two hashes (0-1).

        Args:
            hash1: First hash
            hash2: Second hash

        Returns:
            Similarity score
        """
        if not hash1 or not hash2 or len(hash1) != len(hash2):
            return 0.0
        
        matches = sum(c1 == c2 for c1, c2 in zip(hash1, hash2))
        return matches / len(hash1)

    def _extract_exif(self, img: PILImage) -> Dict[str, Any]:
        """
        ## hypo69 docblock
        Extract EXIF metadata from image.

        Args:
            img: PIL Image object

        Returns:
            Dictionary of EXIF data
        """
        if not PIL_AVAILABLE:
            return {}
        
        try:
            exif_data = {}
            
            if hasattr(img, '_getexif') and img._getexif() is not None:
                from PIL.ExifTags import TAGS
                exif = img._getexif()
                
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    try:
                        exif_data[tag] = str(value)
                    except:
                        pass
            
            return exif_data
        except Exception as e:
            logger.debug(f"Failed to extract EXIF: {e}")
            return {}

    def find_similar(self, image_id: str, threshold: float = 0.85) -> List[Tuple[str, float]]:
        """
        ## hypo69 docblock
        Find similar images to a given image.

        Args:
            image_id: Image identifier
            threshold: Similarity threshold

        Returns:
            List of (image_id, similarity) tuples
        """
        if image_id not in self._metadata:
            return []
        
        query_meta = self._metadata[image_id]
        if not query_meta.perceptual_hash:
            return []
        
        similar: List[Tuple[str, float]] = []
        
        for other_id, other_meta in self._metadata.items():
            if other_id == image_id or not other_meta.perceptual_hash:
                continue
            
            similarity = self._hamming_similarity(
                query_meta.perceptual_hash,
                other_meta.perceptual_hash
            )
            
            if similarity >= threshold:
                similar.append((other_id, similarity))
        
        return sorted(similar, key=lambda x: x[1], reverse=True)

    def deduplicate(self, threshold: float = 0.95) -> Dict[str, List[str]]:
        """
        ## hypo69 docblock
        Find and organize duplicate images.

        Args:
            threshold: Similarity threshold for duplicates

        Returns:
            Dictionary mapping master image to duplicates
        """
        duplicates: Dict[str, List[str]] = {}
        processed: Set[str] = set()
        
        for image_id, meta in self._metadata.items():
            if image_id in processed:
                continue
            
            similar = self.find_similar(image_id, threshold=threshold)
            if similar:
                similar_ids = [sid for sid, _ in similar]
                duplicates[image_id] = similar_ids
                processed.add(image_id)
                processed.update(similar_ids)
        
        return duplicates

    def get_statistics(self) -> Dict[str, Any]:
        """
        ## hypo69 docblock
        Get statistics about indexed images.

        Returns:
            Dictionary of statistics
        """
        if not self._metadata:
            return {
                "total_images": 0,
                "total_versions": 0,
                "total_size_bytes": 0,
                "unique_sources": 0
            }
        
        total_size = sum(
            sum(v.size_bytes for v in meta.versions)
            for meta in self._metadata.values()
        )
        
        sources = {meta.source.source_type for meta in self._metadata.values()}
        
        return {
            "total_images": len(self._metadata),
            "total_versions": sum(len(meta.versions) for meta in self._metadata.values()),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "unique_sources": len(sources),
            "source_types": list(sources),
            "images_by_format": self._count_by_format(),
            "images_with_exif": sum(
                1 for meta in self._metadata.values()
                if meta.exif_data
            ),
        }

    def _count_by_format(self) -> Dict[str, int]:
        """Count images by format."""
        counts: Dict[str, int] = {}
        for meta in self._metadata.values():
            if meta.versions:
                fmt = meta.versions[-1].format
                counts[fmt] = counts.get(fmt, 0) + 1
        return counts

    def cleanup(self) -> None:
        """Save metadata and cleanup resources."""
        self._save_metadata()
        logger.info("ImageMetadataManager cleanup complete")


# Singleton instance
_metadata_manager: Optional[ImageMetadataManager] = None


def get_image_metadata_manager(metadata_dir: Path = None) -> ImageMetadataManager:
    """
    ## hypo69 docblock
    Get or create singleton ImageMetadataManager.

    Args:
        metadata_dir: Optional directory for metadata (used on first call)

    Returns:
        ImageMetadataManager singleton
    """
    global _metadata_manager
    if _metadata_manager is None:
        _metadata_manager = ImageMetadataManager(
            metadata_dir or Path("data/image_metadata")
        )
    return _metadata_manager
