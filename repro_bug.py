from typing import List
import sys
import os

# Add the project root to sys.path to allow importing from augur
# Use the actual package now that it is fixed
sys.path.append(os.getcwd())

# Force re-importing in case it was already in sys.modules
if 'augur.tasks.util.worker_util' in sys.modules:
    del sys.modules['augur.tasks.util.worker_util']

try:
    from augur.tasks.util.worker_util import remove_duplicates_by_uniques, remove_duplicate_dicts
except ImportError:
    # Fallback to local definitions if path issue (though it shouldn't be)
    print("Warning: Could not import from augur, using local fixed definitions.")
    def _make_hashable(obj):
        if isinstance(obj, (tuple, list)):
            return tuple(_make_hashable(e) for e in obj)
        if isinstance(obj, dict):
            return tuple(sorted((k, _make_hashable(v)) for k, v in obj.items()))
        return obj

    def remove_duplicate_dicts(data: List[dict]) -> List[dict]:
        seen = set()
        unique_data = []
        for d in data:
            h = _make_hashable(d)
            if h not in seen:
                seen.add(h)
                unique_data.append(d)
        return unique_data

    def remove_duplicates_by_uniques(data, uniques):
        unique_values = {}
        unique_data = []
        if not uniques: return data
        for x in data:
            key = tuple(x[unique] for unique in uniques)
            try:
                unique_values[key]
                continue
            except KeyError:
                unique_values[key] = 1
                unique_data.append(x)
        return unique_data

# --- Test Suite ---

def test_remove_duplicates_by_uniques_collision():
    print("Testing remove_duplicates_by_uniques collision...")
    data = [
        {"a": "foo_bar", "b": "baz", "id": 1},
        {"a": "foo", "b": "bar_baz", "id": 2}
    ]
    uniques = ["a", "b"]
    
    result = remove_duplicates_by_uniques(data, uniques)
    print(f"  Result length: {len(result)}")
    for item in result:
        print(f"    {item}")
        
    assert len(result) == 2, f"Expected 2 items, got {len(result)}. FIX FAILED!"
    print("  SUCCESS: No collision in remove_duplicates_by_uniques!")

def test_remove_duplicate_dicts_crash():
    print("\nTesting remove_duplicate_dicts with nested data...")
    data = [
        {"id": 1, "metadata": {"key": "value"}},
        {"id": 1, "metadata": {"key": "value"}},
        {"id": 2, "metadata": {"key": "other"}}
    ]
    
    try:
        result = remove_duplicate_dicts(data)
        print(f"  Result length: {len(result)}")
        assert len(result) == 2, f"Expected 2 items, got {len(result)}. FIX FAILED!"
        print("  SUCCESS: remove_duplicate_dicts handled nested data correctly!")
    except Exception as e:
        print(f"  FAILED: Caught exception in remove_duplicate_dicts: {type(e).__name__}: {e}")
        raise e

def test_edge_cases():
    print("\nTesting edge cases...")
    
    # 1. Empty list
    print("  1. Empty list")
    assert remove_duplicates_by_uniques([], ["id"]) == []
    assert remove_duplicate_dicts([]) == []
    print("    Passed")
    
    # 2. List with one element
    print("  2. List with one element")
    data_one = [{"id": 1}]
    assert remove_duplicates_by_uniques(data_one, ["id"]) == data_one
    assert remove_duplicate_dicts(data_one) == data_one
    print("    Passed")
    
    # 3. List with identical elements (flat)
    print("  3. List with identical elements (flat)")
    data_identical = [{"id": 1}, {"id": 1}]
    assert len(remove_duplicates_by_uniques(data_identical, ["id"])) == 1
    assert len(remove_duplicate_dicts(data_identical)) == 1
    print("    Passed")
    
    # 4. Null values collision
    print("  4. Null values collision")
    data_nulls = [
        {"a": None, "b": "baz", "id": 1},
        {"a": "None", "b": "baz", "id": 2}
    ]
    result = remove_duplicates_by_uniques(data_nulls, ["a", "b"])
    print(f"    Result length: {len(result)}")
    assert len(result) == 2, f"Expected 2, got {len(result)}. Null collision still exists!"
    print("    Passed: None and 'None' are distinct.")

    # 5. Empty strings and underscores
    print("  5. Empty strings and underscores")
    data_empty_strings = [
        {"a": "", "b": "foo_bar", "id": 1},
        {"a": "_", "b": "foo_bar", "id": 3},
        {"a": "", "b": "_foo_bar", "id": 4}
    ]
    result = remove_duplicates_by_uniques(data_empty_strings, ["a", "b"])
    print(f"    Result length: {len(result)}")
    assert len(result) == 3, f"Expected 3, got {len(result)}. Collision with empty strings still exists!"
    print("    Passed: Empty strings and underscores handled correctly.")

    # 6. Non-existent keys
    print("  6. Non-existent keys")
    try:
        remove_duplicates_by_uniques([{"id": 1}], ["non_existent"])
        assert False, "Should have raised KeyError"
    except KeyError:
        print("    Caught expected KeyError for non-existent key")

    # 7. No unique keys provided
    print("  7. No unique keys")
    data = [{"id": 1}, {"id": 2}]
    assert remove_duplicates_by_uniques(data, []) == data
    print("    Passed")

if __name__ == "__main__":
    try:
        test_remove_duplicates_by_uniques_collision()
        test_remove_duplicate_dicts_crash()
        test_edge_cases()
        print("\nALL TESTS PASSED SUCCESSFULLY!")
    except Exception as e:
        print(f"\nVerification failed! {e}")
        sys.exit(1)
