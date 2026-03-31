<template>
  <div class="stock-page">
    <!-- 顶部导航 -->
    <div class="stock-header">
      <div class="header-left">
        <n-button text @click="router.push('/')">← 返回</n-button>
        <span class="stock-title">{{ stockCode }}</span>
      </div>
      <div class="header-right">
        <n-select v-model:value="period" :options="periodOptions" style="width: 120px" />
        <n-select v-model:value="adjust" :options="adjustOptions" style="width: 100px" />
        <n-button type="primary" @click="loadData">刷新</n-button>
      </div>
    </div>

    <!-- K线图（叠加缠论） -->
    <div class="chart-section" style="flex: 2">
      <div class="chart-title">K线 + 缠论结构</div>
      <div ref="klineRef" class="chart-container"></div>
    </div>

    <!-- MACD图 -->
    <div class="chart-section">
      <div class="chart-title">MACD</div>
      <div ref="macdRef" class="chart-container"></div>
    </div>

    <!-- 缠论结构面板 -->
    <div class="chanlun-panel" v-if="chanlunData.zhongshu_list?.length">
      <div class="panel-title">中枢 ({{ chanlunData.zhongshu_list?.length }})</div>
      <div class="panel-items">
        <div v-for="(zs, i) in chanlunData.zhongshu_list" :key="i" class="zs-item">
          <span class="zs-badge">中枢{{ Number(i) + 1 }}</span>
          <span>ZD: {{ zs.zd?.toFixed(2) }}</span>
          <span>ZG: {{ zs.zg?.toFixed(2) }}</span>
          <span>中枢价: {{ zs.center?.toFixed(2) }}</span>
        </div>
      </div>
    </div>

    <!-- 信号面板 -->
    <div class="signals-panel" v-if="chanlunData.signals?.length">
      <div class="panel-title">买卖点信号 ({{ chanlunData.signals?.length }})</div>
      <div class="panel-items">
        <n-tag v-for="(sig, i) in chanlunData.signals" :key="i" :type="signalTagType(sig.type)" size="small">
          {{ signalLabel(sig.type) }} {{ sig.date }} {{ sig.price?.toFixed(2) }}
        </n-tag>
      </div>
    </div>

    <!-- 背驰面板 -->
    <div class="divergence-panel" v-if="chanlunData.divergence_list?.length">
      <div class="panel-title">背驰 ({{ chanlunData.divergence_list?.length }})</div>
      <div class="panel-items">
        <n-tag v-for="(d, i) in chanlunData.divergence_list" :key="i" :type="d.type === 'top' ? 'error' : 'success'" size="small">
          {{ d.type === 'top' ? '顶背驰' : '底背驰' }} {{ d.date }} 强度{{ (d.strength * 100).toFixed(0) }}%
        </n-tag>
      </div>
    </div>

    <n-spin :show="loading" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NButton, NSelect, NSpin, NTag } from 'naive-ui'
import * as echarts from 'echarts'
import api from '@/api/axios'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const stockCode = ref(route.params.code as string)
const period = ref('daily')
const adjust = ref('qfq')
const loading = ref(false)

const klineRef = ref<HTMLDivElement>()
const macdRef = ref<HTMLDivElement>()
let klineChart: echarts.ECharts | null = null
let macdChart: echarts.ECharts | null = null

const klineData = ref<any[]>([])
const macdData = ref<any[]>([])
const macdDataL2 = ref<any[]>([])  // 第二层（上层周期）MACD
const macdDataL3 = ref<any[]>([])  // 第三层（再上周期）MACD
const chanlunData = ref<any>({})

const periodOptions = [
  { label: '15分钟', value: '15min' },
  { label: '60分钟', value: '60min' },
  { label: '日线', value: 'daily' },
  { label: '周线', value: 'weekly' },
  { label: '月线', value: 'monthly' },
]
const adjustOptions = [
  { label: '前复权', value: 'qfq' },
  { label: '后复权', value: 'hfq' },
]

// 周期层级映射：当前周期 -> [上层周期, 再上周期, 展开倍数]
const periodHierarchy: Record<string, [string, string, number, number]> = {
  '15min': ['60min', 'daily', 4, 24],    // 15分 -> 60分(×4) -> 日线(×24)
  '60min': ['daily', 'weekly', 4, 5],    // 60分 -> 日线(×4) -> 周线(×5)
  'daily': ['weekly', 'monthly', 5, 4],  // 日线 -> 周线(×5) -> 月线(×4)
  'weekly': ['monthly', 'quarterly', 4, 3], // 周线 -> 月线(×4) -> 季线(×3)
  'monthly': ['quarterly', 'yearly', 3, 4], // 月线 -> 季线(×3) -> 年线(×4)
}
const signalLabel = (type: string): string => {
  const map: Record<string, string> = {
    buy1: '一买', buy2: '二买', buy3: '三买',
    sell1: '一卖', sell2: '二卖', sell3: '三卖',
  }
  return map[type] || type
}

const signalTagType = (type: string) => {
  if (type.startsWith('buy')) return 'success'
  if (type.startsWith('sell')) return 'error'
  return 'default'
}

onMounted(() => { initCharts(); loadData() })
onUnmounted(() => { klineChart?.dispose(); macdChart?.dispose() })

function initCharts() {
  if (klineRef.value) klineChart = echarts.init(klineRef.value)
  if (macdRef.value) macdChart = echarts.init(macdRef.value)
}

async function loadData() {
  loading.value = true
  try {
    const token = localStorage.getItem('token')
    const headers = { Authorization: `Bearer ${token}` }

    // 1. 获取当前周期的缠论数据（含K线和MACD）
    const clRes = await api.get('/chanlun/analyze', {
      params: { stock_code: stockCode.value, period: period.value, adjust: adjust.value, limit: 240 },
      headers,
    })

    const d = clRes.data || {}
    klineData.value = d.kline || []
    macdData.value = d.macd || []
    chanlunData.value = d

    // 2. 获取上层周期的MACD数据（用于三层叠加）
    const hierarchy = periodHierarchy[period.value]
    if (hierarchy) {
      const [upperPeriod, upperUpperPeriod] = hierarchy
      
      // 获取第二层（上层周期）数据
      try {
        const l2Res = await api.get('/chanlun/analyze', {
          params: { stock_code: stockCode.value, period: upperPeriod, adjust: adjust.value, limit: 240 },
          headers,
        })
        macdDataL2.value = l2Res.data?.macd || []
      } catch (e) {
        console.warn('获取第二层MACD数据失败:', e)
        macdDataL2.value = []
      }
      
      // 获取第三层（再上周期）数据
      try {
        const l3Res = await api.get('/chanlun/analyze', {
          params: { stock_code: stockCode.value, period: upperUpperPeriod, adjust: adjust.value, limit: 240 },
          headers,
        })
        macdDataL3.value = l3Res.data?.macd || []
      } catch (e) {
        console.warn('获取第三层MACD数据失败:', e)
        macdDataL3.value = []
      }
    } else {
      macdDataL2.value = []
      macdDataL3.value = []
    }

    renderKline()
    renderMACD()
  } finally {
    loading.value = false
  }
}

function renderKline() {
  if (!klineChart || !klineData.value.length) return

  const dates = klineData.value.map((d: any) => d.date?.split('T')[0])
  const ohlc = klineData.value.map((d: any) => [d.open, d.close, d.low, d.high])

  // 缠论数据
  const fenxing = chanlunData.value.fenxing_list || []
  const bi = chanlunData.value.bi_list || []
  const zhongshu = chanlunData.value.zhongshu_list || []
  const signals = chanlunData.value.signals || []

  // 分型标注
  const fenxingMark = fenxing.map((f: any) => ({
    coord: [f.index, f.price],
    symbol: f.type === 'top' ? 'triangle' : 'triangle',
    symbolSize: f.type === 'top' ? 8 : 8,
    itemStyle: { color: f.type === 'top' ? '#ef5350' : '#26a69a' },
  }))

  // 笔 markLine
  const biMarkLines: any[] = []
  bi.forEach((b: any) => {
    biMarkLines.push({
      xAxis: b.start_index,
      yAxis: b.start_price,
      xAxis2: b.end_index,
      yAxis2: b.end_price,
      lineStyle: { color: b.direction === 'up' ? '#ef5350' : '#26a69a', width: 1.5, type: 'solid' },
    })
  })

  // 中枢 markArea
  const zsMarkAreas: any[] = []
  zhongshu.forEach((zs: any) => {
    zsMarkAreas.push([
      { xAxis: zs.start_index, yAxis: zs.zd, itemStyle: { color: 'rgba(255,215,0,0.15)' } },
      { xAxis: zs.end_index, yAxis: zs.zg },
    ])
  })

  // 买卖点标注
  const signalMark = signals.map((s: any) => ({
    coord: [s.position, s.price],
    symbol: s.type.startsWith('buy') ? 'circle' : 'diamond',
    symbolSize: 10,
    itemStyle: { color: s.type.startsWith('buy') ? '#18a058' : '#d43030' },
  }))

  klineChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    grid: [{ left: '8%', right: '2%', top: '8%', height: '75%' }],
    xAxis: [{ type: 'category', data: dates, axisLabel: { fontSize: 10 } }],
    yAxis: [{ scale: true, axisLabel: { fontSize: 10 } }],
    series: [
      {
        type: 'candlestick',
        data: ohlc,
        itemStyle: { color: '#ef5350', color0: '#26a69a' },
        markPoint: { data: [...fenxingMark, ...signalMark] },
        markLine: { silent: true, symbol: 'none', data: biMarkLines },
        markArea: { silent: true, data: zsMarkAreas },
      },
    ],
  }, true)
}

function renderMACD() {
  if (!macdChart || !macdData.value.length) return

  const dates = macdData.value.map((d: any) => d.date?.split('T')[0])
  const hierarchy = periodHierarchy[period.value] || ['', '', 1, 1]
  const [, , repeatL2, repeatL3] = hierarchy

  // 展开上层周期数据到当前周期长度
  const expand = (arr: any[], repeat: number) => {
    if (!arr.length) return []
    return arr.flatMap(v => Array(repeat).fill(v))
  }

  const difL2 = expand(macdDataL2.value.map((d: any) => d.dif), repeatL2)
  const deaL2 = expand(macdDataL2.value.map((d: any) => d.dea), repeatL2)
  const difL3 = expand(macdDataL3.value.map((d: any) => d.dif), repeatL3)
  const deaL3 = expand(macdDataL3.value.map((d: any) => d.dea), repeatL3)

  // 截断到当前周期长度
  const cutTo = (arr: number[], targetLen: number) => arr.slice(0, targetLen)
  const dif = cutTo(macdData.value.map((d: any) => d.dif), dates.length)
  const dea = cutTo(macdData.value.map((d: any) => d.dea), dates.length)
  const bar = cutTo(macdData.value.map((d: any) => d.macd), dates.length)

  macdChart.setOption({
    legend: { data: ['DIF', 'DEA', 'DIF(L2)', 'DEA(L2)', 'DIF(L3)', 'DEA(L3)'], top: 0 },
    tooltip: { trigger: 'axis' },
    grid: [{ left: '8%', right: '2%', top: '20%', height: '35%' }],
    xAxis: [{ type: 'category', data: dates, axisLabel: { fontSize: 10 } }],
    yAxis: [{ axisLabel: { fontSize: 10 } }],
    series: [
      // 第一层（当前周期）
      { name: 'DIF', type: 'line', data: dif, smooth: true, lineStyle: { color: '#ffffff', width: 1.5 } },
      { name: 'DEA', type: 'line', data: dea, smooth: true, lineStyle: { color: '#ffff00', width: 1.5 } },
      // 第二层（上层周期）
      ...(difL2.length ? [
        { name: 'DIF(L2)', type: 'line', data: cutTo(difL2, dates.length), smooth: true, lineStyle: { color: '#00ffff', width: 1 } },
        { name: 'DEA(L2)', type: 'line', data: cutTo(deaL2, dates.length), smooth: true, lineStyle: { color: '#ff00ff', width: 1 } },
      ] : []),
      // 第三层（再上层周期）
      ...(difL3.length ? [
        { name: 'DIF(L3)', type: 'line', data: cutTo(difL3, dates.length), smooth: true, lineStyle: { color: '#00ff00', width: 1 } },
        { name: 'DEA(L3)', type: 'line', data: cutTo(deaL3, dates.length), smooth: true, lineStyle: { color: '#ffa500', width: 1 } },
      ] : []),
      // 柱状图（只显示第一层）
      {
        type: 'bar',
        data: bar.map((v: number) => v >= 0 ? v : 0),
        itemStyle: { color: '#ef5350' },
        barMaxWidth: 6,
      },
      {
        type: 'bar',
        data: bar.map((v: number) => v < 0 ? v : 0),
        itemStyle: { color: '#26a69a' },
        barMaxWidth: 6,
      },
    ],
  }, true)
}
</script>

<style scoped>
.stock-page { display: flex; flex-direction: column; height: 100vh; background: #1a1a2e; color: #fff; }
.stock-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 24px; background: #16213e; border-bottom: 1px solid #333; }
.header-left { display: flex; align-items: center; gap: 16px; }
.stock-title { font-size: 18px; font-weight: bold; }
.header-right { display: flex; gap: 12px; align-items: center; }
.chart-section { display: flex; flex-direction: column; padding: 8px; min-height: 0; }
.chart-title { font-size: 14px; color: #aaa; padding: 4px 8px; }
.chart-container { flex: 1; min-height: 0; }
.chanlun-panel, .signals-panel, .divergence-panel { padding: 8px 24px; }
.panel-title { font-size: 14px; color: #aaa; margin-bottom: 8px; }
.panel-items { display: flex; flex-wrap: wrap; gap: 8px; }
.zs-item { display: flex; gap: 12px; align-items: center; background: rgba(255,215,0,0.1); padding: 4px 12px; border-radius: 4px; font-size: 13px; }
.zs-badge { background: rgba(255,215,0,0.3); padding: 2px 6px; border-radius: 3px; }
</style>
