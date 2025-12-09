"""
Pipeline v3 - Clean Reddit Data Processing Pipeline

A minimal, type-safe Reddit data extraction and analysis pipeline following ELT pattern:
Extract → Load → Transform

Features:
- PRAW for Reddit API access
- Pydantic + Instructor for LLM output validation
- SQLAlchemy with pgvector for unified storage
- Transaction safety and comprehensive error handling
"""

__version__ = "3.0.0"
