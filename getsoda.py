import json
from playwright.sync_api import sync_playwright

def capture_json_responses(url, proxy_server):
    # 存储所有JSON响应
    json_responses = []
    
    with sync_playwright() as p:
        # 启动浏览器并配置代理
        browser = p.chromium.launch(
            headless=False,
            proxy={"server": proxy_server}
        )
        
        # 创建上下文
        context = browser.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # 监听所有响应
        def handle_response(response):
            # 只处理成功的JSON响应
            if response.ok and "application/json" in response.headers.get("content-type", "").lower():
                try:
                    json_data = response.json()
                    json_responses.append({
                        "url": response.url,
                        "status": response.status,
                        "method": response.request.method,
                        "request_headers": dict(response.request.headers),
                        "response_headers": dict(response.headers),
                        "data": json_data,
                        "timestamp": response.request.timing["startTime"]
                    })
                except Exception as e:
                    print(f"解析JSON响应出错 ({response.url}): {str(e)}")
        
        # 绑定响应处理器
        page.on("response", handle_response)
        
        try:
            # 导航到目标URL
            print(f"正在访问: {url}")
            page.goto(url, timeout=30000, wait_until="networkidle")
            
            # 等待额外时间确保捕获所有异步请求
            page.wait_for_timeout(5000)
            
            return json_responses
            
        except Exception as e:
            print(f"页面导航出错: {str(e)}")
            return None
            
        finally:
            # 确保关闭浏览器
            context.close()
            browser.close()

# 使用示例
if __name__ == "__main__":
    target_url = "https://www.camsoda.com/api/v1/browse/online"  # 替换为实际目标URL
    proxy = "http://127.0.0.1:1081"   # 代理地址
    
    print(f"正在通过代理 {proxy} 捕获 {target_url} 的JSON响应...")
    json_data = capture_json_responses(target_url, proxy)
    
    if json_data:
        # 保存JSON数据到文件
        with open("api_responses.json", "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        # 打印摘要信息
        print(f"\n成功捕获 {len(json_data)} 个JSON响应:")
        for i, resp in enumerate(json_data, 1):
            print(f"\n响应 #{i}:")
            print(f"URL: {resp['url']}")
            print(f"方法: {resp['method']}")
            print(f"状态码: {resp['status']}")
            print(f"数据大小: {len(str(resp['data']))} 字符")
        
        print("\n所有JSON响应已保存到 api_responses.json")
    else:
        print("未能捕获JSON响应数据")