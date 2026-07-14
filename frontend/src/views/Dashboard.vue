<template>
  <div>
    <!-- 加载错误提示 -->
    <el-alert v-if="loadError" type="error" :title="loadError" closable @close="loadError = null"
      style="margin-bottom:16px" />

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card" v-for="s in stats" :key="s.label" @click="goFiltered(s.type)">
        <div class="icon-box" :style="{background: s.color}">
          <el-icon :size="24"><component :is="s.icon" /></el-icon>
        </div>
        <div class="info">
          <div class="number">{{ s.count }}</div>
          <div class="label">{{ s.label }}</div>
        </div>
      </div>
    </div>

    <!-- 报告类型分布 + 最近导入 -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
      <!-- 类型分布 -->
      <div class="page-card">
        <div class="page-title" style="font-size:16px">报告类型分布</div>
        <div style="height:280px;display:flex;align-items:center;justify-content:center">
          <div style="display:flex;gap:32px;align-items:flex-end;height:200px">
            <div v-for="b in typeBars" :key="b.label"
              style="display:flex;flex-direction:column;align-items:center;gap:8px">
              <span style="font-size:16px;font-weight:700;color:#303133">{{ b.count }}</span>
              <div :style="{
                width:'56px',
                height: (b.count / maxTypeCount * 160) + 'px',
                background: b.color,
                borderRadius:'8px 8px 0 0',
                transition: 'height 0.6s'
              }"></div>
              <span style="font-size:12px;color:#909399;white-space:nowrap">{{ b.label }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 最近导入 -->
      <div class="page-card">
        <div class="page-title" style="font-size:16px">最近导入</div>
        <el-table :data="recentReports" style="width:100%" size="small" stripe>
          <el-table-column prop="patient_name" label="患者" width="80" />
          <el-table-column prop="report_type_label" label="类型" width="130" />
          <el-table-column prop="diagnosis_summary" label="诊断" show-overflow-tooltip />
          <el-table-column prop="report_date" label="日期" width="100" />
          <el-table-column width="60">
            <template #default="{row}">
              <el-button type="primary" link size="small" @click="$router.push(`/reports/${row.id}`)">
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getStats } from '../api/index.js'
import { useReportsStore } from '../stores/reports.js'

const router = useRouter()
const reportsStore = useReportsStore()

const loadError = ref(null)

const stats = ref([
  { label: '报告总数', count: 0, type: null, color: '#409eff', icon: 'Document' },
  { label: '细胞学（妇科）', count: 0, type: '细胞学（妇科）', color: '#67c23a', icon: 'Histogram' },
  { label: 'HPV检测', count: 0, type: 'HPV检测', color: '#e6a23c', icon: 'Warning' },
  { label: '细胞学（非妇科）', count: 0, type: '细胞学（非妇科）', color: '#00bcd4', icon: 'Microscope' },
  { label: '常规病理', count: 0, type: '常规病理', color: '#909399', icon: 'Collection' },
])

const typeBars = ref([
  { label: '细胞学\n（妇科）', count: 0, color: '#67c23a' },
  { label: 'HPV检测', count: 0, color: '#e6a23c' },
  { label: '细胞学\n（非妇科）', count: 0, color: '#00bcd4' },
  { label: '常规病理', count: 0, color: '#909399' },
])

const recentReports = ref([])
const maxTypeCount = computed(() => Math.max(...typeBars.value.map(b => b.count), 1))

function goFiltered(type) {
  reportsStore.clearSearchCache()
  if (type) {
    router.push({ path: '/reports', query: { type: type } })
  } else {
    router.push('/reports')
  }
}

onMounted(async () => {
  const { data, error } = await reportsStore.fetchStats()
  if (error) {
    loadError.value = error
    return
  }
  const tc = data.type_counts || {}
  stats.value[0].count = data.total
  stats.value[1].count = tc['细胞学（妇科）'] || 0
  stats.value[2].count = tc['HPV检测'] || 0
  stats.value[3].count = tc['细胞学（非妇科）'] || 0
  stats.value[4].count = tc['常规病理'] || 0

  typeBars.value[0].count = tc['细胞学（妇科）'] || 0
  typeBars.value[1].count = tc['HPV检测'] || 0
  typeBars.value[2].count = tc['细胞学（非妇科）'] || 0
  typeBars.value[3].count = tc['常规病理'] || 0

  recentReports.value = data.recent
})
</script>
