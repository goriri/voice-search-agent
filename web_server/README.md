# Voice Search Demo Web Server

This is a Node.js web server that serves the Voice Search Demo application.

## Prerequisites

- Node.js (v14 or higher)
- npm (Node Package Manager)

## Installation

1. Install dependencies:
```bash
npm install
```

## Running the Server

1. Start the server:
```bash
npm start
```

The server will start on:
- HTTP server: http://localhost:4000
- WebSocket server: ws://localhost:8081

## Environment Variables

You can configure the following environment variables:
- `PORT`: HTTP server port (default: 4000)
- `WS_PORT`: WebSocket server port (default: 8081)

Example:
```bash
PORT=5000 WS_PORT=8082 npm start
```