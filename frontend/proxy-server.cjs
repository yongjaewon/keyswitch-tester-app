const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');

const app = express();
const port = 3000; // This will be the single port we expose via ngrok

// Proxy middleware configuration for API requests
const apiProxy = createProxyMiddleware(['/api', '/ws'], {
    target: 'http://localhost:8000',
    changeOrigin: true,
    ws: true, // Enable WebSocket proxy
    pathRewrite: {
        '^/api': '/api', // Keep the /api prefix when forwarding to backend
    }
});

// Use the API proxy middleware
app.use(['/api', '/ws'], apiProxy);

// Proxy all other requests to the Vite dev server
const viteProxy = createProxyMiddleware({
    target: 'http://localhost:5173',
    changeOrigin: true,
    ws: true
});

app.use('/', viteProxy);

// Start the server
app.listen(port, '0.0.0.0', () => {
    console.log(`Proxy server running on port ${port}`);
}); 