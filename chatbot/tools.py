"""
OpenAI Function Calling Tool Definitions
Generate tool definitions from query templates (DeepSeek-compatible).
"""
from typing import List, Dict, Any
from .templates import load_templates


# query_custom tool definition (static — not from DB templates)
QUERY_CUSTOM_TOOL = {
    "type": "function",
    "function": {
        "name": "query_custom",
        "description": """สร้าง SQL query เองเมื่อไม่มี template ตรงกับคำถาม
ใช้ได้กับทุกตารางใน ERP schema: docinfo, transtkd, transtkh, skumaster, brand,
arfile, apfile, skubalance, skumove, ardetail, apdetail, tranpayh, tranpayd,
arpayment, appayment, bankstatement, bankfile, doctype, batch_branch,
goods, goodsunit, accountchart, arplu, cashbook, companyinfo, glperiod,
paymenttype, salesmans, skuap, sldetail, vattable

⚠️ กฎ:
- SELECT เท่านั้น
- ทุก JOIN ต้องมี branch_id: AND a.branch_id = b.branch_id
- WHERE ต้องกรอง branch_id: AND d.branch_id = :branch_id
- ใช้ ILIKE สำหรับค้นหาภาษาไทย
- ใส่ LIMIT เสมอ
- parameter ใช้ :param_name เท่านั้น ห้ามแทรกค่าใน SQL string""",
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "SQL SELECT statement with :param placeholders (e.g. :date_from, :branch_id). Use ILIKE for Thai text search. Always include branch_id filtering."
                },
                "date_from": {
                    "type": "string",
                    "description": "วันเริ่ม YYYY-MM-DD (ใช้ใน SQL เป็น :date_from)"
                },
                "date_to": {
                    "type": "string",
                    "description": "วันสิ้นสุด YYYY-MM-DD (ใช้ใน SQL เป็น :date_to)"
                },
                "as_of_date": {
                    "type": "string",
                    "description": "วันที่ ณ วันนั้น YYYY-MM-DD (ใช้ใน SQL เป็น :as_of_date)"
                },
                "branch_id": {
                    "type": "integer",
                    "description": "รหัสสาขา (ใช้ใน SQL เป็น :branch_id) null=ทุกสาขา"
                },
                "customer": {
                    "type": "string",
                    "description": "ชื่อลูกค้า/ร้านค้า (ใช้ใน SQL เป็น :customer)"
                },
                "sku": {
                    "type": "string",
                    "description": "ชื่อสินค้า/SKU (ใช้ใน SQL เป็น :sku)"
                },
                "brand": {
                    "type": "string",
                    "description": "ชื่อยี่ห้อ (ใช้ใน SQL เป็น :brand)"
                },
                "supplier": {
                    "type": "string",
                    "description": "ชื่อผู้ขาย/เจ้าหนี้ (ใช้ใน SQL เป็น :supplier)"
                },
                "bank": {
                    "type": "string",
                    "description": "ชื่อธนาคาร (ใช้ใน SQL เป็น :bank)"
                },
                "doc_type": {
                    "type": "string",
                    "description": "ประเภทเอกสาร (ใช้ใน SQL เป็น :doc_type)"
                },
                "limit_rows": {
                    "type": "integer",
                    "description": "จำนวนแถวสูงสุด (ใช้ใน SQL เป็น :limit_rows) default=100, max=100"
                }
            },
            "required": ["sql"]
        }
    }
}


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

    # Add query_custom as the last tool (DeepSeek picks templates first)
    tools.append(QUERY_CUSTOM_TOOL)

    return tools


def build_tools_without_custom() -> List[Dict[str, Any]]:
    """Build tools without query_custom (for template-only mode)."""
    tools = build_tools()
    return [t for t in tools if t["function"]["name"] != "query_custom"]
