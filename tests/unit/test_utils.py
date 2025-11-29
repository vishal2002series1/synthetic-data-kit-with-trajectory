"""Test utility modules."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils import setup_logger, load_config, get_logger
from src.utils import ensure_dir, write_json, read_json


def test_logger():
    """Test logger setup."""
    print("\n" + "="*60)
    print("TEST 1: Logger Setup")
    print("="*60)
    
    logger = setup_logger("INFO", "logs/test.log")
    logger.info("✅ Logger initialized")
    logger.debug("Debug message")
    logger.success("✅ Success message")
    logger.warning("⚠️  Warning message")
    
    print("✅ Logger test passed\n")


def test_config():
    """Test configuration loader."""
    print("="*60)
    print("TEST 2: Configuration Loader")
    print("="*60)
    
    try:
        config = load_config()
        logger = get_logger(__name__)
        
        logger.info(f"✅ Config loaded from: {config.config_path}")
        logger.info(f"Model ID: {config.bedrock.model_id}")
        logger.info(f"Embedding Model: {config.bedrock.embedding_model_id}")
        logger.info(f"ChromaDB Collection: {config.chromadb.collection_name}")
        logger.info(f"Output Format: {config.output.format}")
        logger.info(f"Query Field: {config.output.schema.fields.query}")
        
        print("✅ Config test passed\n")
        return config
        
    except Exception as e:
        print(f"❌ Config test failed: {e}\n")
        raise


def test_file_utils():
    """Test file utilities."""
    print("="*60)
    print("TEST 3: File Utilities")
    print("="*60)
    
    # Test JSON operations
    test_data = {
        "test": "data",
        "number": 123,
        "nested": {"key": "value"}
    }
    
    test_file = "data/output/test_file.json"
    write_json(test_data, test_file)
    print(f"✅ Wrote test file: {test_file}")
    
    read_data = read_json(test_file)
    assert read_data == test_data, "JSON data mismatch"
    print("✅ Read and verified JSON")
    
    print("✅ File utils test passed\n")


if __name__ == "__main__":
    print("\n🧪 TESTING UTILITY MODULES")
    print("="*60)
    
    test_logger()
    config = test_config()
    test_file_utils()
    
    print("\n" + "="*60)
    print("✅ ALL UTILITY TESTS PASSED!")
    print("="*60 + "\n")
