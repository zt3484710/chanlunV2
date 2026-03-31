export interface UserOut {
  id: number
  username: string
  nickname: string | null
  created_at: string
}

export interface Token {
  access_token: string
  token_type: string
}

export interface Watchlist {
  id: number
  user_id: number
  name: string
  description: string | null
  created_at: string
  stocks: WatchlistStock[]
}

export interface WatchlistStock {
  id: number
  watchlist_id: number
  stock_code: string
  stock_name: string | null
  added_at: string
}
