<script setup lang="tsx">
import {
  Attachments,
  type AttachmentsProps,
  Bubble,
  type BubbleListProps,
  Conversations,
  type ConversationsProps,
  Prompts,
  type PromptsProps,
  Sender,
  Welcome,
  useXChat,
} from 'ant-design-x-vue';
import {
  BookOutlined,
  CloudUploadOutlined,
  FileTextOutlined,
  PaperClipOutlined,
  PlusOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons-vue';
import { Badge, Button, Space, theme, Modal, Checkbox, Select, Spin, Empty, Typography } from 'ant-design-vue';
import { computed, ref, watch, onMounted } from 'vue';
import api from '@/services/api';
import markdownit from 'markdown-it';

defineOptions({ name: 'PaperChatInterface' });

// ==================== 类型定义 ====================
interface Library {
  name: string;
  count: number;
  created: string;
}

interface Paper {
  title: string;
  entry_name: string;
  arxiv_url?: string;
  github_repo?: string;
}

interface PaperResponse {
  paper: string;
  answer: string;
  success: boolean;
  error?: string;
}

// ==================== 状态管理 ====================
// 库和论文选择状态
const libraries = ref<Library[]>([]);
const selectedLibrary = ref<string>('');
const papers = ref<Paper[]>([]);
const selectedPapers = ref<string[]>([]);
const loadingLibraries = ref(false);
const loadingPapers = ref(false);

// 对话状态
const headerOpen = ref(false);
const content = ref('');
const conversationsItems = ref<any[]>([]);
const activeKey = ref<string>('');
const attachedFiles = ref<AttachmentsProps['items']>([]);
const askingQuestion = ref(false);

// 模态框状态
const selectModalVisible = ref(false);

// ==================== 样式设置 ====================
const { token } = theme.useToken();
const styles = computed(() => {
  return {
    layout: {
      width: '100%',
      height: 'calc(100vh - 60px)', // 减去导航栏高度
      'border-radius': `${token.value.borderRadius}px`,
      display: 'flex',
      background: `${token.value.colorBgContainer}`,
      'font-family': `${token.value.fontFamily}, sans-serif`,
    },
    menu: {
      background: `${token.value.colorBgLayout}80`,
      width: '280px',
      height: '100%',
      display: 'flex',
      'flex-direction': 'column',
    },
    conversations: {
      padding: '0 12px',
      flex: 1,
      'overflow-y': 'auto',
    },
    chat: {
      height: '100%',
      flex: 1,
      margin: '0 auto',
      'box-sizing': 'border-box',
      display: 'flex',
      'flex-direction': 'column',
      padding: `${token.value.paddingLG}px`,
      gap: '16px',
    },
    messages: {
      flex: 1,
      overflow: 'auto',
    },
    placeholder: {
      'padding-top': '32px',
    },
    sender: {
      'box-shadow': token.value.boxShadow,
    },
    logo: {
      display: 'flex',
      height: '72px',
      'align-items': 'center',
      'justify-content': 'start',
      padding: '0 24px',
      'box-sizing': 'border-box',
    },
    'logo-img': {
      width: '24px',
      height: '24px',
      display: 'inline-block',
    },
    'logo-span': {
      display: 'inline-block',
      margin: '0 8px',
      'font-weight': 'bold',
      color: token.value.colorText,
      'font-size': '16px',
    },
    addBtn: {
      background: '#1677ff0f',
      border: '1px solid #1677ff34',
      width: 'calc(100% - 24px)',
      margin: '0 12px 24px 12px',
    },
    paperResponse: {
      margin: '12px 0',
      padding: '12px',
      'border-radius': '8px',
      border: `1px solid ${token.value.colorBorderSecondary}`,
    },
    paperTitle: {
      'font-weight': 'bold',
      'margin-bottom': '0px',
    },
    paperContent: {
      'white-space': 'pre-wrap',
    },
    expandBtn: {
      'margin-top': '8px',
    },
    librarySelect: {
      width: '100%',
      'margin-bottom': '16px',
    },
    papersContainer: {
      'margin-top': '16px',
      'max-height': '300px',
      'overflow-y': 'auto',
    },
    // 添加 Markdown 相关样式
    markdownP: {
      'margin-bottom': '0px',
      'line-height': '1.6',
      'color': token.value.colorText
    },
  } as const;
});

// ==================== 角色定义 ====================
const roles: BubbleListProps['roles'] = {
  user: {
    placement: 'end',
    variant: 'shadow',
  },
  paper: {
    placement: 'start',
    variant: 'filled',
    styles: {
      content: {
        borderRadius: '16px',
      },
    },
  },
};

// ==================== 数据加载 ====================
onMounted(async () => {
  await loadLibraries();
});

const loadLibraries = async () => {
  loadingLibraries.value = true;
  try {
    const response = await api.getLibraries();
    libraries.value = response.data;
    // 如果有库，默认选择第一个
    if (libraries.value.length > 0) {
      selectedLibrary.value = libraries.value[0].name;
      await loadPapers(selectedLibrary.value);
    }
  } catch (error) {
    console.error('Failed to load libraries:', error);
  } finally {
    loadingLibraries.value = false;
  }
};

const loadPapers = async (libraryName: string) => {
  if (!libraryName) return;
  
  loadingPapers.value = true;
  selectedPapers.value = []; // 清空已选论文
  
  try {
    const response = await api.getLibraryPapers(libraryName);
    papers.value = response.data;
  } catch (error) {
    console.error('Failed to load papers:', error);
    papers.value = [];
  } finally {
    loadingPapers.value = false;
  }
};

// ==================== 聊天功能 ====================
const { messages, setMessages } = useXChat({});

// 添加聊天会话
const addConversation = async () => {
  if (!selectedLibrary.value) {
    Modal.warning({
      title: '请先选择文献库',
      content: '在开始新对话前，请先选择一个文献库',
    });
    return;
  }
  
  selectModalVisible.value = true;
};

// 确认论文选择
const confirmPaperSelection = () => {
  if (selectedPapers.value.length === 0) {
    Modal.warning({
      title: '请选择至少一篇论文',
      content: '您需要选择至少一篇论文才能开始对话',
    });
    return;
  }

  const newConversationId = Date.now().toString();
  const selectedPaperTitles = selectedPapers.value.map(paperId => {
    const paper = papers.value.find(p => p.entry_name === paperId);
    return paper ? paper.title : paperId;
  });

  conversationsItems.value = [
    ...conversationsItems.value,
    {
      key: newConversationId,
      label: `与 ${selectedPaperTitles.length} 篇论文的对话`,
      library: selectedLibrary.value,
      papers: selectedPapers.value
    },
  ];
  
  activeKey.value = newConversationId;
  setMessages([]); // 清空当前消息
  selectModalVisible.value = false;
};

// 切换对话
const onConversationClick: ConversationsProps['onActiveChange'] = (key) => {
  activeKey.value = key;
  setMessages([]);  // 切换对话时清空消息
};

// 提交问题
const onSubmit = async (question: string) => {
  if (!question) return;
  if (!activeKey.value) {
    Modal.warning({
      title: '请先创建对话',
      content: '在提问前，请先选择文献库并创建新对话'
    });
    return;
  }

  const currentConversation = conversationsItems.value.find(item => item.key === activeKey.value);
  if (!currentConversation) return;

  // 添加用户问题到消息列表
  const userMessageId = `user-${Date.now()}`;
  setMessages([
    ...messages.value,
    { id: userMessageId, message: question, status: 'local' }
  ]);

  askingQuestion.value = true;
  try {
    // 发送问题到后端API
    const response = await api.askQuestion(
      currentConversation.library,
      currentConversation.papers,
      question
    );

    const responses = response.data.responses || [];
    
    // 为每个论文回答添加一条消息
    responses.forEach((res: PaperResponse) => {
      const paperTitle = papers.value.find(p => p.entry_name === res.paper)?.title || res.paper;
      const responseContent = res.success 
        ? generatePaperResponseContent(paperTitle, res.answer) 
        : `获取 ${paperTitle} 的回答失败: ${res.error}`;

      setMessages(prev => [
        ...prev, 
        { 
          id: `paper-${Date.now()}-${Math.random()}`, 
          message: responseContent, 
          status: 'ai',
          role: 'paper',
          paperTitle
        }
      ]);
    });
  } catch (error) {
    console.error('提问失败:', error);
    Modal.error({
      title: '提问失败',
      content: '无法获取论文回答，请稍后再试'
    });
  } finally {
    askingQuestion.value = false;
    content.value = '';
  }
};

// 生成论文回答的内容组件
const md = markdownit({ html: true, breaks: true });

const generatePaperResponseContent = (title: string, answer: string) => {
  const expandedState = ref(false);
  
  return () => (
    <div style={styles.value.paperResponse}>
      <div style={styles.value.paperTitle}>
        <FileTextOutlined /> {title}
      </div>
      <div style={styles.value.paperContent}>
        {expandedState.value 
          ? <Typography><div class="markdown-content" v-html={md.render(answer)} /></Typography>
          : answer.length > 100 
            ? <Typography><div class="markdown-content" v-html={md.render(answer.substring(0, 100) + '...')} /></Typography>
            : <Typography><div class="markdown-content" v-html={md.render(answer)} /></Typography>}
      </div>
      {answer.length > 100 && (
        <Button 
          type="link" 
          onClick={() => expandedState.value = !expandedState.value} 
          style={styles.value.expandBtn}>
          {expandedState.value ? '收起' : '展开'}
        </Button>
      )}
    </div>
  );
};

// 处理文件上传
const handleFileChange: AttachmentsProps['onChange'] = (info) => {
  attachedFiles.value = info.fileList;
};

// ==================== 界面元素 ====================
const placeholderNode = computed(() => (
  <Space direction="vertical" size={16} style={styles.value.placeholder}>
    <Welcome
      variant="borderless"
      icon="https://mdn.alipayobjects.com/huamei_iwk9zp/afts/img/A*s5sNRo5LjfQAAAAAAAAAAAAADgCCAQ/fmt.webp"
      title="AskPapers 智能阅读"
      description="选择文献库和论文，开始智能阅读之旅！"
      extra={
        <Button 
          type="primary" 
          icon={<QuestionCircleOutlined />} 
          onClick={addConversation}>
          开始新对话
        </Button>
      }
    />
  </Space>
));

const items = computed<BubbleListProps['items']>(() => messages.value.map(({ id, message, status, role, paperTitle }) => ({
  key: id,
  loading: status === 'loading',
  role: status === 'local' ? 'user' : 'paper',
  content: typeof message === 'function' ? message() : message,
})));

const attachmentsNode = computed(() => (
  <Badge dot={attachedFiles.value.length > 0 && !headerOpen.value}>
    <Button 
      type="text" 
      icon={<PaperClipOutlined />} 
      onClick={() => headerOpen.value = !headerOpen.value} 
    />
  </Badge>
));

const senderHeader = computed(() => (
  <Sender.Header
    title="附件"
    open={headerOpen.value}
    onOpenChange={(open) => headerOpen.value = open}
    styles={{
      content: {
        padding: 0,
      },
    }}
  >
    <Attachments
      beforeUpload={() => false}
      items={attachedFiles.value}
      onChange={handleFileChange}
      placeholder={(type) =>
        type === 'drop'
          ? { title: '拖放文件至此' }
          : {
            icon: <CloudUploadOutlined />,
            title: '上传文件',
            description: '点击或拖放文件到此区域',
          }
      }
    />
  </Sender.Header>
));

const logoNode = computed(() => (
  <div style={styles.value.logo}>
    <BookOutlined style={styles.value['logo-img']} />
    <span style={styles.value['logo-span']}>AskPapers</span>
  </div>
));

// 定义渲染函数
defineRender(() => {
  return (
    <div style={styles.value.layout}>
      <div style={styles.value.menu}>
        {/* Logo */}
        {logoNode.value}
        
        {/* 文献库选择 */}
        <div style={{ padding: '0 12px 16px 12px' }}>
          <p>当前文献库</p>
          <Select
            v-model:value={selectedLibrary.value}
            style={styles.value.librarySelect}
            placeholder="选择文献库"
            loading={loadingLibraries.value}
            onChange={(value) => loadPapers(value)}
          >
            {libraries.value.map(lib => (
              <Select.Option key={lib.name} value={lib.name}>
                {lib.name} ({lib.count || 0}篇论文)
              </Select.Option>
            ))}
          </Select>
        </div>

        {/* 添加会话按钮 */}
        <Button
          onClick={addConversation}
          type="link"
          style={styles.value.addBtn}
          icon={<PlusOutlined />}
          disabled={!selectedLibrary.value}
        >
          新建对话
        </Button>

        {/* 会话列表 */}
        <Conversations
          items={conversationsItems.value}
          style={styles.value.conversations}
          activeKey={activeKey.value}
          onActiveChange={onConversationClick}
          emptyContent={<Empty description="暂无对话" />}
        />
      </div>

      <div style={styles.value.chat}>
        {/* 消息列表 */}
        <Bubble.List
          items={items.value.length > 0 ? items.value : [{ content: placeholderNode.value, variant: 'borderless' }]}
          roles={roles}
          style={styles.value.messages}
        />

        {/* 输入框 */}
        <Sender
          value={content.value}
          header={senderHeader.value}
          onSubmit={onSubmit}
          onChange={(value) => content.value = value}
          prefix={attachmentsNode.value}
          loading={askingQuestion.value}
          style={styles.value.sender}
          placeholder={!activeKey.value ? "请先选择文献库并创建对话" : "输入问题..."}
          disabled={!activeKey.value || askingQuestion.value}
        />
      </div>

      {/* 选择论文模态框 */}
      <Modal
        title="选择要咨询的论文"
        open={selectModalVisible.value}
        onOk={confirmPaperSelection}
        onCancel={() => selectModalVisible.value = false}
        width={600}
      >
        <Spin spinning={loadingPapers.value}>
          {papers.value.length > 0 ? (
            <div style={styles.value.papersContainer}>
              <Checkbox.Group v-model:value={selectedPapers.value} style={{ width: '100%' }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  {papers.value.map(paper => (
                    <Checkbox key={paper.entry_name} value={paper.entry_name}>
                      {paper.title || paper.entry_name}
                    </Checkbox>
                  ))}
                </Space>
              </Checkbox.Group>
            </div>
          ) : (
            <Empty description="该文献库中暂无论文" />
          )}
        </Spin>
      </Modal>
    </div>
  );
});
</script>