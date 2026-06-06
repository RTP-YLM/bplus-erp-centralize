"""
Claude Tool Definitions
Generate tool definitions from query templates
"""
from typing import List, Dict, Any
from .templates import load_templates


def build_tools() -> List[Dict[str, Any]]:
    """
    Build Claude tool definitions from query templates
    Returns: list of tool dicts compatible with Claude API
    """
    templates = load_templates()
    tools = []

    for template in templates.values():
        # Build input schema from params
        properties = {}
        required = []

        for param in template['params']:
            param_name = param['name']
            param_type = param['type']
            param_desc = param.get('description', '')
            param_required = param.get('required', False)

            # Map Python types to JSON schema types
            if param_type == 'string':
                properties[param_name] = {
                    "type": "string",
                    "description": param_desc
                }
            elif param_type == 'integer':
                properties[param_name] = {
                    "type": "integer",
                    "description": param_desc
                }
            elif param_type == 'number':
                properties[param_name] = {
                    "type": "number",
                    "description": param_desc
                }
            elif param_type == 'boolean':
                properties[param_name] = {
                    "type": "boolean",
                    "description": param_desc
                }

            if param_required:
                required.append(param_name)

        # Build tool definition
        tool = {
            "name": template['name'],
            "description": template['description'],
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }

        tools.append(tool)

    return tools
