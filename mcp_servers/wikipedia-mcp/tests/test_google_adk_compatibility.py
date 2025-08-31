"""
Tests for Google ADK compatibility - ensuring tool schemas don't use anyOf alongside other fields.
"""

import pytest
import asyncio
import json
from wikipedia_mcp.server import create_server

class TestGoogleADKCompatibility:
    """Test that all tools generate Google ADK compatible schemas."""

    @pytest.mark.asyncio
    async def test_all_tools_schemas_compatible(self):
        """Test that all tool schemas are compatible with Google ADK agents."""
        server = create_server()
        tools = await server.get_tools()
        
        # Tools that previously had anyOf issues
        problematic_tools = ['summarize_article_for_query', 'summarize_article_section', 'extract_key_facts']
        
        for tool_name in tools:
            tool_obj = await server.get_tool(tool_name)
            schema = tool_obj.parameters
            
            # Check each parameter for anyOf usage
            for param_name, param_schema in schema.get('properties', {}).items():
                assert 'anyOf' not in param_schema, f"Tool '{tool_name}' parameter '{param_name}' uses anyOf which is incompatible with Google ADK"
                
                # Verify that if a default is provided, the schema is simple
                if 'default' in param_schema:
                    # Should only have: type, default, title (and optionally description)
                    allowed_keys = {'type', 'default', 'title', 'description'}
                    actual_keys = set(param_schema.keys())
                    unexpected_keys = actual_keys - allowed_keys
                    assert not unexpected_keys, f"Tool '{tool_name}' parameter '{param_name}' has unexpected keys: {unexpected_keys}"

    @pytest.mark.asyncio 
    async def test_summarize_article_for_query_schema(self):
        """Test specific schema for summarize_article_for_query tool."""
        server = create_server()
        tool_obj = await server.get_tool('summarize_article_for_query')
        schema = tool_obj.parameters
        
        # Check max_length parameter specifically
        max_length_param = schema['properties']['max_length']
        assert max_length_param['type'] == 'integer'
        assert max_length_param['default'] == 250
        assert 'anyOf' not in max_length_param
        assert max_length_param['title'] == 'Max Length'
        
        # Check required parameters
        assert set(schema['required']) == {'title', 'query'}

    @pytest.mark.asyncio
    async def test_summarize_article_section_schema(self):
        """Test specific schema for summarize_article_section tool."""
        server = create_server()
        tool_obj = await server.get_tool('summarize_article_section')
        schema = tool_obj.parameters
        
        # Check max_length parameter specifically
        max_length_param = schema['properties']['max_length']
        assert max_length_param['type'] == 'integer'
        assert max_length_param['default'] == 150
        assert 'anyOf' not in max_length_param
        assert max_length_param['title'] == 'Max Length'
        
        # Check required parameters
        assert set(schema['required']) == {'title', 'section_title'}

    @pytest.mark.asyncio
    async def test_extract_key_facts_schema(self):
        """Test specific schema for extract_key_facts tool."""
        server = create_server()
        tool_obj = await server.get_tool('extract_key_facts')
        schema = tool_obj.parameters
        
        # Check topic_within_article parameter specifically
        topic_param = schema['properties']['topic_within_article']
        assert topic_param['type'] == 'string'
        assert topic_param['default'] == ""
        assert 'anyOf' not in topic_param
        assert topic_param['title'] == 'Topic Within Article'
        
        # Check count parameter
        count_param = schema['properties']['count'] 
        assert count_param['type'] == 'integer'
        assert count_param['default'] == 5
        
        # Check required parameters
        assert set(schema['required']) == {'title'}

    def test_empty_string_to_none_conversion(self):
        """Test the conversion logic for empty string to None."""
        # This tests the logic used in extract_key_facts tool
        def convert_topic(topic_within_article: str):
            return topic_within_article if topic_within_article.strip() else None
        
        # Test cases
        assert convert_topic("") is None
        assert convert_topic("   ") is None  # whitespace only
        assert convert_topic("general") == "general"
        assert convert_topic("history") == "history"
        assert convert_topic(" history ") == " history "  # preserve as-is

    @pytest.mark.asyncio
    async def test_tool_compatibility_json_serialization(self):
        """Test that all tool schemas can be properly JSON serialized for Google ADK."""
        server = create_server()
        tools = await server.get_tools()
        
        for tool_name in tools:
            tool_obj = await server.get_tool(tool_name)
            schema = tool_obj.parameters
            
            # Should be able to serialize to JSON without issues
            json_str = json.dumps(schema)
            
            # Should be able to deserialize back
            parsed_schema = json.loads(json_str)
            assert parsed_schema == schema
            
            # Ensure no complex nested anyOf structures
            def check_no_anyof_recursively(obj):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key == 'anyOf':
                            # If anyOf exists, it should be the only schema key
                            schema_keys = set(obj.keys()) - {'title', 'description', 'default'}
                            if len(schema_keys) > 1:
                                return False
                        if not check_no_anyof_recursively(value):
                            return False
                elif isinstance(obj, list):
                    for item in obj:
                        if not check_no_anyof_recursively(item):
                            return False
                return True
                
            assert check_no_anyof_recursively(schema), f"Tool '{tool_name}' has complex anyOf structure incompatible with Google ADK"