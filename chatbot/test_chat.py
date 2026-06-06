"""
Test Chat Module
Test template loading and basic chat functionality
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.templates import load_templates, list_templates
from chatbot.tools import build_tools
from chatbot.system_prompt import build_system_prompt


def test_template_loading():
    """Test that templates load correctly from database"""
    print("=" * 60)
    print("TEST 1: Template Loading")
    print("=" * 60)

    try:
        templates = load_templates()
        print(f"✓ Loaded {len(templates)} templates")

        # Check we have all 15 templates
        expected_count = 15
        if len(templates) != expected_count:
            print(f"✗ Expected {expected_count} templates, got {len(templates)}")
            return False

        # List template names
        print("\nTemplate names:")
        for name in templates.keys():
            print(f"  - {name}")

        print("\n✓ All templates loaded successfully")
        return True

    except Exception as e:
        print(f"✗ Error loading templates: {str(e)}")
        return False


def test_template_structure():
    """Test that each template has required fields"""
    print("\n" + "=" * 60)
    print("TEST 2: Template Structure")
    print("=" * 60)

    try:
        templates = load_templates()
        required_fields = ['id', 'name', 'description', 'sql_template', 'params']

        all_valid = True
        for name, template in templates.items():
            # Check required fields
            missing = [f for f in required_fields if f not in template]
            if missing:
                print(f"✗ Template '{name}' missing fields: {missing}")
                all_valid = False
                continue

            # Check params is list
            if not isinstance(template['params'], list):
                print(f"✗ Template '{name}' params is not a list")
                all_valid = False
                continue

            # Check SQL template contains LIMIT
            if 'LIMIT' not in template['sql_template'].upper():
                print(f"⚠ Template '{name}' missing LIMIT clause")

            print(f"✓ Template '{name}' structure valid ({len(template['params'])} params)")

        if all_valid:
            print("\n✓ All templates have valid structure")
        return all_valid

    except Exception as e:
        print(f"✗ Error checking template structure: {str(e)}")
        return False


def test_tool_definitions():
    """Test that tool definitions are generated correctly"""
    print("\n" + "=" * 60)
    print("TEST 3: Tool Definitions")
    print("=" * 60)

    try:
        tools = build_tools()
        print(f"✓ Generated {len(tools)} tool definitions")

        # Check first tool structure
        if tools:
            first_tool = tools[0]
            required_keys = ['name', 'description', 'input_schema']

            missing = [k for k in required_keys if k not in first_tool]
            if missing:
                print(f"✗ Tool missing keys: {missing}")
                return False

            print(f"\nExample tool: {first_tool['name']}")
            print(f"  Description: {first_tool['description'][:60]}...")
            print(f"  Properties: {list(first_tool['input_schema']['properties'].keys())}")
            print(f"  Required: {first_tool['input_schema'].get('required', [])}")

        print("\n✓ Tool definitions generated successfully")
        return True

    except Exception as e:
        print(f"✗ Error building tools: {str(e)}")
        return False


def test_system_prompt():
    """Test that system prompt builds correctly"""
    print("\n" + "=" * 60)
    print("TEST 4: System Prompt")
    print("=" * 60)

    try:
        prompt = build_system_prompt()
        print(f"✓ System prompt generated ({len(prompt)} characters)")

        # Check prompt contains expected sections
        expected_sections = ["วันที่ปัจจุบัน", "สาขา", "กฎการแปลค่า", "รูปแบบการตอบ"]
        missing = [s for s in expected_sections if s not in prompt]

        if missing:
            print(f"✗ System prompt missing sections: {missing}")
            return False

        print("\nPrompt sections found:")
        for section in expected_sections:
            print(f"  ✓ {section}")

        # Show first 300 characters
        print(f"\nPrompt preview:\n{prompt[:300]}...")

        print("\n✓ System prompt built successfully")
        return True

    except Exception as e:
        print(f"✗ Error building system prompt: {str(e)}")
        return False


def test_list_templates():
    """Test template listing function"""
    print("\n" + "=" * 60)
    print("TEST 5: List Templates")
    print("=" * 60)

    try:
        template_list = list_templates()
        print(f"✓ Listed {len(template_list)} templates")

        # Show first 3
        for i, t in enumerate(template_list[:3], 1):
            print(f"\n{i}. {t['name']}")
            print(f"   {t['description'][:80]}...")

        print("\n✓ Template listing successful")
        return True

    except Exception as e:
        print(f"✗ Error listing templates: {str(e)}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("B+ ERP CHATBOT - TEMPLATE TESTS")
    print("=" * 60)

    tests = [
        test_template_loading,
        test_template_structure,
        test_tool_definitions,
        test_system_prompt,
        test_list_templates,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test failed with exception: {str(e)}")
            results.append(False)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
