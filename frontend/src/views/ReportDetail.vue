<template>
  <div v-if="report">
    <!-- 返回栏 -->
    <div style="margin-bottom:12px">
      <el-button @click="goBack" :icon="ArrowLeft">返回列表</el-button>
    </div>

    <div class="detail-layout" :class="{ 'left-hidden': collapsed.left, 'mid-hidden': collapsed.mid, 'right-hidden': collapsed.right }">
    <!-- 左栏 -->
    <div class="detail-panel" v-if="!collapsed.left">
      <div class="panel-header">
        <el-icon><List /></el-icon>
        解析结果
        <span class="panel-collapse-btn" @click="collapsed.left = true" title="收起"><el-icon><Fold /></el-icon></span>
      </div>
      <div class="panel-body">
        <!-- 患者信息 -->
        <div style="margin-bottom:20px">
          <h3 style="font-size:14px;color:#909399;margin-bottom:12px">患者信息</h3>
          <div class="info-tags">
            <div class="info-tag"><span class="label">姓名</span><span class="value">{{ report.patient_name }}</span></div>
            <div class="info-tag"><span class="label">性别</span><span class="value">{{ report.gender }}</span></div>
            <div class="info-tag"><span class="label">年龄</span><span class="value">{{ report.age }}岁</span></div>
            <div class="info-tag"><span class="label">病理号</span><span class="value">{{ report.pathology_id }}</span></div>
          </div>
        </div>

        <!-- 报告信息 -->
        <div style="margin-bottom:20px">
          <h3 style="font-size:14px;color:#909399;margin-bottom:12px">报告信息</h3>
          <div class="info-tags">
            <div class="info-tag"><span class="label">类型</span>
              <el-tag :type="getReportTypeColor(report.report_type)"
                      size="small">{{ report.report_type_label }}</el-tag>
            </div>
            <div class="info-tag"><span class="label">医院</span><span class="value">{{ report.hospital }}</span></div>
            <div class="info-tag"><span class="label">科室</span><span class="value">{{ report.department }}</span></div>
            <div class="info-tag"><span class="label">医生</span><span class="value">{{ report.doctor }}</span></div>
            <div class="info-tag"><span class="label">报告日期</span><span class="value">{{ report.report_date }}</span></div>
            <div class="info-tag"><span class="label">采样日期</span><span class="value">{{ report.sample_date }}</span></div>
          </div>
        </div>

        <!-- 诊断结论 -->
        <div style="margin-bottom:20px">
          <h3 style="font-size:14px;color:#909399;margin-bottom:12px">诊断结论</h3>
          <div style="background:#f8f9fa;border-radius:8px;padding:16px;white-space:pre-line;font-size:14px;line-height:1.8">
            {{ report.diagnosis }}
          </div>
        </div>

        <!-- 结构化数据 (根据报告类型展示) -->
        <div v-if="report.report_type === 'DNA' && report.parsed_data.DNA分析表格">
          <h3 style="font-size:14px;color:#909399;margin-bottom:12px">DNA 定量分析</h3>
          <el-table :data="report.parsed_data.DNA分析表格" size="small" border>
            <el-table-column prop="类别" label="类别" />
            <el-table-column prop="Percent" label="Percent (%)" />
            <el-table-column prop="DI均值" label="DI 均值" />
            <el-table-column prop="STD" label="STD" />
          </el-table>
        </div>

        <div v-if="report.report_type === 'TCT' && report.parsed_data.细胞项目">
          <h3 style="font-size:14px;color:#909399;margin-bottom:12px">细胞项目</h3>
          <el-table :data="kvToArray(report.parsed_data.细胞项目)" size="small" border>
            <el-table-column prop="key" label="项目" />
            <el-table-column prop="value" label="结果">
              <template #default="{row}">
                <el-tag :type="row.value === '有' ? 'success' : 'info'" size="small">{{ row.value }}</el-tag>
              </template>
            </el-table-column>
          </el-table>

          <h3 style="font-size:14px;color:#909399;margin:16px 0 12px">微生物项目</h3>
          <el-table :data="kvToArray(report.parsed_data.微生物项目)" size="small" border>
            <el-table-column prop="key" label="项目" />
            <el-table-column prop="value" label="结果">
              <template #default="{row}">
                <el-tag :type="row.value === '无' ? 'success' : 'danger'" size="small">{{ row.value }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div v-if="report.report_type === 'HPV'">
          <div style="display:flex;gap:16px;flex-wrap:wrap">
            <div v-for="(val, key) in {高危型HPV:report.parsed_data['高危型HPV'], 低危型HPV:report.parsed_data['低危型HPV']}"
              :key="key"
              style="flex:1;min-width:120px;background:#f8f9fa;border-radius:8px;padding:16px;text-align:center">
              <div style="font-size:12px;color:#909399;margin-bottom:8px">{{ key }}</div>
              <el-tag :type="val === '阴性' || val === '阴性' ? 'success' : 'danger'" size="large">
                {{ val }}
              </el-tag>
            </div>
          </div>

          <div v-if="report.parsed_data.具体分型 && report.parsed_data.具体分型.length > 0" style="margin-top:16px">
            <h3 style="font-size:14px;color:#909399;margin-bottom:8px">阳性分型</h3>
            <div style="display:flex;gap:8px;flex-wrap:wrap">
              <el-tag v-for="t in report.parsed_data.具体分型" :key="t" type="danger">{{ t }}</el-tag>
            </div>
          </div>
        </div>
        <div style="color:#f56c6c;font-size:12px;padding:12px 20px;border-top:1px solid #f0f0f0;text-align:right;flex-shrink:0">
          * 以上解析结果仅供参考，请以原始PDF报告为准
        </div>
      </div>
    </div>

    <!-- 左栏收起状态 -->
    <div class="collapsed-strip" v-if="collapsed.left" @click="collapsed.left = false" title="展开：解析结果">
      <span class="collapsed-label">解析结果</span>
      <el-icon><Expand /></el-icon>
    </div>

    <!-- 中栏：PDF 原文 -->
    <div class="detail-panel" v-if="!collapsed.mid">
      <div class="panel-header">
        <el-icon><Picture /></el-icon>
        PDF 原文
        <span style="font-size:12px;color:#909399;font-weight:400;margin-left:auto">
          {{ report.pdf_filename }}
        </span>
        <span class="panel-collapse-btn" @click="collapsed.mid = true" title="收起"><el-icon><Fold /></el-icon></span>
      </div>
      <div class="panel-body" style="padding:0;overflow:hidden">
        <PdfViewer :url="pdfUrl" />
      </div>
    </div>

    <!-- 中栏收起状态 -->
    <div class="collapsed-strip" v-if="collapsed.mid" @click="collapsed.mid = false" title="展开：PDF 原文">
      <span class="collapsed-label">PDF 原文</span>
      <el-icon><Expand /></el-icon>
    </div>

    <!-- 右栏：FHIR JSON（默认收起） -->
    <div class="detail-panel" v-if="!collapsed.right">
      <div class="panel-header">
        <el-icon><Document /></el-icon>
        FHIR R4 JSON
        <span class="panel-collapse-btn" @click="collapsed.right = true" title="收起"><el-icon><Fold /></el-icon></span>
      </div>
      <div class="panel-body" style="padding:0;font-family:'JetBrains Mono', 'Fira Code', 'Consolas', monospace">
        <pre style="font-size:12px;line-height:1.6;padding:16px;margin:0;overflow:auto;height:100%;white-space:pre-wrap;word-break:break-all;background:#1e1e2e;color:#c9d1d9">{{ JSON.stringify(report.fhir_bundle, null, 2) }}</pre>
      </div>
    </div>

    <!-- 右栏收起状态 -->
    <div class="collapsed-strip" v-if="collapsed.right" @click="collapsed.right = false" title="展开：FHIR JSON">
      <span class="collapsed-label">FHIR JSON</span>
      <el-icon><Expand /></el-icon>
    </div>
  </div>
  </div>

  <!-- 加载/错误 -->
  <div v-else-if="loading" style="display:flex;align-items:center;justify-content:center;height:60vh">
    <el-icon class="is-loading" :size="32"><Loading /></el-icon>
  </div>
  <div v-else style="display:flex;align-items:center;justify-content:center;height:60vh;flex-direction:column">
    <el-empty description="报告不存在" />
    <el-button type="primary" @click="$router.push('/reports')" style="margin-top:16px">返回报告列表</el-button>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getReport } from '../api/index.js'
import { getReportTypeColor } from '../utils/report.js'
import PdfViewer from '../components/PdfViewer.vue'

const route = useRoute()
const router = useRouter()
const report = ref(null)
const loading = ref(true)
const collapsed = reactive({ left: false, mid: false, right: true })

function goBack() {
  if (route.query.from === 'list') {
    router.push({ path: '/reports', query: route.query })
  } else {
    router.back()
  }
}

const pdfUrl = computed(() => {
  if (!report.value) return ''
  const pid = report.value.pathology_id || ''
  return `/api/reports/${report.value.id}/pdf?pid=${encodeURIComponent(pid)}&_t=${report.value.id}`
})

function kvToArray(obj) {
  if (!obj) return []
  return Object.entries(obj).map(([key, value]) => ({ key, value }))
}

onMounted(async () => {
  const id = parseInt(route.params.id)
  const { data, error } = await getReport(id)
  report.value = data
  loading.value = false
})
</script>
