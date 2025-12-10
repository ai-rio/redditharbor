# SQLModel Loader Architecture

## Component Diagram

```mermaid
graph TB
    subgraph "Pipeline V4"
        Pipeline[Pipeline Orchestrator]
        Factory[Loader Factory]
    end

    subgraph "Loaders"
        Postgres[PostgresLoader<br/>psycopg2]
        SQLModel[SQLModelLoader<br/>SQLModel ORM]
    end

    subgraph "Database Layer"
        Sessions[database.py<br/>Session Management]
        Engine[SQLAlchemy Engine<br/>Connection Pool]
        Models[models/analysis.py<br/>Opportunity Model]
    end

    subgraph "PostgreSQL"
        DB[(opportunities table)]
    end

    subgraph "Configuration"
        Settings[config/settings.py<br/>Feature Flag]
    end

    Pipeline --> Factory
    Factory --> Settings
    Settings -.->|use_sqlmodel_loader| Factory
    Factory --> Postgres
    Factory --> SQLModel
    Postgres --> DB
    SQLModel --> Sessions
    Sessions --> Engine
    Sessions --> Models
    Models --> DB
```

## Class Hierarchy

```mermaid
classDiagram
    class BaseLoader {
        <<interface>>
        +save_opportunity(opportunity: Opportunity) bool
        +save_opportunities(opportunities: List) int
        +get_opportunity(id: str) Opportunity?
        +close()
    }

    class PostgresLoader {
        -pool: psycopg2.pool.SimpleConnectionPool
        +__init__(settings)
        +save_opportunity(opportunity) bool
        +close()
    }

    class SQLModelLoader {
        -settings: Settings
        +__init__(settings)
        +save_opportunity(opportunity) bool
        +save_opportunities(opportunities) int
        +get_opportunity(submission_id) Opportunity?
        +get_opportunities_by_subreddit(subreddit) List
        +_prepare_opportunity(analysis) Opportunity
        +_handle_database_error(error, operation)
        +close()
    }

    class LoaderFactory {
        +get_loader(settings) BaseLoader
    }

    BaseLoader <|-- PostgresLoader
    BaseLoader <|-- SQLModelLoader
    LoaderFactory --> BaseLoader
```

## Session Management Flow

```mermaid
sequenceDiagram
    participant Client as Pipeline Orchestrator
    participant Factory as Loader Factory
    participant Loader as SQLModelLoader
    participant DB as database.py
    participant Session as SQLModel Session
    participant PG as PostgreSQL

    Client->>Factory: get_loader(settings)
    Factory->>Factory: Check use_sqlmodel_loader flag
    Factory-->>Client: SQLModelLoader instance

    Client->>Loader: save_opportunity(opportunity)

    Loader->>Loader: _prepare_opportunity()
    Loader->>DB: get_db_session()

    DB->>Session: Create new session
    DB-->>Loader: Context manager

    Loader->>Session: exec(SELECT by submission_id)
    Session->>PG: SELECT * FROM opportunities...
    PG-->>Session: Result
    Session-->>Loader: existing record or None

    alt Duplicate exists
        Loader-->>Client: False (skipped)
    else New record
        Loader->>Session: add(opportunity)
        Loader->>Session: flush()
        Session->>PG: INSERT INTO opportunities...
        PG-->>Session: Success
        Session->>Session: refresh(opportunity)
        Loader-->>Client: True (saved)
    end

    Note over DB: Context manager automatically
    Note over DB: commits/rolls back and
    Note over DB: closes session
```

## Error Handling Flow

```mermaid
flowchart TD
    Start([save_opportunity]) --> Validate{Validate opportunity}
    Validate -->|Invalid| Error[Return False/Log warning]
    Validate -->|Valid| GetSession[Get session from pool]

    GetSession --> Session{Session available?}
    Session -->|No| PoolError[Log pool error]
    Session -->|Yes| CheckDuplicate[Check for duplicate]

    CheckDuplicate --> Duplicate{Duplicate exists?}
    Duplicate -->|Yes| LogSkip[Log skip duplicate]
    Duplicate -->|No| SaveRecord[Add to session]

    SaveRecord --> Flush[Flush to get ID]
    Flush --> Success{Success?}
    Success -->|No| Rollback[Rollback transaction]
    Success -->|Yes| Refresh[Refresh object with DB values]

    LogSkip --> ReturnFalse[Return False]
    Refresh --> ReturnTrue[Return True]
    Rollback --> RaiseError[Raise RuntimeError]
    PoolError --> RaiseError

    Error --> ReturnFalse
    ReturnFalse --> End([End])
    ReturnTrue --> End
    RaiseError --> End
```

## Performance Considerations

### Connection Pool Strategy
```
┌─────────────────────────────────────────┐
│ SQLModel Loader                         │
├─────────────────────────────────────────┤
│ ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐      │
│ │Sess │  │Sess │  │Sess │  │Sess │ ...  │
│ └─────┘  └─────┘  └─────┘  └─────┘      │
│    │        │        │        │        │
│    └────────┴────────┴────────┴────────┘ │
│                ↓                        │
│ ┌─────────────────────────────────────┐ │
│ │    SQLAlchemy Connection Pool        │ │
│ │  (pool_size=10, max_overflow=20)    │ │
│ └─────────────────────────────────────┘ │
│                ↓                        │
│ ┌─────────────────────────────────────┐ │
│ │        PostgreSQL Server            │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Batch Operations Optimization
```mermaid
graph LR
    subgraph "Inefficient: N Round Trips"
        A1[Opportunity 1] --> B1[Database]
        A2[Opportunity 2] --> B2[Database]
        A3[Opportunity 3] --> B3[Database]
        A4[...] --> B4[...]
    end

    subgraph "Efficient: 2 Round Trips"
        C1[All Opportunities] --> D1[session.add_all()]
        D1 --> D2[Single INSERT]
        D2 --> D3[session.flush()]
    end
```

## Migration Path

```mermaid
timeline
    title SQLModel Loader Migration Timeline

    section Phase 2: Implementation
        Design Review : Complete
        Write Tests    : 2 days
        Implement     : 3 days

    section Phase 3: Integration
        Feature Flag  : 1 day
        Factory Pattern: 1 day
        A/B Testing   : 2 days

    section Phase 4: Production
        10% Traffic  : Day 1
        25% Traffic  : Day 2
        50% Traffic  : Day 3
        75% Traffic  : Day 4
        100% Traffic : Day 5
        Monitor      : 7 days
```