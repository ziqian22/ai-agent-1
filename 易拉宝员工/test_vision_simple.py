import sys
sys.stdout.reconfigure(encoding='utf-8')

from vision_analyzer import VisionAnalyzer
import os
import json
from dotenv import load_dotenv

load_dotenv()

analyzer = VisionAnalyzer(
    os.getenv('CLAUDE_API_KEY'),
    os.getenv('CLAUDE_BASE_URL')
)

print('=' * 60)
print('测试图片分析功能')
print('=' * 60)

print(f'\n使用模型: {analyzer.model}')
print('分析图片: 74f8c6f71010b7553325446bec13f5a5.jpg\n')

result = analyzer.analyze_image('74f8c6f71010b7553325446bec13f5a5.jpg')

print('提取的产品信息:')
print(json.dumps(result, ensure_ascii=False, indent=2))

if result.get('raw_response'):
    print('\n原始响应:')
    print(result['raw_response'])
else:
    print('\n成功解析JSON')
