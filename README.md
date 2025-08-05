# High-Performance IP and Browser Detection API

A fast, secure Python Bottle API for detecting client IP addresses, browser information, and device details with API key authentication. Optimized for both web frontend and Android app scenarios.

## Features

- **High Performance**: In-memory caching with configurable TTL
- **Accurate IP Detection**: Supports proxy headers (X-Forwarded-For, Cloudflare, etc.)
- **Comprehensive Browser Detection**: Detailed browser, OS, and device information
- **API Key Authentication**: Secure access control for different client types
- **Client Type Detection**: Automatically detects web browsers, Android apps, mobile browsers
- **Performance Monitoring**: Built-in statistics and cache hit rates
- **Production Ready**: Error handling, logging, and health checks

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the application:**
```bash
python app.py
```

The API will be available at `http://localhost:8080`

## API Endpoints

### 1. Main Detection Endpoint
**URL:** `GET/POST /api/detect`  
**Authentication:** API Key required  
**Description:** Comprehensive client detection with full metadata

**Headers:**
```
X-API-Key: your_api_key
```

**Response:**
```json
{
  "success": true,
  "data": {
    "timestamp": 1703123456.789,
    "ip_address": "192.168.1.100",
    "user_agent_info": {
      "browser": "Chrome",
      "browser_version": "120.0.0.0",
      "os": "Windows",
      "os_version": "10",
      "device": "Other",
      "is_mobile": false,
      "is_tablet": false,
      "is_pc": true,
      "user_agent_string": "Mozilla/5.0..."
    },
    "client_type": "web_browser",
    "api_key_type": "web_frontend_key",
    "request_method": "GET",
    "request_url": "http://localhost:8080/api/detect",
    "request_headers": {...},
    "query_params": {...}
  },
  "timestamp": 1703123456.789
}
```

### 2. Simple Detection Endpoint
**URL:** `GET/POST /api/detect/simple`  
**Authentication:** API Key required  
**Description:** Lightweight endpoint for basic detection

**Response:**
```json
{
  "ip": "192.168.1.100",
  "browser": "Chrome",
  "browser_version": "120.0.0.0",
  "os": "Windows",
  "os_version": "10",
  "device_type": "web_browser",
  "is_mobile": false
}
```

### 3. Performance Statistics
**URL:** `GET /api/stats`  
**Authentication:** API Key required  
**Description:** Get API performance metrics

**Response:**
```json
{
  "performance": {
    "total_requests": 150,
    "cache_hits": 120,
    "cache_misses": 30,
    "cache_hit_rate": "80.00%",
    "uptime_seconds": 3600,
    "requests_per_second": 0.042,
    "cache_size": 45
  },
  "cache_info": {
    "size": 45,
    "keys": ["hash1", "hash2", ...]
  }
}
```

### 4. Health Check
**URL:** `GET /api/health`  
**Authentication:** None required  
**Description:** Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1703123456.789,
  "version": "1.0.0"
}
```

### 5. Clear Cache
**URL:** `POST /api/clear-cache`  
**Authentication:** API Key required  
**Description:** Clear the request cache

## API Keys

The system supports different API keys for different client types:

- **Web Frontend:** `web_1234567890abcdef`
- **Android App:** `android_9876543210fedcba`
- **Other Projects:** `other_abcdef1234567890`

## Usage Examples

### Web Frontend (JavaScript)

```javascript
// Using fetch API
fetch('http://localhost:8080/api/detect/simple', {
  method: 'GET',
  headers: {
    'X-API-Key': 'web_1234567890abcdef',
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => {
  console.log('Client IP:', data.ip);
  console.log('Browser:', data.browser);
  console.log('OS:', data.os);
  console.log('Device Type:', data.device_type);
})
.catch(error => console.error('Error:', error));
```

### Android App (Java/Kotlin)

```java
// Using OkHttp
OkHttpClient client = new OkHttpClient();

Request request = new Request.Builder()
    .url("http://localhost:8080/api/detect/simple")
    .addHeader("X-API-Key", "android_9876543210fedcba")
    .build();

client.newCall(request).enqueue(new Callback() {
    @Override
    public void onResponse(Call call, Response response) throws IOException {
        String responseData = response.body().string();
        // Parse JSON response
        JSONObject json = new JSONObject(responseData);
        String ip = json.getString("ip");
        String browser = json.getString("browser");
        String deviceType = json.getString("device_type");
    }
    
    @Override
    public void onFailure(Call call, IOException e) {
        // Handle error
    }
});
```

### Python Client

```python
import requests

# Simple detection
response = requests.get(
    'http://localhost:8080/api/detect/simple',
    headers={'X-API-Key': 'web_1234567890abcdef'}
)

data = response.json()
print(f"IP: {data['ip']}")
print(f"Browser: {data['browser']}")
print(f"OS: {data['os']}")

# Full detection
response = requests.get(
    'http://localhost:8080/api/detect',
    headers={'X-API-Key': 'web_1234567890abcdef'}
)

data = response.json()
print(f"Full metadata: {data['data']}")
```

## Performance Optimizations

1. **Caching Strategy**: In-memory cache with MD5 hash keys
2. **Efficient IP Detection**: Checks multiple proxy headers in order
3. **User Agent Parsing**: Uses optimized `user-agents` library
4. **Minimal Dependencies**: Only essential packages included
5. **Async Ready**: Can be easily adapted for async operations

## Production Considerations

1. **Use Redis**: Replace in-memory cache with Redis for distributed deployments
2. **Rate Limiting**: Implement rate limiting per API key
3. **HTTPS**: Always use HTTPS in production
4. **Load Balancing**: Use multiple instances behind a load balancer
5. **Monitoring**: Add application monitoring (Prometheus, etc.)
6. **Logging**: Configure structured logging for better observability

## Security Features

- API key authentication for all endpoints
- IP validation and sanitization
- Error handling without information leakage
- Secure headers handling
- Input validation and sanitization

## Error Codes

- `401`: API key required
- `403`: Invalid API key
- `404`: Endpoint not found
- `500`: Internal server error

## Performance Metrics

The API tracks:
- Total requests
- Cache hit/miss rates
- Requests per second
- Uptime
- Cache size

## License

MIT License - feel free to use in your projects.