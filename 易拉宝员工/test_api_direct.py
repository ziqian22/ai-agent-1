import sys
sys.stdout.reconfigure(encoding='utf-8')

import anthropic
import base64
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(
    api_key=os.getenv('CLAUDE_API_KEY'),
    base_url=os.getenv('CLAUDE_BASE_URL')
)

# 读取图片
with open('74f8c6f71010b7553325446bec13f5a5.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode()

# 简单的提示词
prompt = "请详细描述这张图片中的产品，包括产品名称、品牌、特点等信息。"

print('调用Claude API...\n')

response = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=2000,
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": image_data
                }
            },
            {
                "type": "text",
                "text": prompt
            }
        ]
    }]
)

print('响应内容:')
print(response.content[0].text)
