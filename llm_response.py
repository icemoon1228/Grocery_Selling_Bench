import configparser
from email import message
from openai import OpenAI
import time
import json
import requests
from openai import APIError, OpenAIError

from llm_call import geneClassQuest_byRM

idealab_config = configparser.ConfigParser()
idealab_config.read('config/idealab.ini', encoding='utf-8')

idealab_ak = idealab_config.get('idealab', 'idealab_ak')
idealab_base_url = idealab_config.get('idealab', 'base_url')
dashscope_ak = idealab_config.get('dashscope', 'dashscope_ak')
dashscope_baseurl = idealab_config.get('dashscope', 'dashscope_baseurl')

client = OpenAI(
    api_key=dashscope_ak,
    base_url=dashscope_baseurl
)

# client = OpenAI(
#     api_key=idealab_ak,
#     base_url=idealab_base_url,
# )


def get_llm_response(client, prompt=None, messages=None, system_prompt="You are a helpful assistant.", model_name="qwq-plus", stream=False, **kwargs):
    if not messages:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

    completion = client.chat.completions.create(
        model=model_name,
        messages=messages,
        stream=stream,  # ✅ 注意这里必须设置 stream 参数
        **kwargs
    )

    if not stream:
        result = completion.choices[0].message.content.strip()
        return result
    else:
        collected = []
        for chunk in completion:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                collected.append(chunk.choices[0].delta.content)
        return ''.join(collected).strip()

import json
def get_llm_response_tool_call(
    client,
    messages=None,
    model_name="qwq-plus",
    stream=False,
    **kwargs,
):
    if not messages:
        return "", "", []

    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=messages,
            stream=stream,
            **kwargs
        )
    except (APIError, OpenAIError) as e:
        print(f"❌ API 请求失败：{e}")
        return "", "", []
    except Exception as e:
        print(f"❌ 未知错误：{e}")
        return "", "", []

    reasoning_content = ""
    answer_content = ""
    tool_info = []

    def ensure_tool_slot(index):
        while len(tool_info) <= index:
            tool_info.append({"id": "", "name": "", "arguments": ""})

    def parse_tool_calls(tool_calls):
        for tool_call in tool_calls:
            index = getattr(tool_call, "index", 0)
            ensure_tool_slot(index)

            if getattr(tool_call, "id", None):
                tool_info[index]["id"] += tool_call.id

            func = getattr(tool_call, "function", None)
            if func:
                if getattr(func, "name", None):
                    tool_info[index]["name"] += func.name
                if getattr(func, "arguments", None):
                    tool_info[index]["arguments"] += func.arguments

    if stream:
        try:
            for chunk in completion:
                try:
                    if not hasattr(chunk, "choices") or not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta

                    # 内容片段
                    if hasattr(delta, 'reasoning_content') and delta.reasoning_content is not None:
                        reasoning_content += delta.reasoning_content
                    elif hasattr(delta, "content") and delta.content is not None:
                        answer_content += delta.content

                    # 工具调用
                    if hasattr(delta, "tool_calls") and delta.tool_calls:
                        parse_tool_calls(delta.tool_calls)

                except Exception as e:
                    print(f"⚠️ 流式 chunk 解析失败: {e}")
        except Exception as e:
            print(f"❌ 流式响应异常：{e}")
            return "", "", []
    else:
        try:
            choice = completion.choices[0]
            reasoning_content = getattr(choice.message, "reasoning_content", "")
            answer_content = getattr(choice.message, "content", "")

            if getattr(choice.message, "tool_calls", None):
                parse_tool_calls(choice.message.tool_calls)

        except Exception as e:
            print(f"❌ 非流响应解析失败: {e}")
            return "", "", []

    # 解析工具调用参数
    parsed_tool_info = []
    for i, t in enumerate(tool_info):
        arguments = t.get("arguments", {})
        if isinstance(arguments, str):
            try:
                parsed_args = json.loads(arguments)
            except json.JSONDecodeError as e:
                print(f"⚠️ tool_call[{i}] 参数解析失败: {e}\n原始内容: {arguments}")
                continue
        else:
            parsed_args = arguments

        parsed_tool_info.append({
            "id": t.get("id", ""),
            "name": t.get("name", ""),
            "arguments": parsed_args,
        })

    # 返回推理内容、答案内容、工具调用信息
    final_content = reasoning_content or answer_content
    return final_content, reasoning_content, parsed_tool_info

def get_llm_response_tool_call_model_server(
    messages=None,
    model_name='aliyun_qwen3-32b',
    stream=False,
    tools=[],
    **kwargs,
):
    qest_generator = geneClassQuest_byRM()

    response = qest_generator.predict_via_modelserver(
        messages=messages,
        model=model_name,
        stream=stream,
        is_local=True,
        params={"tools": tools},
        **kwargs,
    )

    response = response[0]

    reasoning_content = response['output']['reasoning_content']

    tool_calls = [item['function'] for item in response['output']['tool_calls']]

    tool_calls = [
        {
            **tool_call,
            'arguments': json.loads(tool_call['arguments']) if isinstance(tool_call.get('arguments'), str) else tool_call['arguments']
        }
        for tool_call in tool_calls
    ]

    return reasoning_content, '', tool_calls

def main():
    prompt = "What is the capital of France?"
    system_prompt = "You are a helpful assistant."

    # Test non-streaming mode
    response_non_stream = get_llm_response(
        client,
        prompt=prompt,
        system_prompt=system_prompt,
        model_name='qwen3-32b',
        stream=True,
    )
    print("Non-streaming Response:", response_non_stream)

    # Test streaming mode
    response_streaming = get_llm_response(client, prompt=prompt, system_prompt=system_prompt, stream=True)
    print("Streaming Response:", response_streaming)

    # Test non-streaming with tool calls
    messages = [{"role": "user", "content": prompt}]
    reasoning_non_stream, answer_non_stream, tool_non_stream = get_llm_response_tool_call(client, messages=messages, stream=False)
    print("Non-stream Reasoning Content:", reasoning_non_stream)
    print("Non-stream Answer Content:", answer_non_stream)
    print("Non-stream Tool Info:", tool_non_stream)

    # Test streaming with tool calls
    reasoning_stream, answer_stream, tool_stream = get_llm_response_tool_call(client, messages=messages, stream=True)
    print("Stream Reasoning Content:", reasoning_stream)
    print("Stream Answer Content:", answer_stream)
    print("Stream Tool Info:", tool_stream)

if __name__ == "__main__":
    main()
