"""Serialize application events. Model-generated text never controls the envelope."""

import json
import uuid

res_tool = {
    "customer_info_tool": "查询客户基本信息",
    "customer_hold_info_tool": "查询客户持仓信息",
    "customer_opened_business_info_tool": "查询指定客户的已开通业务信息",
    "customer_available_business_info_tool": "查询指定客户的可开通业务信息",
    "customer_participated_business_info_tool": "查询指定客户的已参与业务信息",
    "web_search_tool": "正在联网搜索",
    "filter_customer_info_tool": "筛选客户基本信息数据",
    "filter_revenue_generation_info_tool": "筛选客户创收数据",
    "filter_property_info_tool": "筛选客户资产数据",
    "asset_information_tool": "查询客户资产信息",
    "revenue_generating_information_tool": "查询客户创收信息",
    "transaction_volume_information_tool": "查询客户交易量信息",
    "filter_indicator_tool": "正在筛选用户指标数据",
    "get_labels_tool": "正在查询标签数据",
    "branch_company_info_tool": "查询机构基本信息",
    "business_management_tool": "筛选机构经营指标数据",
    "performance_report_tool": "正在生成业绩报告",
    "sandbox_tool": "正在计算并绘图",
}


def generate_yield_json(type, request_id, name, status, data):
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
