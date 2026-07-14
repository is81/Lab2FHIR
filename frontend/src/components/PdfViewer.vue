<template>
  <div class="pdf-viewer">
    <!-- 工具栏 -->
    <div class="pdf-toolbar" v-if="!loading && !error">
      <el-button-group size="small">
        <el-button :disabled="currentPage <= 1" @click="prevPage" :icon="ArrowLeft" />
        <el-button disabled style="min-width:80px">{{ currentPage }} / {{ totalPages }}</el-button>
        <el-button :disabled="currentPage >= totalPages" @click="nextPage" :icon="ArrowRight" />
      </el-button-group>
      <el-button-group size="small" style="margin-left:8px">
        <el-button @click="zoomOut" :icon="ZoomOut" />
        <el-button disabled style="min-width:50px">{{ scaleDisplay }}</el-button>
        <el-button @click="zoomIn" :icon="ZoomIn" />
      </el-button-group>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="pdf-loading">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
      <span>加载PDF中...</span>
    </div>

    <!-- 错误 -->
    <div v-else-if="error" class="pdf-error">
      <el-icon :size="48"><WarningFilled /></el-icon>
      <p>{{ error }}</p>
    </div>

    <!-- Canvas (始终在DOM中，用v-show控制可见性) -->
    <div v-show="!loading && !error" class="pdf-canvas-wrap" ref="canvasWrap">
      <canvas ref="pdfCanvas"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onBeforeUnmount, nextTick } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'

// 使用本地打包的 worker（Vite 会自动拷贝到 assets/）
import pdfWorkerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorkerUrl

const props = defineProps({
  url: { type: String, required: true }
})

const pdfCanvas = ref(null)
const loading = ref(true)
const error = ref(null)
const currentPage = ref(1)
const totalPages = ref(0)
const scale = ref(1.25)

// 用单独的 ref 显示缩放比例，避免 scale 变化触发模板重渲染影响 canvas
const scaleDisplay = ref('125%')

let pdfDoc = null
let renderTask = null

async function loadPdf() {
  loading.value = true
  error.value = null

  try {
    // 3.8 修复：30秒超时
    pdfDoc = await Promise.race([
      pdfjsLib.getDocument(props.url).promise,
      new Promise((_, reject) => setTimeout(() => reject(new Error('加载超时')), 30000))
    ])
    totalPages.value = pdfDoc.numPages
    currentPage.value = 1
    loading.value = false
    await nextTick()
    await renderPage(1)
  } catch (e) {
    console.error('PDF load error:', e)
    error.value = '无法加载PDF: ' + (e.message || '未知错误')
    loading.value = false
  }
}

async function renderPage(pageNum) {
  if (!pdfDoc || !pdfCanvas.value) return

  if (renderTask) {
    try { renderTask.cancel() } catch (_) {}
    renderTask = null
  }

  try {
    const page = await pdfDoc.getPage(pageNum)
    const viewport = page.getViewport({ scale: scale.value })

    const canvas = pdfCanvas.value
    const ctx = canvas.getContext('2d')
    canvas.height = viewport.height
    canvas.width = viewport.width
    canvas.style.height = viewport.height + 'px'
    canvas.style.width = viewport.width + 'px'

    renderTask = page.render({ canvasContext: ctx, viewport })
    await renderTask.promise
    renderTask = null
    scaleDisplay.value = Math.round(scale.value * 100) + '%'
  } catch (e) {
    if (e?.name !== 'RenderingCancelledException') {
      console.error('PDF render error:', e)
    }
    renderTask = null
  }
}

function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--
    renderPage(currentPage.value)
  }
}

function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    renderPage(currentPage.value)
  }
}

function zoomIn() {
  scale.value = Math.min(scale.value + 0.25, 4)
  renderPage(currentPage.value)
}

function zoomOut() {
  scale.value = Math.max(scale.value - 0.25, 0.5)
  renderPage(currentPage.value)
}

watch(() => props.url, () => {
  if (props.url) loadPdf()
}, { immediate: true })

onBeforeUnmount(() => {
  if (renderTask) {
    try { renderTask.cancel() } catch (_) {}
    renderTask = null
  }
  pdfDoc = null
})
</script>

<style scoped>
.pdf-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #525659;
}

.pdf-toolbar {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: #3a3d40;
  flex-shrink: 0;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.pdf-loading,
.pdf-error {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: rgba(255,255,255,0.7);
  font-size: 14px;
}

.pdf-error {
  color: #f56c6c;
}

.pdf-canvas-wrap {
  flex: 1;
  overflow: auto;
  display: flex;
  justify-content: center;
  padding: 16px;
}

.pdf-canvas-wrap canvas {
  box-shadow: 0 2px 16px rgba(0,0,0,0.5);
}
</style>
