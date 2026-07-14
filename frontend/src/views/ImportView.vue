<template>
  <div>
    <div class="page-card" style="max-width:900px;margin:0 auto">
      <div class="page-title">导入化验单 PDF</div>
      <p style="color:#909399;margin-bottom:24px">
        支持 DNA倍体、TCT、HPV、胃镜病理、病理诊断报告。可单个或批量上传，单次最多 500 份。
      </p>

      <!-- 上传区域 -->
      <el-upload
        ref="uploadRef"
        class="upload-area"
        drag
        multiple
        :auto-upload="false"
        :limit="500"
        accept=".pdf"
        v-model:file-list="fileList"
        :disabled="importing"
      >
        <el-icon class="el-icon--upload" :size="48" color="#c0c4cc"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          将PDF文件拖拽到此处，或 <em>点击选择文件</em>
        </div>
      </el-upload>

      <!-- 文件列表 + 操作 -->
      <div v-if="fileList.length > 0" style="margin-top:24px">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
          <span style="font-weight:600">已选择 {{ fileList.length }} 个文件</span>
          <div style="display:flex;gap:8px">
            <el-button @click="clearAll" :disabled="importing">清空</el-button>
            <el-button type="primary" @click="startImport" :loading="importing" :icon="Upload">
              {{ importing ? `正在导入 ${completedCount}/${fileList.length}...` : '开始导入' }}
            </el-button>
          </div>
        </div>

        <!-- 进度条 -->
        <el-progress
          v-if="importing"
          :percentage="Math.round(completedCount / fileList.length * 100)"
          :stroke-width="8"
          style="margin-bottom:12px"
        />

        <el-table :data="fileList" size="small" max-height="360">
          <el-table-column prop="name" label="文件名" show-overflow-tooltip />
          <el-table-column label="大小" width="90">
            <template #default="{row}">{{ formatSize(row.size) }}</template>
          </el-table-column>
          <el-table-column label="状态" width="140">
            <template #default="{row}">
              <el-tag v-if="row.status === 'success'" type="success" size="small">解析成功</el-tag>
              <el-tag v-else-if="row.status === 'skipped'" type="info" size="small">已存在</el-tag>
              <el-tag v-else-if="row.status === 'error'" type="danger" size="small">解析失败</el-tag>
              <el-tag v-else-if="row.status === 'parsing'" type="warning" size="small">
                <el-icon class="is-loading"><Loading /></el-icon> 解析中...
              </el-tag>
              <span v-else style="color:#c0c4cc">等待导入</span>
            </template>
          </el-table-column>
          <el-table-column label="识别类型" width="110">
            <template #default="{row}">
              <el-tag v-if="row.reportType" size="small" :type="tagType(row.reportType)">{{ row.reportType }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="患者" width="90">
            <template #default="{row}">
              <span v-if="row.patientName" style="font-size:13px">{{ row.patientName }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- ====== 导入报告 ====== -->
      <div v-if="importReport" style="margin-top:24px">
        <el-divider />

        <h3 style="font-size:16px;font-weight:600;margin-bottom:16px">
          <el-icon><DataAnalysis /></el-icon> 导入情况报告
        </h3>

        <!-- 总体概况 -->
        <el-row :gutter="16" style="margin-bottom:16px">
          <el-col :span="6">
            <div class="report-stat">
              <div class="number" style="color:#303133">{{ importReport.total }}</div>
              <div class="label">总文件数</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="report-stat">
              <div class="number" style="color:#67c23a">{{ importReport.success }}</div>
              <div class="label">解析成功</div>
            </div>
          </el-col>
          <el-col :span="4">
            <div class="report-stat">
              <div class="number" style="color:#f56c6c">{{ importReport.fail }}</div>
              <div class="label">解析失败</div>
            </div>
          </el-col>
          <el-col :span="4">
            <div class="report-stat">
              <div class="number" style="color:#909399">{{ importReport.skipped || 0 }}</div>
              <div class="label">已存在</div>
            </div>
          </el-col>
          <el-col :span="4">
            <div class="report-stat">
              <div class="number" style="color:#409eff">{{ importReport.duration }}</div>
              <div class="label">耗时(秒)</div>
            </div>
          </el-col>
        </el-row>

        <!-- 类型分布 -->
        <div v-if="Object.keys(importReport.typeStats).length > 0" style="margin-bottom:16px">
          <h4 style="font-size:14px;color:#606266;margin-bottom:8px">报告类型分布</h4>
          <div style="display:flex;gap:12px;flex-wrap:wrap">
            <el-tag
              v-for="(count, type) in importReport.typeStats"
              :key="type"
              :type="tagType(type)"
              size="large"
            >
              {{ type }}：{{ count }} 份
            </el-tag>
          </div>
        </div>

        <!-- 新入库记录数 -->
        <el-alert
          :title="`数据库当前共 ${importReport.dbTotal} 条记录（本次新增 ${importReport.dbNew} 条）`"
          type="info"
          :closable="false"
          show-icon
          style="margin-bottom:12px"
        />

        <!-- 失败列表 -->
        <div v-if="importReport.failList.length > 0" style="margin-bottom:16px">
          <h4 style="font-size:14px;color:#f56c6c;margin-bottom:8px">失败文件明细</h4>
          <el-table :data="importReport.failList" size="small" max-height="200" border>
            <el-table-column prop="name" label="文件名" show-overflow-tooltip />
            <el-table-column prop="reason" label="原因" width="200" show-overflow-tooltip />
          </el-table>
        </div>

        <div style="display:flex;gap:8px">
          <el-button type="primary" @click="$router.push('/reports')">
            <el-icon><Document /></el-icon> 查看全部报告
          </el-button>
          <el-button @click="$router.push('/')">
            <el-icon><DataBoard /></el-icon> 返回首页
          </el-button>
          <el-button @click="resetImport">
            <el-icon><RefreshRight /></el-icon> 继续导入
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { uploadPdfBatch } from '../api/index.js'
import { getReportTypeColor, formatFileSize } from '../utils/report.js'
import axios from 'axios'

const fileList = ref([])
const importing = ref(false)
const completedCount = ref(0)
const importReport = ref(null)

const formatSize = formatFileSize
const tagType = getReportTypeColor

function removeFile(index) {
  fileList.value.splice(index, 1)
}

function clearAll() {
  fileList.value = []
  importReport.value = null
}

function resetImport() {
  fileList.value = []
  importReport.value = null
}

async function startImport() {
  if (fileList.value.length === 0) {
    ElMessage.warning('请先选择PDF文件')
    return
  }

  importing.value = true
  completedCount.value = 0
  importReport.value = null

  const startTime = Date.now()
  let success = 0
  let fail = 0
  let skipped = 0
  const typeStats = {}
  const failList = []
  const dbTotalBefore = await fetchDbTotal()

  // 标记全部为等待中
  fileList.value.forEach(fw => { fw.status = 'waiting' })

  // 3.11 修复：使用并发批处理（API 层控制 3 并发）
  const rawFiles = fileList.value
    .map(fw => fw.raw)
    .filter(Boolean)

  const batchResult = await uploadPdfBatch(rawFiles, ({ completed, total, file, result }) => {
    completedCount.value = completed
    // 找到对应的 fileWrapper 并更新状态
    const fw = fileList.value.find(f => f.name === file)
    if (!fw) return

    if (result.success) {
      fw.status = 'success'
      fw.reportType = result.report_type
      fw.patientName = result.patient_name
    } else if (result.skipped) {
      fw.status = 'skipped'
      fw.reportType = result.report_type
    } else {
      fw.status = 'error'
    }
  })

  // 汇总结果
  for (const r of batchResult.results) {
    if (r.success) {
      success++
      if (r.report_type) {
        typeStats[r.report_type] = (typeStats[r.report_type] || 0) + 1
      }
    } else if (r.skipped) {
      skipped++
    } else {
      fail++
      failList.push({ name: r.file, reason: r.error || '解析失败' })
    }
  }

  importing.value = false
  const duration = ((Date.now() - startTime) / 1000).toFixed(1)
  const dbTotalAfter = await fetchDbTotal()

  importReport.value = {
    total: fileList.value.length,
    success,
    fail,
    skipped,
    duration,
    typeStats,
    dbTotal: dbTotalAfter,
    dbNew: dbTotalAfter - dbTotalBefore,
    failList
  }

  if (fail === 0) {
    ElMessage.success(`全部 ${success} 份报告解析成功！耗时 ${duration} 秒`)
  } else {
    ElMessage.warning(`成功 ${success} 份，失败 ${fail} 份，耗时 ${duration} 秒`)
  }
}

async function fetchDbTotal() {
  try {
    const { data } = await axios.get('/api/stats')
    return data.total || 0
  } catch {
    return 0
  }
}
</script>

<style scoped>
.upload-area :deep(.el-upload-dragger) {
  padding: 40px;
  border-radius: 12px;
}

.upload-area :deep(.el-upload-dragger .el-upload-list) {
  max-height: 250px;
  overflow-y: auto;
}

.upload-area :deep(.el-upload) {
  width: 100%;
}

.upload-area :deep(.el-upload-list) {
  max-height: 360px;
  overflow-y: auto;
  padding-right: 4px;
}

.report-stat {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.report-stat .number {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.report-stat .label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}
</style>
