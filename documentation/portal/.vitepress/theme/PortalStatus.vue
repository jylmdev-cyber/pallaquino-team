<script setup>
import data from '../generated.json'
import { withBase } from 'vitepress'
</script>
<template>
  <section class="portal-overview" aria-label="Explorar el proyecto">
    <div class="section-kicker">EL PROYECTO, EN CONTEXTO</div>
    <h2>Encuentra tu siguiente paso.</h2>
    <p>Desde la primera instalación hasta una entrega revisada. Guías conectadas al código del proyecto.</p>
    <div class="portal-stats">
      <a :href="withBase('/generated/agents/index.html')"><strong>{{ data.agents }}</strong><span>perfiles de agentes</span><small>Roles, permisos y entregables ↗</small></a>
      <a :href="withBase('/generated/skills/index.html')"><strong>{{ data.skills }}</strong><span>skills operativas</span><small>Instrucciones y restricciones ↗</small></a>
      <a :href="withBase('/generated/examples/index.html')"><strong>{{ data.examples }}</strong><span>referencias por rubro</span><small>Plantillas, sin aplicaciones ficticias ↗</small></a>
    </div>
    <div class="portal-version"><span class="status-dot"></span>Fuentes del software v{{ data.version }} · Portal UDP v1 · Español <a :href="withBase('/changelog/versions.html')">Ver compatibilidad →</a></div>
  </section>
</template>
