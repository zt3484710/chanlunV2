<template>
  <div class="login-page">
    <n-card class="login-card" title="缠论分析平台">
      <n-tabs v-model:value="activeTab" type="line" justify-space="center">
        <n-tab-pane name="login" tab="登录">
          <n-form ref="loginFormRef" :model="loginForm" :rules="rules">
            <n-form-item path="username" label="用户名">
              <n-input v-model:value="loginForm.username" placeholder="输入用户名" />
            </n-form-item>
            <n-form-item path="password" label="密码">
              <n-input v-model:value="loginForm.password" type="password" placeholder="输入密码" show-password-on="mousedown" />
            </n-form-item>
            <n-button type="primary" block :loading="loading" @click="handleLogin">登录</n-button>
          </n-form>
        </n-tab-pane>
        <n-tab-pane name="register" tab="注册">
          <n-form ref="regFormRef" :model="regForm" :rules="rules">
            <n-form-item path="username" label="用户名">
              <n-input v-model:value="regForm.username" placeholder="3-50位用户名" />
            </n-form-item>
            <n-form-item path="password" label="密码">
              <n-input v-model:value="regForm.password" type="password" placeholder="至少6位" show-password-on="mousedown" />
            </n-form-item>
            <n-form-item label="昵称（选填）">
              <n-input v-model:value="regForm.nickname" placeholder="昵称" />
            </n-form-item>
            <n-button type="primary" block :loading="loading" @click="handleRegister">注册</n-button>
          </n-form>
        </n-tab-pane>
      </n-tabs>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NTabs, NTabPane, NForm, NFormItem, NInput, NButton, useMessage } from 'naive-ui'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const message = useMessage()
const activeTab = ref('login')
const loading = ref(false)

const loginForm = ref({ username: '', password: '' })
const regForm = ref({ username: '', password: '', nickname: '' })

const rules = {
  username: { required: true, message: '请输入用户名', trigger: 'blur' },
  password: { required: true, message: '请输入密码', trigger: 'blur' },
}

async function handleLogin() {
  loading.value = true
  try {
    await auth.login(loginForm.value.username, loginForm.value.password)
    message.success('登录成功')
    router.push('/')
  } catch {
    message.error('用户名或密码错误')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  loading.value = true
  try {
    await auth.register(regForm.value.username, regForm.value.password, regForm.value.nickname || undefined)
    message.success('注册成功，请登录')
    activeTab.value = 'login'
  } catch (e: any) {
    message.error(e.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
}
.login-card {
  width: 400px;
  max-width: 95vw;
}
</style>
