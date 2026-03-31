import api from './axios'
import type { UserOut, Token } from './types'

export const authApi = {
  register(username: string, password: string, nickname?: string) {
    return api.post<UserOut>('/auth/register', { username, password, nickname })
  },
  login(username: string, password: string) {
    return api.post<Token>('/auth/login', { username, password })
  },
  me() {
    return api.get<UserOut>('/auth/me')
  },
}
