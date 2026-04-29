import json

# Check if file exists and view first few lines
jsonl_path = "D:/TwitterBirth/data/json/batch_requests_child_gender_batch_0.jsonl"

try:
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"File exists: Yes")
    print(f"Total lines: {len(lines)}")
    print(f"File size: {len(''.join(lines))} bytes")

    # Check first line
    if lines:
        print("\nFirst request:")
        first_request = json.loads(lines[0])
        print(json.dumps(first_request, indent=2)[:500])

    # Check if all lines are valid JSON
    invalid_lines = []
    for i, line in enumerate(lines[:100]):  # Check first 100
        try:
            json.loads(line)
        except json.JSONDecodeError as e:
            invalid_lines.append((i, str(e)))

    if invalid_lines:
        print(f"\n⚠️ Found {len(invalid_lines)} invalid JSON lines:")
        for i, error in invalid_lines[:5]:
            print(f"Line {i}: {error}")
    else:
        print("\n✓ First 100 lines are valid JSON")

except FileNotFoundError:
    print(f"File not found: {jsonl_path}")
except Exception as e:
    print(f"Error: {e}")