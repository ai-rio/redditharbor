#!/usr/bin/env python3
"""
RedditHarbor Documentation Chunker

Uses semchunk to split large documentation files into LLM-manageable chunks.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import semchunk
import tiktoken


def chunk_documentation(
    input_file: Path,
    output_dir: Path,
    chunk_size: int = 4000,  # tokens, good for most LLMs
    overlap: float = 0.1,    # 10% overlap to maintain context
    encoding: str = "cl100k_base"  # OpenAI's encoding
) -> None:
    """
    Split a documentation file into chunks using semchunk.

    Args:
        input_file: Path to the input documentation file
        output_dir: Directory to save chunk files
        chunk_size: Maximum chunk size in tokens
        overlap: Overlap ratio between chunks (0-1)
        encoding: Tokenizer encoding to use
    """

    print(f"🔧 Loading tokenizer: {encoding}")
    try:
        tokenizer = tiktoken.get_encoding(encoding)
    except Exception as e:
        print(f"❌ Failed to load tokenizer {encoding}: {e}")
        print("🔄 Falling back to cl100k_base")
        tokenizer = tiktoken.get_encoding("cl100k_base")

    print(f"📄 Reading input file: {input_file}")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        print(f"❌ Failed to read file {input_file}: {e}")
        return

    print(f"📊 Text stats:")
    print(f"   - Characters: {len(text):,}")
    print(f"   - Estimated tokens: {len(tokenizer.encode(text)):,}")

    # Create chunker
    print(f"🧩 Creating chunker (size: {chunk_size} tokens, overlap: {overlap*100:.0f}%)")
    chunker = semchunk.chunkerify(tokenizer, chunk_size)

    # Generate chunks
    print("⚡ Generating chunks...")
    try:
        chunks = chunker(text, overlap=overlap)
    except Exception as e:
        print(f"❌ Failed to generate chunks: {e}")
        return

    print(f"✅ Generated {len(chunks)} chunks")

    # Prepare output directory
    output_dir.mkdir(exist_ok=True)

    # Write chunks to files
    base_name = input_file.stem
    for i, chunk in enumerate(chunks, 1):
        chunk_file = output_dir / f"{base_name}_chunk_{i:03d}.md"

        # Add chunk metadata header
        chunk_content = f"""---
chunk: {i}/{len(chunks)}
source: {input_file.name}
tokens: ~{len(tokenizer.encode(chunk))}
---

{chunk}
"""

        try:
            with open(chunk_file, 'w', encoding='utf-8') as f:
                f.write(chunk_content)
        except Exception as e:
            print(f"❌ Failed to write chunk {i}: {e}")
            continue

    print(f"💾 Saved {len(chunks)} chunks to: {output_dir}")

    # Generate summary index
    index_file = output_dir / f"{base_name}_index.md"
    index_content = f"""# {base_name} - Chunk Index

**Source**: {input_file}
**Total Chunks**: {len(chunks)}
**Chunk Size**: {chunk_size} tokens
**Overlap**: {overlap*100:.0f}%

## Chunks

"""

    for i in range(1, len(chunks) + 1):
        chunk_file = f"{base_name}_chunk_{i:03d}.md"
        index_content += f"- [Chunk {i}]({chunk_file}) (~{len(tokenizer.encode(chunks[i-1]))} tokens)\n"

    try:
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(index_content)
        print(f"📋 Created index file: {index_file}")
    except Exception as e:
        print(f"❌ Failed to write index file: {e}")

    print("🎉 Chunking completed successfully!")


def main():
    """Main execution function."""

    # Define paths
    docs_dir = Path("docs/claude-code-ai")
    input_file = docs_dir / "Claude Code  Claude.md"
    output_dir = docs_dir / "chunks"

    # Check if input file exists
    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        print("💡 Make sure the file path is correct")
        return 1

    # Validate parameters
    chunk_size = 4000  # Good for most LLMs
    overlap = 0.1      # 10% overlap maintains context

    print(f"🚀 Starting documentation chunking")
    print(f"📁 Input: {input_file}")
    print(f"📁 Output: {output_dir}")
    print(f"⚙️  Chunk size: {chunk_size} tokens")
    print(f"🔄 Overlap: {overlap*100:.0f}%")
    print("-" * 50)

    # Run chunking
    try:
        chunk_documentation(
            input_file=input_file,
            output_dir=output_dir,
            chunk_size=chunk_size,
            overlap=overlap
        )
        return 0
    except Exception as e:
        print(f"❌ Chunking failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())