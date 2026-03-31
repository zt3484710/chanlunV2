<template>
  <div class="watchlist-page">
    <n-layout class="app-layout">
      <n-layout-header class="app-header">
        <div class="header-content">
          <h2>📈 缠论分析平台</h2>
          <n-button size="small" @click="router.push('/')">返回首页</n-button>
        </div>
      </n-layout-header>
      <n-layout-content class="app-content">
        <h3>我的股票池</h3>
        <n-button type="primary" @click="showCreateModal = true">+ 新建股票池</n-button>

        <div v-if="watchlistStore.watchlists.length === 0" class="empty">
          暂无股票池
        </div>
        <div v-else class="wl-list">
          <n-card v-for="wl in watchlistStore.watchlists" :key="wl.id" :title="wl.name" class="wl-card">
            <template #header-extra>
              <n-button size="tiny" text type="error" @click="removeWl(wl.id)">删除</n-button>
            </template>
            <div v-if="wl.stocks.length === 0" class="empty">暂无股票</div>
            <n-list v-else hoverable clickable>
              <n-list-item v-for="s in wl.stocks" :key="s.id">
                <div class="stock-row" @click="router.push(`/stock/${s.stock_code}`)">
                  <span class="code">{{ s.stock_code }}</span>
                  <span class="name">{{ s.stock_name }}</span>
                  <n-button size="tiny" text type="error" @click.stop="removeStock(wl.id, s.id)">移除</n-button>
                </div>
              </n-list-item>
            </n-list>
            <template #footer>
              <n-button size="small" @click="openAdd(wl)">+ 添加股票</n-button>
            </template>
          </n-card>
        </div>
      </n-layout-content>
    </n-layout>

    <n-modal v-model:show="showCreateModal">
      <n-card style="width:400px" title="新建股票池">
        <n-form :model="newWl" label-placement="top">
          <n-form-item label="名称"><n-input v-model:value="newWl.name" /></n-form-item>
          <n-form-item label="描述"><n-input v-model:value="newWl.description" /></n-form-item>
        </n-form>
        <template #footer><n-button type="primary" @click="createWl">创建</n-button></template>
      </n-card>
    </n-modal>

    <n-modal v-model:show="showAddModal">
      <n-card style="width:400px" title="添加股票">
        <n-form :model="newStock" label-placement="top">
          <n-form-item label="股票代码"><n-input v-model:value="newStock.code" placeholder="000001" /></n-form-item>
          <n-form-item label="名称"><n-input v-model:value="newStock.name" /></n-form-item>
        </n-form>
        <template #footer><n-button type="primary" @click="addStock">添加</n-button></template>
      </n-card>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NLayout, NLayoutHeader, NLayoutContent, NCard, NButton, NModal, NForm, NFormItem, NList, NListItem, NInput, useMessage } from 'naive-ui'
import { useWatchlistStore } from '@/stores/watchlist'
import type { Watchlist } from '@/api/types'

const router = useRouter()
const watchlistStore = useWatchlistStore()
const message = useMessage()

const showCreateModal = ref(false)
const showAddModal = ref(false)
const newWl = ref({ name: '', description: '' })
const newStock = ref({ code: '', name: '' })
const currentWl = ref<Watchlist | null>(null)

onMounted(() => watchlistStore.fetchAll())

function openAdd(wl: Watchlist) { currentWl.value = wl; showAddModal.value = true }
async function createWl() {
  if (!newWl.value.name) return
  await watchlistStore.create(newWl.value.name, newWl.value.description)
  showCreateModal.value = false
  newWl.value = { name: '', description: '' }
}
async function removeWl(id: number) {
  await watchlistStore.remove(id)
  message.success('已删除')
}
async function addStock() {
  if (!newStock.value.code || !currentWl.value) return
  await watchlistStore.addStock(currentWl.value.id, newStock.value.code, newStock.value.name || undefined)
  showAddModal.value = false
  message.success('已添加')
}
async function removeStock(wlId: number, sId: number) {
  await watchlistStore.removeStock(wlId, sId)
}
</script>

<style scoped>
.app-layout { min-height: 100vh; }
.app-header { background: #fff; border-bottom: 1px solid #eee; padding: 0 24px; }
.header-content { display: flex; justify-content: space-between; align-items: center; height: 60px; }
.app-content { background: #f5f5f5; padding: 24px; max-width: 960px; margin: 0 auto; }
.wl-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; margin-top: 16px; }
.stock-row { display: flex; gap: 12px; align-items: center; cursor: pointer; }
.code { font-weight: bold; min-width: 80px; }
.name { flex: 1; color: #666; }
.empty { color: #999; text-align: center; padding: 16px; }
</style>
