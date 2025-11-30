"""
Validate training data format.

Checks:
- Required fields present
- Field types correct
- Values within expected ranges
- No empty or malformed data
"""

import sys
import json
from pathlib import Path
from collections import Counter

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils import read_jsonl


def validate_training_example(example: dict, index: int, config_fields: dict) -> list:
    """
    Validate a single training example.
    
    Returns list of errors (empty if valid).
    """
    errors = []
    
    # Check required fields
    query_field = config_fields.get('query', 'Q')
    cot_field = config_fields.get('cot', 'COT')
    tools_field = config_fields.get('tools', 'Tool Set')
    decision_field = config_fields.get('decision', 'Decision')
    
    required_fields = [query_field, cot_field, tools_field, decision_field]
    
    for field in required_fields:
        if field not in example:
            errors.append(f"Example {index}: Missing required field '{field}'")
    
    if errors:
        return errors
    
    # Validate query
    query = example.get(query_field, '')
    if not isinstance(query, str) or len(query.strip()) < 10:
        errors.append(f"Example {index}: Query too short or invalid")
    
    # Validate COT
    cot = example.get(cot_field, '')
    if not isinstance(cot, str) or len(cot.strip()) < 20:
        errors.append(f"Example {index}: COT too short (should be reasoning)")
    
    # Validate tools
    tools = example.get(tools_field, [])
    if not isinstance(tools, list):
        errors.append(f"Example {index}: Tool Set must be a list")
    
    # Validate decision
    decision = example.get(decision_field, '')
    if not isinstance(decision, str):
        errors.append(f"Example {index}: Decision must be a string")
    else:
        # Check decision format
        valid_decisions = ['CALL', 'ASK', 'ANSWER']
        decision_upper = decision.upper()
        
        is_valid = False
        for valid_dec in valid_decisions:
            if decision_upper.startswith(valid_dec):
                is_valid = True
                break
        
        if not is_valid:
            errors.append(f"Example {index}: Invalid decision format (should start with CALL, ASK, or ANSWER)")
    
    return errors


def validate_file(file_path: Path, config_fields: dict = None) -> dict:
    """
    Validate entire training file.
    
    Returns validation report.
    """
    if config_fields is None:
        config_fields = {
            'query': 'Q',
            'cot': 'COT',
            'tools': 'Tool Set',
            'decision': 'Decision'
        }
    
    print(f"\n{'='*60}")
    print(f"VALIDATING: {file_path.name}")
    print(f"{'='*60}\n")
    
    # Load data
    try:
        examples = read_jsonl(file_path)
    except Exception as e:
        return {
            'valid': False,
            'error': f"Failed to load file: {e}",
            'total_examples': 0
        }
    
    print(f"Loaded {len(examples)} examples\n")
    
    # Validate each example
    all_errors = []
    valid_count = 0
    
    for i, example in enumerate(examples, 1):
        errors = validate_training_example(example, i, config_fields)
        if errors:
            all_errors.extend(errors)
        else:
            valid_count += 1
    
    # Report
    is_valid = len(all_errors) == 0
    
    report = {
        'valid': is_valid,
        'total_examples': len(examples),
        'valid_examples': valid_count,
        'invalid_examples': len(examples) - valid_count,
        'errors': all_errors
    }
    
    # Print summary
    if is_valid:
        print("✅ ALL EXAMPLES VALID!")
    else:
        print(f"❌ VALIDATION FAILED")
        print(f"\nErrors found: {len(all_errors)}")
        for error in all_errors[:10]:  # Show first 10
            print(f"  - {error}")
        if len(all_errors) > 10:
            print(f"  ... and {len(all_errors) - 10} more errors")
    
    print(f"\nSummary:")
    print(f"  Total examples: {len(examples)}")
    print(f"  Valid: {valid_count}")
    print(f"  Invalid: {len(examples) - valid_count}")
    
    return report


def main():
    """Main validation function."""
    
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_format.py <file.jsonl>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    # Validate
    report = validate_file(file_path)
    
    # Exit code
    sys.exit(0 if report['valid'] else 1)


if __name__ == "__main__":
    main()
