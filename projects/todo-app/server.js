const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// In-memory storage
const todos = [];

function sendJSON(res, status, data) {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(data));
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch {
        reject(new Error('Invalid JSON'));
      }
    });
    req.on('error', reject);
  });
}

function matchRoute(method, url) {
  // GET /api/todos
  if (method === 'GET' && url === '/api/todos') return { handler: 'list' };
  // POST /api/todos
  if (method === 'POST' && url === '/api/todos') return { handler: 'create' };
  // PATCH /api/todos/:id
  const patch = url.match(/^\/api\/todos\/(.+)$/);
  if (method === 'PATCH' && patch) return { handler: 'update', id: patch[1] };
  // DELETE /api/todos/:id
  const del = url.match(/^\/api\/todos\/(.+)$/);
  if (method === 'DELETE' && del) return { handler: 'delete', id: del[1] };
  return null;
}

function serveStatic(res, filePath) {
  const fullPath = path.join(__dirname, filePath);
  fs.readFile(fullPath, 'utf-8', (err, data) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Not Found');
      return;
    }
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(data);
  });
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`).pathname;
  const method = req.method;

  // Static file: GET /
  if (method === 'GET' && url === '/') {
    return serveStatic(res, 'index.html');
  }

  // API routes
  const route = matchRoute(method, url);
  if (!route) {
    return sendJSON(res, 404, { error: 'Not Found' });
  }

  try {
    switch (route.handler) {
      case 'list': {
        return sendJSON(res, 200, todos);
      }
      case 'create': {
        const body = await readBody(req);
        if (!body.text || !body.text.trim()) {
          return sendJSON(res, 400, { error: 'text is required' });
        }
        const todo = {
          id: crypto.randomUUID(),
          text: body.text.trim(),
          done: false,
          createdAt: new Date().toISOString(),
        };
        todos.unshift(todo);
        return sendJSON(res, 201, todo);
      }
      case 'update': {
        const todo = todos.find(t => t.id === route.id);
        if (!todo) {
          return sendJSON(res, 404, { error: 'Todo not found' });
        }
        const body = await readBody(req);
        if (typeof body.done !== 'boolean') {
          return sendJSON(res, 400, { error: 'done must be a boolean' });
        }
        todo.done = body.done;
        return sendJSON(res, 200, todo);
      }
      case 'delete': {
        const idx = todos.findIndex(t => t.id === route.id);
        if (idx === -1) {
          return sendJSON(res, 404, { error: 'Todo not found' });
        }
        todos.splice(idx, 1);
        res.writeHead(204);
        return res.end();
      }
    }
  } catch (err) {
    if (err.message === 'Invalid JSON') {
      return sendJSON(res, 400, { error: 'Invalid JSON body' });
    }
    return sendJSON(res, 500, { error: 'Internal Server Error' });
  }
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
