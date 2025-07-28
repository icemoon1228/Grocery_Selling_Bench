import re
import os
import json
import logging
from roll.datasets.chat_template import get_chat_template
from roll.distributed.scheduler.protocol import DataProto
from transformers import PreTrainedTokenizer


""" rl dataset 格式：(0709 v1 版) 支持 math、llm as judge 训练
以下所有字段都是 str
{
    "id": "123", 
    "tag": "abc", # 在 rewards 中通过 domain-to-tag 指定该条样本使用啥 worker(例如 llm_as_judge) 计算 reward
    "messages": "[...]", 
    "ground_truth": "42", # 对于 math 用于 verify 函数，对于 llm_judge 用作为 reference
    "mcp_args": "{"tool_map": {"search": "wiki_knowledge_retrieval", "fetch": "..."}, "default_arguments": {"cate": "musique"}}"
}
"""

# TensorDict(
#     fields={
#         attention_mask: Tensor(shape=torch.Size([128, 18432]), device=cpu, dtype=torch.int64, is_shared=False),
#         input_ids: Tensor(shape=torch.Size([128, 18432]), device=cpu, dtype=torch.int64, is_shared=False),
#         position_ids: Tensor(shape=torch.Size([128, 18432]), device=cpu, dtype=torch.int64, is_shared=False),
#         prompt_mask: Tensor(shape=torch.Size([128, 18432]), device=cpu, dtype=torch.bool, is_shared=False),
#         prompts: Tensor(shape=torch.Size([128, 2048]), device=cpu, dtype=torch.int64, is_shared=False),
#         response_level_rewards: Tensor(shape=torch.Size([128]), device=cpu, dtype=torch.float16, is_shared=False),
#         response_mask: Tensor(shape=torch.Size([128, 18432]), device=cpu, dtype=torch.int64, is_shared=False),
#         responses: Tensor(shape=torch.Size([128, 16384]), device=cpu, dtype=torch.int64, is_shared=False),
#         scores: Tensor(shape=torch.Size([128]), device=cpu, dtype=torch.float16, is_shared=False),
#         token_level_rewards: Tensor(shape=torch.Size([128, 16384]), device=cpu, dtype=torch.float16, is_shared=False)},
#     batch_size=torch.Size([128]),
#     device=None,
#     is_shared=False)


def save_rollout(data: DataProto, tokenizer: PreTrainedTokenizer, save_path: str):
    prompts_lens = data.batch["prompt_mask"].sum(dim=1) # 每个样本的prompt所占的token长度
    prompts_list = tokenizer.batch_decode(data.batch["prompts"], skip_special_tokens=False)
    responses_list = tokenizer.batch_decode(data.batch["responses"], skip_special_tokens=False)
    response_level_rewards_list = data.batch["response_level_rewards"].tolist()
    difficulty_mask_list = data.batch["difficulty_mask"].tolist()
    response_mask_list = data.batch["response_mask"].tolist()

    id_list = data.non_tensor_batch["id"].tolist()
    ground_truth_list = data.non_tensor_batch["ground_truth"].tolist()

    # 解码每个batch中未被mask的responses
    unmasked_responses = []
    for i, (response, mask) in enumerate(zip(data.batch["responses"], response_mask_list)):
        mask = mask[prompts_lens[i]:]
        unmasked_tokens = response[[i for i, m in enumerate(mask) if m == 1]]
        unmasked_text = tokenizer.decode(unmasked_tokens, skip_special_tokens=False)
        unmasked_responses.append(unmasked_text)
    
    directory = os.path.dirname(save_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    
    with open(save_path, "w", encoding="utf-8") as f:
        for i in range(len(id_list)):
            f.write(">"*66 + "\n")
            f.write("$@$>i: " + str(i) + "\n")
            f.write("$@$>id: " + str(id_list[i]) + "\n")
            f.write("$@$>ground_truth: " + str(ground_truth_list[i]) + "\n")
            f.write("$@$>difficulty_mask: " + str(difficulty_mask_list[i]) + "\n")
            f.write("$@$>response_level_rewards: " + str(response_level_rewards_list[i]) + "\n")
            f.write("$@$>prompts: \n" + str(prompts_list[i]).replace("<|endoftext|>", "") + "\n")
            f.write("$@$>responses: \n" + str(responses_list[i]).replace("<|endoftext|>", "") + "\n")
            f.write("$@$>unmasked_responses: \n" + str(unmasked_responses[i]) + "\n")
            # f.write(">>> debug responses_ids: \n" + str(data.batch["responses"][i].tolist()) + "\n")
            # f.write(">>> debug response_mask: \n" + str(data.batch["response_mask"][i].tolist()) + "\n")
            f.write("\n"*6)
    return

tools = [
    {
        "type": "function",
        "function": {
            "name": "google_search",
            "description": "Google搜索工具可以帮助用户快速查找并获取互联网上的最新信息，支持从各种网站提取相关内容，适用于查询新闻、产品、研究资料等多种场景。",
            "parameters": {
                "properties": {
                    "google_query": {
                        "description": "利于检索出相关通识资料的问句",
                        "type": "string"
                    }
                },
                "required": [
                    "google_query"
                ],
                "type": "object"
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "nl2dsl2data",
            "description": "根据自然语言提问来获取用户相关数据的取数工具",
            "parameters": {
                "properties": {
                    "user_parameters": {
                        "type": "object",
                        "properties": {
                            "shopId": {
                                "description": "商户店铺ID，例如 2000062404",
                                "type": "string"
                            }
                        },
                        "required": [
                            "shopId"
                        ]
                    },
                    "query": {
                        "description": "利于检索出相关资料的口语化问句，不要使用关键词，例如，如何修改配送范围",
                        "type": "string"
                    }
                },
                "required": [
                    "query",
                    "user_parameters"
                ],
                "type": "object"
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "dsl2data",
            "description": "根据DSL协议读取数据 ，这里的DSL和SQL很像，有选择字段，聚合操作，排序操作。等等。有些可以不写。但是至少有选择了哪些字段，选择哪天数据，以及过滤条件等。比如一般情况下的查询如下。\n{\n    \"select\": [{\"columnEName\": \"下单转化率\"}],\n    \"ds\": {\"type\": \"between\",\"values\": [    \"20250616\",    \"20250616\"]},\n    \"filter\": { \"relation\": \"and\", \"conditions\": [{     \"queryRule\": \"in\",     \"params\": [         2000062404     ],     \"columnEName\": \"商户id\" }]}\n}\n注意返回结果中”ratio“代表比率 ”delta “代表差值”val“代表对比值",
            "parameters": {
                "properties": {
                    "filter": {
                        "default": {},
                        "description": "过滤条件，是个存MAP的LIST。relation= and or 两种。案例：{\"relation\": \"and\",\"conditions\": [{\"queryRule\": \"in\",\"params\": [\"上海市\"],\"columnEName\":\"城市\"}]}",
                        "type": "object"
                    },
                    "compare": {
                        "default": [],
                        "description": "可以填写一下数字，dod（日环比）、wow（周同比）、mom（月同比）、yoy（年同比）、qoq（季度同比）",
                        "type": "array"
                    },
                    "select": {
                        "description": "选择透出那些指标，是个存MAP的LIST。案例：[{ \"columnEName\": \"GMV\"},...]",
                        "type": "array"
                    },
                    "statisticType": {
                        "default": "sum",
                        "description": "主要两种 avg 求平均 sum 求和",
                        "type": "string"
                    },
                    "orderBy": {
                        "default": [],
                        "description": "排序，是个存MAP的LIST。案例：[{\"columnEName\": \"净GMV\",\"suffix\": \"mom\",\"orderType\": \"asc\"},..]，其中 orderType 是asc、desc",
                        "type": "array"
                    },
                    "ds": {
                        "description": "选择日期时间，DICT 如下{\"type\": \"between\",\"values\": [\"20240601\",\"20240604\"]}，目前type值等于between",
                        "type": "object"
                    },
                    "group": {
                        "default": [],
                        "description": "聚合，是个存MAP的LIST。案例：[{ \"columnEName\": \"城市\"},...]",
                        "type": "array"
                    }
                },
                "required": [
                    "select",
                    "filter",
                    "ds"
                ],
                "type": "object"
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "nl2semantic",
            "description": "根据query召回标准语义。标准语义主要包含维度，维度值和指标。\n",
            "parameters": {
                "properties": {
                    "topK": {
                        "description": "返回多少数量",
                        "type": "integer"
                    },
                    "entityType": {
                        "description": "三种值 metric 指标 dimension 维度 dimension_value 维值，也可以不传递",
                        "type": "string"
                    },
                    "query": {
                        "description": "输入query根据当前的query进行召回标准语义。query要根据用户输入以及上下文进行改写。",
                        "type": "string"
                    }
                },
                "required": [
                    "query"
                ],
                "type": "object"
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wiki_knowledge_retrieval",
            "description": "搜索开源库的知识",
            "parameters": {
                "properties": {
                    "cate": {
                        "description": "搜索知识库类型目前主要有四个 musique , 2wikimultihopqa , iirc  hotpotqa ",
                        "type": "string"
                    },
                    "query": {
                        "description": "搜索query",
                        "type": "string"
                    }
                },
                "required": [
                    "query",
                    "cate"
                ],
                "type": "object"
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ele_knowledge_retrieval",
            "description": "查询饿了么商家知识库，从饿了么商家资料库中检索出饿了么平台规则或操作文档以及店铺经营策略，好的搜索短句能提升检索效果。\n",
            "parameters": {
                "properties": {
                    "query": {
                        "description": "利于检索出相关资料的口语化问句，不要使用关键词，例如，如何修改配送范围",
                        "type": "string"
                    }
                },
                "required": [
                    "query"
                ],
                "type": "object"
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "common_search",
            "description": "根据query查询互联网的公开信息，包括但不限于百科、咨询、问答、天气、微博、新闻、新闻热榜、时间、日历、航班等领域信息。注意返回信息已经经过排序，尽可能参考排在前列的信息。\n",
            "parameters": {
                "properties": {
                    "query": {
                        "description": "要检索的query，应该尽可能精简明确。",
                        "type": "string"
                    }
                },
                "required": [
                    "query"
                ],
                "type": "object"
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "google_search_idealab",
            "description": "Google搜索工具可以帮助用户快速查找并获取互联网上的最新信息，支持从各种网站提取相关内容，适用于查询新闻、产品、研究资料等多种场景。",
            "parameters": {
                "properties": {
                    "query": {
                        "description": "询问query，尽量精简明确",
                        "type": "string"
                    }
                },
                "required": [
                    "query"
                ],
                "type": "object"
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ele_knowledge_retrieval_v2",
            "description": "搜索饿了么知识库",
            "parameters": {
                "properties": {
                    "query": {
                        "description": "搜索query",
                        "type": "string"
                    }
                },
                "required": [
                    "query"
                ],
                "type": "object"
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_data_by_nature_language_2",
            "description": "根据自然语言查询数据，这里的数据主要围绕饿了么商户的经营数据，比如曝光，点击，营销，订单相关。\n商户和门店是等价关系",
            "parameters": {
                "properties": {
                    "cate1": {
                        "description": "一级分类 只能填写其中之一【“门店”】",
                        "type": "string"
                    },
                    "cate1Value": {
                        "description": "一级分类取值，门店填写门店ID",
                        "type": "string"
                    },
                    "queryList": {
                        "description": "查询的通过自然语言描述的字段列表",
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },
                    "ds": {
                        "description": "基于哪个时间分区查询数据，取值如20250520，非必传",
                        "type": "string"
                    }
                },
                "required": [
                    "queryList",
                    "cate1",
                    "cate1Value"
                ],
                "type": "object"
            }
        }
    }
]

def get_encode_function(template_name, tokenizer):
    chat_template_func = get_chat_template(template_name, tokenizer)

    def encode_function(data_i):
        text_list = []

        default_tools = [
            {
                "type": "function",
                "function": {
                    "name": "wiki_knowledge_retrieval",
                    "description": "搜索开源库的知识",
                    "parameters": {
                        "properties": {
                            "cate": {
                                "description": "搜索知识库类型目前主要有四个 musique , 2wikimultihopqa , iirc  hotpotqa ",
                                "type": "string"
                            },
                            "query": {
                                "description": "搜索query",
                                "type": "string"
                            }
                        },
                        "required": [
                            "query",
                            "cate"
                        ],
                        "type": "object"
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ele_knowledge_retrieval",
                    "description": "查询饿了么商家知识库，从饿了么商家资料库中检索出饿了么平台规则或操作文档以及店铺经营策略，好的搜索短句能提升检索效果。\n",
                    "parameters": {
                        "properties": {
                            "query": {
                                "description": "利于检索出相关资料的口语化问句，不要使用关键词，例如，如何修改配送范围",
                                "type": "string"
                            }
                        },
                        "required": [
                            "query"
                        ],
                        "type": "object"
                    }
                }
            },
        ]

        for messages in data_i["messages"]:
            if isinstance(messages, str):
                messages = json.loads(messages)
            text_list.append(chat_template_func(messages, tools=default_tools))

        encodings = tokenizer(text_list)
        return encodings

    return encode_function


def parser_last_user_content(text: str, logger: logging.Logger = None, pad_token: str = None):
    text_list = [i.strip() for i in text.split("<|im_end|>")]
    text_list = [i for i in text_list if i.startswith("<|im_start|>user")]

    to_return = text.replace("<|im_start|>", "").replace("<|im_end|>", "")
    need_warning = True
    if text_list:
        last_user_content = text_list[-1].replace("<|im_start|>user", "").strip()
        if last_user_content:
            to_return = last_user_content
            need_warning = False
    
    if logger and need_warning:
        logger.warning(f"WARNING: parser_last_user_content 未按照正常逻辑解析，走兜底方案\n" * 10)
    
    to_return = to_return.replace(pad_token, "")
    return to_return


def parser_response_answer(text: str, pad_token: str = None):
    patterns = [
        (r'<think>.*?</think>', ''),
        (r'<tool_call>.*?</tool_call>', ''),
        (r'<tool_response>.*?</tool_response>', '')
    ]

    text = text.split("<|im_start|>assistant")[-1]
    
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text, flags=re.DOTALL)
    
    text = text.split("</think>")[-1]
    text = text.replace("<|im_end|>", "").replace("<|im_start|>user", "").replace("<|im_start|>assistant", "").replace(pad_token, "")

    return text.strip()


# def fix_response_mask(responses, prompt_mask, response_mask, tokenizer: PreTrainedTokenizer):
#     prompts_lens = prompt_mask.clone().sum(dim=1)
#     responses_text = tokenizer.batch_decode(responses, skip_special_tokens=False)

#     pattern = r"\s*<\|im_start\|>user\n<tool_response>.*?</tool_response><\|im_end\|>\s*"

#     for i in range(len(responses_text)):
#         # 所有 pattern 的起至位置
#         matches = [(m.start(), m.end()) for m in re.finditer(pattern, responses_text[i], flags=re.DOTALL)]
#         # 每个 token 的起至位置
#         offset_mapping = tokenizer(responses_text[i], return_offsets_mapping=True, add_special_tokens=False)["offset_mapping"]

#         for j, (token_start, token_end) in enumerate(offset_mapping):
#             if token_start == token_end == 0:
#                 continue
#             for start, end in matches:
#                 if token_start >= start and token_end <= end:
#                     # assert response_mask[i][j] == 1, f"位置 {j} 处的 token ({responses_text[i][token_start:token_end]})的 response_mask != 1"
#                     response_mask[i][j+prompts_lens[i]] = 0
    
#     return response_mask


def fix_response_mask(responses, prompt_mask, response_mask, tokenizer: PreTrainedTokenizer):
    start_tokens = tokenizer.encode(
        "<|im_start|>user\n<tool_response>", 
        add_special_tokens=False
    )
    end_tokens = tokenizer.encode(
        "</tool_response><|im_end|>", 
        add_special_tokens=False
    )
    
    prompts_lens = prompt_mask.sum(dim=1)
    
    for i in range(len(responses)):
        tokens = responses[i].tolist()
        pos = 0
        while pos < len(tokens):
            # 查找起始标记
            if tokens[pos:pos+len(start_tokens)] == start_tokens:
                start_pos = pos
                pos += len(start_tokens)
                # 查找结束标记
                while pos <= len(tokens) - len(end_tokens):
                    if tokens[pos:pos+len(end_tokens)] == end_tokens:
                        end_pos = pos + len(end_tokens)
                        # fix mask
                        for j in range(start_pos, end_pos):
                            idx = prompts_lens[i] + j
                            response_mask[i, idx] = 0
                        pos = end_pos
                        break
                    pos += 1
                else:  # 未找到结束标记
                    break
            else:
                pos += 1
    return response_mask
