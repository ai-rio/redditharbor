# ADR-001: Repository Pattern Implementation

**Status:** Accepted
**Date:** November 30, 2025
**Deciders:** Development Team

## Context

The pipeline needed a clean separation between business logic and data access operations. Direct database operations in the DatabaseLoader were creating tight coupling, making testing difficult and violating clean architecture principles.

## Decision

Implement the Repository Pattern with abstract base classes and concrete SQLAlchemy implementations.

## Detailed Design

### Abstract Repository Interface

```python
class OpportunityRepository(ABC):
    """Abstract repository for Opportunity data operations"""

    @abstractmethod
    def save(self, opportunity: Opportunity) -> bool: pass

    @abstractmethod
    def save_batch(self, opportunities: List[Opportunity]) -> Dict[str, int]: pass

    @abstractmethod
    def find_by_submission_id(self, submission_id: str) -> Optional[Opportunity]: pass

    @abstractmethod
    def find_similar(self, embedding: List[float], similarity_threshold: float = 0.8) -> List[Opportunity]: pass
```

### Concrete Implementation

```python
class SQLAlchemyOpportunityRepository(OpportunityRepository):
    """SQLAlchemy implementation of Opportunity repository"""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    def save_batch(self, opportunities: List[Opportunity]) -> Dict[str, int]:
        # Transaction management with rollback on errors
        with self.session_factory() as session:
            try:
                session.begin()
                # Batch operations with duplicate detection
                for opportunity in opportunities:
                    existing = session.query(Opportunity).filter_by(
                        submission_id=opportunity.submission_id
                    ).first()
                    if not existing:
                        session.add(opportunity)
                        stats["stored"] += 1
                    else:
                        stats["skipped"] += 1
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                raise RuntimeError(f"Batch save failed: {e}")
```

## Advanced Features Implemented

### 1. Vector Similarity Search

```python
def find_similar(self, embedding: List[float], similarity_threshold: float = 0.8) -> List[Opportunity]:
    """Find opportunities similar to the given embedding using cosine similarity"""
    with self.session_factory() as session:
        all_opportunities = session.query(Opportunity).filter(
            Opportunity.embedding.isnot(None)
        ).all()

        similar_opportunities = []
        for opportunity in all_opportunities:
            similarity = self._calculate_cosine_similarity(embedding, opportunity.embedding)
            if similarity >= similarity_threshold:
                similar_opportunities.append(opportunity)

        # Sort by similarity score (descending)
        return sorted(similar_opportunities,
                     key=lambda opp: self._calculate_cosine_similarity(embedding, opp.embedding),
                     reverse=True)
```

### 2. Statistics and Analytics

```python
def get_statistics(self) -> Dict[str, Any]:
    """Get database statistics and summary metrics"""
    with self.session_factory() as session:
        total_count = session.query(func.count(Opportunity.id)).scalar()
        avg_score = session.query(func.avg(Opportunity.final_score)).scalar() or 0
        high_score_count = session.query(func.count(Opportunity.id)).filter(
            Opportunity.final_score >= 70
        ).scalar()

        return {
            "total_opportunities": total_count,
            "average_score": float(avg_score),
            "high_score_percentage": (high_score_count / total_count * 100) if total_count > 0 else 0,
        }
```

## Consequences

### Positive Consequences

1. **Clean Separation of Concerns**: Business logic completely separated from data access
2. **Testability**: Easy to mock repositories for unit testing
3. **Transaction Safety**: Proper transaction management with rollback capabilities
4. **Advanced Features**: Vector similarity search and batch operations
5. **Performance**: Optimized database operations with connection pooling
6. **Maintainability**: Easy to swap database implementations

### Negative Consequences

1. **Code Complexity**: Additional abstraction layer increases complexity
2. **Learning Curve**: Team needs to understand repository pattern
3. **Initial Effort**: Required significant implementation effort (misdocumented as debt)

### Neutral Consequences

1. **Performance Overhead**: Minimal overhead from abstraction layer
2. **Maintenance**: Additional code to maintain but improves organization

## Implementation Status

✅ **FULLY IMPLEMENTED** in `load/repositories.py` (399 lines)

- Abstract OpportunityRepository base class
- SQLAlchemyOpportunityRepository concrete implementation
- Full CRUD operations with transaction safety
- Vector similarity search with cosine similarity
- Comprehensive error handling and logging
- Batch operations with duplicate detection
- Statistics and analytics capabilities

## Integration Points

### DatabaseLoader Integration
```python
class DatabaseLoader:
    def __init__(self):
        self.repository = SQLAlchemyOpportunityRepository(session_factory)

    def store_analyses(self, analyses: List[AnalysisResult], submissions: List[RedditSubmission]) -> Dict[str, int]:
        opportunities = []
        for analysis, submission in zip(analyses, submissions):
            opportunity = self.mapper.to_opportunity(analysis, submission)
            opportunities.append(opportunity)

        return self.repository.save_batch(opportunities)
```

## Testing Strategy

### Unit Testing
- Mock repository interface for business logic testing
- Test repository implementations with in-memory databases

### Integration Testing
- Test repository with actual PostgreSQL database
- Verify transaction rollback behavior
- Test vector similarity search with real embeddings

### Performance Testing
- Batch operation performance with large datasets
- Vector search performance with increasing dataset sizes
- Connection pool efficiency under load

## Migration Path

1. **Phase 1**: Implement abstract interfaces
2. **Phase 2**: Create concrete SQLAlchemy implementation
3. **Phase 3**: Refactor DatabaseLoader to use repositories
4. **Phase 4**: Add advanced features (vector search, statistics)
5. **Phase 5**: Comprehensive testing and optimization

## Related Decisions

- **ADR-002**: Quality Validation System Design (integrates with repositories)
- **ADR-003**: Vector Embedding Strategy (utilizes repository vector search)
- Database Schema: pgvector integration for similarity search

## Notes

This implementation was incorrectly documented as technical debt (DEBT-004) when it was actually a complete, production-ready solution. The repository pattern provides a solid foundation for data access operations and enables advanced features like vector similarity search and efficient batch processing.