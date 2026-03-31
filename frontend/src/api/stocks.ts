import api from './axios'

export const stocksApi = {
  getKline(stock_code: string, period = 'daily', adjust = 'qfq') {
    return api.get('/stocks/kline', { params: { stock_code, period, adjust } })
  },
  getQuote(stock_code: string) {
    return api.get('/stocks/quote', { params: { stock_code } })
  },
  getInfo(stock_code: string) {
    return api.get('/stocks/info', { params: { stock_code } })
  },
  getMultiPeriodMACD(stock_code: string) {
    return api.get('/stocks/macd/multi', { params: { stock_code } })
  },
}

export const watchlistApi = {
  list() {
    return api.get('/watchlist/')
  },
  create(name: string, description?: string) {
    return api.post('/watchlist/', { name, description })
  },
  delete(id: number) {
    return api.delete(`/watchlist/${id}`)
  },
  addStock(watchlistId: number, stock_code: string, stock_name?: string) {
    return api.post(`/watchlist/${watchlistId}/stocks`, { stock_code, stock_name })
  },
  removeStock(watchlistId: number, stockId: number) {
    return api.delete(`/watchlist/${watchlistId}/stocks/${stockId}`)
  },
}
