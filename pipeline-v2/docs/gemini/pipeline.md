# Comprehensive Architecture Document: LLM-Powered Reddit Idea Generator

## 1\. Executive Summary

This document outlines the technical architecture for a data pipeline designed to extract community discussions from Reddit, transform them into structured application ideas using a Large Language Model (LLM), and store them for analysis.

The system utilizes a modern **ELT (Extract, Load, Transform)** pattern, prioritizing data integrity, type safety, and infrastructure simplicity by leveraging **Supabase** as a unified storage solution and a robust **Python** tech stack.

-----

## 2\. 🏗️ Architecture Overview

The pipeline is designed to be resilient and modular, separating the unstable extraction of data from the intelligent transformation process.

### The ELT Workflow

1.  **Extract (E):** Raw data is fetched from the **Reddit API**.
2.  **Staging (L):** Raw text is cleaned and stored immediately in a **Staging Area**. This is a critical "pro" step that prevents data loss if the LLM step fails and allows for deduplication before processing.
3.  **Transform (T):** The **LLM Agent** reads the staged data, analyzes it, and generates structured "Idea" objects (Title, Problem, Feature, Sentiment).
4.  **Load (L):** Validated, structured ideas are written to the final **Supabase** database.

### System Diagram

```mermaid
graph LR
    subgraph 1. Extraction
        A[Reddit API] -->|Raw JSON| B{PRAW Client};
    end

    subgraph 2. Staging Layer
        B -->|Cleaned Text| C[Staging Area];
        C -.->|Deduplication| C;
        note[Resilience Checkpoint]
    end

    subgraph 3. Transformation Engine
        C -->|Batch Input| D[LLM Agent];
        D -->|Validation| E{Pydantic + Instructor};
        E -- Schema Enforced --> F((Structured Object));
    end

    subgraph 4. Supabase Storage
        F --> G{SQLAlchemy ORM};
        G -->|Transactional Write| H[(PostgreSQL)];
        G -->|Vector Write| I[(pgvector)];
    end

    style A fill:#FF4500,stroke:#333,stroke-width:2px
    style C fill:#E0E0E0,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
    style E fill:#0077B6,stroke:#333,stroke-width:2px,color:white
    style H fill:#3ECF8E,stroke:#333,stroke-width:2px,color:white
    style I fill:#3ECF8E,stroke:#333,stroke-width:2px,color:white
```

-----

## 3\. ⚡ Supabase & Storage Strategy

**Supabase** serves as the unified storage layer, dramatically simplifying the architecture by combining relational data and vector embeddings in a single instance.

  * **Unified Database (PostgreSQL):** Supabase provides a standard PostgreSQL environment. You will store the structured idea data (e.g., `title`, `sentiment_score`) in standard relational tables.
  * **Vector Engine (`pgvector`):** Instead of adding a complex second database (like Chroma or Pinecone), we enable the `pgvector` extension within Supabase.
      * **Benefit:** This allows you to store the semantic embedding of an idea (for search) in the *same row* as the idea itself.
      * **Querying:** You can perform hybrid queries (e.g., "Find ideas similar to 'finance tool' AND have a sentiment score \> 8") in a single SQL query.
  * **Connection:** The pipeline connects to Supabase using standard PostgreSQL connection strings (`postgresql://user:pass@host:port/db`), requiring no proprietary API calls for basic writes.

-----

## 4\. 🐍 Python Modules & Tech Stack

The Python ecosystem is selected to enforce **strict typing** and **schema validation**, turning the unpredictable nature of LLMs into reliable engineering.

### A. Environment & Package Management: `uv`

  * **Role:** Replaces `pip` and `virtualenv`.
  * **Why:** It is 10-100x faster than standard tools. It manages the project dependencies and virtual environments efficiently, speeding up Docker builds and local development.

### B. Extraction: `PRAW`

  * **Role:** The **P**ython **R**eddit **A**PI **W**rapper.
  * **Why:** Handles the complexity of Reddit's API authentication (OAuth), rate limiting, and pagination automatically.

### C. Transformation & Validation (The "Pro" Stack)

This combination is the secret to preventing write failures.

  * **`Pydantic` (The Contract):** You define the *exact* shape of the data you want in Python.
    ```python
    class AppIdea(BaseModel):
        title: str
        problem: str
        sentiment_score: int
    ```
  * **`Instructor` (The Enforcer):** A library that wraps the LLM client. It forces the LLM to output JSON that matches your `Pydantic` model. If the LLM tries to output a string for `sentiment_score` instead of an integer, Instructor catches it and asks the LLM to correct itself *before* your code crashes.

### D. Database Interaction: `SQLAlchemy`

  * **Role:** The Object-Relational Mapper (ORM).
  * **Why:** It translates your Pydantic objects into SQL commands.
      * **Transaction Safety:** It allows you to wrap writes in a transaction (`session.commit()`). If one record in a batch fails, the whole batch rolls back, preventing partial/corrupt data.
      * **UPSERT Logic:** It enables "On Conflict Do Update" logic. If the pipeline runs twice on the same Reddit thread, SQLAlchemy can update the existing record instead of crashing with a "Duplicate Key" error.

-----

## 5\. 🛡️ Best Practices for Reliability

### Fixing Write Failures

If the connection to Supabase is healthy but writes are failing, the cause is almost certainly **Schema Mismatch**.

  * **Diagnosis:** The LLM is likely generating a field that violates a database constraint (e.g., a `NULL` value in a non-nullable column).
  * **Fix:** Use **Instructor** to enforce the schema rigidly.

### The "Pro" Workflow

1.  **Stage First:** Always dump the raw LLM output to a file or staging table before the final write. This creates a "save point."
2.  **Validate:** Ensure the Pydantic model matches the SQLAlchemy model 1:1.
3.  **Batch:** Use `session.add_all()` for performance.
4.  **Upsert:** Never just `INSERT`; always use logic that handles duplicates gracefully.