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
      4. Normalizes Windows backslashes and benign leading slashes.
    Returns:
      (extracted_files_count, total_bytes_extracted, skipped_paths)
    """
    target_dir = target_dir.resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    
    if isinstance(zip_source, (str, Path)):
        try:
            zf = zipfile.ZipFile(zip_source, "r")
        except zipfile.BadZipFile:
            raise ZipSecurityError("The uploaded file is not a valid or readable ZIP archive.")
    else:
        import io
        try:
            zf = zipfile.ZipFile(io.BytesIO(zip_source), "r")
        except zipfile.BadZipFile:
            raise ZipSecurityError("The uploaded file is not a valid or readable ZIP archive.")
        
    try:
        infolist = zf.infolist()
        if not infolist:
            raise ZipSecurityError("The archive is empty and contains no files.")
        
        # 1. Check file count limit
        if len(infolist) > settings.MAX_FILE_COUNT:
            raise ZipSecurityError(
                f"Archive contains {len(infolist)} entries, exceeding the maximum allowed ({settings.MAX_FILE_COUNT})."
            )
            
        total_extracted_bytes = 0
        extracted_count = 0
        skipped_paths: List[str] = []

        # Normalize filenames (convert backslashes to forward slashes, strip whitespace and leading slashes)
        normalized_entries = []
        for info in infolist:
            norm_name = info.filename.replace("\\", "/").strip().lstrip("/")
            is_dir = info.is_dir() or norm_name.endswith("/")
            normalized_entries.append((info, norm_name, is_dir))

        # Find common root prefix if archive is wrapped in a top-level folder (e.g. repo-main/)
        file_names = [norm for _, norm, is_dir in normalized_entries if not is_dir and norm]
        common_prefix = ""
        if file_names:
            first_parts = [n.split("/", 1)[0] for n in file_names if "/" in n]
            if len(first_parts) == len(file_names) and len(set(first_parts)) == 1:
                common_prefix = first_parts[0] + "/"

        for info, norm_name, is_dir in normalized_entries:
            # Check uncompressed size quota
            total_extracted_bytes += info.file_size
            if total_extracted_bytes > settings.MAX_EXTRACTED_SIZE_BYTES:
                raise ZipSecurityError(
                    f"Extracted archive size exceeds limit of {settings.MAX_EXTRACTED_SIZE_BYTES // (1024 * 1024)} MB."
                )

            # Strip common prefix if present
            if common_prefix and norm_name.startswith(common_prefix):
                rel_path = norm_name[len(common_prefix):]
            else:
                rel_path = norm_name

            # Skip directory entries and empty relative paths
            if not rel_path or is_dir or rel_path.endswith("/"):
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
