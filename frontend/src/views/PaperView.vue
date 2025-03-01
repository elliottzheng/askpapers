<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '@/services/api';

const route = useRoute();
const router = useRouter();
const libraryName = ref(route.params.library as string);
const papers = ref<any[]>([]);
const loading = ref(true);
const error = ref('');
const processingPaper = ref('');
const showAddPaperDialog = ref(false);
const paperDescription = ref('');
const isUploading = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);
const selectedFile = ref<File | null>(null);
const addMethod = ref<'url' | 'file'>('url');

// 监听路由变化，更新当前库名
watch(() => route.params.library, (newLibrary) => {
  libraryName.value = newLibrary as string;
  fetchPapers();
});

// 获取所有论文
const fetchPapers = async () => {
  if (!libraryName.value) return;
  
  loading.value = true;
  error.value = '';
  try {
    const response = await api.getLibraryPapers(libraryName.value);
    papers.value = response.data;
  } catch (err: any) {
    error.value = '获取论文列表失败: ' + (err.message || '未知错误');
    console.error('获取论文列表失败:', err);
  } finally {
    loading.value = false;
  }
};

// 通过URL添加论文
const addPaperByUrl = async () => {
  if (!paperDescription.value.trim()) {
    return;
  }
  
  isUploading.value = true;
  error.value = '';
  try {
    // 将输入的URL作为论文描述传递
    const response = await api.addPapers(libraryName.value, [paperDescription.value.trim()]);
    showAddPaperDialog.value = false;
    paperDescription.value = '';
    await fetchPapers();
  } catch (err: any) {
    error.value = '添加论文失败: ' + (err.message || '未知错误');
    console.error('添加论文失败:', err);
  } finally {
    isUploading.value = false;
  }
};

// 通过文件上传添加论文
const addPaperByFile = async () => {
  if (!selectedFile.value) {
    return;
  }
  
  isUploading.value = true;
  error.value = '';
  try {
    await api.uploadPaper(libraryName.value, selectedFile.value);
    showAddPaperDialog.value = false;
    selectedFile.value = null;
    await fetchPapers();
  } catch (err: any) {
    error.value = '上传论文失败: ' + (err.message || '未知错误');
    console.error('上传论文失败:', err);
  } finally {
    isUploading.value = false;
  }
};

// 添加论文 - 根据选择的方法调用不同函数
const addPaper = () => {
  if (addMethod.value === 'url') {
    addPaperByUrl();
  } else {
    addPaperByFile();
  }
};

// 删除论文
const deletePaper = async (paperName: string) => {
  if (!confirm(`确定要删除论文"${paperName}"吗？此操作不可恢复。`)) {
    return;
  }
  
  processingPaper.value = paperName;
  try {
    await api.deletePaper(libraryName.value, paperName);
    await fetchPapers();
  } catch (err: any) {
    error.value = '删除论文失败: ' + (err.message || '未知错误');
    console.error('删除论文失败:', err);
  } finally {
    processingPaper.value = '';
  }
};

// 打开论文阅读页面
const openPaper = (paperName: string) => {
  router.push({ 
    name: 'reader', 
    params: { 
      library: libraryName.value,
      paper: paperName 
    } 
  });
};

// 处理文件选择
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0];
  }
};

// 返回文献库列表
const goBack = () => {
  router.push({ name: 'library' });
};

// 格式化日期
const formatDate = (timestamp: number) => {
  if (!timestamp) return '未知日期';
  return new Date(timestamp * 1000).toLocaleDateString('zh-CN');
};

onMounted(() => {
  fetchPapers();
});
</script>

<template>
  <div class="papers">
    <div class="papers-header">
      <div class="header-left">
        <button class="btn back-btn" @click="goBack">返回</button>
        <h1>{{ libraryName }} - 论文管理</h1>
      </div>
      <button class="btn add-btn" @click="showAddPaperDialog = true">添加论文</button>
    </div>
    
    <div v-if="error" class="error-message">
      {{ error }}
      <button @click="fetchPapers">重试</button>
    </div>
    
    <div v-if="loading" class="loading">
      加载中...
    </div>
    
    <div v-else-if="papers.length === 0" class="empty-state">
      <p>暂无论文</p>
      <button class="btn" @click="showAddPaperDialog = true">添加第一篇论文</button>
    </div>
    
    <div v-else class="papers-list">
      <div v-for="paper in papers" :key="paper.entry_name" class="paper-card">
        <div class="paper-info" @click="openPaper(paper.entry_name)">
          <h2 class="paper-title">{{ paper.title }}</h2>
          <div class="paper-meta">
            <span v-if="paper.authors" class="paper-authors">作者: {{ paper.authors.join(', ') }}</span>
            <div class="paper-links">
              <a v-if="paper.arxiv_url" 
                 :href="paper.arxiv_url" 
                 target="_blank"
                 @click.stop>arXiv</a>
              <a v-if="paper.github_repo" 
                 :href="paper.github_repo" 
                 target="_blank"
                 @click.stop>GitHub</a>
            </div>
            <span class="paper-size">大小: {{ (paper.size / (1024 * 1024)).toFixed(2) }} MB</span>
          </div>
        </div>
        <button class="delete-btn" 
          @click.stop="deletePaper(paper.entry_name)"
          :disabled="processingPaper === paper.entry_name">
          {{ processingPaper === paper.entry_name ? '删除中...' : '删除' }}
        </button>
      </div>
    </div>
    
    <!-- 添加论文对话框 -->
    <div v-if="showAddPaperDialog" class="dialog-overlay">
      <div class="dialog">
        <h3>添加论文</h3>
        <div class="dialog-tabs">
          <button 
            :class="['tab-btn', { active: addMethod === 'url' }]" 
            @click="addMethod = 'url'">
            通过URL添加
          </button>
          <button 
            :class="['tab-btn', { active: addMethod === 'file' }]" 
            @click="addMethod = 'file'">
            上传PDF文件
          </button>
        </div>
        
        <div v-if="addMethod === 'url'" class="dialog-content">
          <p class="help-text">支持 arXiv URL、PDF 直链或 GitHub 仓库链接</p>
          <input 
            v-model="paperDescription" 
            placeholder="输入论文URL"
            @keyup.enter="addPaper"
            autofocus
          />
        </div>
        
        <div v-else class="dialog-content">
          <input 
            type="file" 
            ref="fileInput"
            accept=".pdf"
            @change="handleFileSelect"
            style="display: none"
          />
          <button class="file-select-btn" @click="fileInput?.click()">
            选择PDF文件
          </button>
          <div v-if="selectedFile" class="selected-file">
            已选择: {{ selectedFile.name }}
          </div>
        </div>
        
        <div class="dialog-actions">
          <button 
            class="btn cancel" 
            @click="showAddPaperDialog = false"
            :disabled="isUploading">
            取消
          </button>
          <button 
            class="btn confirm" 
            @click="addPaper"
            :disabled="(addMethod === 'url' && !paperDescription.trim()) || 
                      (addMethod === 'file' && !selectedFile) || 
                      isUploading">
            {{ isUploading ? '添加中...' : '添加' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.papers {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.papers-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  background-color: #f0f0f0;
  color: #333;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.add-btn {
  background-color: #4CAF50;
  color: white;
}

.add-btn:hover {
  background-color: #45a049;
}

.loading, .empty-state {
  text-align: center;
  padding: 40px 0;
  color: #666;
}

.empty-state .btn {
  margin-top: 16px;
  background-color: #4CAF50;
  color: white;
}

.papers-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.paper-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  transition: box-shadow 0.2s, transform 0.1s;
}

.paper-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.paper-info {
  flex: 1;
  cursor: pointer;
}

.paper-title {
  margin: 0 0 8px 0;
  font-size: 18px;
}

.paper-meta {
  display: flex;
  flex-direction: column;
  color: #666;
  font-size: 14px;
  gap: 4px;
}

.paper-links {
  display: flex;
  gap: 12px;
}

.paper-links a {
  color: #1890ff;
  text-decoration: none;
}

.paper-links a:hover {
  text-decoration: underline;
}

.delete-btn {
  background-color: transparent;
  color: #ff4d4f;
  border: 1px solid #ff4d4f;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.delete-btn:hover {
  background-color: #fff1f0;
}

.delete-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-message {
  background-color: #fff2f0;
  border: 1px solid #ffccc7;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.error-message button {
  background-color: #ff4d4f;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 4px 8px;
  cursor: pointer;
}

/* 对话框样式 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
}

.dialog {
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  width: 450px;
  max-width: 90%;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.dialog h3 {
  margin-top: 0;
  margin-bottom: 16px;
}

.dialog-tabs {
  display: flex;
  margin-bottom: 16px;
  border-bottom: 1px solid #e0e0e0;
}

.tab-btn {
  padding: 8px 16px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  border-bottom: 2px solid transparent;
}

.tab-btn.active {
  color: #1890ff;
  border-bottom-color: #1890ff;
}

.help-text {
  margin-top: 0;
  margin-bottom: 8px;
  font-size: 12px;
  color: #666;
}

.dialog-content {
  margin-bottom: 20px;
}

.dialog-content input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
}

.file-select-btn {
  width: 100%;
  padding: 12px;
  background-color: #f5f5f5;
  color: #333;
  border: 1px dashed #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
  text-align: center;
}

.selected-file {
  margin-top: 12px;
  padding: 8px;
  background-color: #f5f5f5;
  border-radius: 4px;
  font-size: 14px;
  color: #333;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.cancel {
  background-color: #f5f5f5;
  color: #333;
}

.confirm {
  background-color: #4CAF50;
  color: white;
}

.confirm:disabled {
  background-color: #a0d9a3;
  cursor: not-allowed;
}
</style>