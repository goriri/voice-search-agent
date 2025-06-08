const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const path = require('path');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Serve static files from the 'static' directory
app.use(express.static(path.join(__dirname, 'static')));

// WebSocket connection handling
wss.on('connection', (ws) => {
    console.log('New WebSocket connection');

    ws.on('message', (message) => {
        try {
            const data = JSON.parse(message);
            // Forward the message to your voice search agent
            // This is where you'd integrate with the BedrockStreamManager
            console.log('Received:', data);
        } catch (error) {
            console.error('Error processing message:', error);
        }
    });

    ws.on('close', () => {
        console.log('Client disconnected');
    });
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'healthy' });
});

const PORT = process.env.PORT || 4000;
const WS_PORT = process.env.WS_PORT || 8081;

server.listen(PORT, () => {
    console.log(`HTTP Server running on port ${PORT}`);
});