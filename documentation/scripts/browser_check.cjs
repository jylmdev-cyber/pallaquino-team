/* Optional real-browser QA. Requires Playwright externally, no production dependency. */
const fs = require('node:fs/promises')
const path = require('node:path')
const { chromium } = require('playwright')

async function main() {
  const target = process.env.PORTAL_URL || 'http://localhost:4173/pallaquino-team/'
  const parsed = new URL(target)
  if (!['localhost','127.0.0.1'].includes(parsed.hostname)) throw new Error('QA local requiere localhost')
  const output = path.resolve(process.env.PORTAL_QA_OUTPUT || 'documentation/reports/browser')
  await fs.mkdir(output, { recursive: true })
  const browser = await chromium.launch({ headless: true, ...(process.platform === 'win32' ? {channel: 'msedge'} : {}) })
  const context = await browser.newContext({ viewport: {width:1440,height:1000}, reducedMotion: 'reduce' })
  const page = await context.newPage()
  const errors=[], failed=[]
  page.on('pageerror',error=>errors.push(error.message))
  page.on('response',response=>{if(response.status()>=400) failed.push({url:response.url(),status:response.status()})})
  const check=(value,message)=>{if(!value) throw new Error(message)}
  const response=await page.goto(target,{waitUntil:'networkidle'})
  check(response.status()===200,'Inicio no devuelve 200')
  await page.getByRole('heading',{level:1}).waitFor()
  check(await page.locator('html').getAttribute('lang')==='es-PE','Idioma incorrecto')
  await page.screenshot({path:path.join(output,'desktop-light.png'),fullPage:true})
  const switcher=page.getByRole('switch').first()
  const before=await page.locator('html').getAttribute('class')
  await switcher.click()
  check((await page.locator('html').getAttribute('class'))!==before,'El cambio de tema no funciona')
  await page.screenshot({path:path.join(output,'desktop-dark.png'),fullPage:true})
  await page.getByRole('button',{name:'Buscar documentación',exact:true}).click()
  await page.locator('.VPLocalSearchBox input').fill('checkpoint')
  await page.locator('.VPLocalSearchBox .result').first().waitFor({timeout:20000})
  const searchResults=await page.locator('.VPLocalSearchBox .result').count()
  await page.keyboard.press('Escape')
  await page.goto(target+'architecture/overview.html',{waitUntil:'networkidle'})
  await page.locator('.diagram svg').first().waitFor({timeout:30000})
  await page.waitForFunction(()=>document.querySelectorAll('.diagram svg').length===3)
  check(await page.locator('.diagram [role="alert"]').count()===0,'Error de renderizado Mermaid')
  await page.getByRole('button',{name:'Ampliar diagrama',exact:true}).first().click()
  await page.screenshot({path:path.join(output,'architecture.png'),fullPage:true})
  // Every generated Mermaid page is exercised, including sector templates.
  const site=path.resolve('documentation/portal/.vitepress/dist')
  const diagramPages=[]
  async function walk(folder) {
    for(const item of await fs.readdir(folder,{withFileTypes:true})) {
      const file=path.join(folder,item.name)
      if(item.isDirectory() && item.name!=='assets') await walk(file)
      else if(item.name.endsWith('.html') && (await fs.readFile(file,'utf8')).includes('diagram-scroll')) diagramPages.push(file)
    }
  }
  await walk(site)
  let diagrams=0
  for(const file of diagramPages) {
    const relative=path.relative(site,file).split(path.sep).join('/')
    await page.goto(target+relative,{waitUntil:'networkidle'})
    await page.waitForFunction(()=>[...document.querySelectorAll('.diagram')].every(d=>d.querySelector('svg')||d.querySelector('[role="alert"]')),{timeout:30000})
    check(await page.locator('.diagram [role="alert"]').count()===0,'Mermaid inválido: '+relative)
    diagrams+=await page.locator('.diagram svg').count()
  }
  await page.setViewportSize({width:390,height:844})
  await page.goto(target,{waitUntil:'networkidle'})
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Overflow horizontal móvil en inicio')
  await page.screenshot({path:path.join(output,'mobile.png'),fullPage:true})
  await page.locator('.VPNavBarHamburger').click()
  check(await page.locator('.VPNavScreen').isVisible(),'Menú móvil no abre')
  await page.goto(target+'getting-started/install.html',{waitUntil:'networkidle'})
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Overflow horizontal móvil en guía')
  await page.locator('.VPLocalNav .menu').click()
  check(await page.locator('.VPSidebar.open').isVisible(),'Navegación lateral móvil no abre')
  await page.keyboard.press('Escape')
  await page.keyboard.press('Tab')
  check(await page.evaluate(()=>document.activeElement!==document.body),'No hay foco de teclado')
  check(errors.length===0,'Errores JavaScript: '+errors.join('; '))
  check(failed.length===0,'Respuestas fallidas: '+JSON.stringify(failed))
  const result={passed:true,url:target,browser:'Chromium/Edge headless',searchResults,diagramPages:diagramPages.length,diagrams,
    checks:['inicio HTTP','tema claro/oscuro','búsqueda local','Mermaid en todas las páginas','zoom','móvil 390px','menú móvil','sidebar móvil','foco de teclado','sin errores JS o HTTP'],
    accessibility:'Comprobaciones básicas; no certificación WCAG.',deployed:false}
  await fs.writeFile(path.join(output,'result.json'),JSON.stringify(result,null,2)+'\n')
  await browser.close()
  console.log(JSON.stringify(result,null,2))
}
main().catch(error=>{console.error(error);process.exit(1)})
