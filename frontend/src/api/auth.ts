import api from './axios'
import type { UserOut, Token } from './types'

export const authApi = {
  register(username: string, password: string, nickname?: string) {
    return api.post<UserOut>('/auth/register', { username, password, nickname })
  },
  login(username: string, password: string) {
    const params = new URLSearchParams()
    params.append('username', username)
    params.append('password', password)
    return api.post<Token>('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
  },
  me() {
    return api.get<UserOut>('/auth/me')
  },
}
