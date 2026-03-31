<template>
  <n-layout class="app-layout">
    <!-- 顶部导航 -->
    <n-layout-header class="app-header">
      <div class="header-content">
        <h2 class="logo">📈 缠论分析平台</h2>
        <div class="header-actions">
          <span class="username">{{ auth.user?.nickname || auth.user?.username }}</span>
          <n-button size="small" @click="handleLogout">退出</n-button>
        </div>
      </div>
    </n-layout-header>

    <n-layout-content class="app-content">
      <div class="content-wrapper">
        <!-- 快捷搜索 -->
        <n-card title="股票搜索" class="search-card">
          <n-input-group>
            <n-input v-model:value="searchCode" placeholder="输入股票代码，如 000001" @keyup.enter="goStock" />
            <n-button type="primary" @click="goStock">分析</n-button>
          </n-input-group>
        </n-card>

        <!-- 我的股票池 -->
        <n-card title="我的股票池">
          <template #header-extra>
            <n-button size="small" type="primary" @click="showCreateModal = true">+ 新建股票池</n-button>
          </template>
          <n-spin :show="loading">
            <div v-if="watchlistStore.watchlists.length === 0" class="empty-tip">
              暂无股票池，点击右上角新建
            </div>
            <div v-else class="watchlist-grid">
              <div v-for="wl in watchlistStore.watchlists" :key="wl.id" class="watchlist-item">
                <div class="wl-header">
                  <strong>{{ wl.name }}</strong>
                  <n-button size="tiny" text @click="deleteWatchlist(wl.id)">删除</n-button>
                </div>
                <div class="stock-tags">
                  <n-tag v-for="s in wl.stocks" :key="s.id" round size="small" class="stock-tag" @click="router.push(`/stock/${s.stock_code}`)">
                    {{ s.stock_code }}
                  </n-tag>
                </div>
                <n-button size="tiny" @click="openAddStock(wl)">+ 添加股票</n-button>
              </div>
            </div>
          </n-spin>
        </n-card>
      </div>
    </n-layout-content>

    <!-- 新建股票池弹窗 -->
    <n-modal v-model:show="showCreateModal">
      <n-card style="width: 400px" title="新建股票池">
        <n-form :model="newWl" label-placement="top">
          <n-form-item label="名称">
            <n-input v-model:value="newWl.name" placeholder="如：我的自选" />
          </n-form-item>
          <n-form-item label="描述（选填）">
            <n-input v-model:value="newWl.description" placeholder="描述" />
          </n-form-item>
        </n-form>
        <template #footer>
          <n-button type="primary" @click="createWatchlist">创建</n-button>
        </template>
      </n-card>
    </n-modal>

    <!-- 添加股票弹窗 -->
    <n-modal v-model:show="showAddStockModal">
      <n-card style="width: 400px" title="添加股票">
        <n-form :model="newStock" label-placement="top">
          <n-form-item label="股票代码">
            <n-input v-model:value="newStock.code" placeholder="6位代码，如 000001" />
          </n-form-item>
          <n-form-item label="股票名称（选填）">
            <n-input v-model:value="newStock.name" placeholder="股票名称" />
          </n-form-item>
        </n-form>
        <template #footer>
          <n-button type="primary" @click="addStock">添加</n-button>
        </template>
      </n-card>
    </n-modal>
  </n-layout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NLayout, NLayoutHeader, NLayoutContent, NCard, NInput, NInputGroup, NButton, NTag, NModal, NForm, NFormItem, NSpin, useMessage } from 'naive-ui'
import { useAuthStore } from '@/stores/auth'
import { useWatchlistStore } from '@/stores/watchlist'
import type { Watchlist } from '@/api/types'

const router = useRouter()
const auth = useAuthStore()
const watchlistStore = useWatchlistStore()
const message = useMessage()

const searchCode = ref('')
const loading = ref(false)
const showCreateModal = ref(false)
const showAddStockModal = ref(false)
const newWl = ref({ name: '', description: '' })
const newStock = ref({ code: '', name: '' })
const currentWl = ref<Watchlist | null>(null)

onMounted(() => {
  watchlistStore.fetchAll()
})

function goStock() {
  if (searchCode.value.trim()) {
    router.push(`/stock/${searchCode.value.trim()}`)
  }
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}

async function createWatchlist() {
  if (!newWl.value.name.trim()) return
  await watchlistStore.create(newWl.value.name, newWl.value.description)
  newWl.value = { name: '', description: '' }
  showCreateModal.value = false
  message.success('股票池创建成功')
}

async function deleteWatchlist(id: number) {
  await watchlistStore.remove(id)
  message.success('已删除')
}

function openAddStock(wl: Watchlist) {
  currentWl.value = wl
  newStock.value = { code: '', name: '' }
  showAddStockModal.value = true
}

async function addStock() {
  if (!newStock.value.code || !currentWl.value) return
  await watchlistStore.addStock(currentWl.value.id, newStock.value.code, newStock.value.name || undefined)
  showAddStockModal.value = false
  message.success('股票已添加')
}
</script>

<style scoped>
.app-layout { min-height: 100vh; }
.app-header { background: #fff; border-bottom: 1px solid #eee; padding: 0 24px; }
.header-content { display: flex; justify-content: space-between; align-items: center; height: 60px; }
.logo { margin: 0; font-size: 18px; }
.header-actions { display: flex; gap: 12px; align-items: center; }
.username { color: #666; font-size: 14px; }
.app-content { background: #f5f5f5; padding: 24px; }
.content-wrapper { max-width: 960px; margin: 0 auto; display: flex; flex-direction: column; gap: 16px; }
.empty-tip { color: #999; text-align: center; padding: 20px; }
.watchlist-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }
.wl-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.stock-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px; min-height: 28px; }
.stock-tag { cursor: pointer; }
</style>
