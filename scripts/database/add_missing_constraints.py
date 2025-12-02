#!/usr/bin/env python3
"""
Add missing foreign key constraints for deduplication integration
"""

import psycopg2

# Database connection parameters
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 54322,
    'database': 'postgres',
    'user': 'postgres',
    'password': 'postgres'
}

def add_missing_constraints():
    """Add the missing foreign key constraints"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        print("Adding missing foreign key constraints...")

        # Add constraint for llm_monetization_analysis.business_concept_id
        try:
            cur.execute("""
                ALTER TABLE llm_monetization_analysis
                ADD CONSTRAINT fk_llm_analysis_business_concept
                FOREIGN KEY (business_concept_id) REFERENCES business_concepts(id);
            """)
            print("✓ Added fk_llm_analysis_business_concept")
        except psycopg2.Error as e:
            if "already exists" in str(e).lower():
                print("✓ fk_llm_analysis_business_concept already exists")
            else:
                print(f"✗ Error adding fk_llm_analysis_business_concept: {e}")

        # Add constraint for llm_monetization_analysis.primary_opportunity_id
        try:
            cur.execute("""
                ALTER TABLE llm_monetization_analysis
                ADD CONSTRAINT fk_llm_analysis_primary_opportunity
                FOREIGN KEY (primary_opportunity_id) REFERENCES opportunities_unified(id)
                DEFERRABLE INITIALLY DEFERRED;
            """)
            print("✓ Added fk_llm_analysis_primary_opportunity")
        except psycopg2.Error as e:
            if "already exists" in str(e).lower():
                print("✓ fk_llm_analysis_primary_opportunity already exists")
            else:
                print(f"✗ Error adding fk_llm_analysis_primary_opportunity: {e}")

        # Add constraint for opportunities_unified.primary_opportunity_id
        try:
            cur.execute("""
                ALTER TABLE opportunities_unified
                ADD CONSTRAINT fk_opportunities_primary_opportunity
                FOREIGN KEY (primary_opportunity_id) REFERENCES opportunities_unified(id)
                DEFERRABLE INITIALLY DEFERRED;
            """)
            print("✓ Added fk_opportunities_primary_opportunity")
        except psycopg2.Error as e:
            if "already exists" in str(e).lower():
                print("✓ fk_opportunities_primary_opportunity already exists")
            else:
                print(f"✗ Error adding fk_opportunities_primary_opportunity: {e}")

        conn.commit()
        cur.close()
        conn.close()

        print("\nAll constraints added successfully!")
        return True

    except Exception as e:
        print(f"✗ Error adding constraints: {e}")
        return False

if __name__ == "__main__":
    success = add_missing_constraints()
    exit(0 if success else 1)