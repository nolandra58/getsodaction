import json
from datetime import datetime
from urllib.parse import quote
from playwright.sync_api import sync_playwright

def capture_json_responses(url, proxy_server):
    # 存储所有JSON响应
    json_responses = []
    
    with sync_playwright() as p:
        # 启动浏览器并配置代理
        browser = p.chromium.launch(
            headless=False,
            #proxy={"server": proxy_server}
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
#dict2m3u
#由字典生成m3u函数
def dict_to_m3u(channel_dict, output_file="playlist.m3u"):
    """
    将字典 {频道名: URL} 转换为 M3U 文件
    
    Args:
        channel_dict (dict): 字典格式 {频道名: URL}
        output_file (str): 输出文件名（默认 playlist.m3u）
    """
    proxy = "http://127.0.0.1:1081"
    live_url = ''
    live_token = ''
    user_url = "https://www.camsoda.com/api/v1/video/vtoken/"
    status1 = 0
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")  # M3U 文件头
        i = 0
        for strname, strlogo in channel_dict.items():
            json_data = capture_json_responses(user_url + strname, proxy)
            json2 = json_data[0]['data']
            status1 = json2['status']
            #print(f"{status1}数据类型: {type(status1)}")
            if status1 == 1:
                #print(f"{json2['width']}数据类型: {type(json2['width'])}")
                if json2['edge_servers']:
                    live_token = str(json2['token'])
                    live_url = "https://" + str(json2['edge_servers'][0]) + "/" + str(json2['stream_name']) + "_v1/index.m3u8?token=" + quote(live_token)
                    f.write(f'#EXTINF:-1 group-title="livesoda" tvg-logo="{strlogo}",{strname}\n')
                    f.write(f"{live_url}\n")
            i+=1
            if i == 50:
                break
# 使用示例
if __name__ == "__main__":
    target_url = "https://www.camsoda.com/api/v1/browse/online"  # 替换为实际目标URL
    proxy = "http://127.0.0.1:1081"   # 代理地址
    # 返回当前日期和时间（含年月日时分秒毫秒）
    current_time = datetime.now()
    # 格式化输出
    formatted_time = current_time.strftime("%Y-%m-%d--%H:%M:%S")
    dict1 = {f"更新时间{formatted_time}": "http://example.com/cctv"}
    print(f"正在通过代理 {proxy} 捕获 {target_url} 的JSON响应...")
    json_data = capture_json_responses(target_url, proxy)
    print("解析成功，数据类型:", type(json_data))
    if json_data:
        # 保存JSON数据到文件
        with open("api_responses.json", "w", encoding="utf-8") as f:
            #json.dump(json_data[0]['data'], f, indent=2, ensure_ascii=False)
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        print("\n所有JSON响应已保存到 api_responses.json")
        #print("解析成功，数据类型:", type(json_data))
        for item in json_data[0]['data']['results']:
            #print(item)
            #if "data" in item["metadata"]:
            if '1' in item['tpl'] and '15' in item['tpl']:
                strname = str(item['tpl']['1'])
                strlogo = str(item['tpl']['15'])
                dict1[strname] = strlogo
        print(dict1)
        dict_to_m3u(dict1,"livesoda.m3u")
    else:
        print("未能捕获JSON响应数据")
