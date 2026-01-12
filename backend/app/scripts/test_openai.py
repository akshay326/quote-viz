#!/usr/bin/env python3
"""Test OpenAI API to diagnose cleaning script issues."""

from openai import OpenAI
import os
import json

# Get API key from environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("✗ ERROR: OPENAI_API_KEY environment variable not set")
    print("  Set it with: export OPENAI_API_KEY='your-key-here'")
    exit(1)

client = OpenAI(api_key=api_key)

print("=" * 60)
print("OpenAI API Diagnostic Tests")
print("=" * 60)

# Test 1: Basic API call
print("\nTest 1: Basic API connectivity")
print("-" * 60)
try:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Say 'API works'"}],
        temperature=0
    )
    content = response.choices[0].message.content
    print(f"✓ API works!")
    print(f"  Response: {content}")
    print(f"  Model used: {response.model}")
    print(f"  Tokens: prompt={response.usage.prompt_tokens}, completion={response.usage.completion_tokens}")
except Exception as e:
    print(f"✗ API failed: {e}")
    exit(1)

# Test 2: JSON array response (current approach)
print("\nTest 2: Requesting JSON array (current approach)")
print("-" * 60)
test_quotes = [
    {"author": "Unknown", "quote": "Everything's funny until it happens to u - dave chapelle"},
    {"author": "Unknown", "quote": "akshay if your product requires users to manipulate >4 things"}
]

try:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Fix quote data. Return JSON array."},
            {"role": "user", "content": f"Fix these quotes:\n{json.dumps(test_quotes, indent=2)}\n\nReturn ONLY a valid JSON array."}
        ],
        temperature=0.1,
        max_tokens=1000
    )

    content = response.choices[0].message.content
    print(f"Raw response type: {type(content)}")
    print(f"Raw response length: {len(content) if content else 0}")
    print(f"Raw response:")
    print(content)
    print()

    if not content:
        print("✗ Response is empty/None!")
    elif not content.strip():
        print("✗ Response is whitespace only!")
    elif not content.strip().startswith('['):
        print(f"⚠ Response doesn't start with '[' - starts with: {content[:50]}")
    else:
        parsed = json.loads(content)
        print(f"✓ JSON parsed successfully: {len(parsed)} quotes")
        print(f"  First quote: {parsed[0]}")

except json.JSONDecodeError as e:
    print(f"✗ JSON parse error: {e}")
    print(f"  Response was: {content[:200]}")
except Exception as e:
    print(f"✗ Test failed: {e}")

# Test 3: With response_format (recommended approach)
print("\nTest 3: Using response_format=json_object")
print("-" * 60)
try:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Fix quote data. Return JSON with 'quotes' array."},
            {"role": "user", "content": f"Fix these quotes:\n{json.dumps(test_quotes, indent=2)}\n\nReturn valid JSON with a 'quotes' array."}
        ],
        response_format={"type": "json_object"},  # Force JSON
        temperature=0.1,
        max_tokens=1000
    )

    content = response.choices[0].message.content
    print(f"Raw response:")
    print(content)
    print()

    parsed = json.loads(content)
    print(f"✓ JSON parsed successfully!")
    print(f"  Keys: {list(parsed.keys())}")
    if 'quotes' in parsed:
        print(f"  Quotes array length: {len(parsed['quotes'])}")
        print(f"  First quote: {parsed['quotes'][0]}")

except Exception as e:
    print(f"✗ Test failed: {e}")

# Test 4: Check if it's the batch size
print("\nTest 4: Batch size test (30 quotes)")
print("-" * 60)
large_batch = [{"author": f"Author{i}", "quote": f"Quote text {i}"} for i in range(30)]

try:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Return the quotes as JSON with 'quotes' array."},
            {"role": "user", "content": f"{json.dumps(large_batch)}"}
        ],
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=8000
    )

    content = response.choices[0].message.content
    parsed = json.loads(content)
    print(f"✓ Batch of 30 processed successfully!")
    print(f"  Response length: {len(content)} chars")
    print(f"  Tokens: prompt={response.usage.prompt_tokens}, completion={response.usage.completion_tokens}")

except Exception as e:
    print(f"✗ Large batch failed: {e}")

print("\n" + "=" * 60)
print("Diagnostic Complete")
print("=" * 60)
