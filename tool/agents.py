# 创建推理接入点 https://www.volcengine.com/docs/82379/1099522
# ChatCompletions https://www.volcengine.com/docs/82379/1302008
from openai import OpenAI
import os

from dotenv import load_dotenv  # 用于加载环境变量
import json
import copy
import requests
load_dotenv()  # 加载 .env 文件中的环境变量

from volcenginesdkarkruntime import Ark
from volcenginesdkarkruntime._exceptions import ArkAPIError

def load_content(f):
    with open(f, 'r', encoding='utf-8') as f:
        return f.read()

class ProcessText(object):
    system_prompt = """你是 Doubao AI，由 字节跳动 提供的人工智能助手，你更擅长中文的对话。你会为用户提供安全，有帮助，准确的回答。"""


class DoubaoAgentClient(object):

    def __init__(self, api_key, window_size=5):
        # Headers

        # 从环境变量中读取您的方舟API Key。
        self.url = "https://ark.cn-beijing.volces.com/api/v3"

        self.client = Ark(base_url=self.url, api_key=api_key)
        self.window_messages = []
        self.prompt = ""
        self.WINDOW_LENGTH = window_size
        self.messages = [
            {"role": "system", "content": ProcessText.system_prompt},
            {"role": "system", "content": self.prompt}
        ]

        self.model = "ep-20241217230300-z4h68"

    def chat(self, query):
        # https://www.volcengine.com/docs/82379/1099455
        new_messages: list = copy.deepcopy(self.messages)

        if len(self.window_messages) > self.WINDOW_LENGTH:
            self.window_messages = self.window_messages[-self.WINDOW_LENGTH:]

        new_messages.extend(self.window_messages)
        new_messages.append({
            "role": "user",
            "content": query
        })
        # print("messages:", new_messages)

        completion = self.client.chat.completions.create(
            # 您的方舟推理接入点。
            model=self.model,
            messages=new_messages,
            temperature=0.8,
            response_format={"type": "json_object"}
        )

        resp = {}
        success = True
        try:
            resp = json.loads(completion.choices[0].message.content)
        except Exception as e:
            print("fail on loads:", e)
            print(completion.choices[0].finish_reason)
            print(completion.choices[0].message.content)
            success = False

        # print("resp:\n", resp)
        self.window_messages.append({
            "role": "assistant",
            "content": completion.choices[0].message.content
        })

        return resp, success

    def generate(self, text):
        messages = [
            {"role": "system", "content": ProcessText.system_prompt},
            {'role': 'user', 'content': text}
        ]
        completion = self.client.chat.completions.create(
            # 您的方舟推理接入点。
            model=self.model,
            messages=messages,
            temperature=0.8,
        )
        resp = ''
        success = True
        try:
            resp = completion.choices[0].message.content
        except Exception as e:
            print("fail on loads:", e)
            resp = completion.choices[0].finish_reason
            print(completion.choices[0].finish_reason)
            print(completion.choices[0].message.content)
            success = False
        return resp, success

    def generate_stream(self, text):
        messages = [
            {"role": "system", "content": ProcessText.system_prompt},
            {'role': 'user', 'content': text}
        ]
        completion = self.client.chat.completions.create(
            # 您的方舟推理接入点。
            model=self.model,
            messages=messages,
            temperature=0.8,
            stream=True
        )
        for chunk in completion:
            if not chunk.choices:
                continue
            yield  chunk.choices[0].delta.content, True

    def get_completion(self, messages):
        for message in messages:
            print("message:", message)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0,  # 模型输出的随机性，0 表示随机性最小
            tools=[{
                "type": "function",
                "function": {
                    "name": "get_location_coordinate",
                    "description": "根据POI名称，获得POI的经纬度坐标",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "POI名称，必须是中文",
                            },
                            "city": {
                                "type": "string",
                                "description": "POI所在的城市名，必须是中文",
                            }
                        },
                        "required": ["location", "city"],
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_nearby_pois",
                    "description": "搜索给定坐标附近的poi",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "longitude": {
                                "type": "string",
                                "description": "中心点的经度",
                            },
                            "latitude": {
                                "type": "string",
                                "description": "中心点的纬度",
                            },
                            "keyword": {
                                "type": "string",
                                "description": "目标poi的关键字",
                            }
                        },
                        "required": ["longitude", "latitude", "keyword"],
                    }
                }
            }],
        )
        return response.choices[0].message

    # def get_completion(self, messages):
    #     return self.client.chat.completions.create(
    #             # 您的方舟推理接入点。
    #             model=self.model,
    #             messages=messages,
    #             temperature=0.8,
    #             response_format={"type": "json_object"}
    #     )

    def fill_default_items(self, items):
        for _, item in enumerate(items):
            item['C'] = '旁白'
            item['E'] = '平静'
            item['A'] = ''
        return items

def get_doubao_agent() -> DoubaoAgentClient:
    return DoubaoAgentClient(api_key=os.environ.get('ARK_API_KEY'))

class DoubaoTTSAgent(object):
    def __init__(self):
        self.url = ''
        self.client = None

    def text_to_speech(self, speaker_id, text):
        content = ''
        return content

def get_tts_agent():
    # 每10k token 4.5元;
    return DoubaoAgentClient(api_key=os.environ.get('ARK_API_KEY'))


if __name__ == "__main__":
    query = """
    春风亭老朝手中不知有多少条像临四十七巷这样的产业，他往日交往的枭雄达官不知凡几，似这等人物若要离开长安城，需要告别的对象绝对不应该是临四十七巷里的这些店铺老板。
    然而今天他离开之前，却特意来到临四十七巷，与那些店铺老板们和声告别，若在帝国那些上层贵人们眼中，
    """
    agent = DoubaoAgentClient(api_key=os.environ.get('ARK_API_KEY'))
    print(agent.generate(query))
