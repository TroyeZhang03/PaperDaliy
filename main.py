import arxiv
import openai
import json
import datetime
import os
import time

# ================= 配置区域 =================
# 搜索关键词
KEYWORDS = ["Large Language Model", "Computer Vision", "Generative AI"]

# 从 GitHub Secrets 获取 Key
API_KEY = os.environ.get("AI_API_KEY")
BASE_URL = "https://chat.ecnu.edu.cn/open/api/v1"
MODEL_NAME = "ecnu-max"

# ===========================================

def get_papers():
    """
    获取 Arxiv 上的最新论文
    """
    print("--- 正在连接 Arxiv 获取论文列表 ---")
    
    # 使用新的 Client 写法，修复 DeprecationWarning
    client = arxiv.Client()
    
    search = arxiv.Search(
        query=" OR ".join(KEYWORDS),
        max_results=5, # 每天只处理最新的 5 篇，避免 token 消耗过多
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    paper_list = []
    
    try:
        results = client.results(search)
        for result in results:
            paper_info = {
                "title": result.title,
                "url": result.entry_id,
                # 替换掉摘要里的换行符，保持整洁
                "abstract_en": result.summary.replace("\n", " "),
                "date": result.published.strftime("%Y-%m-%d")
            }
            paper_list.append(paper_info)
    except Exception as e:
        print(f"❌ Arxiv 获取失败: {e}")
        
    print(f"✅ 成功获取 {len(paper_list)} 篇论文原数据")
    return paper_list

def summarize_paper(paper):
    """
    调用大模型生成中文总结
    """
    if not API_KEY:
        raise ValueError("❌ 错误：未找到 API Key，请检查 GitHub Secrets 设置！")

    client = openai.OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL
    )

    prompt = f"""
    请阅读这篇计算机论文的摘要：
    {paper['abstract_en']}
    
    任务：
    1. 用中文一句话概括核心创新点 (字段名: one_sentence)。
    2. 生成一段约100字的中文摘要 (字段名: summary_cn)。
    
    请直接返回 JSON 格式，不要包含 Markdown 格式标记。
    格式示例：
    {{
        "one_sentence": "本文提出了一种...",
        "summary_cn": "这是一篇关于..."
    }}
    """
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        # 强制要求 JSON 模式，防止模型乱说话
        response_format={"type": "json_object"}
    )
    
    content = response.choices[0].message.content
    return json.loads(content)

def main():
    papers = get_papers()
    final_data = []
    
    if not papers:
        print("⚠️以此警告：没有获取到任何论文，脚本结束。")
        return

    print("--- 开始 AI 总结任务 ---")
    
    for paper in papers:
        try:
            print(f"🤖 正在处理: {paper['title'][:30]}...")
            
            # 调用 AI
            ai_res = summarize_paper(paper)
            
            # 填充数据
            paper["summary_cn"] = ai_res.get("summary_cn", "AI 总结生成失败")
            paper["one_sentence"] = ai_res.get("one_sentence", "暂无一句话总结")
            
            final_data.append(paper)
            print("   ✅ 处理成功")
            
            # 休息 1 秒，防止并发太快
            time.sleep(1)
            
        except Exception as e:
            print(f"   ❌ 处理失败: {e}")
            # 即使 AI 失败，也把原始论文存下来，保证 App 有东西看
            paper["summary_cn"] = "AI 接口暂时不可用，请阅读下方英文摘要。"
            paper["one_sentence"] = "生成失败"
            final_data.append(paper)

    # 保存为 JSON 文件
    filename = "latest_papers.json" 
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        print(f"\n🎉 全部完成！数据已保存到 {filename}")
    except Exception as e:
        print(f"❌ 文件保存失败: {e}")

if __name__ == "__main__":
    main()
