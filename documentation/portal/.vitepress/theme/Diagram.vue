<script setup>
import { ref, onMounted, watch } from 'vue'
import { useData } from 'vitepress'
const props = defineProps({ source: { type: String, required: true } })
const source = decodeURIComponent(props.source)
const svg = ref(''), error = ref(''), zoom = ref(1)
const { isDark } = useData()
let mounted = false
let generation = 0
async function render() {
  const revision = ++generation
  try {
    const { default: mermaid } = await import('mermaid')
    mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', theme: isDark.value ? 'dark' : 'default' })
    const result = await mermaid.render(`diagram-${crypto.randomUUID()}`, source)
    if (revision === generation) { svg.value = result.svg; error.value = '' }
  } catch (e) { if (revision === generation) error.value = 'No se pudo dibujar el diagrama. Consulta su fuente textual.' }
}
onMounted(() => { mounted = true; render() })
watch(isDark, () => { if (mounted) render() })
</script>

<template>
  <figure class="diagram">
    <figcaption>Diagrama técnico · <span>fuente Mermaid versionada</span></figcaption>
    <div class="diagram-tools" aria-label="Escala del diagrama">
      <button @click="zoom = Math.min(2, zoom + .2)" aria-label="Ampliar diagrama">+</button>
      <button @click="zoom = Math.max(.6, zoom - .2)" aria-label="Reducir diagrama">−</button>
      <button @click="zoom = 1">Restablecer</button>
    </div>
    <p v-if="error" role="alert">{{ error }}</p>
    <div v-else class="diagram-scroll" role="img" aria-label="Diagrama técnico; fuente textual disponible debajo" tabindex="0">
      <div :style="{ width: `${zoom * 100}%` }" v-html="svg"></div>
    </div>
    <details><summary>Ver fuente textual accesible</summary><pre>{{ source }}</pre></details>
  </figure>
</template>
