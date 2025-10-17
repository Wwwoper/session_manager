#!/usr/bin/env python3
"""
Session Manager - Main entry point
"""

import sys
from pathlib import Path

from .core.config import GlobalConfig, ConfigError
from .core.project_registry import ProjectRegistry
from .cli.commands import CLI
from .utils.formatters import print_error, print_warning


def main(args: list = None) -> int:
    """
    Main entry point for Session Manager CLI
    
    Args:
        args: Command line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    if args is None:
        args = sys.argv[1:]
    
    try:
        # Initialize configuration
        config = GlobalConfig()
        config.load()
        
        # Initialize project registry
        registry = ProjectRegistry(config)
        
        # Initialize CLI
        cli = CLI(config, registry)
        
        # Run command
        return cli.run(args)
        
    except ConfigError as e:
        print_error(f"Configuration error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n")
        print_warning("Interrupted by user")
        return 130
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())