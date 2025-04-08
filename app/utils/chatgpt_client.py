import logging
import json
import os
from typing import Dict, Any
import httpx
import asyncio

logger = logging.getLogger(__name__)


class ChatGPTClient:
    """与ChatGPT API交互的客户端"""

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.api_url = "https://api.openai.com/v1/chat/completions"
        if not self.api_key:
            logger.error("未设置OpenAI API密钥")
            raise ValueError("未设置OpenAI API密钥")

    async def analyze_consumer_data(
        self, consumer_data: Dict[str, Any]
    ) -> Dict[str, Any]:

        try:
            # 构建提示词
            prompt = self._build_analysis_prompt(consumer_data)

            # 准备API请求
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }

            payload = {
                "model": "gpt-3.5-turbo-16k",  # 使用支持更长上下文的模型
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一位专业的财务分析师和消费顾问，擅长分析购物数据并提供洞察和建议。",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.api_url, headers=headers, json=payload
                )

                response_data = response.json()

                if response.status_code != 200:
                    logger.error(f"ChatGPT API请求失败: {response_data}")
                    return {
                        "error": f"API请求失败: {response_data.get('error', {}).get('message')}"
                    }

                analysis_result = response_data["choices"][0]["message"]["content"]

                try:

                    if analysis_result.startswith("{") and analysis_result.endswith(
                        "}"
                    ):
                        result_json = json.loads(analysis_result)
                    else:
                        # 尝试提取JSON部分
                        json_start = analysis_result.find("{")
                        json_end = analysis_result.rfind("}") + 1
                        if json_start >= 0 and json_end > json_start:
                            result_json = json.loads(
                                analysis_result[json_start:json_end]
                            )
                        else:
                            # 如果没有JSON格式，将文本作为分析内容返回
                            result_json = {"analysis_text": analysis_result}
                except json.JSONDecodeError:
                    result_json = {"analysis_text": analysis_result}

                return {"analysis": result_json, "raw_response": analysis_result}

        except Exception as e:
            logger.error(f"调用ChatGPT API分析数据时出错: {str(e)}")
            return {"error": f"分析过程中出错: {str(e)}"}

    def _build_analysis_prompt(self, consumer_data: Dict[str, Any]) -> str:

        # 修改简化数据结构
        simplified_data = {
            "summary": consumer_data["summary"],
            "invoices_count": len(consumer_data["invoices"]),
            "recent_invoices": consumer_data["invoices"][:5],  # 只包含最近5份发票
        }

        all_items = []
        item_counts = {}

        for invoice in consumer_data["invoices"]:
            for item in invoice.get("items", []):
                all_items.append(
                    {
                        "name": item["name"],
                        "total_price": item["total_price"],
                        "date": invoice["date"],
                    }
                )

                item_name = item["name"].strip().upper()
                if item_name not in item_counts:
                    item_counts[item_name] = 0
                item_counts[item_name] += 1

        top_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)

        simplified_data["all_items"] = all_items
        simplified_data["item_counts"] = top_items[:10]  # 前10个最常购买的商品

        # 构建提示词，明确强调商品数据
        prompt = f"""
you are a professional financial analyst and consumer advisor, good at analyzing shopping data and providing insights and suggestions.

shopping data:

- summary of invoice: {consumer_data['summary']['total_invoices']}
- summary of items: {consumer_data['summary']['total_items']}
- summart of spent: {consumer_data['summary']['total_spent']} 欧元

Items purchased and frequency:
{json.dumps(simplified_data['item_counts'], indent=2, ensure_ascii=False)}

Recent invoice details:
{json.dumps(simplified_data['recent_invoices'], indent=2, ensure_ascii=False)}

Please pay special attention to the following aspects:
1. Basic consumption pattern analysis: overall consumption, average consumption amount, shopping frequency, etc.
2. Product analysis: most frequently purchased products and their category distribution
- Please infer possible categories based on product names (such as fruits and vegetables, meat, beverages, etc.)
3. Consumption habit insights: consumption habit analysis based on shopping time, store selection, etc.
4. Personalized suggestions: how to optimize consumption, possible money-saving strategies, etc.

Please return the analysis results in JSON format with the following structure:
{{
  "basic_analysis": {{
    "spending_pattern": "Describe overall consumption patterns",
    "avg_spending": "average consumption amount",
    "shopping_frequency": "frequency of shopping",
  }},
  "items_analysis": {{
    "frequently_bought": ["most frequently bought products"],
    "possible_categories": {{"category decription": "Proportion/Number of products"}}
  }},
  "shopping_habits": {{
    "preferred_stores": ["Preferred Store"],
    "time_patterns": "model of shopping time",
  }},
  "recommendations": [
    "suggestion 1",
    "suggestion 2",
    "..."
  ]
}}
"""
        return prompt
