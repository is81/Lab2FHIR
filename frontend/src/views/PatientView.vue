<template>
  <div>
    <!-- 返回栏 -->
    <div style="margin-bottom:12px">
      <el-button @click="goBack" :icon="ArrowLeft">返回列表</el-button>
    </div>

    <!-- 患者信息头部 -->
    <div class="page-card" v-if="patientName">
      <div style="display:flex;align-items:center;gap:16px">
        <el-avatar :size="56" style="background:#409eff;font-size:24px">
          {{ patientName.charAt(0) }}
        </el-avatar>
        <div>
          <h2 style="font-size:22px;font-weight:600;margin-bottom:4px">{{ patientName }}</h2>
          <div v-if="reports.length > 0" style="color:#909399;font-size:13px">
            {{ reports[0].gender }} · {{ reports[0].age }}岁 · 共 {{ reports.length }} 份报告
          </div>
        </div>
      </div>
    </div>

    <!-- 报告时间线 -->
    <div style="margin-top:20px">
      <el-timeline>
        <el-timeline-item
          v-for="r in reports"
          :key="r.id"
          :timestamp="r.report_date"
          placement="top"
          :color="r.report_type === 'TCT' ? '#67c23a' :
                  r.report_type === 'HPV' ? '#e6a23c' :
                  r.report_type === 'DNA' ? '#f56c6c' :
                  r.report_type === '胃镜' ? '#909399' : '#409eff'"
        >
          <div class="page-card" style="cursor:pointer" @click="$router.push(`/reports/${r.id}`)">
            <div style="display:flex;justify-content:space-between;align-items:flex-start">
              <div>
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
                  <el-tag :type="r.report_type === 'TCT' ? 'success' :
                                r.report_type === 'HPV' ? 'warning' :
                                r.report_type === 'DNA' ? 'danger' : 'info'"
                          size="small">
                    {{ r.report_type_label }}
                  </el-tag>
                  <span style="font-size:13px;color:#909399">{{ r.department }} · {{ r.doctor }}</span>
                </div>
                <div style="font-size:15px;font-weight:500;color:#303133;margin-bottom:4px">
                  {{ r.diagnosis_summary }}
                </div>
                <div style="font-size:13px;color:#909399">病理号: {{ r.pathology_id }}</div>
              </div>
              <el-button type="primary" link>查看详情 →</el-button>
            </div>
          </div>
        </el-timeline-item>
      </el-timeline>
    </div>

    <div v-if="!loading && reports.length === 0" style="text-align:center;padding:60px">
      <el-empty description="未找到该患者的报告" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getPatientReports } from '../api/index.js'
import { getReportTypeColor } from '../utils/report.js'

const route = useRoute()
const router = useRouter()
const patientName = ref('')
const reports = ref([])
const loading = ref(true)

function goBack() {
  if (route.query.from === 'list') {
    router.push({ path: '/reports', query: route.query })
  } else {
    router.back()
  }
}

onMounted(async () => {
  patientName.value = decodeURIComponent(route.params.name)
  reports.value = await getPatientReports(patientName.value)
  loading.value = false
})
</script>
