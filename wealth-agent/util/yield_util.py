"""Serialize application events. Model-generated text never controls the envelope."""

import json
import uuid

res_tool = {
    "query_fund_info_tool": "获取基金相关信息",
    "query_customer_info_tool": "获取客户相关信息",
    "query_manager_info_tool": "获取基金经理相关信息",
    "query_company_info_tool": "获取基金公司相关信息",
    "compare_funds_tool": "正在进行基金比较",
    "choose_fund_tool": "筛选符合条件的基金",
    "choose_customer_tool": "筛选符合条件的客户",
    "choose_manager_tool": "筛选符合条件的基金经理",
    "choose_company_tool": "筛选符合条件的基金公司",
}


async def generate_yield_json(type, request_id, name, status, data):
    result = {"type": type, "request_id": request_id}
    if type == "text":
        result["answer"] = data
    elif type == "plugin":
        result["plugin"] = {
            "request_id": request_id,
            "pluginName": name,
            "status": status,
            "describe": data,
        }
    elif type == "error":
        result["error"] = data
    elif type == "card":
        result.update(card_id=name, data=data, data_id=uuid.uuid4().hex)
    else:
        raise ValueError("Unsupported event type")
    return json.dumps(result, ensure_ascii=False, allow_nan=False)
