const express = require('express');
const httpProxy = require('http-proxy');
const path = require('path');

const app = express();
const port = 3000;
const backendURL = 'http://localhost:8000';

// Create proxy server
const proxy = httpProxy.createProxyServer({
    target: backendURL,
    ws: true,
    changeOrigin: true,
    secure: false,
    ignorePath: false,
    xfwd: true,  // Forward the original host header
    protocolRewrite: 'http'  // Rewrite HTTPS to HTTP for backend
});

// Add CORS and security headers
app.use((req, res, next) => {
    // CORS headers
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
    
    // Security headers
    res.header('Content-Security-Policy', "default-src * 'unsafe-inline' 'unsafe-eval'; img-src * data: blob:; font-src * data:;");
    res.header('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
    
    // Handle OPTIONS request
    if (req.method === 'OPTIONS') {
        res.sendStatus(200);
        return;
    }
    next();
});

// Log proxy errors
proxy.on('error', (err, req, res) => {
    console.error('Proxy error:', err);
    if (res && res.writeHead) {
        res.writeHead(502);
        res.end('Proxy error: ' + err.message);
    } else {
        console.error('WebSocket proxy error:', err.message);
    }
});

// Log successful proxy requests
proxy.on('proxyReq', (proxyReq, req, res) => {
    const fullPath = req.originalUrl || req.url;
    console.log(`Proxying ${req.method} ${fullPath} to ${backendURL}${fullPath}`);
});

// Basic request logging
app.use((req, res, next) => {
    console.log(`${new Date().toISOString()} ${req.method} ${req.url}`);
    next();
});

// Handle all API requests
app.use((req, res, next) => {
    // Check if this is an API request (either directly or via ngrok)
    if (req.url.startsWith('/api') || 
        req.url.startsWith('/station') || 
        req.url.startsWith('/test') ||
        req.url.includes('ngrok-free.app/api') ||
        req.url.includes('ngrok-free.app/station') ||
        req.url.includes('ngrok-free.app/test')) {
        
        // Clean up the URL if it contains the ngrok domain
        if (req.url.includes('ngrok-free.app')) {
            req.url = req.url.substring(req.url.indexOf('/', 8));
        }
        
        // Add /api prefix if needed
        if (req.url.startsWith('/station') || req.url.startsWith('/test')) {
            req.url = '/api' + req.url;
        }
        
        console.log('API request:', req.method, req.url);
        proxy.web(req, res);
    } else {
        next();
    }
});

// Serve static files with caching headers
app.use(express.static(path.join(__dirname, 'build'), {
    maxAge: '1y',
    setHeaders: (res, path) => {
        if (path.endsWith('.html')) {
            res.setHeader('Cache-Control', 'no-cache');
        } else if (path.match(/\.(js|css|woff|woff2|ttf|eot)$/)) {
            res.setHeader('Cache-Control', 'public, max-age=31536000');
        }
    }
}));

// Default route handler for all other requests
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

// Create server
const server = app.listen(port, '0.0.0.0', () => {
    console.log(`Proxy server running on port ${port}`);
    console.log(`Proxying requests to ${backendURL}`);
});

// Handle WebSocket
server.on('upgrade', (req, socket, head) => {
    console.log('WebSocket upgrade request:', req.url);
    try {
        if (req.url.startsWith('/ws')) {
            console.log('Proxying WebSocket connection to backend');
            proxy.ws(req, socket, head);
        }
    } catch (err) {
        console.error('Error in WebSocket upgrade handler:', err);
        socket.end();
    }
});

// Additional WebSocket proxy logging
proxy.on('proxyReqWs', (proxyReq, req, socket, options, head) => {
    console.log('WebSocket proxy request:', req.url);
});

proxy.on('open', (proxySocket) => {
    console.log('WebSocket proxy socket open');
});

proxy.on('close', (res, socket, head) => {
    console.log('WebSocket proxy socket closed');
}); 