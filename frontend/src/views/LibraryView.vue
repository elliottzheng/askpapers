<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';

const router = useRouter();
const libraries = ref<any[]>([]);
const loading = ref(true);
const error = ref('');
const showNewLibraryDialog = ref(false);
const newLibraryName = ref('');
const processingLibrary = ref('');

// 获取所有文献库
const fetchLibraries = async () => {
  loading.value = true;
  error.value = '';
  try {
    const response = await api.getLibraries();
    libraries.value = response.data;
  } catch (err: any) {
    error.value = '获取文献库列表失败: ' + (err.message || '未知错误');
    console.error('获取文献库列表失败:', err);
  } finally {
    loading.value = false;
  }
};

// 创建新的文献库
const createLibrary = async () => {
  if (!newLibraryName.value.trim()) {
    return;
  }
  
  processingLibrary.value = newLibraryName.value;
  try {
    await api.createLibrary(newLibraryName.value.trim());
    showNewLibraryDialog.value = false;
    newLibraryName.value = '';
    await fetchLibraries();
  } catch (err: any) {
    error.value = '创建文献库失败: ' + (err.message || '未知错误');
    console.error('创建文献库失败:', err);
  } finally {
    processingLibrary.value = '';
  }
};

// 删除文献库
const deleteLibrary = async (libraryName: string) => {
  if (!confirm(`确定要删除文献库"${libraryName}"吗？此操作不可恢复。`)) {
    return;
  }
  
  processingLibrary.value = libraryName;
  try {
    await api.deleteLibrary(libraryName);
    await fetchLibraries();
  } catch (err: any) {
    error.value = '删除文献库失败: ' + (err.message || '未知错误');
    console.error('删除文献库失败:', err);
  } finally {
    processingLibrary.value = '';
  }
};

// 打开文献库进入论文管理页面
const openLibrary = (libraryName: string) => {
  router.push({ name: 'papers', params: { library: libraryName } });
};

// 格式化日期
const formatDate = (timestamp: number) => {
  if (!timestamp) return '未知日期';
  return new Date(timestamp * 1000).toLocaleDateString('zh-CN');
};

onMounted(() => {
  fetchLibraries();
});
</script>

<template>
  <div class="library">
    <div class="library-header">
      <h1>文献库管理</h1>
      <button class="btn create-btn" @click="showNewLibraryDialog = true">创建文献库</button>
    </div>
    
    <div v-if="error" class="error-message">
      {{ error }}
      <button @click="fetchLibraries">重试</button>
    </div>
    
    <div v-if="loading" class="loading">
      加载中...
    </div>
    
    <div v-else-if="libraries.length === 0" class="empty-state">
      <p>暂无文献库</p>
      <button class="btn" @click="showNewLibraryDialog = true">创建第一个文献库</button>
    </div>
    
    <div v-else class="library-list">
      <div v-for="library in libraries" :key="library.name" class="library-card">
        <div class="library-info" @click="openLibrary(library.name)">
          <h2 class="library-name">{{ library.name }}</h2>
          <div class="library-meta">
            <span class="library-count">{{ library.count || 0 }} 篇论文</span>
            <span class="library-date">创建于 {{ formatDate(library.created) }}</span>
          </div>
        </div>
        <button class="delete-btn" 
          @click.stop="deleteLibrary(library.name)"
          :disabled="processingLibrary === library.name">
          {{ processingLibrary === library.name ? '删除中...' : '删除' }}
        </button>
      </div>
    </div>
    
    <!-- 创建新文献库对话框 -->
    <div v-if="showNewLibraryDialog" class="dialog-overlay">
      <div class="dialog">
        <h3>创建新文献库</h3>
        <div class="dialog-content">
          <input 
            v-model="newLibraryName" 
            placeholder="输入文献库名称"
            @keyup.enter="createLibrary"
            autofocus
          />
        </div>
        <div class="dialog-actions">
          <button 
            class="btn cancel" 
            @click="showNewLibraryDialog = false"
            :disabled="processingLibrary === newLibraryName">
            取消
          </button>
          <button 
            class="btn confirm" 
            @click="createLibrary"
            :disabled="!newLibraryName.trim() || processingLibrary === newLibraryName">
            {{ processingLibrary === newLibraryName ? '创建中...' : '创建' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.library {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.library-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.create-btn {
  background-color: #4CAF50;
  color: white;
}

.create-btn:hover {
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

.library-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.library-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  transition: box-shadow 0.2s, transform 0.1s;
}

.library-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.library-info {
  flex: 1;
  cursor: pointer;
}

.library-name {
  margin: 0 0 8px 0;
  font-size: 18px;
}

.library-meta {
  display: flex;
  flex-direction: column;
  color: #666;
  font-size: 14px;
  gap: 4px;
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
  width: 400px;
  max-width: 90%;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.dialog h3 {
  margin-top: 0;
  margin-bottom: 16px;
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