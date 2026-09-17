<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, UploadFilled, Document, MagicStick, Close, Clock, Delete, Download } from '@element-plus/icons-vue'
import { generateLessonPlan, parseTextbookFile } from './api/lesson'
import { exportMarkdown, exportDocx, exportPdf } from './utils/export'

const HISTORY_KEY = 'lessonsynth_history'
const MAX_HISTORY = 50

const form = reactive({
  subject: '数学',
  grade: '四年级',
  unit: '第一单元',
  lesson_title: '从结绳计数说起',
  duration: '1课时',
  textbook_content: '',
})

const loading = ref(false)
const parsing = ref(false)
const result = ref(null)
const uploadedFiles = ref([])
const historyList = ref([])
const showHistory = ref(false)
const activeHistoryId = ref('')

const subjectOptions = ['语文', '数学', '英语', '科学', '道德与法治']
const gradeOptions = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']

const validExts = ['.pdf', '.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif', '.txt', '.md', '.docx']

function loadHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY)
    historyList.value = raw ? JSON.parse(raw) : []
  } catch {
    historyList.value = []
  }
}

function saveHistory() {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(historyList.value.slice(0, MAX_HISTORY)))
  } catch {
    ElMessage.warning('历史记录保存失败，可能是存储空间不足')
  }
}

function addToHistory(data) {
  const record = {
    id: Date.now().toString(),
    lesson_title: data.lesson_title,
    subject: form.subject,
    grade: form.grade,
    duration: form.duration,
    created_at: new Date().toISOString(),
    content: data,
  }
  historyList.value.unshift(record)
  activeHistoryId.value = record.id
  saveHistory()
}

function viewHistory(record) {
  result.value = record.content
  activeHistoryId.value = record.id
  showHistory.value = false
}

function deleteHistory(id) {
  ElMessageBox.confirm('确定要删除这条历史记录吗？', '提示', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  }).then(() => {
    historyList.value = historyList.value.filter(r => r.id !== id)
    saveHistory()
    if (activeHistoryId.value === id) {
      activeHistoryId.value = ''
      result.value = null
    }
    ElMessage.success('已删除')
  }).catch(() => {})
}

function clearAllHistory() {
  ElMessageBox.confirm('确定要清空所有历史记录吗？此操作不可恢复。', '提示', {
    type: 'warning',
    confirmButtonText: '清空',
    cancelButtonText: '取消',
  }).then(() => {
    historyList.value = []
    activeHistoryId.value = ''
    result.value = null
    saveHistory()
    ElMessage.success('已清空历史记录')
  }).catch(() => {})
}

function formatDate(iso) {
  const d = new Date(iso)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function newDesign() {
  result.value = null
  activeHistoryId.value = ''
  form.textbook_content = ''
  uploadedFiles.value = []
}

function handleExport(format) {
  if (!result.value) return
  try {
    if (format === 'md') {
      exportMarkdown(result.value)
      ElMessage.success('已导出 Markdown 文件')
    } else if (format === 'docx') {
      exportDocx(result.value)
      ElMessage.success('已导出 Word 文件')
    } else if (format === 'pdf') {
      ElMessage.info('正在生成 PDF，请稍候...')
      exportPdf(result.value)
    }
  } catch (e) {
    ElMessage.error(`导出失败：${e.message}`)
  }
}

onMounted(() => {
  loadHistory()
})

async function handleFileUpload(file) {
  const name = file.name.toLowerCase()
  const isValid = validExts.some(ext => name.endsWith(ext))
  if (!isValid) {
    ElMessage.error(`文件「${file.name}」格式不支持，仅支持 PDF、图片、TXT、MD、DOCX`)
    return false
  }

  const fileItem = { name: file.name, status: 'parsing' }
  uploadedFiles.value.push(fileItem)

  parsing.value = true
  try {
    const { data } = await parseTextbookFile(file)
    const existing = form.textbook_content.trim()
    form.textbook_content = existing
      ? `${existing}\n\n--- ${file.name} ---\n${data.content}`
      : data.content
    fileItem.status = 'done'
    fileItem.length = data.content.length
    ElMessage.success(`文件「${file.name}」解析成功，共 ${data.content.length} 字`)
  } catch (e) {
    const msg = e.response?.data?.detail || e.message || '文件解析失败'
    fileItem.status = 'error'
    ElMessage.error(`文件「${file.name}」解析失败：${msg}`)
  } finally {
    parsing.value = uploadedFiles.value.some(f => f.status === 'parsing')
  }
  return false
}

function removeUploadedFile(index) {
  uploadedFiles.value.splice(index, 1)
  if (uploadedFiles.value.length === 0) {
    form.textbook_content = ''
  }
}

async function handleGenerate() {
  if (!form.textbook_content.trim()) {
    ElMessage.warning('请输入课本内容或上传课本文件')
    return
  }
  loading.value = true
  result.value = null
  try {
    const { data } = await generateLessonPlan({
      subject: form.subject,
      grade: form.grade,
      unit: form.unit,
      lesson_title: form.lesson_title,
      duration: form.duration,
      textbook_content: form.textbook_content,
    })
    result.value = data
    addToHistory(data)
    ElMessage.success('教案生成成功！')
  } catch (e) {
    const msg = e.response?.data?.detail || e.message || '生成失败'
    ElMessage.error(`生成失败：${msg}`)
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.textbook_content = ''
  uploadedFiles.value = []
  result.value = null
}
</script>

<template>
  <div class="app">
    <header class="navbar">
      <div class="navbar-inner">
        <div class="brand">
          <div class="brand-logo">
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none">
              <path d="M12 2L2 7l10 5 10-5-10-5z" :fill="'#fff'"/>
              <path d="M2 17l10 5 10-5M2 12l10 5 10-5" :stroke="'#fff'" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <span class="brand-name">LessonSynth</span>
          <span class="brand-tag">教学活动设计 Agent</span>
        </div>
        <div class="navbar-right">
          <el-button class="nav-btn" @click="newDesign">
            <el-icon><MagicStick /></el-icon>
            <span>新建设计</span>
          </el-button>
          <el-button class="nav-btn history-btn" @click="showHistory = true">
            <el-icon><Clock /></el-icon>
            <span>历史记录</span>
            <el-badge v-if="historyList.length" :value="historyList.length" :max="99" class="history-badge" />
          </el-button>
          <span class="powered">Powered by LangGraph × DeepSeek</span>
        </div>
      </div>
    </header>

    <el-drawer
      v-model="showHistory"
      title="历史记录"
      direction="rtl"
      size="400px"
      :with-header="false"
    >
      <div class="history-drawer">
        <div class="history-header">
          <div class="history-title">
            <el-icon><Clock /></el-icon>
            <span>历史记录</span>
            <el-tag v-if="historyList.length" type="info" size="small" effect="plain">{{ historyList.length }} 条</el-tag>
          </div>
          <el-icon class="history-close" @click="showHistory = false"><Close /></el-icon>
        </div>

        <div v-if="historyList.length === 0" class="history-empty">
          <el-icon :size="40" class="empty-icon"><Document /></el-icon>
          <p>暂无历史记录</p>
          <small>生成的教案会自动保存在这里</small>
        </div>

        <div v-else class="history-list">
          <div
            v-for="record in historyList"
            :key="record.id"
            class="history-item"
            :class="{ active: record.id === activeHistoryId }"
            role="button"
            tabindex="0"
            @click="viewHistory(record)"
            @keydown.enter="viewHistory(record)"
          >
            <div class="history-item-main">
              <div class="history-item-title">{{ record.lesson_title }}</div>
              <div class="history-item-meta">
                <el-tag effect="plain" round size="small">{{ record.subject }}</el-tag>
                <el-tag effect="plain" round size="small">{{ record.grade }}</el-tag>
                <span class="history-date">{{ formatDate(record.created_at) }}</span>
              </div>
            </div>
            <el-icon class="history-delete" @click.stop="deleteHistory(record.id)"><Delete /></el-icon>
          </div>
        </div>

        <div v-if="historyList.length" class="history-footer">
          <el-button type="danger" plain size="small" @click="clearAllHistory">清空全部</el-button>
        </div>
      </div>
    </el-drawer>

    <div class="workspace">
      <aside class="input-panel">
        <div class="panel-header">
          <el-icon><Document /></el-icon>
          <span>课本信息</span>
        </div>

        <div class="form-row">
          <div class="form-item">
            <label>学科</label>
            <el-select v-model="form.subject" size="large">
              <el-option v-for="s in subjectOptions" :key="s" :label="s" :value="s" />
            </el-select>
          </div>
          <div class="form-item">
            <label>年级</label>
            <el-select v-model="form.grade" size="large">
              <el-option v-for="g in gradeOptions" :key="g" :label="g" :value="g" />
            </el-select>
          </div>
        </div>

        <div class="form-row">
          <div class="form-item">
            <label>单元</label>
            <el-input v-model="form.unit" size="large" placeholder="如：第一单元" />
          </div>
          <div class="form-item">
            <label>课时长度</label>
            <el-input v-model="form.duration" size="large" />
          </div>
        </div>

        <div class="form-item">
          <label>课时标题</label>
          <el-input v-model="form.lesson_title" size="large" placeholder="如：从结绳计数说起" />
        </div>

        <div class="form-item">
          <label>课本文件</label>
          <el-upload
            :auto-upload="false"
            :show-file-list="false"
            :on-change="(uploadFile) => handleFileUpload(uploadFile.raw)"
            accept=".pdf,.png,.jpg,.jpeg,.webp,.bmp,.gif,.txt,.md,.docx"
            multiple
            drag
            class="upload-area"
          >
            <div class="upload-inner">
              <el-icon :size="24" class="upload-icon"><UploadFilled /></el-icon>
              <div class="upload-text">
                <span>拖拽文件到此处，或 <b>点击上传</b>（支持多文件）</span>
                <small>支持 PDF、图片（png/jpg 等）、TXT、MD、DOCX</small>
              </div>
            </div>
          </el-upload>
          <div v-if="uploadedFiles.length" class="uploaded-list">
            <div
              v-for="(f, idx) in uploadedFiles"
              :key="idx"
              class="uploaded-file"
            >
              <el-icon><Document /></el-icon>
              <span class="fname">{{ f.name }}</span>
              <el-tag v-if="f.status === 'parsing'" type="info" size="small" effect="plain">解析中...</el-tag>
              <el-tag v-else-if="f.status === 'done'" type="success" size="small" effect="plain">{{ f.length }} 字</el-tag>
              <el-tag v-else type="danger" size="small" effect="plain">失败</el-tag>
              <el-icon class="remove-btn" @click="removeUploadedFile(idx)"><Close /></el-icon>
            </div>
          </div>
        </div>

        <div class="form-item">
          <label>课本内容</label>
          <el-input
            v-model="form.textbook_content"
            type="textarea"
            :rows="8"
            resize="none"
            placeholder="可直接粘贴课本原文，或上传文件自动解析..."
          />
        </div>

        <div class="action-row">
          <el-button
            type="primary"
            size="large"
            class="generate-btn"
            :loading="loading"
            @click="handleGenerate"
          >
            <el-icon class="btn-icon"><MagicStick /></el-icon>
            <span>{{ loading ? '生成中...' : '生成教案' }}</span>
          </el-button>
          <el-button size="large" class="reset-btn" @click="resetForm">重置</el-button>
        </div>
      </aside>

      <main class="output-panel">
        <div v-if="loading" class="state-box">
          <div class="spinner-wrap">
            <el-icon class="is-loading spinner" :size="40"><Loading /></el-icon>
          </div>
          <p class="state-title">正在生成教案</p>
          <p class="state-desc">多智能体协作中，约需 3-7 分钟，请耐心等待...</p>
          <div class="progress-steps">
            <div class="step"><span class="dot done"></span>课本解析</div>
            <div class="step"><span class="dot done"></span>目标生成</div>
            <div class="step"><span class="dot done"></span>重难点分析</div>
            <div class="step"><span class="dot active"></span>教学过程设计</div>
            <div class="step"><span class="dot"></span>教案审核</div>
          </div>
        </div>

        <div v-else-if="result" class="lesson-content">
          <div class="lesson-hero">
            <div class="lesson-hero-left">
              <h1>{{ result.lesson_title }}</h1>
              <div class="lesson-meta">
                <el-tag effect="plain" round>{{ form.subject }}</el-tag>
                <el-tag effect="plain" round>{{ form.grade }}</el-tag>
                <el-tag effect="plain" round>{{ form.duration }}</el-tag>
              </div>
            </div>
            <div class="export-bar">
              <el-dropdown @command="handleExport" trigger="click">
                <el-button type="primary" class="export-btn">
                  <el-icon><Document /></el-icon>
                  <span>导出教案</span>
                  <el-icon class="arrow"><Download /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="pdf">导出为 PDF</el-dropdown-item>
                    <el-dropdown-item command="docx">导出为 Word (DOCX)</el-dropdown-item>
                    <el-dropdown-item command="md">导出为 Markdown</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>

          <section class="block">
            <div class="block-title"><span class="bar"></span>教学目标</div>
            <div class="obj-grid">
              <div class="obj-card">
                <div class="obj-label obj-knowledge">知识与技能</div>
                <p>{{ result.teaching_objectives.knowledge }}</p>
              </div>
              <div class="obj-card">
                <div class="obj-label obj-process">过程与方法</div>
                <p>{{ result.teaching_objectives.process }}</p>
              </div>
              <div class="obj-card">
                <div class="obj-label obj-emotion">情感态度</div>
                <p>{{ result.teaching_objectives.emotion }}</p>
              </div>
            </div>
          </section>

          <section class="block">
            <div class="block-title"><span class="bar"></span>重点难点</div>
            <div class="kd-row">
              <div class="kd-card kd-key">
                <div class="kd-tag">重点</div>
                <p>{{ result.key_difficult_points.key_point }}</p>
              </div>
              <div class="kd-card kd-diff">
                <div class="kd-tag">难点</div>
                <p>{{ result.key_difficult_points.difficult_point }}</p>
              </div>
            </div>
          </section>

          <section class="block">
            <div class="block-title"><span class="bar"></span>教学过程</div>
            <div
              v-for="(stage, idx) in result.teaching_design.teaching_process"
              :key="idx"
              class="stage-card"
            >
              <div class="stage-head">
                <div class="stage-num">{{ idx + 1 }}</div>
                <h3>{{ stage.stage_name }}</h3>
              </div>

              <div class="intent-box">
                <span class="intent-label">设计意图</span>
                <p>{{ stage.design_intent }}</p>
              </div>

              <div class="stage-block">
                <div class="stage-sub">教学步骤</div>
                <ol class="steps">
                  <li v-for="(s, i) in stage.steps" :key="i">{{ s }}</li>
                </ol>
              </div>

              <div v-if="stage.student_presets?.length" class="stage-block">
                <div class="stage-sub">学情预设</div>
                <ul class="presets">
                  <li v-for="(p, i) in stage.student_presets" :key="i">{{ p }}</li>
                </ul>
              </div>

              <div v-if="stage.teacher_summary" class="stage-block">
                <div class="stage-sub">教师小结</div>
                <p class="summary">{{ stage.teacher_summary }}</p>
              </div>
            </div>
          </section>

          <section class="block">
            <div class="block-title"><span class="bar"></span>板书设计</div>
            <div class="blackboard">
              <pre>{{ result.teaching_design.blackboard_design }}</pre>
            </div>
          </section>

          <section class="block">
            <div class="block-title"><span class="bar"></span>作业设计</div>
            <ul class="homework">
              <li v-for="(h, i) in result.teaching_design.homework" :key="i">
                <span class="hw-idx">{{ i + 1 }}</span>{{ h }}
              </li>
            </ul>
          </section>

          <section v-if="result.teaching_design.teaching_reflection" class="block">
            <div class="block-title"><span class="bar"></span>教学研讨</div>
            <p class="reflection">{{ result.teaching_design.teaching_reflection }}</p>
          </section>
        </div>

        <div v-else class="state-box empty">
          <div class="empty-illust">
            <svg viewBox="0 0 120 120" width="100" height="100" fill="none">
              <rect x="14" y="20" width="92" height="80" rx="10" fill="#eef2ff"/>
              <rect x="22" y="34" width="60" height="6" rx="3" fill="#c7d2fe"/>
              <rect x="22" y="48" width="76" height="4" rx="2" fill="#e0e7ff"/>
              <rect x="22" y="58" width="70" height="4" rx="2" fill="#e0e7ff"/>
              <rect x="22" y="68" width="50" height="4" rx="2" fill="#e0e7ff"/>
              <circle cx="88" cy="78" r="16" fill="#4d6bfe"/>
              <path d="M82 78l4 4 8-9" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
            </svg>
          </div>
          <p class="state-title">开始设计你的教案</p>
          <p class="state-desc">在左侧填写课本信息并粘贴或上传课本内容，点击「生成教案」即可</p>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  background: var(--bg-page);
}

/* ===== 顶部导航 ===== */
.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: #fff;
  border-bottom: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
}
.navbar-inner {
  max-width: 1400px;
  margin: 0 auto;
  height: 60px;
  padding: 0 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.brand-logo {
  width: 34px;
  height: 34px;
  background: linear-gradient(135deg, #4d6bfe 0%, #6d5bff 100%);
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 10px rgba(77, 107, 254, 0.3);
}
.brand-name {
  font-size: 17px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.3px;
}
.brand-tag {
  font-size: 12px;
  color: var(--text-muted);
  padding: 3px 10px;
  background: var(--primary-light);
  border-radius: 20px;
  margin-left: 4px;
}
.powered {
  font-size: 12px;
  color: var(--text-muted);
}
.navbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.nav-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 34px;
  padding: 0 14px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: #fff;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.nav-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: var(--primary-light);
}
.nav-btn .el-icon {
  font-size: 15px;
}
.history-btn {
  position: relative;
}
.history-badge {
  margin-left: 2px;
}

/* ===== 历史记录抽屉 ===== */
.history-drawer {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-light);
}
.history-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}
.history-title .el-icon {
  color: var(--primary);
}
.history-close {
  font-size: 18px;
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.2s;
}
.history-close:hover {
  color: var(--text-primary);
}
.history-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  gap: 8px;
}
.history-empty .empty-icon {
  color: var(--border);
}
.history-empty p {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}
.history-empty small {
  font-size: 12px;
}
.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}
.history-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
}
.history-item:hover {
  border-color: #c7d2fe;
  box-shadow: var(--shadow-md);
}
.history-item.active {
  border-color: var(--primary);
  background: var(--primary-light);
}
.history-item-main {
  flex: 1;
  min-width: 0;
}
.history-item-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.history-item-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.history-date {
  font-size: 11px;
  color: var(--text-muted);
  margin-left: 4px;
}
.history-delete {
  color: var(--text-muted);
  cursor: pointer;
  flex-shrink: 0;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
}
.history-delete:hover {
  color: #ef4444;
  background: #fef2f2;
}
.history-footer {
  padding: 16px 24px;
  border-top: 1px solid var(--border-light);
}

/* ===== 工作区 ===== */
.workspace {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px 32px;
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 24px;
  align-items: start;
}

/* ===== 输入面板 ===== */
.input-panel {
  position: sticky;
  top: 84px;
  background: #fff;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-sm);
}
.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-light);
}
.panel-header .el-icon {
  color: var(--primary);
  font-size: 18px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.form-item {
  margin-bottom: 16px;
}
.form-item label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 6px;
}
.form-item :deep(.el-input__wrapper),
.form-item :deep(.el-select__wrapper) {
  border-radius: var(--radius-sm);
  box-shadow: 0 0 0 1px var(--border) inset;
}
.form-item :deep(.el-input__wrapper:hover),
.form-item :deep(.el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--primary) inset;
}
.form-item :deep(.el-textarea__inner) {
  border-radius: var(--radius-sm);
  border-color: var(--border);
}

/* ===== 上传区 ===== */
.upload-area {
  width: 100%;
}
.upload-area :deep(.el-upload-dragger) {
  border: 1.5px dashed #c7d2fe;
  border-radius: var(--radius-md);
  background: #fafbff;
  padding: 16px;
  transition: all 0.2s;
}
.upload-area :deep(.el-upload-dragger:hover) {
  border-color: var(--primary);
  background: var(--primary-light);
}
.upload-inner {
  display: flex;
  align-items: center;
  gap: 12px;
}
.upload-icon {
  color: var(--primary);
  flex-shrink: 0;
}
.upload-text {
  text-align: left;
}
.upload-text span {
  font-size: 13px;
  color: var(--text-primary);
}
.upload-text span b {
  color: var(--primary);
}
.upload-text small {
  display: block;
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}
.uploaded-list {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.uploaded-file {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
  padding: 6px 10px;
  background: #fafbff;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
}
.uploaded-file .el-icon {
  color: var(--primary);
  flex-shrink: 0;
}
.uploaded-file .remove-btn {
  color: var(--text-muted);
  cursor: pointer;
  margin-left: auto;
  flex-shrink: 0;
  transition: color 0.2s;
}
.uploaded-file .remove-btn:hover {
  color: #ef4444;
}
.fname {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 160px;
}

/* ===== 按钮 ===== */
.action-row {
  display: flex;
  gap: 10px;
  margin-top: 8px;
}
.generate-btn {
  flex: 1;
  background: linear-gradient(135deg, #4d6bfe 0%, #6d5bff 100%);
  border: none;
  border-radius: var(--radius-sm);
  font-weight: 600;
  height: 44px;
  box-shadow: 0 4px 12px rgba(77, 107, 254, 0.3);
  transition: all 0.2s;
}
.generate-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(77, 107, 254, 0.4);
}
.generate-btn .btn-icon {
  margin-right: 4px;
}
.reset-btn {
  border-radius: var(--radius-sm);
  height: 44px;
  padding: 0 20px;
}

/* ===== 输出面板 ===== */
.output-panel {
  min-height: calc(100vh - 140px);
}

/* ===== 空状态 / 加载状态 ===== */
.state-box {
  background: #fff;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  min-height: calc(100vh - 140px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 40px;
  box-shadow: var(--shadow-sm);
}
.spinner {
  color: var(--primary);
}
.state-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 20px 0 8px;
}
.state-desc {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0;
}
.progress-steps {
  display: flex;
  gap: 20px;
  margin-top: 32px;
  flex-wrap: wrap;
  justify-content: center;
}
.step {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-muted);
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #e5e7eb;
}
.dot.done {
  background: #10b981;
}
.dot.active {
  background: var(--primary);
  box-shadow: 0 0 0 4px rgba(77, 107, 254, 0.2);
  animation: pulse 1.4s infinite;
}
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 4px rgba(77, 107, 254, 0.2); }
  50% { box-shadow: 0 0 0 8px rgba(77, 107, 254, 0.05); }
}
.empty-illust {
  margin-bottom: 8px;
}

/* ===== 教案内容 ===== */
.lesson-content {
  background: #fff;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: 36px 40px;
  box-shadow: var(--shadow-sm);
}

.lesson-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 24px;
  margin-bottom: 28px;
  border-bottom: 2px solid var(--primary-light);
}
.lesson-hero-left {
  flex: 1;
  min-width: 0;
}
.lesson-hero h1 {
  margin: 0 0 12px;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}
.lesson-meta {
  display: flex;
  gap: 8px;
}
.lesson-meta :deep(.el-tag) {
  border-radius: 20px;
}
.export-bar {
  flex-shrink: 0;
}
.export-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 38px;
  padding: 0 18px;
  border-radius: 10px;
  background: linear-gradient(135deg, #4d6bfe, #6d5bff);
  border: none;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(77, 107, 254, 0.3);
  transition: all 0.2s;
}
.export-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(77, 107, 254, 0.4);
}
.export-btn .arrow {
  font-size: 12px;
}

.block {
  margin-bottom: 32px;
}
.block-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
}
.bar {
  width: 4px;
  height: 18px;
  background: linear-gradient(180deg, #4d6bfe, #6d5bff);
  border-radius: 2px;
}

/* 教学目标 */
.obj-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}
.obj-card {
  background: #fafbff;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 16px;
  transition: all 0.2s;
}
.obj-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}
.obj-label {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 20px;
  margin-bottom: 10px;
}
.obj-knowledge {
  background: #eef2ff;
  color: #4d6bfe;
}
.obj-process {
  background: #ecfdf5;
  color: #059669;
}
.obj-emotion {
  background: #fef3c7;
  color: #d97706;
}
.obj-card p {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-secondary);
}

/* 重点难点 */
.kd-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.kd-card {
  border-radius: var(--radius-md);
  padding: 16px 18px;
  border: 1px solid var(--border-light);
}
.kd-key {
  background: linear-gradient(135deg, #fff5f5 0%, #fff 100%);
  border-color: #fecaca;
}
.kd-diff {
  background: linear-gradient(135deg, #fffbeb 0%, #fff 100%);
  border-color: #fde68a;
}
.kd-tag {
  display: inline-block;
  font-size: 12px;
  font-weight: 700;
  color: #dc2626;
  margin-bottom: 8px;
}
.kd-diff .kd-tag {
  color: #d97706;
}
.kd-card p {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-primary);
}

/* 教学过程环节卡片 */
.stage-card {
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 20px;
  margin-bottom: 16px;
  background: #fff;
  transition: all 0.2s;
}
.stage-card:hover {
  box-shadow: var(--shadow-md);
  border-color: #c7d2fe;
}
.stage-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}
.stage-num {
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #4d6bfe, #6d5bff);
  color: #fff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}
.stage-head h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.intent-box {
  background: var(--primary-light);
  border-left: 3px solid var(--primary);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  padding: 10px 14px;
  margin-bottom: 14px;
}
.intent-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--primary);
  margin-right: 6px;
}
.intent-box p {
  display: inline;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.7;
}

.stage-block {
  margin-bottom: 12px;
}
.stage-sub {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}
.steps {
  margin: 0;
  padding-left: 22px;
}
.steps li {
  font-size: 13.5px;
  line-height: 1.8;
  color: var(--text-secondary);
  margin-bottom: 4px;
}
.presets {
  margin: 0;
  padding: 0;
  list-style: none;
}
.presets li {
  font-size: 13px;
  line-height: 1.8;
  color: #6b7280;
  padding-left: 16px;
  position: relative;
}
.presets li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 10px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #c7d2fe;
}
.summary {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  color: #4b5563;
  background: #f9fafb;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
}

/* 板书 */
.blackboard {
  background: #1e293b;
  border-radius: var(--radius-md);
  padding: 20px 24px;
}
.blackboard pre {
  margin: 0;
  color: #e2e8f0;
  font-family: 'Courier New', monospace;
  font-size: 13.5px;
  line-height: 1.8;
  white-space: pre-wrap;
}

/* 作业 */
.homework {
  margin: 0;
  padding: 0;
  list-style: none;
}
.homework li {
  display: flex;
  gap: 10px;
  font-size: 13.5px;
  line-height: 1.7;
  color: var(--text-secondary);
  padding: 10px 14px;
  background: #fafbff;
  border-radius: var(--radius-sm);
  margin-bottom: 8px;
  border: 1px solid var(--border-light);
}
.hw-idx {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  background: var(--primary-light);
  color: var(--primary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}

/* 教学研讨 */
.reflection {
  margin: 0;
  font-size: 13.5px;
  line-height: 1.8;
  color: var(--text-secondary);
  background: linear-gradient(135deg, #fafbff 0%, #fff 100%);
  padding: 16px 18px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);
}
</style>
