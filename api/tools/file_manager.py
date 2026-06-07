"""File Manager — Read/write/zip project output files."""

import io
import os
import zipfile
from pathlib import Path
from typing import Optional

import aiofiles
import structlog

log = structlog.get_logger()


class FileManager:
    """Manages file I/O for generated project outputs."""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)

    def get_session_dir(self, session_id: str) -> Path:
        return self.output_dir / session_id

    async def write_file(self, session_id: str, file_path: str, content: str) -> Path:
        """Write content to a file, creating parent dirs as needed."""
        full_path = self.get_session_dir(session_id) / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
            await f.write(content)
        log.debug("file_written", path=str(full_path))
        return full_path

    async def read_file(self, session_id: str, file_path: str) -> Optional[str]:
        """Read file content, return None if not found."""
        full_path = self.get_session_dir(session_id) / file_path
        if not full_path.exists():
            return None
        async with aiofiles.open(full_path, "r", encoding="utf-8") as f:
            return await f.read()

    async def list_files(self, session_id: str) -> list[dict]:
        """List all files in a session's output directory."""
        session_dir = self.get_session_dir(session_id)
        if not session_dir.exists():
            return []

        files = []
        for root, dirs, filenames in os.walk(session_dir):
            for filename in filenames:
                full = Path(root) / filename
                rel = full.relative_to(session_dir)
                files.append({
                    "path": str(rel).replace("\\", "/"),
                    "size_bytes": full.stat().st_size,
                    "extension": full.suffix,
                })
        return files

    async def create_zip(self, session_id: str) -> bytes:
        """Create a ZIP archive of all session output files."""
        session_dir = self.get_session_dir(session_id)
        if not session_dir.exists():
            raise FileNotFoundError(f"No output for session {session_id}")

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, filenames in os.walk(session_dir):
                for filename in filenames:
                    full = Path(root) / filename
                    arc_name = full.relative_to(session_dir)
                    zf.write(full, arc_name)

        return buffer.getvalue()

    async def delete_session_files(self, session_id: str) -> None:
        """Delete all files for a session."""
        import shutil
        session_dir = self.get_session_dir(session_id)
        if session_dir.exists():
            shutil.rmtree(session_dir)
