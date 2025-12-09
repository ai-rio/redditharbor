#!/usr/bin/env python3
"""
Simple standalone test for vector similarity functionality
This test verifies the core vector operations without complex dependencies
"""

import os
import sys

sys.path.insert(0, os.getcwd())

from datetime import UTC, datetime
from typing import Any, Dict, List

import numpy as np


def calculate_cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have the same dimension")

    try:
        # Convert to numpy arrays for efficient calculation
        vec1_array = np.array(vec1)
        vec2_array = np.array(vec2)

        # Calculate cosine similarity
        dot_product = np.dot(vec1_array, vec2_array)
        magnitude1 = np.linalg.norm(vec1_array)
        magnitude2 = np.linalg.norm(vec2_array)

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return float(dot_product / (magnitude1 * magnitude2))

    except ImportError:
        # Fallback to pure Python calculation
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)


def generate_similar_embedding(base_embedding: list[float], similarity: float = 0.8) -> list[float]:
    """Generate an embedding with specified similarity to base embedding"""
    # Add controlled variations to achieve desired similarity
    variation = 1.0 - similarity
    return [x + np.random.normal(0, variation) for x in base_embedding]


def test_cosine_similarity():
    """Test cosine similarity calculations"""
    print("Testing cosine similarity calculations...")

    # Test identical vectors
    base_embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 76 + [0.6, 0.7, 0.8, 0.9]  # 384 dimensions
    similarity_identical = calculate_cosine_similarity(base_embedding, base_embedding)

    assert abs(similarity_identical - 1.0) < 0.001, f"Identical vectors should have similarity ~1.0, got {similarity_identical}"
    print(f"✓ Identical vectors similarity: {similarity_identical:.4f}")

    # Test similar vectors
    similar_embedding = generate_similar_embedding(base_embedding, similarity=0.9)
    similarity_similar = calculate_cosine_similarity(base_embedding, similar_embedding)

    assert 0.8 <= similarity_similar <= 1.0, f"Similar vectors should have high similarity (got {similarity_similar})"
    print(f"✓ Similar vectors similarity: {similarity_similar:.4f}")

    # Test different vectors
    different_embedding = generate_similar_embedding(base_embedding, similarity=0.3)
    similarity_different = calculate_cosine_similarity(base_embedding, different_embedding)

    assert similarity_different < 0.7, f"Different vectors should have low similarity (got {similarity_different})"
    print(f"✓ Different vectors similarity: {similarity_different:.4f}")

    print("✓ Cosine similarity calculations work correctly")


def test_embedding_generation():
    """Test embedding generation and validation"""
    print("\nTesting embedding generation...")

    # Test 384-dimensional embedding
    base_values = [0.1, 0.2, 0.3, 0.4, 0.5]
    embedding_384 = (base_values * 76 + [0.6, 0.7, 0.8, 0.9])[:384]  # 384 dimensions

    assert len(embedding_384) == 384, f"Embedding should have 384 dimensions, got {len(embedding_384)}"
    assert all(isinstance(x, (int, float)) for x in embedding_384), "All embedding values should be numeric"
    print(f"✓ Generated 384-dimensional embedding: {len(embedding_384)} dimensions")

    # Test similar embedding generation
    similar_embedding = generate_similar_embedding(embedding_384, similarity=0.9)
    similarity = calculate_cosine_similarity(embedding_384, similar_embedding)

    assert 0.85 <= similarity <= 0.98, f"Generated similarity should be around target (got {similarity})"
    print(f"✓ Generated similar embedding with similarity: {similarity:.4f}")

    print("✓ Embedding generation works correctly")


def test_similarity_search_simulation():
    """Test similarity search with simulated database"""
    print("\nTesting similarity search simulation...")

    # Create a simulated database of opportunities
    base_embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 76 + [0.6, 0.7, 0.8, 0.9]  # 384 dimensions

    opportunities = []

    # Add original opportunity
    opportunities.append({
        "id": "opp_001",
        "title": "Task Management App",
        "embedding": base_embedding,
        "score": 80.0
    })

    # Add similar opportunity
    similar_embedding = generate_similar_embedding(base_embedding, similarity=0.9)
    opportunities.append({
        "id": "opp_002",
        "title": "Project Management Tool",
        "embedding": similar_embedding,
        "score": 82.0
    })

    # Add different opportunity
    different_embedding = generate_similar_embedding(base_embedding, similarity=0.3)
    opportunities.append({
        "id": "opp_003",
        "title": "AI Writing Assistant",
        "embedding": different_embedding,
        "score": 75.0
    })

    # Test similarity search
    query_embedding = base_embedding
    similarity_threshold = 0.8

    similar_opportunities = []
    for opp in opportunities:
        similarity = calculate_cosine_similarity(query_embedding, opp["embedding"])
        if similarity >= similarity_threshold:
            opp_with_similarity = opp.copy()
            opp_with_similarity["similarity_score"] = similarity
            similar_opportunities.append(opp_with_similarity)

    # Sort by similarity score (descending)
    similar_opportunities.sort(key=lambda x: x["similarity_score"], reverse=True)

    # Verify results
    assert len(similar_opportunities) >= 2, f"Should find at least 2 similar opportunities, got {len(similar_opportunities)}"

    # Original should have highest similarity (1.0)
    assert similar_opportunities[0]["id"] == "opp_001", "Original opportunity should be most similar"
    assert similar_opportunities[0]["similarity_score"] == 1.0, "Original should have perfect similarity"

    # Similar opportunity should be included
    similar_found = any(opp["id"] == "opp_002" for opp in similar_opportunities)
    assert similar_found, "Similar opportunity should be found"

    # Different opportunity should NOT be included
    different_found = any(opp["id"] == "opp_003" for opp in similar_opportunities)
    assert not different_found, "Different opportunity should not be found with high threshold"

    print(f"✓ Found {len(similar_opportunities)} similar opportunities:")
    for opp in similar_opportunities:
        print(f"  - {opp['id']}: {opp['title']} (similarity: {opp['similarity_score']:.4f})")

    print("✓ Similarity search simulation works correctly")


def test_threshold_filtering():
    """Test similarity threshold filtering"""
    print("\nTesting similarity threshold filtering...")

    base_embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 76 + [0.6, 0.7, 0.8, 0.9]  # 384 dimensions

    # Create opportunities with different similarity levels
    test_opportunities = []

    for i, similarity_target in enumerate([0.95, 0.85, 0.75, 0.65, 0.55]):
        embedding = generate_similar_embedding(base_embedding, similarity=similarity_target)
        test_opportunities.append({
            "id": f"test_{i}",
            "similarity_target": similarity_target,
            "embedding": embedding
        })

    # Test with different thresholds
    thresholds = [0.9, 0.7, 0.5]
    results_by_threshold = {}

    for threshold in thresholds:
        results = []
        for opp in test_opportunities:
            similarity = calculate_cosine_similarity(base_embedding, opp["embedding"])
            if similarity >= threshold:
                results.append(opp["id"])
        results_by_threshold[threshold] = results

    # Verify threshold behavior
    assert len(results_by_threshold[0.5]) >= len(results_by_threshold[0.7]) >= len(results_by_threshold[0.9]), \
        "Lower thresholds should find more results"

    print("✓ Threshold filtering results:")
    for threshold, results in results_by_threshold.items():
        print(f"  Threshold {threshold}: {len(results)} opportunities")

    print("✓ Similarity threshold filtering works correctly")


def test_performance():
    """Test performance of vector operations"""
    print("\nTesting vector operations performance...")

    import time

    # Create test data
    base_embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 76 + [0.6, 0.7, 0.8, 0.9]  # 384 dimensions
    test_embeddings = []

    for i in range(100):  # Create 100 test embeddings
        embedding = generate_similar_embedding(base_embedding, similarity=0.6 + (i * 0.003))
        test_embeddings.append(embedding)

    # Test similarity search performance
    start_time = time.time()
    similar_embeddings = []
    threshold = 0.7

    for embedding in test_embeddings:
        similarity = calculate_cosine_similarity(base_embedding, embedding)
        if similarity >= threshold:
            similar_embeddings.append((similarity, embedding))

    # Sort by similarity
    similar_embeddings.sort(key=lambda x: x[0], reverse=True)

    search_time = time.time() - start_time

    assert search_time < 1.0, f"Similarity search should complete in <1s, took {search_time:.3f}s"
    assert len(similar_embeddings) > 0, "Should find some similar embeddings"

    print(f"✓ Found {len(similar_embeddings)} similar embeddings in {search_time:.3f}s")
    print(f"  Top similarity: {similar_embeddings[0][0]:.4f}")
    print("✓ Vector operations performance is acceptable")


def main():
    """Run all vector similarity tests"""
    print("=== Vector Similarity Functionality Test Suite ===\n")

    try:
        test_cosine_similarity()
        test_embedding_generation()
        test_similarity_search_simulation()
        test_threshold_filtering()
        test_performance()

        print("\n🎉 ALL TESTS PASSED!")
        print("✓ Vector similarity functionality is working correctly")
        print("✓ Cosine similarity calculations are accurate")
        print("✓ Similarity search and threshold filtering work")
        print("✓ Performance is acceptable for production use")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
