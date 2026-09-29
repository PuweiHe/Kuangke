import asyncio
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from config.prompt import get_pre_agent_prompt
from config import get_project_client_config, get_project_api_uri
from util.http_util import http_execute_async, UpstreamError
from model.ChatBody import ChatBody
from model.exceptions import EntityConflictError, TokenInvalidError


async def query_single_entity(
    entity: str,
) -> None | dict[str, str | None] | dict[str, str] | dict[str, str | list[Any]]:
    try:
        url = get_project_api_uri("wealth", "search_entity")
        header = {}
        payload = {"name": entity}
        response = await http_execute_async(url, "POST", payload, header)
        if str(response["code"]) in {"0", "200"}:
            content_list = response.get("content")
            if content_list is None:
                content_list = []
            if not isinstance(content_list, list) or any(
                not isinstance(item, dict) for item in content_list
            ):
                raise UpstreamError("Invalid entity response")
            if len(content_list) == 0:
                return {"entity": entity, "status": "not_found", "data": None}
            elif len(content_list) == 1:
                entity_type = content_list[0].get("type", "")
                if entity_type == "产品":
                    prod_code_qry = content_list[0].get("prod_code", "")
                    if prod_code_qry:
                        return {
                            "entity": entity,
                            "status": "success",
                            "data": f"{entity}(基金代码：{prod_code_qry})",
                        }
                    else:
                        return {"entity": entity, "status": "no_code", "data": entity}
                elif entity_type == "公司":
                    company_id = content_list[0].get("prod_code", "")
                    if company_id:
                        return {
                            "entity": entity,
                            "status": "success",
                            "data": f"{entity} 是家基金公司,基金公司ID为{company_id}",
                        }
                    else:
                        return {"entity": entity, "status": "no_code", "data": entity}
            else:
                entity_options = []
                for item in content_list:
                    if item.get("type") == "产品":
                        fund_dict = {
                            "基金简称": item.get("short_name_exchange", ""),
                            "基金代码": item.get("prod_code", ""),
                            "基金全称": item.get("full_name", ""),
                        }
                        entity_options.append(fund_dict)
                    elif item.get("type") == "公司":
                        company_dict = {
                            "基金公司全称": item.get("full_name", ""),
                            "基金公司ID": item.get("prod_code", ""),
                        }
                        entity_options.append(company_dict)
                return {"entity": entity, "status": "multiple", "data": entity_options}
        else:
            raise UpstreamError("Entity lookup failed")
    except (TokenInvalidError, UpstreamError):
        raise
    except (KeyError, TypeError, AttributeError) as exc:
        raise UpstreamError("Invalid entity response") from exc
    return {"entity": entity, "status": "no_code", "data": entity}


async def query_entities_with_concurrency(
    entities: List[str], max_concurrent: int = 3
) -> tuple[List[str], Optional[List[Dict]]]:
    if not isinstance(max_concurrent, int) or max_concurrent < 1:
        raise ValueError("max_concurrent must be positive")
    if not entities:
        return ([], None)
    semaphore = asyncio.Semaphore(max_concurrent)

    async def query_with_semaphore(entity: str):
        async with semaphore:
            return await query_single_entity(entity)

    tasks = [query_with_semaphore(entity) for entity in entities]
    results = await asyncio.gather(*tasks)
    result_list = []
    multiple_results_list = []
    for result in results:
        if result["status"] == "multiple":
            multiple_results_list.append(result)
        elif result["status"] == "success":
            result_list.append(result["data"])
        elif result["status"] in ["not_found", "no_code"]:
            continue
        else:
            continue
    return (result_list, multiple_results_list if multiple_results_list else None)


async def recognize_and_query_entities(chat_body: ChatBody, question: str):
    from agent.entity_schema import EntityNames

    model = ChatOpenAI(
        base_url=get_project_client_config(chat_body.product_id, "base_url"),
        model=get_project_client_config(chat_body.product_id, "model"),
        api_key=get_project_client_config(chat_body.product_id, "api_key"),
        temperature=0,
        timeout=20,
        max_retries=1,
    )
    extracted = await model.with_structured_output(EntityNames).ainvoke(
        [
            {"role": "system", "content": get_pre_agent_prompt()},
            {"role": "user", "content": question},
        ]
    )
    names = EntityNames.model_validate(extracted).entities
    results, multiple = await query_entities_with_concurrency(names)
    if multiple:
        raise EntityConflictError(
            conflicts=[{"entity_name": r["entity"], "options": r["data"]} for r in multiple]
        )
    return results
