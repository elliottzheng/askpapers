import requests

def create_library(library_name):
    """创建一个新的文献库"""
    url = "http://localhost:5000/api/libraries"
    payload = {"name": library_name}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print(f"成功创建文献库: {library_name}")
        return True
    else:
        print(f"创建文献库失败: {response.json().get('error', '未知错误')}")
        return False

def add_papers_to_library(library_name, paper_descs):
    """向文献库添加论文"""
    url = f"http://localhost:5000/api/libraries/{library_name}/add"
    payload = {"paper_descs": paper_descs}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print(f"成功添加 {len(response.json().get('added', []))} 篇论文到 {library_name}")
        return response.json().get('added', [])
    else:
        print(f"添加论文失败: {response.json().get('error', '未知错误')}")
        return []
    
def get_papers_by_library(library_name):
    """获取文献库中的所有论文"""
    url = f"http://localhost:5000/api/libraries/{library_name}/papers"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"获取论文失败: {response.json().get('error', '未知错误')}")
        return []
    
def ask_papers(library_name, question, paper_folders=None):
    """向文献库中的论文提问
    
    Args:
        library_name: 文献库名称
        question: 要提问的问题
        paper_folders: 要查询的论文文件夹名称列表，如果为None则查询所有论文
        
    Returns:
        包含会话ID、响应和元数据的字典
    """
    url = "http://localhost:5000/api/ask"
    payload = {
        "question": question,
        "library": library_name,
    }
    
    if paper_folders:
        payload["papers"] = paper_folders
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"提问失败: {response.json().get('error', '未知错误')}")
        return {}

if __name__ == "__main__":
    # create library named 'test'
    library_name = "test"
    create_library(library_name)
    
    # add paper
    paper_descs = ['https://github.com/Zejun-Yang/AniPortrait']
    added_papers = add_papers_to_library(library_name, paper_descs)
    
    # 打印添加结果
    if added_papers:
        print("添加的论文信息：")
        for paper in added_papers:
            print(f"- 标题: {paper.get('title', 'N/A')}")
            print(f"  存储路径: {paper.get('entry_name', 'N/A')}")
            print(f"  Github: {paper.get('github_repo', 'N/A')}")

    # 获取文献库中的所有论文
    papers = get_papers_by_library(library_name)
    print(f"文献库 {library_name} 中的论文：")
    for paper in papers:
        print(paper)

    # 提问示例
    question = "这个论文的主要创新点是什么？"
    paper_folders = [paper.get('entry_name') for paper in papers]  # 获取所有论文的文件夹名
    
    print(f"\n向论文提问: {question}")
    answers = ask_papers(library_name, question, paper_folders)
    
    if answers and 'responses' in answers:
        print("\n回答结果:")
        for response in answers['responses']:
            if response.get('success', False):
                print(f"论文 {response.get('paper')} 的回答:")
                print(response.get('answer', '无回答'))
                print("-" * 50)
            else:
                print(f"论文 {response.get('paper')} 回答失败: {response.get('error')}")
    else:
        print("未获得回答")