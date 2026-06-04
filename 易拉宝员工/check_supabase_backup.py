import httpx
import os
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv('SUPABASE_URL')
supabase_bucket = os.getenv('SUPABASE_BUCKET', 'banner-images')

print("检查 Supabase 备份内容...")
print(f"URL: {supabase_url}")
print(f"Bucket: {supabase_bucket}")
print()

# 下载 products.json
remote_path = "backups/products.json"
public_url = f"{supabase_url}/storage/v1/object/public/{supabase_bucket}/{remote_path}"

print(f"下载: {public_url}")
response = httpx.get(public_url, timeout=30.0)

if response.status_code == 200:
    import json
    data = response.json()
    print(f"✓ 成功下载")
    print(f"产品数量: {len(data)}")
    print()
    print("产品列表:")
    for i, p in enumerate(data, 1):
        print(f"  {i}. {p.get('product_info', {}).get('product_name', 'N/A')} (ID: {p.get('id', 'N/A')})")
else:
    print(f"✗ 下载失败: {response.status_code}")

print()

# 下载 generation_history.json
remote_path = "backups/generation_history.json"
public_url = f"{supabase_url}/storage/v1/object/public/{supabase_bucket}/{remote_path}"

print(f"下载: {public_url}")
response = httpx.get(public_url, timeout=30.0)

if response.status_code == 200:
    import json
    data = response.json()
    print(f"✓ 成功下载")
    print(f"生成记录数量: {len(data)}")
else:
    print(f"✗ 下载失败: {response.status_code}")
