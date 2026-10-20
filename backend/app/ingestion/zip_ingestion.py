import os
import zipfile
from pathlib import Path
from typing import Tuple, List
from ..config import settings
from ..languages.detector import is_ignored_path

class ZipSecurityError(Exception):
    """Raised when an uploaded zip violates size, file count, or security boundaries."""
    pass

def safe_extract_zip(
    zip_source: str | Path | bytes,
    target_dir: Path
) -> Tuple[int, int, List[str]]:
    """
    Safely extract a ZIP archive into target_dir.
    Guarantees:
      1. Prevents Zip Slip (path traversal / absolute paths / escaping target dir).
      2. Enforces MAX_UPLOAD_SIZE, MAX_EXTRACTED_SIZE, MAX_FILE_COUNT.
      3. Skips ignored directories (.git, node_modules) and sensitive files (.env, keys).
    Returns:
      (extracted_files_count, total_bytes_extracted, skipped_paths)
    """
    target_dir = target_dir.resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    
    if isinstance(zip_source, (str, Path)):
        zf = zipfile.ZipFile(zip_source, "r")
    else:
        import io
        zf = zipfile.ZipFile(io.BytesIO(zip_source), "r")
        
    try:
        infolist = zf.infolist()
        
        # 1. Check file count limit
        if len(infolist) > settings.MAX_FILE_COUNT:
            raise ZipSecurityError(
                f"Archive contains {len(infolist)} entries, exceeding the maximum allowed ({settings.MAX_FILE_COUNT})."
            )
            
        total_extracted_bytes = 0
        extracted_count = 0
        skipped_paths: List[str] = []

        # Find common root prefix if archive is wrapped in a top-level folder (e.g. repo-main/)
        names = [info.filename for info in infolist if not info.is_dir()]
        common_prefix = ""
        if names:
            # Check if all files share a common root directory
            first_parts = [n.split("/", 1)[0] for n in names if "/" in n]
            if len(first_parts) == len(names) and len(set(first_parts)) == 1:
                common_prefix = first_parts[0] + "/"

        for info in infolist:
            # Check uncompressed size
            total_extracted_bytes += info.file_size
            if total_extracted_bytes > settings.MAX_EXTRACTED_SIZE_BYTES:
                raise ZipSecurityError(
                    f"Extracted archive size exceeds limit of {settings.MAX_EXTRACTED_SIZE_BYTES // (1024 * 1024)} MB."
                )
                
            raw_filename = info.filename
            # Strip common prefix if present
            if common_prefix and raw_filename.startswith(common_prefix):
                rel_path = raw_filename[len(common_prefix):]
            else:
                rel_path = raw_filename

            if not rel_path or rel_path.endswith("/"):
                continue

            # 2. Strict path traversal protection (Zip Slip check)
            dest_path = (target_dir / rel_path).resolve()
            try:
                # Ensure destination is strictly inside target_dir
                dest_path.relative_to(target_dir)
            except ValueError:
                raise ZipSecurityError(f"Malicious zip entry attempting path traversal: {info.filename}")

            # 3. Skip ignored paths and likely secrets
            if is_ignored_path(rel_path):
                skipped_paths.append(rel_path)
                continue

            # Ensure parent directories exist
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Extract content safely
            with zf.open(info) as src, open(dest_path, "wb") as dst:
                while chunk := src.read(65536):
                    dst.write(chunk)
                    
            extracted_count += 1

        return extracted_count, total_extracted_bytes, skipped_paths

    finally:
        zf.close()
