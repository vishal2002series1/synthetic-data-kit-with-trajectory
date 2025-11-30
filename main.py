"""
Trajectory Synthetic Data Generator - Main CLI Entry Point

Usage:
    python main.py <command> [options]

Commands:
    ingest          Ingest single PDF
    ingest-batch    Ingest directory of PDFs
    generate-qa     Generate Q&A from documents
    transform       Transform queries (30× expansion)
    generate        Generate trajectories
    pipeline        Run complete pipeline
    stats           Show system statistics
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils import setup_logger, load_config
from src.cli import (
    ingest_commands,
    generate_commands,
    transform_commands,
    pipeline_commands
)


def create_parser():
    """Create argument parser with all commands."""
    
    parser = argparse.ArgumentParser(
        description="Trajectory Synthetic Data Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest PDFs
  python main.py ingest data/pdfs/document.pdf
  python main.py ingest-batch data/pdfs/
  
  # Generate Q&A
  python main.py generate-qa --limit 50
  
  # Transform queries
  python main.py transform queries.json --output expanded.jsonl
  
  # Generate trajectories
  python main.py generate queries.json --output trajectories.jsonl
  
  # Complete pipeline
  python main.py pipeline queries.json --output-dir output/
  
  # Show statistics
  python main.py stats
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Ingest commands
    ingest_commands.add_ingest_parser(subparsers)
    ingest_commands.add_ingest_batch_parser(subparsers)
    
    # Generate commands
    generate_commands.add_generate_qa_parser(subparsers)
    generate_commands.add_generate_trajectories_parser(subparsers)
    
    # Transform commands
    transform_commands.add_transform_parser(subparsers)
    
    # Pipeline commands
    pipeline_commands.add_pipeline_parser(subparsers)
    pipeline_commands.add_stats_parser(subparsers)
    
    return parser


def main():
    """Main CLI entry point."""
    
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Setup logging
    setup_logger(
        level="INFO",
        log_file="logs/trajectory_generator.log"
    )
    
    # Load config
    config = load_config()
    
    # Route to appropriate command
    if args.command == 'ingest':
        ingest_commands.run_ingest(args, config)
    
    elif args.command == 'ingest-batch':
        ingest_commands.run_ingest_batch(args, config)
    
    elif args.command == 'generate-qa':
        generate_commands.run_generate_qa(args, config)
    
    elif args.command == 'generate':
        generate_commands.run_generate_trajectories(args, config)
    
    elif args.command == 'transform':
        transform_commands.run_transform(args, config)
    
    elif args.command == 'pipeline':
        pipeline_commands.run_pipeline(args, config)
    
    elif args.command == 'stats':
        pipeline_commands.run_stats(args, config)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
