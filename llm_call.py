import copy
import uuid
import time
import json
import requests
import configparser
from typing import Optional
from vipserver.vip_client import get_one_validate_host

modelserver_config = configparser.ConfigParser()

modelserver_config.read('config/modelserver.ini', encoding='utf-8')

class TppSseClient:

    def __init__(self, params: dict = {}, modelserver_name: Optional[str] = None, modelserver_config_path: str = 'configs/modelserver.ini',
                 domain: str = "aigc.tpp.taobao.com.vipserver_pre"):
        # 线上PUBLISH，预发PRE_PUBLISH
        # 预发tppwork.taobao.com/pre
        # 预发aigc.tpp.taobao.com.vipserver_pre，生产aigc.tpp.taobao.com.vipserver
        self.vip_domain = domain
        modelserver_config.read(modelserver_config_path, encoding='utf-8')

        api = modelserver_config.get('modelserver', 'api')
        biz = modelserver_config.get('modelserver', 'biz')
        if modelserver_name:
            model = modelserver_name
        else:
            model = modelserver_config.get('modelserver', 'model')
        key = modelserver_config.get('modelserver', 'key')

        # print('Model server request config')
        # print(f'api : {api}\nbiz : {biz}\nmodel : {model}\nkey : {key}')

        self.formatter = {
            "api": api,  # 流式调用用callModelStream， 非流式用callModel
            "reqTraceId": "",  # 调用方traceid， 非场景互调时请传入（ 因为http调tpp时， traceid会换
            "biz": biz,  # 和modelserver平台对接后分配
            "model": model,  # 和modelserver平台对接后分配
            "key": key,  # 使用阿里云或idealab接口时分配的子key， 对接后提供
            "input": {
                "messages": [],  # 模型业务参数
            },
            "parameters": {},
        }
    
    # def post(self, messages, trace_id, output_type="default", is_local=False, **kwargs):
    #     data = copy.deepcopy(self.formatter)
    #     data['input']['messages'] = messages
    #     data['input'] = json.dumps(data['input'], ensure_ascii=False)
    #     data['reqTraceId'] = trace_id

    #     if 'model' in kwargs:
    #         data['model'] = kwargs.pop('model')
    #     params = kwargs.pop('params', {})
    #     data['parameters'] = json.dumps(params)
    #     data['parameters'] = data['parameters'].replace('False', 'false')

    #     if output_type == "stream":
    #         api_suffix = 'aigc'
    #         data['api'] = data['api'] + "Stream"
    #     else:
    #         api_suffix = 'recommend'

    #     if not is_local:
    #         host = get_one_validate_host(self.vip_domain)
    #         url = f"http://{host.ip}:{host.port}/{api_suffix}?_input_charset=utf-8&_output_charset=utf-8&appid=43001"
    #     else:
    #         url = f"http://tppwork.taobao.com/pre/{api_suffix}?_input_charset=utf-8&_output_charset=utf-8&appid=43001"

    #     headers = {"Content-Type": "application/x-www-form-urlencoded"}
    #     def request_post():
    #         response = requests.post(url, data=data, headers=headers, timeout=60)
    #         if not response.text:
    #             return 503, {
    #                 'result': [
    #                     {'output': {'text': ''}}
    #                 ]
    #             }
    #         try:
    #             rsp = json.loads(response.text)
    #             return 200, rsp
    #         except json.decoder.JSONDecodeError as e:
    #             print(f"Invalid JSON: {response.text}")
    #             return 503, {
    #                 'result': [
    #                     {'output': {'text': 'Failed to decode JSON'}}
    #                 ]
    #             }

    #     def request_post_stream():
    #         answer = ''
    #         reason = ''
    #         usage_info = {}
    #         try:
    #             with requests.post(url, data=data, headers=headers, timeout=60, stream=True) as response:
    #                 if response.status_code != 200:
    #                     print(f"HTTP error: {response.status_code}")
    #                     return response.status_code, {
    #                         'result': [{'output': {'text': ''}}]
    #                     }

    #                 encoding = response.encoding
    #                 for line in response.iter_lines(decode_unicode=True):
    #                     if not line:
    #                         continue

    #                     line = line.decode(encoding) if isinstance(line, bytes) else line
    #                     if line.startswith('data:'):
    #                         ms_output = line.split('data:')[1]
    #                         try:
    #                             json_response = json.loads(ms_output)
    #                             json_output = json_response.get('result', [{}])[0].get('output', {})
    #                             if json_output.get('finish_reason') == 'stop':
    #                                 answer = json_output.get('text', '')
    #                                 reason = json_output.get('reasoning_content', '')
    #                                 tool_calls = []
    #                             elif json_output.get('finish_reason') == 'tool_calls':
    #                                 answer = json_output.get('text', '')
    #                                 reason = json_output.get('reasoning_content', '')
    #                                 tool_calls = json_output.get('tool_calls', [])

    #                             usage_info = json_response.get('result', [{}])[0].get('usage', {})
    #                         except json.JSONDecodeError:
    #                             continue
    #                     elif line.startswith('event:'):
    #                         ms_event = line.split('event:')[1]
    #                         if ms_event == 'complete':
    #                             break
    #                     else:
    #                         break

    #                 return response.status_code, {
    #                     'result': [
    #                         {   
    #                             'output': {
    #                                 'text': answer,
    #                                 'reasoning_content': reason,
    #                                 'tool_calls': tool_calls,
    #                             },
    #                             'usage': usage_info
    #                         }
    #                     ]
    #                 }
    #         except requests.exceptions.RequestException as e:
    #             print(f"Request failed: {e}")
    #             return 503, {
    #                 'result': [
    #                     {'output': {'text': 'Request failed.'}}
    #                 ]
    #             }

    #     if output_type == "stream":
    #         request_post_selected = request_post_stream
    #     else:
    #         request_post_selected = request_post

    #     status_code, result = request_post_selected()
    #     if status_code != 200:
    #         time.sleep(1)
    #         _, result = request_post_selected()
    #     return result

    def post(self, messages, trace_id, stream=False, is_local=False, **kwargs):
        """
        统一的模型调用接口：
        - stream=False：普通非流式调用，返回完整结果字典
        - stream=True：流式生成器，逐步 yield 每段响应内容
        """
        data = copy.deepcopy(self.formatter)
        data['input']['messages'] = messages
        data['input'] = json.dumps(data['input'], ensure_ascii=False)
        data['reqTraceId'] = trace_id

        if 'model' in kwargs:
            data['model'] = kwargs.pop('model')
        params = kwargs.pop('params', {})
        data['parameters'] = json.dumps(params).replace('False', 'false')

        if stream:
            data['api'] = data['api'] + "Stream"
            api_suffix = "aigc"
        else:
            api_suffix = "recommend"

        if not is_local:
            host = get_one_validate_host(self.vip_domain)
            url = f"http://{host.ip}:{host.port}/{api_suffix}?_input_charset=utf-8&_output_charset=utf-8&appid=43001"
        else:
            url = f"http://tppwork.taobao.com/pre/{api_suffix}?_input_charset=utf-8&_output_charset=utf-8&appid=43001"

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        if not stream:
            # 非流式：直接请求，返回完整响应
            try:
                response = requests.post(url, data=data, headers=headers, timeout=60)
                if not response.text:
                    return {
                        'result': [{'output': {'text': ''}}]
                    }
                return json.loads(response.text)
            except Exception as e:
                print(f"[非流式请求异常] {e}")
                return {
                    'result': [{'output': {'text': 'Request failed or invalid JSON'}}]
                }

        else:
            # 流式：逐行解析，使用生成器 yield
            try:
                with requests.post(url, data=data, headers=headers, timeout=60, stream=True) as response:
                    if response.status_code != 200:
                        yield {"error": f"HTTP error: {response.status_code}"}
                        return

                    encoding = response.encoding
                    for line in response.iter_lines(decode_unicode=True):
                        if not line:
                            continue
                        line = line.decode(encoding) if isinstance(line, bytes) else line

                        if line.startswith('data:'):
                            try:
                                json_response = json.loads(line[len('data:'):])
                                result = json_response.get('result', [{}])[0]
                                output = result.get('output', {})
                                usage = result.get('usage', {})

                                yield {
                                    "text": output.get('text', ''),
                                    "reasoning_content": output.get('reasoning_content', ''),
                                    "tool_calls": output.get('tool_calls', []),
                                    "finish_reason": output.get('finish_reason'),
                                    "usage": usage
                                }

                                if output.get("finish_reason") in ("stop", "tool_calls"):
                                    break
                            except json.JSONDecodeError:
                                continue
                        elif line.startswith('event:') and line.endswith('complete'):
                            break
            except requests.exceptions.RequestException as e:
                yield {"error": f"Request failed: {e}"}


llm_config = configparser.ConfigParser()

class geneClassQuest_byRM:
    def __init__(self, **kwargs):
        default_config = {}
        default_config.update(kwargs)
        # print(default_config)
        self.tpp_client = TppSseClient(default_config)

    def predict_via_modelserver(self, messages=None, prompt=None, stream=False, **kwargs):
        if not messages and not prompt:
            raise ValueError("messages and prompt cannot be both None")
        if not messages:
            messages = [{"role": "user", "content": prompt}]
        
        trace_id = generate_random_trace_id()
        response = self.tpp_client.post(messages, trace_id, stream=stream, **kwargs)

        if stream:
            # 收集所有流式 chunk
            final_text = ''
            final_reasoning = ''
            final_tool_calls = []
            usage = {}
            for chunk in response:
                if "error" in chunk:
                    print("⚠️ 流式响应出错：", chunk["error"])
                    break
                final_text += chunk.get("text", "")
                final_reasoning = chunk.get("reasoning_content", final_reasoning)
                final_tool_calls = chunk.get("tool_calls", [])
                usage = chunk.get("usage", usage)
            
            return [{
                "output": {
                    "text": final_text,
                    "reasoning_content": final_reasoning,
                    "tool_calls": final_tool_calls,
                },
                "usage": usage
            }]
        else:
            # 非流式，直接返回字典结构
            return response.get('result', [])


def generate_random_trace_id():
    return str(uuid.uuid4())



if __name__ == '__main__':
    tpp = TppSseClient()
    messages = [
        {
            'role': 'system',
            'content': '你是一个有用的助手'
        },
        {
            'role': 'user',
            'content': '今天周几啊'
        }
    ]
    # 使用函数生成一个trace ID
    # trace_id = generate_random_trace_id()
    # response = tpp.post(messages, trace_id, output_type='stream', params={"enable_thinking": False})
    # print(response)

    qest_generator = geneClassQuest_byRM()
    # response = qest_generator.predict_via_modelserver(messages, output_type='stream')
    # response = qest_generator.predict_via_modelserver(messages, output_type='default', model='aliyun_qwen-max-latest')
    # response = qest_generator.predict_via_modelserver(prompt='以"我已枷锁境，无须多言"为中心，写一个短篇玄幻故事', output_type='stream', model='aliyun_deepseek-r1')
    # response = qest_generator.predict_via_modelserver(prompt='你好', model='aliyun_qwen3-32b', output_type='stream', params={"enable_thinking": False})
    
    # 本地执行
    # response = qest_generator.predict_via_modelserver(prompt='你好', model='aliyun_qwen3-32b', output_type='stream', is_local=True, params={"enable_thinking": False})
    # print(response)

    # response = qest_generator.predict_via_modelserver(prompt='你好', model='aliyun_qwen3-32b', output_type='stream', is_local=True, params={"enable_thinking": True})
    # print(response)

    shop_env_tools = [
        {
            "type": "function",
            "function": {
                "name": "view_orders",
                "description": "查看当前所有订单信息，消耗10分钟。",
                "parameters": {
                    "properties": {},
                    "required": [],
                    "type": "object"
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "buy_goods",
                "description": "进货指定商品。支持批量进货,每个商品需指定商品id、数量。消耗60分钟。",
                "parameters": {
                    "properties": {
                        "orders": {
                            "description": "进货订单数组,每个元素包含商品id、数量",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"description": "商品id(整数)", "type": "integer"},
                                    "num": {"description": "进货数量", "type": "integer"},
                                },
                                "required": ["id", "num", "arrive"]
                            }
                        }
                    },
                    "required": ["orders"],
                    "type": "object"
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "sell_order",
                "description": "售出指定订单。参数为订单id(order_id), 只能售出一个订单。消耗10分钟。",
                "parameters": {
                    "properties": {
                        "order_id": {
                            "description": "要售出的订单id(整数)",
                            "type": "integer"
                        }
                    },
                    "required": ["order_id"],
                    "type": "object"
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "view_inventory",
                "description": "查看当前库存状况, 展示所有商品的库存数量。消耗20分钟。",
                "parameters": {
                    "properties": {},
                    "required": [],
                    "type": "object"
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "view_cash",
                "description": "查看当前剩余的现金。消耗1分钟。",
                "parameters": {
                    "properties": {},
                    "required": [],
                    "type": "object"
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "view_incoming_goods",
                "description": "查看所有尚未到货的进货订单，包括商品id、数量、预计到货时间。消耗5分钟。",
                "parameters": {
                    "properties": {},
                    "required": [],
                    "type": "object"
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "view_goods_price_list",
                "description": "查看所有商品的基本信息，包括名称、进价、售价和类别。用于分析利润空间。",
                "parameters": {
                    "properties": {},
                    "required": [],
                    "type": "object"
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "wait_time",
                "description": "等待今日时间流逝",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
    ]

    response = qest_generator.predict_via_modelserver(
        prompt='你好',
        model='aliyun_qwen3-32b',
        output_type='stream',
        is_local=True,
        tools=shop_env_tools,
        stream=True,
        params={"enable_thinking": True},
    )
    print(response)





