import { defineStore } from 'pinia'
import { ref } from 'vue'
import { watchlistApi } from '@/api/stocks'
import type { Watchlist } from '@/api/types'

export const useWatchlistStore = defineStore('watchlist', () => {
  const watchlists = ref<Watchlist[]>([])

  async function fetchAll() {
    const { data } = await watchlistApi.list()
    watchlists.value = data
  }

  async function create(name: string, description?: string) {
    const { data } = await watchlistApi.create(name, description)
    watchlists.value.push(data)
    return data
  }

  async function remove(id: number) {
    await watchlistApi.delete(id)
    watchlists.value = watchlists.value.filter((w) => w.id !== id)
  }

  async function addStock(watchlistId: number, stock_code: string, stock_name?: string) {
    const { data } = await watchlistApi.addStock(watchlistId, stock_code, stock_name)
    const wl = watchlists.value.find((w) => w.id === watchlistId)
    if (wl) wl.stocks.push(data)
    return data
  }

  async function removeStock(watchlistId: number, stockId: number) {
    await watchlistApi.removeStock(watchlistId, stockId)
    const wl = watchlists.value.find((w) => w.id === watchlistId)
    if (wl) wl.stocks = wl.stocks.filter((s) => s.id !== stockId)
  }

  return { watchlists, fetchAll, create, remove, addStock, removeStock }
})
