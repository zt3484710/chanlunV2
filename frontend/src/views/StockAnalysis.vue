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

    <!-- K线图 -->
    <div class="chart-section">
      <div class="chart-title">K线</div>
      <div ref="klineRef" class="chart-container"></div>
    </div>

    <!-- MACD图 -->
    <div class="chart-section">
      <div class="chart-title">MACD</div>
      <div ref="macdRef" class="chart-container"></div>
    </div>

    <!-- 加载状态 -->
    <n-spin :show="loading">
      <div v-if="!hasData && !loading" class="no-data">暂无数据，请检查股票代码</div>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NButton, NSelect, NSpin, useMessage } from 'naive-ui'
import * as echarts from 'echarts'
import { stocksApi } from '@/api/stocks'

const route = useRoute()
const router = useRouter()
const message = useMessage()

const stockCode = ref(route.params.code as string)
const period = ref('daily')
const adjust = ref('qfq')
const loading = ref(false)
const hasData = ref(false)

const klineRef = ref<HTMLDivElement>()
const macdRef = ref<HTMLDivElement>()
let klineChart: echarts.ECharts | null = null
let macdChart: echarts.ECharts | null = null

const periodOptions = [
  { label: '日线', value: 'daily' },
  { label: '周线', value: 'weekly' },
  { label: '月线', value: 'monthly' },
]
const adjustOptions = [
  { label: '前复权', value: 'qfq' },
  { label: '后复权', value: 'hfq' },
]

onMounted(() => {
  initCharts()
  loadData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  klineChart?.dispose()
  macdChart?.dispose()
  window.removeEventListener('resize', handleResize)
})

function initCharts() {
  if (klineRef.value) {
    klineChart = echarts.init(klineRef.value)
  }
  if (macdRef.value) {
    macdChart = echarts.init(macdRef.value)
  }
}

function handleResize() {
  klineChart?.resize()
  macdChart?.resize()
}

async function loadData() {
  loading.value = true
  try {
    const { data } = await stocksApi.getKline(stockCode.value, period.value, adjust.value)
    if (data.error) {
      message.error(data.error)
      return
    }
    hasData.value = true
    renderKline(data.kline)
    renderMACD(data.macd)
  } catch (e: any) {
    message.error('加载数据失败：' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

function renderKline(kline: any[]) {
  if (!klineChart || !kline.length) return

  const dates = kline.map((d: any) => d.date?.split(' ')[0] || d.date)
  const data = kline.map((d: any) => [d.open, d.close, d.low, d.high])

  const option: echarts.EChartsOption = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    grid: [{ left: '8%', right: '2%', top: '10%', height: '75%' }],
    xAxis: [{ type: 'category', data: dates, axisLabel: { fontSize: 10 } }],
    yAxis: [{ scale: true, axisLabel: { fontSize: 10 } }],
    series: [
      {
        type: 'candlestick',
        data,
        itemStyle: { color: '#ef5350', color0: '#26a69a' },
      },
    ],
  }
  klineChart.setOption(option, true)
}

function renderMACD(macd: any[]) {
  if (!macdChart || !macd.length) return

  const dates = macd.map((d: any) => d.date?.split(' ')[0] || d.date)
  const dif = macd.map((d: any) => d.dif)
  const dea = macd.map((d: any) => d.dea)
  const bar = macd.map((d: any) => d.macd)

  const option: echarts.EChartsOption = {
    legend: { data: ['DIF', 'DEA'], top: 0 },
    tooltip: { trigger: 'axis' },
    grid: [{ left: '8%', right: '2%', top: '15%', height: '40%' }],
    xAxis: [{ type: 'category', data: dates, axisLabel: { fontSize: 10 } }],
    yAxis: [{ axisLabel: { fontSize: 10 } }],
    series: [
      { name: 'DIF', type: 'line', data: dif, smooth: true },
      { name: 'DEA', type: 'line', data: dea, smooth: true },
      {
        type: 'bar',
        data: bar.map((v: number) => (v >= 0 ? v : 0)),
        itemStyle: { color: '#ef5350' },
        barMaxWidth: 6,
      },
      {
        type: 'bar',
        data: bar.map((v: number) => (v < 0 ? v : 0)),
        itemStyle: { color: '#26a69a' },
        barMaxWidth: 6,
      },
    ],
  }
  macdChart.setOption(option, true)
}
</script>

<style scoped>
.stock-page { display: flex; flex-direction: column; height: 100vh; background: #1a1a2e; color: #fff; }
.stock-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 24px; background: #16213e; border-bottom: 1px solid #333; }
.header-left { display: flex; align-items: center; gap: 16px; }
.stock-title { font-size: 18px; font-weight: bold; }
.header-right { display: flex; gap: 12px; align-items: center; }
.chart-section { flex: 1; display: flex; flex-direction: column; padding: 8px; min-height: 0; }
.chart-title { font-size: 14px; color: #aaa; padding: 4px 8px; }
.chart-container { flex: 1; min-height: 0; }
.no-data { text-align: center; color: #888; padding: 40px; }
</style>
