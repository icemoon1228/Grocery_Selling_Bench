import configparser
from openai import OpenAI
import time
import json
import requests

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

    completion = client.chat.completions.create(
        model=model_name,
        messages=messages,
        stream=stream,
        **kwargs
    )

    reasoning_content = ""
    answer_content = ""
    tool_info = []
    is_answering = False

    if stream:
        for chunk in completion:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            # 推理内容
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content is not None:
                reasoning_content += delta.reasoning_content

            # 普通回答内容
            elif delta.content is not None:
                is_answering = True
                answer_content += delta.content

            # 工具调用
            if delta.tool_calls is not None:
                for tool_call in delta.tool_calls:
                    index = tool_call.index
                    while len(tool_info) <= index:
                        tool_info.append({"id": "", "name": "", "arguments": ""})

                    if tool_call.id:
                        tool_info[index]["id"] += tool_call.id
                    if tool_call.function and tool_call.function.name:
                        tool_info[index]["name"] += tool_call.function.name
                    if tool_call.function and tool_call.function.arguments:
                        tool_info[index]["arguments"] += tool_call.function.arguments

    else:
        choice = completion.choices[0]
        if hasattr(choice.message, 'reasoning_content'):
            reasoning_content = choice.message.reasoning_content
        answer_content = choice.message.content

        if choice.message.tool_calls is not None:
            for tool_call in choice.message.tool_calls:
                index = tool_call.index
                while len(tool_info) <= index:
                    tool_info.append({"id": "", "name": "", "arguments": ""})

                if tool_call.id:
                    tool_info[index]["id"] = tool_call.id
                if tool_call.function and tool_call.function.name:
                    tool_info[index]["name"] = tool_call.function.name
                if tool_call.function and tool_call.function.arguments:
                    tool_info[index]["arguments"] = tool_call.function.arguments

    # 尝试解析 arguments 为 dict，失败则跳过该 tool_call
    parsed_tool_info = []
    for i, t in enumerate(tool_info):
        try:
            parsed_args = json.loads(t.get("arguments", "{}"))
        except json.JSONDecodeError as e:
            print(f"⚠️ tool_call[{i}] 参数解析失败: {e}\n内容为: {t.get('arguments')}")
            continue  # 跳过非法 tool_call

        parsed_tool_info.append({
            "id": t.get("id", ""),
            "name": t.get("name", ""),
            "arguments": parsed_args,
        })

    return reasoning_content, answer_content, parsed_tool_info


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
