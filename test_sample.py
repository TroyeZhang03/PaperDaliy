import arxiv
import openai
import json
import os

# ================= 配置区域 =================
# 注意：你原代码写的是 os.environ.get("sk-...")，这是去系统环境变量里找一个叫 sk-... 的变量名
# 实际上你应该直接把 Key 赋值给 api_key，或者设置环境变量名为 "OPENAI_API_KEY"
# 为了测试方便，这里直接填入你的字符串：
API_KEY = "api_key" 
BASE_URL = "https://chat.ecnu.edu.cn/open/api/v1"
MODEL_NAME = "ecnu-max"

# 关键词
KEYWORDS = ["Large Language Model"] 
# ===========================================

def test_arxiv_fetch():
    print("--- 步骤 1: 正在尝试连接 Arxiv 获取 1 篇论文 ---")
    try:
        # 只获取 1 篇，减少等待时间
        search = arxiv.Search(
            query=" OR ".join(KEYWORDS),
            max_results=1,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        
        results = list(search.results())
        if not results:
            print("❌ Arxiv 未返回任何结果，请检查网络或关键词。")
            return None
            
        paper = results[0]
        print(f"✅ 成功获取论文: {paper.title}")
        print(f"📄 摘要长度: {len(paper.summary)} 字符")
        
        return {
            "title": paper.title,
            "abstract_en": paper.summary
        }
        
    except Exception as e:
        print(f"❌ Arxiv 连接失败: {e}")
        print("💡 提示: Arxiv 在国内访问可能不稳定，如果一直超时，需要检查网络代理。")
        return None

def test_llm_call(paper_data):
    print("\n--- 步骤 2: 正在尝试调用大模型 API 生成总结 ---")
    
    client = openai.OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL
    )
    
    prompt = f"""
    请阅读这篇论文的摘要：
    {paper_data['abstract_en']}
    
    任务：
    1. 用中文一句话概括核心创新点。
    2. 生成一段约100字的中文摘要。
    
    返回JSON格式：{{"one_sentence": "...", "summary_cn": "..."}}
    """
    
    try:
        print(f"🚀 正在发送请求给模型: {MODEL_NAME} ...")
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            # 注意：如果 ecnu-max 模型不支持 json_object 模式，这里可能会报错
            # 如果报错，可以尝试去掉 response_format 参数
            response_format={"type": "json_object"} 
        )
        
        content = response.choices[0].message.content
        print("✅ API 调用成功！返回原始内容：")
        print(content)
        
        # 尝试解析 JSON
        try:
            parsed_json = json.loads(content)
            print("\n✨ JSON 解析验证成功：")
            print(f"🔹 一句话总结: {parsed_json.get('one_sentence')}")
            print(f"🔹 详细摘要: {parsed_json.get('summary_cn')}")
        except json.JSONDecodeError:
            print("⚠️ API 返回了内容，但不是标准的 JSON 格式，可能模型未严格遵循指令。")
            
    except openai.APIConnectionError:
        print("❌ 连接 API 服务器失败。请检查 BASE_URL 是否正确，或网络是否通畅。")
    except openai.AuthenticationError:
        print("❌ 认证失败。请检查 API Key 是否正确/过期。")
    except Exception as e:
        print(f"❌ 其他错误: {e}")

if __name__ == "__main__":
    print("开始测试...\n")
    
    # 1. 抓数据
    paper_data = test_arxiv_fetch()
    
    # 2. 如果抓到了，就测 AI
    if paper_data:
        test_llm_call(paper_data)
    
    print("\n测试结束。")