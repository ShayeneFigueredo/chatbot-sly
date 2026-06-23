// Service Worker — Maya Sly Design PWA
// Cache para acesso offline e carregamento instantaneo

const CACHE = 'maya-v2'

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => {
      return cache.addAll([
        '/painel/',
        '/painel/manifest.json',
      ])
    })
  )
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    })
  )
  self.clients.claim()
})

self.addEventListener('fetch', (event) => {
  // So cacheia GET requests
  if (event.request.method !== 'GET') return

  event.respondWith(
    caches.match(event.request).then((cached) => {
      // Tenta rede primeiro, fallback pro cache
      return fetch(event.request)
        .then((response) => {
          // Nao cacheia APIs (dados dinamicos)
          if (
            response.ok &&
            !event.request.url.includes('/painel/dados') &&
            !event.request.url.includes('/painel/mes') &&
            !event.request.url.includes('/painel/faturamento') &&
            !event.request.url.includes('/painel/hoje')
          ) {
            const clone = response.clone()
            caches.open(CACHE).then((cache) => {
              cache.put(event.request, clone)
            })
          }
          return response
        })
        .catch(() => {
          // Offline: serve do cache
          return cached || new Response('Offline — conecte-se a internet para carregar os dados')
        })
    })
  )
})
