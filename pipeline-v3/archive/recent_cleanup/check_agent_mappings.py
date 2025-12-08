#!/usr/bin/env python3
"""
Direct verification of agent name mappings by reading the source file

This script checks the agno_agents.py file directly to verify
that all 5 agents are properly defined with correct name mappings.
"""

import ast
import os
import sys


def read_agent_file():
    """Read and parse the agno_agents.py file"""

    agent_file_path = os.path.join(os.path.dirname(__file__), '..', 'transform', 'agno_agents.py')

    try:
        with open(agent_file_path) as f:
            content = f.read()
        return content
    except FileNotFoundError:
        print(f"❌ Could not find agno_agents.py at {agent_file_path}")
        return None

def parse_agent_classes(content):
    """Parse the Python code to extract agent classes and their _get_agent_name method"""

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"❌ Syntax error in agno_agents.py: {e}")
        return {}

    agent_classes = {}

    # Find all class definitions
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if node.name.endswith('Agent') and node.name != 'Agent':
                # Find the _get_agent_name method
                agent_name = None
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == '_get_agent_name':
                        # Parse the return value from _get_agent_name
                        for return_node in ast.walk(item):
                            if isinstance(return_node, ast.Return):
                                if hasattr(return_node, 'value') and hasattr(return_node.value, 'elts'):
                                    # This is a return statement with a dict (name_map.get(...))
                                    # We need to find the mapping
                                    pass
                        agent_name = extract_agent_name_from_method(item)
                        break

                if agent_name is None:
                    # Try to infer from name_map in the method
                    agent_name = infer_agent_name_from_class(node.name)

                agent_classes[node.name] = agent_name

    return agent_classes

def extract_agent_name_from_method(method_node):
    """Extract agent name from _get_agent_name method"""

    # Look for the name_map dictionary
    for node in ast.walk(method_node):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if hasattr(target, 'id') and target.id == 'name_map':
                    # Found the name_map assignment
                    if hasattr(node.value, 'keys'):
                        return extract_from_dict_literal(node.value)

    return None

def extract_from_dict_literal(dict_node):
    """Extract agent name mapping from dictionary literal"""

    # This is complex to parse with AST, so we'll use a simpler approach
    # by looking at the source code directly
    return None

def infer_agent_name_from_class(class_name):
    """Infer agent name based on class name"""

    mapping = {
        "WillingnessToPayAgent": "wtp",
        "MarketSegmentAgent": "segment",
        "PricePointAgent": "price",
        "PaymentBehaviorAgent": "payment",
        "MarketResearchAgent": "market"
    }

    return mapping.get(class_name, None)

def check_name_mapping_in_code(content):
    """Check the name_map dictionary directly in the source code"""

    # Look for the name_map dictionary in the code
    lines = content.split('\n')
    name_map_found = False
    agent_mappings = {}

    for i, line in enumerate(lines):
        if 'name_map = {' in line:
            name_map_found = True
            # Parse the dictionary
            j = i
            while j < len(lines) and '}' not in lines[j]:
                j += 1
            j += 1  # Include the closing brace

            dict_content = '\n'.join(lines[i:j])
            # Extract mappings
            agent_mappings = extract_mappings_from_dict(dict_content)
            break

    return name_map_found, agent_mappings

def extract_mappings_from_dict(dict_content):
    """Extract agent mappings from dictionary string"""

    mappings = {}

    # Simple string parsing
    lines = dict_content.split('\n')
    for line in lines:
        if '":' in line and '"' in line:
            # Extract key and value
            parts = line.strip().split('":')
            if len(parts) == 2:
                key = parts[0].strip().strip('"')
                value = parts[1].strip().rstrip(',').strip('"')
                mappings[key] = value

    return mappings

def check_agent_classes_exist(content):
    """Check that all expected agent classes exist"""

    expected_classes = [
        "class WillingnessToPayAgent",
        "class MarketSegmentAgent",
        "class PricePointAgent",
        "class PaymentBehaviorAgent",
        "class MarketResearchAgent"
    ]

    found_classes = []

    for expected_class in expected_classes:
        if expected_class in content:
            found_classes.append(expected_class)

    return found_classes, expected_classes

def main():
    """Main verification"""

    print("🔍 AGENT METRICS TRACKING VERIFICATION")
    print("=" * 60)

    # Read the agent file
    content = read_agent_file()
    if content is None:
        return False

    # Check 1: All agent classes exist
    print("\n1. CHECKING AGENT CLASSES")
    print("-" * 40)

    found_classes, expected_classes = check_agent_classes_exist(content)

    for cls in expected_classes:
        if cls in found_classes:
            print(f"✅ {cls}")
        else:
            print(f"❌ {cls} - NOT FOUND")

    # Check 2: Name mapping dictionary exists
    print("\n2. CHECKING NAME MAPPING")
    print("-" * 40)

    name_map_found, agent_mappings = check_name_mapping_in_code(content)

    if name_map_found:
        print("✅ name_map dictionary found")
        print("\nAgent name mappings:")
        expected_mappings = {
            "WillingnessToPayAgent": "wtp",
            "MarketSegmentAgent": "segment",
            "PricePointAgent": "price",
            "PaymentBehaviorAgent": "payment",
            "MarketResearchAgent": "market"
        }

        mapping_ok = True
        for class_name, expected_name in expected_mappings.items():
            actual_name = agent_mappings.get(class_name)
            if actual_name == expected_name:
                print(f"✅ {class_name} → {actual_name}")
            else:
                print(f"❌ {class_name} → expected: {expected_name}, got: {actual_name}")
                mapping_ok = False
    else:
        print("❌ name_map dictionary NOT found")
        mapping_ok = False

    # Check 3: All agents inherit from base Agent class
    print("\n3. CHECKING INHERITANCE")
    print("-" * 40)

    inheritance_ok = True
    for cls_name in expected_classes:
        class_name = cls_name.replace("class ", "")
        if f"class {class_name}(Agent)" in content:
            print(f"✅ {class_name} inherits from Agent")
        else:
            print(f"❌ {class_name} - inheritance issue")
            inheritance_ok = False

    # Overall result
    print("\n" + "=" * 60)
    print("OVERALL RESULT")
    print("=" * 60)

    classes_ok = len(found_classes) == len(expected_classes)

    if classes_ok and name_map_found and mapping_ok and inheritance_ok:
        print("✅ ALL VERIFICATIONS PASSED")
        print("\nThe QA audit finding should be resolved:")
        print(f"✅ Found all {len(expected_classes)} required agents")
        print("✅ Correct agent name mappings (wtp, segment, price, payment, market)")
        print("✅ Proper inheritance from Agent base class")
        print("✅ All agents should track metrics with correct agent_name")
        return True
    else:
        print("❌ VERIFICATION ISSUES FOUND")
        if not classes_ok:
            print(f"- Missing agent classes: {len(expected_classes) - len(found_classes)}")
        if not name_map_found:
            print("- name_map dictionary not found")
        if not mapping_ok:
            print("- Agent name mapping issues")
        if not inheritance_ok:
            print("- Inheritance issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
