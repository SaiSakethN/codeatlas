"""Symbol-aware code chunking."""

import hashlib

from codeatlas.models import CodeChunk, ParsedFile

MAX_CHUNK_LINES = 80
OVERLAP_LINES = 10


def create_chunks(
    parsed: ParsedFile,
    repository: str,
) -> list[CodeChunk]:
    """Create searchable code chunks with source metadata."""

    chunks = []

    def append_chunks(
        content: str,
        start_line: int,
        symbol_name: str,
        symbol_type: str,
    ) -> None:
        lines = content.splitlines()
        step = MAX_CHUNK_LINES - OVERLAP_LINES

        for offset in range(0, len(lines), step):
            segment = lines[offset : offset + MAX_CHUNK_LINES]

            if not any(line.strip() for line in segment):
                continue

            start = start_line + offset
            end = start + len(segment) - 1

            key = f"{repository}:{parsed.file_path}:{symbol_name}:{start}:{end}"

            chunk_id = hashlib.sha256(key.encode()).hexdigest()

            chunks.append(
                CodeChunk(
                    chunk_id=chunk_id,
                    repository=repository,
                    file_path=parsed.file_path,
                    content="\n".join(segment),
                    start_line=start,
                    end_line=end,
                    symbol_name=symbol_name,
                    symbol_type=symbol_type,
                )
            )

            if offset + MAX_CHUNK_LINES >= len(lines):
                break

    for symbol in parsed.symbols:
        append_chunks(
            symbol.source,
            symbol.start_line,
            symbol.name,
            symbol.kind,
        )

    append_chunks(
        parsed.source,
        1,
        "<module>",
        "module",
    )

    return chunks
