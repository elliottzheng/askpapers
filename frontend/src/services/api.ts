import axios from 'axios'
import type { AxiosResponse } from 'axios'

const API_BASE_URL = 'http://localhost:5000/api'

// 定义接口类型
interface Library {
  name: string;
  // 可根据实际返回数据添加其他属性
}

interface Paper {
  name: string;
  path?: string;
  // 可根据实际返回数据添加其他属性
}


interface QuestionResponse {
  answer: string;
  sources?: string[];
  // 可能还有其他字段
}

interface HistorySession {
  id: string;
  timestamp: string;
  question: string;
  // 可能还有其他字段
}

interface SessionDetail extends HistorySession {
  answer: string;
  sources?: string[];
  // 可能还有其他字段
}

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

export default {
  // 文献库相关
  getLibraries(): Promise<AxiosResponse<Library[]>> {
    return apiClient.get('/libraries')
  },
  createLibrary(name: string): Promise<AxiosResponse<Library>> {
    return apiClient.post('/libraries', { name })
  },
  deleteLibrary(name: string): Promise<AxiosResponse<void>> {
    return apiClient.delete(`/libraries/${name}`)
  },
  
  // 论文相关
  getLibraryPapers(libraryName: string): Promise<AxiosResponse<Paper[]>> {
    return apiClient.get(`/libraries/${libraryName}/papers`)
  },
  uploadPaper(libraryName: string, file: File): Promise<AxiosResponse<Paper>> {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post(`/libraries/${libraryName}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  addPapers(libraryName: string, paperDescs: String[]): Promise<AxiosResponse<Paper[]>> {
    return apiClient.post(`/libraries/${libraryName}/add`, { paper_descs: paperDescs })
  },
  deletePaper(libraryName: string, paperName: string): Promise<AxiosResponse<void>> {
    return apiClient.delete(`/libraries/${libraryName}/papers/${paperName}`)
  },
  
  // 问答相关
  askQuestion(libraryName: string, papers: string[], question: string): Promise<AxiosResponse<QuestionResponse>> {
    return apiClient.post('/ask', {
      library: libraryName,
      papers: papers,
      question: question
    })
  },
  
  // 历史记录相关
  getHistory(): Promise<AxiosResponse<HistorySession[]>> {
    return apiClient.get('/history')
  },
  getSessionDetail(sessionId: string): Promise<AxiosResponse<SessionDetail>> {
    return apiClient.get(`/history/${sessionId}`)
  }
}