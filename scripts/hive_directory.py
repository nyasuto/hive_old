#!/usr/bin/env python3
"""
Hive Directory CLI Script

.hive/ディレクトリ操作のためのCLIスクリプト
"""

import sys
from pathlib import Path

# プロジェクトのパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from hive.hive_directory.cli import main

if __name__ == "__main__":
    sys.exit(main())
