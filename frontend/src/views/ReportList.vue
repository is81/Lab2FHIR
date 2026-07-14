<template>
  <div>
    <!-- 搜索栏 -->
    <div class="page-card">
      <div class="search-bar">
        <el-input
          v-model="searchQuery"
          placeholder="搜索姓名 / 病理号 / 诊断..."
          clearable
          @keyup.enter="doSearch"
          @clear="doSearch"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>

        <el-select v-model="filterType" placeholder="报告类型" clearable @change="doSearch">
          <el-option label="全部类型" value="" />
          <el-option label="细胞学（妇科）" value="细胞学（妇科）" />
          <el-option label="HPV检测" value="HPV检测" />
          <el-option label="细胞学（非妇科）" value="细胞学（非妇科）" />
          <el-option label="常规病理" value="常规病理" />
        </el-select>

        <el-date-picker
          v-model="filterDateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width:170px"
        />

        <el-button type="primary" @click="doSearch" :icon="Search">搜索</el-button>
        <el-button @click="resetSearch">重置</el-button>
      </div>
    </div>

    <!-- 报告表格 -->
    <div class="page-card" style="margin-top:16px">
      <el-alert v-if="searchError" type="error" :title="searchError" closable @close="searchError = null"
        style="margin-bottom:12px" />
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
        <span style="font-weight:600;font-size:15px">
          共 {{ total }} 份报告
        </span>
        <el-button type="primary" size="small" @click="$router.push('/import')" :icon="Upload">
          导入新报告
        </el-button>
      </div>

      <el-table
        :data="reports"
        stripe
        style="width:100%"
        @row-click="goDetail"
        :row-style="{cursor:'pointer'}"
        v-loading="loading"
        max-height="calc(100vh - 360px)"
      >
        <el-table-column prop="pathology_id" label="病理号" width="110" />
        <el-table-column prop="patient_name" label="患者姓名" width="100" />
        <el-table-column prop="gender" label="性别" width="60" />
        <el-table-column prop="age" label="年龄" width="60" />
        <el-table-column label="报告类型" width="140">
          <template #default="{row}">
            <el-tag :type="getReportTypeColor(row.report_type)"
                    size="small">
              {{ row.report_type_label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="diagnosis_summary" label="诊断摘要" min-width="220" show-overflow-tooltip />
        <el-table-column prop="department" label="科室" width="100" show-overflow-tooltip />
        <el-table-column label="报告日期" width="110" sortable>
          <template #default="{row}">
            <span style="font-size:13px">{{ row.report_date }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{row}">
            <el-button type="primary" link size="small" @click.stop="goDetail(row)">详情</el-button>
            <el-button type="primary" link size="small" @click.stop="goPatient(row)">患者</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div style="display:flex;justify-content:flex-end;margin-top:16px">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="doSearch"
          @current-change="doSearch"
          background
          small
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getReports } from '../api/index.js'
import { getReportTypeColor } from '../utils/report.js'
import { useReportsStore } from '../stores/reports.js'

const router = useRouter()
const route = useRoute()
const reportsStore = useReportsStore()

const searchQuery = ref(reportsStore.lastSearchQuery || '')
const filterType = ref(reportsStore.lastFilterType || '')
const filterDateRange = ref(null)
const page = ref(reportsStore.lastPage || 1)
const pageSize = ref(reportsStore.lastPageSize || 10)
const total = ref(0)
const reports = ref([])
const loading = ref(false)
const searchError = ref(null)

async function doSearch() {
  // 缓存搜索状态到 Pinia store
  reportsStore.cacheSearchState(
    searchQuery.value, filterType.value, page.value, pageSize.value
  )

  // 同步搜索状态到 URL
  const q = {}
  if (searchQuery.value) q.search = searchQuery.value
  if (filterType.value) q.type = filterType.value
  if (page.value > 1) q.page = page.value
  router.replace({ query: q })

  loading.value = true
  searchError.value = null
  const params = {
    search: searchQuery.value,
    report_type: filterType.value,
    page: page.value,
    page_size: pageSize.value
  }
  if (filterDateRange.value && filterDateRange.value.length === 2) {
    params.date_from = filterDateRange.value[0]
    params.date_to = filterDateRange.value[1]
  }

  const { data, error } = await getReports(params)
  if (error) {
    searchError.value = error
    reports.value = []
    total.value = 0
  } else {
    reports.value = data.items
    total.value = data.total
  }
  loading.value = false
}

function resetSearch() {
  searchQuery.value = ''
  filterType.value = ''
  filterDateRange.value = null
  page.value = 1
  reportsStore.clearSearchCache()
  doSearch()
}

function goDetail(row) {
  router.push({ path: `/reports/${row.id}`, query: { from: 'list', ...route.query } })
}

function goPatient(row) {
  router.push({ path: `/patients/${encodeURIComponent(row.patient_name)}`, query: { from: 'list', ...route.query } })
}

// 从 URL 恢复搜索状态
function restoreFromUrl() {
  if (route.query.search) searchQuery.value = route.query.search
  if (route.query.type) filterType.value = route.query.type
  if (route.query.page) page.value = parseInt(route.query.page) || 1
}

onMounted(() => {
  restoreFromUrl()
  doSearch()
})
</script>
