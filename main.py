import arxiv
import openai
import json
import datetime
import os

# 配置你的关键词
KEYWORDS = ["Large Language Model", "Computer Vision", "Generative AI"]
# 配置知名机构关键词（用于简单筛选）
FAMOUS_ORGS = ["Google", "Meta", "Microsoft", "Stanford", "MIT", "Berkeley", "Tencent", "Alibaba"]

# 初始化 AI 客户端 (这里以 OpenAI 格式为例，可换 DeepSeek)
client = openai.OpenAI(
    api_key = os.environ.get("AI_API_KEY"),  # 从环境变量获取 Key
    base_url="https://chat.ecnu.edu.cn/open/api/v1" # 如果用 DeepSeek
)

def get_papers():
    search = arxiv.Search(
        query=" OR ".join(KEYWORDS),
        max_results=50,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    paper_list = []
    
    for result in search.results():
        # 简单的筛选逻辑：检查作者单位或备注中是否包含知名机构
        # 注意：Arxiv API 的单位信息有时不全，这里是简易实现
        # 实际中可能需要爬取 PDF 或 HTML 页面来获得更准确的单位
        # 这里为了演示，我们先不过滤太狠，或者暂时不过滤单位，只过滤内容
        
        paper_info = {
            "title": result.title,
            "url": result.entry_id,
            "abstract_en": result.summary,
            "date": result.published.strftime("%Y-%m-%d")
        }
        paper_list.append(paper_info)
        
        if len(paper_list) >= 5: # 每天只推前5篇高质量的
            break
            
    return paper_list

def summarize_paper(paper):
    prompt = f"""
    请阅读这篇论文的摘要：
    {paper['abstract_en']}
    
    任务：
    1. 用中文一句话概括核心创新点。
    2. 生成一段约100字的中文摘要。
    
    返回JSON格式：{{"one_sentence": "...", "summary_cn": "..."}}
    """
    
    response = client.chat.completions.create(
        model="ecnu-max", # 或 gpt-3.5-turbo
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)

def main():
    papers = get_papers()
    final_data = []
    
    for paper in papers:
        try:
            ai_res = summarize_paper(paper)
            paper["summary_cn"] = ai_res["summary_cn"]
            paper["one_sentence"] = ai_res["one_sentence"]
            final_data.append(paper)
            print(f"Processed: {paper['title']}")
        except Exception as e:
            print(f"Error processing {paper['title']}: {e}")

    # 保存为 JSON 文件，供 App 读取
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = "latest_papers.json" 
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()