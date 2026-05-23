"""
检查 Running Hub 账户状态和可用服务
"""

import httpx
import os
from dotenv import load_dotenv

load_dotenv()

def check_account_status():
    """检查账户状态"""

    api_key = os.getenv("RUNNINGHUB_API_KEY")
    base_url = os.getenv("RUNNINGHUB_BASE_URL", "https://www.runninghub.cn/openapi/v2")

    if not api_key:
        print("[ERROR] 未找到 RUNNINGHUB_API_KEY")
        return

    print(f"[INFO] API Key: {api_key[:10]}...")
    print(f"[INFO] Base URL: {base_url}")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # 尝试不同的 API 端点来检查账户状态
    endpoints_to_test = [
        "/account/info",
        "/account/balance",
        "/user/info",
        "/query",  # 查询端点（用假 taskId 测试）
    ]

    print("\n=== 测试 API 端点 ===")

    for endpoint in endpoints_to_test:
        url = f"{base_url}{endpoint}"
        print(f"\n[INFO] 测试: {url}")

        try:
            if endpoint == "/query":
                # 查询端点需要 POST 请求
                response = httpx.post(
                    url,
                    json={"taskId": "test"},
                    headers=headers,
                    timeout=30.0
                )
            else:
                # 其他端点尝试 GET 请求
                response = httpx.get(
                    url,
                    headers=headers,
                    timeout=30.0
                )

            print(f"  状态码: {response.status_code}")
            print(f"  响应: {response.text[:200]}")

            if response.status_code == 200:
                print(f"  [OK] 端点可访问")
            elif response.status_code == 401:
                print(f"  [ERROR] 认证失败 - API 密钥无效")
            elif response.status_code == 403:
                print(f"  [ERROR] 权限不足")
            elif response.status_code == 404:
                print(f"  [INFO] 端点不存在")

        except Exception as e:
            print(f"  [ERROR] 请求失败: {str(e)}")

    # 测试图片上传功能
    print("\n=== 测试图片上传 ===")

    upload_url = f"{base_url}/media/upload/binary"
    print(f"[INFO] 上传端点: {upload_url}")

    # 创建一个简单的测试图片
    from PIL import Image
    import io

    # 创建一个 100x100 的红色图片
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    try:
        files = {'file': ('test.png', img_bytes, 'image/png')}
        response = httpx.post(
            upload_url,
            files=files,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60.0
        )

        print(f"  状态码: {response.status_code}")
        print(f"  响应: {response.text[:200]}")

        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                print(f"  [OK] 上传成功")
                print(f"  文件名: {result['data'].get('fileName')}")
            else:
                print(f"  [ERROR] 上传失败: {result.get('message')}")
        else:
            print(f"  [ERROR] 上传失败")

    except Exception as e:
        print(f"  [ERROR] 上传异常: {str(e)}")


if __name__ == "__main__":
    print("=" * 60)
    print("Running Hub 账户状态检查")
    print("=" * 60)

    check_account_status()

    print("\n" + "=" * 60)
    print("检查完成")
    print("\n建议:")
    print("1. 登录 Running Hub 控制台检查账户余额和配额")
    print("2. 确认 API 密钥有访问 rhart-image-g-2 服务的权限")
    print("3. 查看 Running Hub 文档确认 API 端点是否正确")
    print("=" * 60)
