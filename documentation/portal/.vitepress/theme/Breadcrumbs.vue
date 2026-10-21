<script setup>
import { computed } from 'vue'
import { useData, withBase } from 'vitepress'
const { page } = useData()
const categories = { introduction: 'Introducción', 'getting-started': 'Instalación', architecture: 'Arquitectura',
  development: 'Desarrollo', agents: 'Agentes', skills: 'Skills', automation: 'Automatización', security: 'Seguridad',
  integrations: 'Integraciones', deployment: 'Despliegue', api: 'API y CLI', examples: 'Ejemplos',
  troubleshooting: 'Solución de problemas', changelog: 'Versiones', generated: 'Referencia generada' }
const section = computed(() => categories[page.value.relativePath.split('/')[0]] || 'Documentación')
</script>
<template><nav class="breadcrumbs" aria-label="Ruta de navegación"><a :href="withBase('/')">Inicio</a><span aria-hidden="true">/</span><span>{{ section }}</span><span aria-hidden="true">/</span><span aria-current="page">{{ page.title }}</span></nav></template>
