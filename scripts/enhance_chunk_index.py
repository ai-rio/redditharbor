#!/usr/bin/env python3
"""
Enhanced Chunk Index Generator

Analyzes chunks to extract context and create a meaningful index.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import tiktoken


def extract_chunk_context(chunk_text: str, tokenizer, max_preview: int = 200) -> dict:
    """
    Extract meaningful context from a chunk.

    Returns:
        dict with context info
    """
    # Remove YAML frontmatter
    lines = chunk_text.split('\n')
    content_start = 0
    for i, line in enumerate(lines):
        if line.strip() == '---' and i > 0:
            content_start = i + 1
            break

    content = '\n'.join(lines[content_start:])

    # Extract first few paragraphs for preview
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    preview = ' '.join(paragraphs[:3])[:max_preview]

    # Look for key topics/keywords
    content_lower = content.lower()

    topics = []

    # Technical topics
    if any(keyword in content_lower for keyword in ['database', 'schema', 'table', 'sql']):
        topics.append('Database/Schema')

    if any(keyword in content_lower for keyword in ['api', 'endpoint', 'rest', 'http']):
        topics.append('API Development')

    if any(keyword in content_lower for keyword in ['llm', 'ai', 'claude', 'gpt', 'model']):
        topics.append('AI/LLM')

    if any(keyword in content_lower for keyword in ['monetization', 'revenue', 'pricing', 'payment']):
        topics.append('Monetization')

    if any(keyword in content_lower for keyword in ['reddit', 'subreddit', 'post', 'comment']):
        topics.append('Reddit Platform')

    if any(keyword in content_lower for keyword in ['b2b', 'b2c', 'business', 'customer', 'lead']):
        topics.append('Business Strategy')

    if any(keyword in content_lower for keyword in ['git', 'commit', 'branch', 'merge']):
        topics.append('Git/Version Control')

    if any(keyword in content_lower for keyword in ['script', 'python', 'code', 'function']):
        topics.append('Code/Development')

    if any(keyword in content_lower for keyword in ['chunk', 'token', 'analyze', 'process']):
        topics.append('Text Processing')

    # Detect conversation vs technical content
    conversation_indicators = ['i\'ll help', 'let me', 'you asked', 'here\'s', 'perfect', 'excellent']
    technical_indicators = ['create table', 'def ', 'class ', 'import', 'function', 'api', 'schema']

    content_type = 'Mixed'
    if sum(1 for indicator in conversation_indicators if indicator in content_lower) > 3:
        content_type = 'Conversation/Dialogue'
    elif sum(1 for indicator in technical_indicators if indicator in content_lower) > 3:
        content_type = 'Technical/Implementation'

    # Look for specific entities mentioned
    entities = []

    # Files mentioned
    import re
    file_patterns = re.findall(r'[\w\-_\.]+\.(py|md|sql|json|yaml|yml|js|ts)', content)
    if file_patterns:
        entities.extend([f"File: {file}" for file in set(file_patterns[:3])])

    # Tool/library mentions
    tools = re.findall(r'\b(supabase|claude|gpt|python|javascript|typescript|react|next\.js|django|flask)\b', content, re.IGNORECASE)
    if tools:
        entities.extend([f"Tool: {tool.title()}" for tool in set(tools[:3])])

    return {
        'preview': preview,
        'topics': topics or ['General'],
        'content_type': content_type,
        'entities': entities
    }


def enhance_index(chunks_dir: Path, base_name: str) -> None:
    """
    Create an enhanced index with context for each chunk.
    """

    print(f"🔍 Analyzing chunks in: {chunks_dir}")

    # Find all chunk files
    chunk_files = sorted(chunks_dir.glob(f"{base_name}_chunk_*.md"))

    if not chunk_files:
        print(f"❌ No chunk files found for pattern: {base_name}_chunk_*.md")
        return

    print(f"📊 Found {len(chunk_files)} chunks to analyze")

    # Initialize tokenizer
    tokenizer = tiktoken.get_encoding("cl100k_base")

    # Analyze each chunk
    chunks_info = []

    for chunk_file in chunk_files:
        print(f"  📖 Analyzing: {chunk_file.name}")

        try:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"    ❌ Failed to read: {e}")
            continue

        # Extract chunk number from filename
        chunk_num = int(chunk_file.stem.split('_')[-1])

        # Get token count from YAML frontmatter or calculate
        tokens = len(tokenizer.encode(content))

        # Extract context
        context = extract_chunk_context(content, tokenizer)

        chunks_info.append({
            'num': chunk_num,
            'filename': chunk_file.name,
            'tokens': tokens,
            'preview': context['preview'],
            'topics': context['topics'],
            'content_type': context['content_type'],
            'entities': context['entities']
        })

    # Sort by chunk number
    chunks_info.sort(key=lambda x: x['num'])

    # Generate enhanced index
    index_file = chunks_dir / f"{base_name}_enhanced_index.md"

    print(f"📝 Generating enhanced index: {index_file}")

    index_content = f"""# {base_name.replace('_', ' ')} - Enhanced Chunk Index

**Source**: {base_name}.md
**Total Chunks**: {len(chunks_info)}
**Analysis**: AI-powered content extraction
**Generated**: {chunks_info[0]['preview'][:50] if chunks_info else 'N/A'}...

## Content Overview

This document appears to cover the following main topics:
{', '.join(sorted(set(topic for chunk in chunks_info for topic in chunk['topics'])))}

---

## Detailed Chunk Breakdown

"""

    for chunk in chunks_info:
        # Generate topics badge
        topics_badge = " | ".join([f"`{topic}`" for topic in chunk['topics'][:3]])

        # Generate entity list (truncate if too many)
        entities_str = ""
        if chunk['entities']:
            entities_str = "\n  **Mentions**: " + " • ".join(chunk['entities'][:3])
            if len(chunk['entities']) > 3:
                entities_str += f" (+{len(chunk['entities']) - 3} more)"

        index_content += f"""### 📄 Chunk {chunk['num']}: {chunk['content_type']}

**File**: [{chunk['filename']}]({chunk['filename']})
**Tokens**: ~{chunk['tokens']} tokens
**Topics**: {topics_badge}
**Preview**: {chunk['preview']}...{entities_str}

---

"""

    # Add usage recommendations
    index_content += """## 🎯 Usage Recommendations

### For Quick Reference:
- Use chunks based on your topic of interest from the topics list above
- Each chunk preview gives you a sense of the content covered

### For Technical Implementation:
- Look for chunks marked "Technical/Implementation"
- These typically contain code, schemas, or configuration details

### For Strategic Context:
- Look for chunks marked "Conversation/Dialogue"
- These contain decision-making discussions and strategic insights

### For B2B/Lead Generation Content:
- Search for chunks with "Business Strategy" or "Monetization" topics
- These discuss market opportunities and revenue models

### For Database/API Design:
- Look for chunks with "Database/Schema" or "API Development" topics
- These contain technical specifications and implementation details

---

*Generated by RedditHarbor Enhanced Chunk Indexer*
"""

    # Write enhanced index
    try:
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(index_content)
        print(f"✅ Enhanced index saved: {index_file}")
    except Exception as e:
        print(f"❌ Failed to write enhanced index: {e}")
        return

    print(f"🎉 Index enhancement completed!")


def main():
    """Main execution function."""

    # Define paths
    chunks_dir = Path("docs/claude-code-ai/chunks")
    base_name = "Claude Code  Claude"

    if not chunks_dir.exists():
        print(f"❌ Chunks directory not found: {chunks_dir}")
        return 1

    print(f"🚀 Starting enhanced index generation")
    print(f"📁 Chunks directory: {chunks_dir}")
    print(f"📄 Base name: {base_name}")
    print("-" * 50)

    try:
        enhance_index(chunks_dir, base_name)
        return 0
    except Exception as e:
        print(f"❌ Index enhancement failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())