"""
Integration tests for kg_construction scripts
"""

import pytest
import subprocess
from pathlib import Path


class TestSplitMainScript:
    """测试 split_main_ttl.py 脚本"""

    def test_script_help(self):
        """测试脚本帮助信息"""
        result = subprocess.run(
            ['python', 'scripts/kg_construction/split_main_ttl.py', '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'input' in result.stdout.lower() or 'input' in result.stdout

    def test_script_output_files(self):
        """测试脚本能正常执行并输出文件"""
        split_dir = Path('data/edukg/split')
        if split_dir.exists():
            files = list(split_dir.glob('main-*.ttl'))
            assert len(files) >= 8, f"Expected at least 8 split files, found {len(files)}"


class TestSplitMaterialScript:
    """测试 split_material_ttl.py 脚本"""

    def test_script_help(self):
        """测试脚本帮助信息"""
        result = subprocess.run(
            ['python', 'scripts/kg_construction/split_material_ttl.py', '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

    def test_script_output_files(self):
        """测试脚本能正常执行并输出文件"""
        split_dir = Path('data/edukg/split')
        if split_dir.exists():
            files = list(split_dir.glob('material-*.ttl'))
            assert len(files) >= 9, f"Expected at least 9 material split files, found {len(files)}"


class TestSchemaScript:
    """测试 create_neo4j_schema.py 脚本"""

    def test_script_help(self):
        """测试脚本帮助信息"""
        result = subprocess.run(
            ['python', 'scripts/kg_construction/create_neo4j_schema.py', '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

    def test_script_dry_run(self):
        """测试 dry-run 模式"""
        result = subprocess.run(
            ['python', 'scripts/kg_construction/create_neo4j_schema.py', '--dry-run'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'kp_uri_unique' in result.stdout
        assert 'subject_code_unique' in result.stdout
        assert 'textbook_isbn_unique' in result.stdout


class TestValidateScript:
    """测试 validate_schema.py 脚本"""

    def test_script_help(self):
        """测试脚本帮助信息"""
        result = subprocess.run(
            ['python', 'scripts/kg_construction/validate_schema.py', '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0