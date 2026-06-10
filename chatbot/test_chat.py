"""
Test Chat Module
Test template loading, system prompt, custom query, and cache hits.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.templates import load_templates, list_templates
from chatbot.tools import build_tools, build_tools_without_custom
from chatbot.system_prompt import build_system_prompt, STATIC_SYSTEM_PROMPT
from chatbot.runner import validate_custom_sql, run_custom_sql


# ── Test 1: Template Loading ──────────────────────────────────
def test_template_loading():
    """Test that templates load correctly from database"""
    print("=" * 60)
    print("TEST 1: Template Loading")
    print("=" * 60)

    try:
        templates = load_templates()
        print(f"✓ Loaded {len(templates)} templates")

        expected_count = 15
        if len(templates) != expected_count:
            print(f"✗ Expected {expected_count} templates, got {len(templates)}")
            return False

        print("\nTemplate names:")
        for name in templates.keys():
            print(f"  - {name}")

        print("\n✓ All templates loaded successfully")
        return True

    except Exception as e:
        print(f"✗ Error loading templates: {str(e)}")
        return False


# ── Test 2: Template Structure ────────────────────────────────
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
            missing = [f for f in required_fields if f not in template]
            if missing:
                print(f"✗ Template '{name}' missing fields: {missing}")
                all_valid = False
                continue

            if not isinstance(template['params'], list):
                print(f"✗ Template '{name}' params is not a list")
                all_valid = False
                continue

            if 'LIMIT' not in template['sql_template'].upper():
                print(f"⚠ Template '{name}' missing LIMIT clause")

            print(f"✓ Template '{name}' structure valid ({len(template['params'])} params)")

        if all_valid:
            print("\n✓ All templates have valid structure")
        return all_valid

    except Exception as e:
        print(f"✗ Error checking template structure: {str(e)}")
        return False


# ── Test 3: Tool Definitions (with query_custom) ──────────────
def test_tool_definitions():
    """Test that tool definitions include query_custom"""
    print("\n" + "=" * 60)
    print("TEST 3: Tool Definitions")
    print("=" * 60)

    try:
        tools = build_tools()
        print(f"✓ Generated {len(tools)} tool definitions (expected: 16 = 15 templates + query_custom)")

        if len(tools) != 16:
            print(f"✗ Expected 16 tools, got {len(tools)}")
            return False

        # Check query_custom is last
        last_tool = tools[-1]
        if last_tool["function"]["name"] != "query_custom":
            print(f"✗ Last tool should be query_custom, got: {last_tool['function']['name']}")
            return False
        print(f"✓ query_custom is the last tool (DeepSeek picks templates first)")

        # Check query_custom has 'sql' as required param
        required = last_tool["function"]["parameters"].get("required", [])
        if "sql" not in required:
            print("✗ query_custom missing required 'sql' parameter")
            return False
        print(f"✓ query_custom requires: {required}")

        # Check first tool structure
        first_tool = tools[0]
        fn = first_tool["function"]
        expected_keys = ['name', 'description', 'parameters']
        missing = [k for k in expected_keys if k not in fn]
        if missing:
            print(f"✗ First tool missing function keys: {missing}")
            return False

        print(f"✓ Tool definitions OK — {len(tools)} tools total")

        # Test without custom
        tools_no_custom = build_tools_without_custom()
        if len(tools_no_custom) != 15:
            print(f"✗ build_tools_without_custom should return 15 tools, got {len(tools_no_custom)}")
            return False
        print(f"✓ build_tools_without_custom returns {len(tools_no_custom)} tools")

        return True

    except Exception as e:
        print(f"✗ Error building tools: {str(e)}")
        return False


# ── Test 4: System Prompt (Schema) ─────────────────────────────
def test_system_prompt():
    """Test that system prompt includes schema, glossary, and business rules"""
    print("\n" + "=" * 60)
    print("TEST 4: System Prompt (Schema)")
    print("=" * 60)

    try:
        prompt = build_system_prompt()
        print(f"✓ System prompt generated ({len(prompt)} chars, ~{len(prompt)//4} tokens)")

        # Check prompt contains expected sections
        schema_sections = [
            "docinfo",
            "transtkd",
            "skumaster",
            "query_custom",
            "KEY JOIN PATTERNS",
            "column `branch_id`",
            "กฎทางธุรกิจ",
            "ยอดขาย",
            "กำไรขั้นต้น",
            "มาร์จิ้น",
            "Few-Shot",
            "รูปแบบการตอบ",
            "ข้อห้าม",
        ]

        missing = []
        for s in schema_sections:
            if s.lower() not in prompt.lower():
                missing.append(s)
                print(f"✗ Missing section: {s}")

        if missing:
            print(f"\n✗ System prompt missing {len(missing)} expected sections")
            return False

        print(f"\n✓ All {len(schema_sections)} expected sections found")

        # Check schema has column details
        assert "di_date" in prompt, "Missing di_date column"
        assert "trd_n_amt" in prompt, "Missing trd_n_amt column"
        assert "ard_n_amt" in prompt, "Missing ard_n_amt column"
        print("✓ Key columns documented (di_date, trd_n_amt, ard_n_amt)")

        # Check glossary
        assert "dt_doccode" in prompt, "Missing doctype codes"
        assert "IV=ขาย" in prompt, "Missing IV code"
        print("✓ Column glossary present with doctype codes")

        print("\n✓ System prompt complete with schema")
        return True

    except Exception as e:
        print(f"✗ Error building system prompt: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ── Test 5: SQL Validation ────────────────────────────────────
def test_sql_validation():
    """Test SQL validation for custom queries"""
    print("\n" + "=" * 60)
    print("TEST 5: SQL Validation")
    print("=" * 60)

    try:
        # Valid queries
        valid_sqls = [
            "SELECT * FROM docinfo WHERE di_date > '2026-01-01' LIMIT 10",
            "SELECT sku_name, SUM(trd_qty) FROM transtkd t JOIN skumaster s ON s.sku_key = t.trd_sku AND s.branch_id = t.branch_id WHERE t.branch_id = :branch_id GROUP BY sku_name LIMIT 20",
            "WITH sales AS (SELECT * FROM docinfo) SELECT * FROM sales LIMIT 5",
        ]

        for sql in valid_sqls:
            cleaned = validate_custom_sql(sql)
            print(f"✓ Valid: {cleaned[:60]}...")
            assert cleaned.upper().startswith('SELECT') or cleaned.upper().startswith('WITH')

        # Should add LIMIT
        sql_no_limit = "SELECT * FROM docinfo"
        result = validate_custom_sql(sql_no_limit)
        assert "LIMIT" in result.upper(), "Should add LIMIT"
        print(f"✓ Auto-added LIMIT: {result}")

        # Should cap LIMIT
        sql_high_limit = "SELECT * FROM docinfo LIMIT 500"
        result = validate_custom_sql(sql_high_limit)
        assert "LIMIT 100" in result.upper(), f"Should cap at 100, got: {result}"
        print(f"✓ Capped LIMIT: {result}")

        # Invalid: contains DROP
        invalid_sqls = [
            ("DROP TABLE docinfo", "DROP"),
            ("DELETE FROM docinfo", "DELETE"),
            ("INSERT INTO docinfo VALUES (1)", "INSERT"),
            ("UPDATE docinfo SET x=1", "UPDATE"),
            ("SELECT * FROM docinfo; DROP TABLE x", ";"),
        ]

        for sql, expected_block in invalid_sqls:
            try:
                validate_custom_sql(sql)
                print(f"✗ Should have rejected: {sql}")
                return False
            except ValueError as e:
                print(f"✓ Rejected [{expected_block}]: {str(e)[:60]}")

        print("\n✓ SQL validation working correctly")
        return True

    except Exception as e:
        print(f"✗ Error in SQL validation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ── Test 6: List Templates ────────────────────────────────────
def test_list_templates():
    """Test template listing function"""
    print("\n" + "=" * 60)
    print("TEST 6: List Templates")
    print("=" * 60)

    try:
        template_list = list_templates()
        print(f"✓ Listed {len(template_list)} templates")

        for i, t in enumerate(template_list[:3], 1):
            print(f"\n{i}. {t['name']}")
            print(f"   {t['description'][:80]}...")

        print("\n✓ Template listing successful")
        return True

    except Exception as e:
        print(f"✗ Error listing templates: {str(e)}")
        return False


# ── Test 7: Cache Hit Detection (simulated) ────────────────────
def test_cache_logging():
    """Test that cache hit stats are logged (mock check)"""
    print("\n" + "=" * 60)
    print("TEST 7: Cache Hit Logging (structure check)")
    print("=" * 60)

    try:
        from chatbot.chat import _log_usage

        # Create a mock usage object
        class MockUsage:
            prompt_tokens = 1200
            completion_tokens = 50
            total_tokens = 1250
            prompt_cache_hit_tokens = 922
            prompt_cache_miss_tokens = 278

        usage = MockUsage()

        # Check _log_usage doesn't crash
        import io
        import sys as _sys
        old_stdout = _sys.stdout
        _sys.stdout = io.StringIO()
        _log_usage("TEST", usage)
        output = _sys.stdout.getvalue()
        _sys.stdout = old_stdout

        assert "cache_hit=922" in output, f"Missing cache_hit in: {output}"
        assert "cache_miss=278" in output, f"Missing cache_miss in: {output}"
        assert "hit_rate=77%" in output, f"Missing hit_rate in: {output}"
        print(f"✓ Cache hit logging works: {output.strip()}")

        # Check without cache (older API response)
        class MockUsageNoCache:
            prompt_tokens = 1000
            completion_tokens = 50
            total_tokens = 1050

        _sys.stdout = io.StringIO()
        _log_usage("NO_CACHE", MockUsageNoCache())
        output = _sys.stdout.getvalue()
        _sys.stdout = old_stdout
        print(f"✓ No-cache fallback works: {output.strip()}")

        return True

    except Exception as e:
        print(f"✗ Error in cache logging: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ── Run All ────────────────────────────────────────────────────
def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("B+ ERP CHATBOT — FULL TEST SUITE (Schema + Custom Query)")
    print("=" * 60)

    tests = [
        test_template_loading,
        test_template_structure,
        test_tool_definitions,
        test_system_prompt,
        test_sql_validation,
        test_list_templates,
        test_cache_logging,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test '{test.__name__}' failed with exception: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append(False)

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✅ All tests passed!")
        return 0
    else:
        failed = [tests[i].__name__ for i, r in enumerate(results) if not r]
        print(f"\n❌ {total - passed} test(s) failed: {failed}")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
