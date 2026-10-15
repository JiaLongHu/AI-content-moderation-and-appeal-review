import { createPinia } from 'pinia'
import { createApp } from 'vue'
import {
  ElAlert,
  ElButton,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElInput,
} from 'element-plus'
import 'element-plus/es/components/alert/style/css'
import 'element-plus/es/components/button/style/css'
import 'element-plus/es/components/empty/style/css'
import 'element-plus/es/components/form/style/css'
import 'element-plus/es/components/form-item/style/css'
import 'element-plus/es/components/input/style/css'

import App from './App.vue'
import router from './router'
import './styles.css'

const app = createApp(App)

app.component('ElAlert', ElAlert)
app.component('ElButton', ElButton)
app.component('ElEmpty', ElEmpty)
app.component('ElForm', ElForm)
app.component('ElFormItem', ElFormItem)
app.component('ElInput', ElInput)

app.use(createPinia()).use(router).mount('#app')
