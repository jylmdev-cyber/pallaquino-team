import DefaultTheme from 'vitepress/theme'
import Diagram from './Diagram.vue'
import PortalStatus from './PortalStatus.vue'
import Breadcrumbs from './Breadcrumbs.vue'
import { h } from 'vue'
import './style.css'

export default {
  extends: DefaultTheme,
  Layout: () => h(DefaultTheme.Layout, null, { 'doc-before': () => h(Breadcrumbs) }),
  enhanceApp({ app }) {
    app.component('Diagram', Diagram)
    app.component('PortalStatus', PortalStatus)
  }
}
