"""
Tests for create_neo4j_schema.py
"""

import pytest
from pathlib import Path
import sys

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent.parent / 'scripts' / 'kg_construction'
sys.path.insert(0, str(scripts_dir))

from create_neo4j_schema import (
    NODE_LABELS,
    UNIQUE_CONSTRAINTS,
    RELATIONSHIP_TYPES
)


class TestSchemaDefinitions:
    """测试 Schema 定义常量"""

    def test_node_labels_count(self):
        """测试节点标签数量（应为 6 个）"""
        assert len(NODE_LABELS) == 6

    def test_node_labels_content(self):
        """测试节点标签内容"""
        expected = ['Subject', 'Stage', 'Grade', 'Textbook', 'Chapter', 'KnowledgePoint']
        assert NODE_LABELS == expected

    def test_constraints_count(self):
        """测试约束数量（应为 3 个）"""
        assert len(UNIQUE_CONSTRAINTS) == 3

    def test_constraints_names(self):
        """测试约束名称"""
        names = [c[0] for c in UNIQUE_CONSTRAINTS]
        assert 'kp_uri_unique' in names
        assert 'subject_code_unique' in names
        assert 'textbook_isbn_unique' in names

    def test_constraints_labels(self):
        """测试约束标签"""
        labels = [c[1] for c in UNIQUE_CONSTRAINTS]
        assert 'KnowledgePoint' in labels
        assert 'Subject' in labels
        assert 'Textbook' in labels

    def test_relationship_types_count(self):
        """测试关系类型数量（应为 11 个）"""
        assert len(RELATIONSHIP_TYPES) == 11

    def test_relationship_types_content(self):
        """测试关系类型包含关键字段"""
        assert 'PREREQUISITE' in RELATIONSHIP_TYPES
        assert 'TEACHES_BEFORE' in RELATIONSHIP_TYPES
        assert 'PREREQUISITE_ON' in RELATIONSHIP_TYPES
        assert 'RELATED_TO' in RELATIONSHIP_TYPES
        assert 'SUB_CATEGORY' in RELATIONSHIP_TYPES


class TestCypherGeneration:
    """测试 Cypher 语句生成"""

    def test_constraint_cypher_format(self):
        """测试约束 Cypher 语句格式"""
        for name, label, prop in UNIQUE_CONSTRAINTS:
            cypher = (
                f"CREATE CONSTRAINT IF NOT EXISTS {name} "
                f"FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE"
            )
            assert "CREATE CONSTRAINT" in cypher
            assert "IF NOT EXISTS" in cypher
            assert "IS UNIQUE" in cypher
            assert label in cypher
            assert prop in cypher