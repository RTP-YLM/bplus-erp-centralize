"""
OpenAI Function Calling Tool Definitions
Generate tool definitions from query templates (DeepSeek-compatible).
"""
from typing import List, Dict, Any
from .templates import load_templates


def build_tools() -> List[Dict[str, Any]]:
    """
    Build OpenAI function-calling tool definitions from query templates.
    Returns: list of tool dicts compatible with OpenAI/DeepSeek API.
    """
    templates = load_templates()
    tools = []

    for template in templates.values():
        # Build parameters schema from params
        properties = {}
        required = []

        for param in template['params']:
            param_name = param['name']
            param_type = param['type']
            param_desc = param.get('description', '')
            param_required = param.get('required', False)

            # Map Python types to JSON schema types
            type_map = {
                'string': 'string',
                'integer': 'integer',
                'number': 'number',
                'boolean': 'boolean',
            }
            json_type = type_map.get(param_type, 'string')

            properties[param_name] = {
                "type": json_type,
                "description": param_desc
            }

            if param_required:
                required.append(param_name)

        # Build OpenAI function-calling tool definition
        tool = {
            "type": "function",
            "function": {
                "name": template['name'],
                "description": template['description'],
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

        tools.append(tool)

    return tools
