import os
import json
import uuid
import glob
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime
from werkzeug.utils import secure_filename

# 导入现有功能模块
from readers.gemini_reader import GeminiPDFReader
from retrieval.main import import_papers

# 加载环境变量
load_dotenv()

app = Flask(__name__)
CORS(app)  # 启用跨域请求支持

# 配置
LIBRARY_ROOT = os.path.join(os.path.dirname(__file__), '../data/libraries/')
HISTORY_FOLDER = os.path.join(os.path.dirname(__file__), '../data/history/')
ALLOWED_EXTENSIONS = {'pdf'}

# 确保目录存在
os.makedirs(LIBRARY_ROOT, exist_ok=True)
os.makedirs(HISTORY_FOLDER, exist_ok=True)

# 初始化 PDF 阅读器
reader = GeminiPDFReader(os.getenv("API_KEY"))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 获取所有文献库
@app.route('/api/libraries', methods=['GET'])
def get_libraries():
    libraries = []
    # 假设每个库是一个文件夹
    lib_folders = glob.glob(os.path.join(LIBRARY_ROOT, '*'))
    for folder in lib_folders:
        if os.path.isdir(folder):
            lib_name = os.path.basename(folder)
            # 计算包含的论文数量 (每个子文件夹是一篇论文)
            paper_folders = glob.glob(os.path.join(folder, '*'))
            pdf_count = sum(1 for f in paper_folders if os.path.isdir(f))
            libraries.append({
                'name': lib_name,
                'count': pdf_count,
                'created': os.path.getctime(folder)
            })
    return jsonify(libraries)

# 创建新文献库
@app.route('/api/libraries', methods=['POST'])
def create_library():
    data = request.json
    library_name = secure_filename(data.get('name', ''))
    if not library_name:
        return jsonify({'error': 'Library name is required'}), 400
    
    library_path = os.path.join(LIBRARY_ROOT, library_name)
    if os.path.exists(library_path):
        return jsonify({'error': 'Library already exists'}), 400
    
    os.makedirs(library_path)
    return jsonify({'name': library_name, 'created': datetime.now().isoformat()})

# 删除文献库
@app.route('/api/libraries/<library_name>', methods=['DELETE'])
def delete_library(library_name):
    library_path = os.path.join(LIBRARY_ROOT, secure_filename(library_name))
    if not os.path.exists(library_path):
        return jsonify({'error': 'Library not found'}), 404
    
    # 递归删除文件夹
    import shutil
    shutil.rmtree(library_path)
    return jsonify({'success': True})

# 上传 PDF 到文献库 - NEED CHECK, HAS NOT BEEN TESTED
@app.route('/api/libraries/<library_name>/upload', methods=['POST'])
def upload_pdf(library_name):
    library_path = os.path.join(LIBRARY_ROOT, secure_filename(library_name))
    if not os.path.exists(library_path):
        return jsonify({'error': 'Library not found'}), 404
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # 从文件名提取论文标题作为文件夹名
        paper_title = os.path.splitext(filename)[0]
        paper_folder_name = secure_filename(paper_title)
        paper_folder = os.path.join(library_path, paper_folder_name)
        
        # 创建论文文件夹
        os.makedirs(paper_folder, exist_ok=True)
        
        # 保存PDF文件到论文文件夹中
        file_path = os.path.join(paper_folder, filename)
        file.save(file_path)
        
        # 创建简单的info.json
        paper_info = {
            "title": paper_title,
            "arxiv_url": None,
            "github_repo": None,
            "pdf_url": None,
            "entry_name": paper_folder_name
        }
        
        with open(os.path.join(paper_folder, "info.json"), "w", encoding="utf-8") as f:
            json.dump(paper_info, f, ensure_ascii=False, indent=4)
        
        return jsonify({'filename': filename, 'folder': paper_folder_name})
    
    return jsonify({'error': 'Invalid file type'}), 400

# 添加论文到文献库 - 这个已经使用 main.py 中的 import_papers 方法，结构兼容
@app.route('/api/libraries/<library_name>/add', methods=['POST'])
def add_paper(library_name):
    data = request.json
    library_path = os.path.join(LIBRARY_ROOT, secure_filename(library_name))
    
    paper_descs = data.get('paper_descs', [])

    if not paper_descs:
        return jsonify({'error': 'Paper descs is required'}), 400
    
    if not os.path.exists(library_path):
        return jsonify({'error': 'Library not found'}), 404

    downloaded_papers = import_papers(paper_descs, library_path)
    
    return jsonify({'added': downloaded_papers})

def get_paper_info(folder):
    info_file = os.path.join(folder, 'info.json')
    with open(info_file, 'r', encoding='utf-8') as f:
        paper_info = json.load(f)
    folder_name = os.path.basename(folder)
    # Use entry_name from info.json as the PDF filename
    pdf_filename = paper_info.get('entry_name', folder_name) + '.pdf'
    pdf_path = os.path.abspath(os.path.join(folder, pdf_filename))
    return {
        **paper_info,
        'path': pdf_path,
        'size': os.path.getsize(pdf_path),
    }
     

# 获取文献库中的所有 PDF - 修改以适应新结构
@app.route('/api/libraries/<library_name>/papers', methods=['GET'])
def get_library_papers(library_name):
    library_path = os.path.join(LIBRARY_ROOT, secure_filename(library_name))
    if not os.path.exists(library_path):
        return jsonify({'error': 'Library not found'}), 404
    
    papers = []
    paper_folders = [f for f in glob.glob(os.path.join(library_path, '*')) if os.path.isdir(f) and os.path.exists(os.path.join(f, 'info.json'))]
    
    for folder in paper_folders:
        try:
            paper_info = get_paper_info(folder)
            # 敏感信息不应该暴露给前端
            paper_info.pop('path', None)
            papers.append(paper_info)
        except Exception as e:
            print(f"Error processing {folder}: {str(e)}")
    
    return jsonify(papers)

# 从文献库中删除论文 - 修改为删除整个论文文件夹
@app.route('/api/libraries/<library_name>/papers/<folder_name>', methods=['DELETE'])
def delete_paper(library_name, folder_name):
    folder_path = os.path.join(LIBRARY_ROOT, secure_filename(library_name), folder_name)
    if not os.path.exists(folder_path):
        return jsonify({'error': 'Paper folder not found'}), 404
    
    import shutil
    shutil.rmtree(folder_path)
    return jsonify({'success': True})


# 向多个 PDF 提问 - 修改为使用新的文件结构
@app.route('/api/ask', methods=['POST'])
def ask_papers():
    data = request.json
    question = data.get('question')
    library_name = data.get('library')
    paper_folders = data.get('papers', [])  # 现在接收的是文件夹名而不是文件名
    
    if not question:
        return jsonify({'error': 'Question is required'}), 400
    
    library_path = os.path.join(LIBRARY_ROOT, library_name)
    library_path = os.path.abspath(library_path)
    if not os.path.exists(library_path):
        return jsonify({'error': 'Library not found'}), 404
    
    # 生成包含时间戳的唯一会话 ID
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    session_id = f"{library_name}_{timestamp}"
    session_folder = os.path.join(HISTORY_FOLDER, session_id)
    os.makedirs(session_folder, exist_ok=True)
    
    # 保存问题
    with open(os.path.join(session_folder, 'question.txt'), 'w', encoding='utf-8') as f:
        f.write(question)
    
    # 对每个 PDF 提问并保存回答
    responses = []
    for folder_name in paper_folders:
        paper_folder = os.path.join(library_path, folder_name)
        if os.path.exists(paper_folder):
            try:
                paper_info = get_paper_info(paper_folder)
                pdf_path = paper_info.get('path')
                pdf_basename = paper_info.get('entry_name')
                # 保存回答
                answer_file = os.path.join(session_folder, f"{pdf_basename}_response.md")
                response = reader.ask_pdf(question, pdf_path)
                reader.dump_response(response, answer_file)
                
                responses.append({
                    'paper': paper_info.get('title'),
                    'answer': response,
                    'success': True
                })
            except Exception as e:
                responses.append({
                    'paper': folder_name,
                    'error': str(e),
                    'success': False
                })
        else:
            print(f"Paper folder not found: {paper_folder}")
            responses.append({
                'paper': folder_name,
                'error': 'Paper folder not found',
                'success': False
            })
    
    # 保存会话元数据
    metadata = {
        'id': session_id,
        'question': question,
        'library': library_name,
        'papers': paper_folders,  # 保存文件夹名称
        'timestamp': datetime.now().isoformat(),
        'responses': [r['success'] for r in responses]
    }
    
    with open(os.path.join(session_folder, 'metadata.json'), 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    return jsonify({
        'session_id': session_id,
        'responses': responses,
        'metadata': metadata
    })

# 获取历史问答记录和历史会话详情方法不需要修改

# 继续保留原有的历史问答相关方法
@app.route('/api/history', methods=['GET'])
def get_history():
    history_folders = glob.glob(os.path.join(HISTORY_FOLDER, '*'))
    history = []
    
    for folder in history_folders:
        metadata_file = os.path.join(folder, 'metadata.json')
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                try:
                    metadata = json.load(f)
                    history.append(metadata)
                except:
                    pass
    
    # 按时间戳排序
    history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return jsonify(history)

# 获取特定历史会话详情
@app.route('/api/history/<session_id>', methods=['GET'])
def get_history_detail(session_id):
    session_folder = os.path.join(HISTORY_FOLDER, secure_filename(session_id))
    if not os.path.exists(session_folder):
        return jsonify({'error': 'Session not found'}), 404
    
    metadata_file = os.path.join(session_folder, 'metadata.json')
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # 读取每个回答文件
    responses = []
    for paper in metadata.get('papers', []):
        # 查找与该paper对应的响应文件
        # 假设PDF名称格式为paper名+.pdf
        pdf_basename = os.path.splitext(paper)[0]
        answer_file = os.path.join(session_folder, f"{pdf_basename}_response.md")
        
        if os.path.exists(answer_file):
            with open(answer_file, 'r', encoding='utf-8') as f:
                response = f.read()
            responses.append({
                'paper': paper,
                'answer': response
            })
    
    return jsonify({
        'metadata': metadata,
        'responses': responses
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)