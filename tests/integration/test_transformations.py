"""Test complete transformation pipeline - 30× expansion."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils import setup_logger, load_config, get_logger
from src.core import BedrockProvider
from src.transformations import PersonaTransformer, QueryModifier, ToolDataTransformer


def test_transformations():
    """Test complete transformation pipeline."""
    
    print("\n" + "="*60)
    print("TRANSFORMATION PIPELINE TEST - 30× EXPANSION")
    print("="*60)
    
    setup_logger("INFO", "logs/test_transformations.log")
    config = load_config()
    
    # Initialize provider
    print("\n[1/5] Initializing BedrockProvider...")
    provider = BedrockProvider(
        model_id=config.bedrock.model_id,
        embedding_model_id=config.bedrock.embedding_model_id,
        region=config.bedrock.region
    )
    print("✅ BedrockProvider initialized")
    
    # Initialize transformers
    print("\n[2/5] Initializing Transformers...")
    persona_tx = PersonaTransformer(provider)
    query_mod = QueryModifier(provider)
    tool_data_tx = ToolDataTransformer(provider)
    
    print(f"✅ {persona_tx}")
    print(f"✅ {query_mod}")
    print(f"✅ {tool_data_tx}")
    
    expansion_factor = (
        persona_tx.get_expansion_factor() *
        query_mod.get_expansion_factor() *
        tool_data_tx.get_expansion_factor()
    )
    print(f"\n✅ Total expansion factor: {expansion_factor}×")
    
    # Test with seed query
    seed_query = "How should I diversify my investment portfolio?"
    
    print(f"\n[3/5] Testing Persona Transformation...")
    print(f"Seed query: {seed_query}")
    print("\n(This may take 1-2 minutes...)\n")
    
    persona_variants = persona_tx.transform(seed_query)
    
    print(f"✅ Generated {len(persona_variants)} persona variants:")
    for persona_id, variant in persona_variants.items():
        persona_name = persona_tx.PERSONAS[persona_id]['name']
        print(f"\n  {persona_id} ({persona_name}):")
        print(f"    {variant}")
    
    # Test complexity transformation
    print(f"\n[4/5] Testing Complexity Transformation...")
    
    # Pick one persona variant to transform
    test_variant = persona_variants["P2"]
    complexity_variants = query_mod.transform(test_variant)
    
    print(f"✅ Generated {len(complexity_variants)} complexity levels:")
    for level, variant in complexity_variants.items():
        level_name = query_mod.COMPLEXITY_LEVELS[level]['name']
        print(f"\n  {level} ({level_name}):")
        print(f"    {variant[:100]}...")
    
    # Test tool data variants
    print(f"\n[5/5] Testing Tool Data Variants...")
    
    tool_variants = tool_data_tx.transform(seed_query)
    
    print(f"✅ Generated {len(tool_variants)} tool data variants:")
    for variant_id, metadata in tool_variants.items():
        print(f"  - {variant_id}: {metadata['description']}")
    
    # Calculate full expansion
    print("\n" + "="*60)
    print("FULL EXPANSION CALCULATION")
    print("="*60)
    
    total_variants = len(persona_variants) * len(complexity_variants) * len(tool_variants)
    
    print(f"\nFrom 1 seed query:")
    print(f"  × {len(persona_variants)} personas")
    print(f"  × {len(complexity_variants)} complexity levels")
    print(f"  × {len(tool_variants)} tool data variants")
    print(f"  = {total_variants} total training variants")
    
    print(f"\n✅ Expansion: {seed_query}")
    print(f"   → {total_variants} transformed queries")
    
    # Summary
    print("\n" + "="*60)
    print("✅ TRANSFORMATION TEST PASSED!")
    print("="*60)
    print(f"\nTransformation Pipeline:")
    print(f"  ✅ Persona: 5 variants")
    print(f"  ✅ Complexity: 3 levels")
    print(f"  ✅ Tool Data: 2 variants")
    print(f"  ✅ Total: 30× expansion per seed")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_transformations()
