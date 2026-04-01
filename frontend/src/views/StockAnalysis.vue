<template>
  <div class="stock-page">
    <!-- 顶部导航 -->
    <div class="stock-header">
      <div class="header-left">
        <n-button text size="small" @click="router.push('/')">←</n-button>
        <span class="stock-title">{{ stockCode }}</span>
      </div>
      <div class="header-right">
        <n-select v-model:value="period" :options="periodOptions" size="small" style="width: 90px" />
        <n-select v-model:value="adjust" :options="adjustOptions" size="small" style="width: 80px" />
        <n-button type="primary" size="small" @click="loadData">刷</n-button>
      </div>
    </div>

    <!-- 图表区域（占主要空间） -->
    <div class="charts-area">
      <div class="chart-section">
        <div class="chart-title">K线 + 缠论</div>
        <div ref="klineRef" class="chart-container"></div>
      </div>
      <div class="chart-section">
        <div class="chart-title">MACD</div>
        <div ref="macdRef" class="chart-container"></div>
      </div>
    </div>

    <!-- 底部数据面板（折叠） -->
    <div class="bottom-panels">
      <n-collapse-transition :show="!!chanlunData.zhongshu_list?.length" :native="false">
        <div class="quick-stats" v-if="chanlunData.zhongshu_list?.length">
          <span class="stat-badge">中枢 {{ chanlunData.zhongshu_list.length }}</span>
          <span class="stat-badge">笔 {{ chanlunData.bi_list?.length }}</span>
          <span class="stat-badge">信号 {{ chanlunData.signals?.length }}</span>
          <span class="stat-badge" :type="chanlunData.divergence_list?.length ? 'error' : 'default'">
            背驰 {{ chanlunData.divergence_list?.length || 0 }}
          </span>
        </div>
      </n-collapse-transition>

      <n-tabs type="segment" size="small" class="panel-tabs">
        <n-tab-pane name="zs" tab="中枢">
          <div class="panel-scroll">
            <div v-if="!chanlunData.zhongshu_list?.length" class="empty-hint">暂无中枢</div>
            <div v-for="(zs, i) in chanlunData.zhongshu_list" :key="i" class="zs-row">
              <span>Z{{ Number(i) + 1 }}</span>
              <span>{{ zs.zd?.toFixed(2) }}</span>
              <span>~ {{ zs.zg?.toFixed(2) }}</span>
              <span>{{ zs.center?.toFixed(2) }}</span>
            </div>
          </div>
        </n-tab-pane>

        <n-tab-pane name="sig" tab="信号">
          <div class="panel-scroll">
            <div v-if="!chanlunData.signals?.length" class="empty-hint">暂无信号</div>
            <div v-else class="signal-list">
              <div v-for="(sig, i) in chanlunData.signals.slice(0, 50)" :key="i" class="sig-item" :class="sig.type.startsWith('buy') ? 'buy' : 'sell'">
                <span class="sig-label">{{ signalLabel(sig.type) }}</span>
                <span class="sig-date">{{ sig.date?.slice(5) }}</span>
                <span class="sig-price">{{ sig.price?.toFixed(2) }}</span>
              </div>
              <div v-if="chanlunData.signals.length > 50" class="empty-hint">
                还有 {{ chanlunData.signals.length - 50 }} 条...
              </div>
            </div>
          </div>
        </n-tab-pane>

        <n-tab-pane name="div" tab="背驰">
          <div class="panel-scroll">
            <div v-if="!chanlunData.divergence_list?.length" class="empty-hint">暂无背驰</div>
            <div v-for="(d, i) in chanlunData.divergence_list" :key="i" class="sig-item" :class="d.type === 'top' ? 'sell' : 'buy'">
              <span class="sig-label">{{ d.type === 'top' ? '顶背驰' : '底背驰' }}</span>
              <span class="sig-date">{{ d.date?.slice(5) }}</span>
              <span class="sig-price">{{ (d.strength * 100).toFixed(0) }}%</span>
            </div>
          </div>
        </n-tab-pane>
      </n-tabs>
    </div>

    <n-spin :show="loading" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NButton, NSelect, NSpin, NTag, NTabs, NTabPane, NCollapseTransition } from 'naive-ui'
import * as echarts from 'echarts'
import api from '@/api/axios'

const route = useRoute()
const router = useRouter()

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
const macdDataL2 = ref<any[]>([])
const macdDataL3 = ref<any[]>([])
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

const periodHierarchy: Record<string, [string, string, number, number]> = {
  '15min': ['60min', 'daily', 4, 24],
  '60min': ['daily', 'weekly', 4, 5],
  'daily': ['weekly', 'monthly', 5, 4],
  'weekly': ['monthly', 'quarterly', 4, 3],
  'monthly': ['quarterly', 'yearly', 3, 4],
}

const signalLabel = (type: string): string => {
  const map: Record<string, string> = {
    buy1: '一买', buy2: '二买', buy3: '三买',
    sell1: '一卖', sell2: '二卖', sell3: '三卖',
  }
  return map[type] || type
}

onMounted(() => { initCharts(); window.addEventListener('resize', handleResize) })
onUnmounted(() => { klineChart?.dispose(); macdChart?.dispose(); window.removeEventListener('resize', handleResize) })

// T3: watch stockCode, adjust, period changes and auto reload
watch([stockCode, adjust, period], () => loadData(), { immediate: true })

function initCharts() {
  if (klineRef.value) klineChart = echarts.init(klineRef.value)
  if (macdRef.value) macdChart = echarts.init(macdRef.value)
}

function handleResize() { klineChart?.resize(); macdChart?.resize() }

async function loadData() {
  loading.value = true
  try {
    const token = localStorage.getItem('token')
    const headers = { Authorization: `Bearer ${token}` }
    const clRes = await api.get('/chanlun/analyze', {
      params: { stock_code: stockCode.value, period: period.value, adjust: adjust.value, limit: 240 },
      headers,
    })
    const d = clRes.data || {}
    klineData.value = d.kline || []
    macdData.value = d.macd || []
    chanlunData.value = d
    macdDataL2.value = d.macd_l2 || []
    macdDataL3.value = d.macd_l3 || []
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
  const fenxing = chanlunData.value.fenxing_list || []
  const bi = chanlunData.value.bi_list || []
  const zhongshu = chanlunData.value.zhongshu_list || []
  const signals = chanlunData.value.signals || []

  const fenxingMark = fenxing.map((f: any) => ({
    coord: [f.index, f.price],
    symbol: 'triangle', symbolSize: 7,
    itemStyle: { color: f.type === 'top' ? '#ef5350' : '#26a69a' },
  }))
  // T5: 笔用粗线绘制
  const biMarkLines = bi.map((b: any) => ({
    xAxis: b.start_index, yAxis: b.start_price,
    xAxis2: b.end_index, yAxis2: b.end_price,
    lineStyle: { color: b.direction === 'up' ? '#ef5350' : '#26a69a', width: 2.5, type: 'solid' },
  }))

  // T5: 线段用虚线绘制
  const xianduan = chanlunData.value.xianduan_list || []
  const xianduanMarkLines = xianduan.map((xd: any) => ({
    xAxis: xd.start_index, yAxis: xd.start_price,
    xAxis2: xd.end_index, yAxis2: xd.end_price,
    lineStyle: { color: xd.direction === 'up' ? '#ff6b6b' : '#4ecdc4', width: 2, type: 'dashed' },
  }))
  // T5: 中枢用填充矩形绘制
  const zsMarkAreas = zhongshu.map((zs: any) => [
    { xAxis: zs.start_index, yAxis: zs.zd, itemStyle: { color: 'rgba(255,215,0,0.25)' } },
    { xAxis: zs.end_index, yAxis: zs.zg },
  ])
  const signalMark = signals.slice(0, 30).map((s: any) => ({
    coord: [s.position, s.price],
    symbol: s.type.startsWith('buy') ? 'circle' : 'diamond', symbolSize: 8,
    itemStyle: { color: s.type.startsWith('buy') ? '#18a058' : '#d43030' },
  }))

  klineChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    grid: [{ left: '2%', right: '2%', top: '8%', height: '78%' }],
    xAxis: [{ type: 'category', data: dates, axisLabel: { fontSize: 9, interval: Math.floor(dates.length / 6) } }],
    yAxis: [{ scale: true, axisLabel: { fontSize: 9 } }],
    series: [{
      type: 'candlestick', data: ohlc,
      itemStyle: { color: '#ef5350', color0: '#26a69a' },
      markPoint: { data: [...fenxingMark, ...signalMark] },
      markLine: { silent: true, symbol: 'none', data: [...biMarkLines, ...xianduanMarkLines] },
      markArea: { silent: true, data: zsMarkAreas },
    }],
  }, true)
}

function renderMACD() {
  if (!macdChart || !macdData.value.length) return
  const dates = macdData.value.map((d: any) => d.date?.split('T')[0])
  const hierarchy = periodHierarchy[period.value] || ['', '', 1, 1]
  const [, , repeatL2, repeatL3] = hierarchy
  const expand = (arr: any[], rep: number) => arr.length ? arr.flatMap(v => Array(rep).fill(v)) : []
  const cutTo = (arr: number[], len: number) => arr.slice(0, len)
  const dif = cutTo(macdData.value.map((d: any) => d.dif), dates.length)
  const dea = cutTo(macdData.value.map((d: any) => d.dea), dates.length)
  const bar = cutTo(macdData.value.map((d: any) => d.macd), dates.length)
  const difL2 = cutTo(expand(macdDataL2.value.map((d: any) => d.dif), repeatL2), dates.length)
  const deaL2 = cutTo(expand(macdDataL2.value.map((d: any) => d.dea), repeatL2), dates.length)
  const difL3 = cutTo(expand(macdDataL3.value.map((d: any) => d.dif), repeatL3), dates.length)
  const deaL3 = cutTo(expand(macdDataL3.value.map((d: any) => d.dea), repeatL3), dates.length)

  macdChart.setOption({
    legend: { data: ['DIF', 'DEA', 'L2', 'L3'], top: 0 },
    tooltip: { trigger: 'axis' },
    grid: [{ left: '2%', right: '2%', top: '18%', height: '32%' }],
    xAxis: [{ type: 'category', data: dates, axisLabel: { fontSize: 9, interval: Math.floor(dates.length / 6) } }],
    yAxis: [{ axisLabel: { fontSize: 9 } }],
    series: [
      { name: 'DIF', type: 'line', data: dif, smooth: true, lineStyle: { color: '#fff', width: 1.5 } },
      { name: 'DEA', type: 'line', data: dea, smooth: true, lineStyle: { color: '#ffff00', width: 1.5 } },
      ...(difL2.length ? [
        { name: 'DIF(L2)', type: 'line', data: difL2, smooth: true, lineStyle: { color: '#0FF', width: 1 } },
        { name: 'DEA(L2)', type: 'line', data: deaL2, smooth: true, lineStyle: { color: '#F0F', width: 1 } },
      ] : []),
      ...(difL3.length ? [
        { name: 'DIF(L3)', type: 'line', data: difL3, smooth: true, lineStyle: { color: '#0F0', width: 1 } },
        { name: 'DEA(L3)', type: 'line', data: deaL3, smooth: true, lineStyle: { color: '#FA0', width: 1 } },
      ] : []),
      { type: 'bar', data: bar.map((v: number) => v >= 0 ? v : 0), itemStyle: { color: '#ef5350' }, barMaxWidth: 4 },
      { type: 'bar', data: bar.map((v: number) => v < 0 ? v : 0), itemStyle: { color: '#26a69a' }, barMaxWidth: 4 },
    ],
  }, true)
}
</script>

<style scoped>
.stock-page { display: flex; flex-direction: column; height: 100vh; background: #1a1a2e; color: #fff; overflow: hidden; }

/* 顶部导航 */
.stock-header { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: #16213e; border-bottom: 1px solid #333; flex-shrink: 0; }
.header-left { display: flex; align-items: center; gap: 8px; }
.stock-title { font-size: 16px; font-weight: bold; }
.header-right { display: flex; gap: 6px; align-items: center; }

/* 图表区域：占据主要空间 */
.charts-area { flex: 1; display: flex; flex-direction: column; min-height: 0; overflow: hidden; }
.chart-section { display: flex; flex-direction: column; min-height: 0; }
.chart-section:first-child { flex: 1.2; }
.chart-section:last-child { flex: 0.9; }
.chart-title { font-size: 11px; color: #888; padding: 2px 8px; flex-shrink: 0; }
.chart-container { flex: 1; min-height: 0; }

/* 底部面板 */
.bottom-panels { flex-shrink: 0; background: #16213e; max-height: 42vh; display: flex; flex-direction: column; overflow: hidden; }
.quick-stats { display: flex; gap: 6px; padding: 6px 10px; flex-wrap: wrap; }
.stat-badge { background: rgba(255,255,255,0.08); padding: 2px 8px; border-radius: 10px; font-size: 12px; color: #ccc; }
.panel-tabs { flex: 1; overflow: hidden; }
.panel-tabs :deep(.n-tabs-nav) { padding: 0 8px; }
.panel-tabs :deep(.n-tab-pane) { padding: 8px; }
.panel-tabs :deep(.n-tabs-pane-wrapper) { overflow: hidden; }
.panel-scroll { max-height: 22vh; overflow-y: auto; }

/* 信号列表 */
.signal-list { display: flex; flex-wrap: wrap; gap: 4px; }
.sig-item { display: flex; gap: 4px; align-items: center; padding: 2px 6px; border-radius: 3px; font-size: 11px; }
.sig-item.buy { background: rgba(24,160,88,0.2); border: 1px solid rgba(24,160,88,0.4); }
.sig-item.sell { background: rgba(212,48,48,0.2); border: 1px solid rgba(212,48,48,0.4); }
.sig-label { font-weight: bold; }
.sig-date { color: #aaa; }
.sig-price { color: #ddd; }

/* 中枢列表 */
.zs-row { display: flex; gap: 8px; align-items: center; padding: 3px 6px; font-size: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); }
.zs-row span:first-child { color: #ffd700; min-width: 20px; }
.zs-row span:nth-child(2) { color: #aaa; }
.zs-row span:nth-child(3) { color: #fff; }
.zs-row span:last-child { color: #aaa; margin-left: auto; }

.empty-hint { color: #555; font-size: 12px; text-align: center; padding: 10px; }
</style>
