import { createServer } from 'node:http'
import { createReadStream, statSync } from 'node:fs'
import { join, resolve, normalize } from 'node:path'
import { Readable } from 'node:stream'
import handler from './dist/server/server.js'

const PORT = Number(process.env.PORT ?? 3000)
const HOST = process.env.HOST ?? '0.0.0.0'
const CLIENT_DIR = resolve('dist/client')

const MIME = {
  '.js': 'application/javascript; charset=utf-8',
  '.mjs': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.ico': 'image/x-icon',
  '.webp': 'image/webp',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.map': 'application/json; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8',
}

function tryStaticFile(urlPath) {
  const safe = normalize(urlPath).replace(/^\/+/, '')
  if (safe.startsWith('..')) return null
  const full = join(CLIENT_DIR, safe)
  if (!full.startsWith(CLIENT_DIR)) return null
  try {
    const st = statSync(full)
    if (st.isFile()) return { full, size: st.size }
  } catch {}
  return null
}

function toWebRequest(req) {
  const url = `http://${req.headers.host ?? `${HOST}:${PORT}`}${req.url}`
  const method = req.method ?? 'GET'
  const headers = new Headers()
  for (const [k, v] of Object.entries(req.headers)) {
    if (Array.isArray(v)) v.forEach((vv) => headers.append(k, vv))
    else if (v != null) headers.set(k, v)
  }
  const hasBody = method !== 'GET' && method !== 'HEAD'
  return new Request(url, {
    method,
    headers,
    body: hasBody ? Readable.toWeb(req) : undefined,
    duplex: hasBody ? 'half' : undefined,
  })
}

async function writeWebResponse(response, res) {
  res.statusCode = response.status
  response.headers.forEach((v, k) => res.setHeader(k, v))
  if (!response.body) return res.end()
  const reader = response.body.getReader()
  try {
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      if (!res.write(value)) {
        await new Promise((r) => res.once('drain', r))
      }
    }
  } finally {
    res.end()
  }
}

createServer(async (req, res) => {
  try {
    const path = new URL(req.url ?? '/', `http://${req.headers.host ?? HOST}`).pathname

    if (path === '/health') {
      res.setHeader('content-type', 'text/plain; charset=utf-8')
      return res.end('ok')
    }

    if (req.method === 'GET' || req.method === 'HEAD') {
      const hit = tryStaticFile(path)
      if (hit) {
        const ext = hit.full.slice(hit.full.lastIndexOf('.'))
        res.setHeader('content-type', MIME[ext] ?? 'application/octet-stream')
        res.setHeader('content-length', String(hit.size))
        if (path.startsWith('/assets/') || path.startsWith('/_build/')) {
          res.setHeader('cache-control', 'public, max-age=31536000, immutable')
        }
        if (req.method === 'HEAD') return res.end()
        return createReadStream(hit.full).pipe(res)
      }
    }
    const response = await handler.fetch(toWebRequest(req))
    await writeWebResponse(response, res)
  } catch (err) {
    console.error('[server] request error:', err)
    if (!res.headersSent) res.statusCode = 500
    res.end('Internal Server Error')
  }
}).listen(PORT, HOST, () => {
  console.log(`[server] listening on http://${HOST}:${PORT}`)
})
