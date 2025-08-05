# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Option 1: Docker (Recommended)

1. **Clone and deploy:**
```bash
git clone <your-repo>
cd <your-repo>
./deploy.sh
```

2. **Test the API:**
```bash
curl -H "X-API-Key: web_1234567890abcdef" http://localhost:8080/api/detect/simple
```

### Option 2: Local Development

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the API:**
```bash
python app.py
```

3. **Test the API:**
```bash
curl -H "X-API-Key: web_1234567890abcdef" http://localhost:8080/api/detect/simple
```

## 📋 API Endpoints

### Quick Detection
```bash
curl -H "X-API-Key: web_1234567890abcdef" \
     http://localhost:8080/api/detect/simple
```

### Full Detection
```bash
curl -H "X-API-Key: web_1234567890abcdef" \
     http://localhost:8080/api/detect
```

### Health Check
```bash
curl http://localhost:8080/api/health
```

## 🔑 API Keys

| Client Type | API Key |
|-------------|---------|
| Web Frontend | `web_1234567890abcdef` |
| Android App | `android_9876543210fedcba` |
| Other Projects | `other_abcdef1234567890` |

## 📱 Usage Examples

### JavaScript (Web Frontend)
```javascript
fetch('http://localhost:8080/api/detect/simple', {
  headers: {
    'X-API-Key': 'web_1234567890abcdef'
  }
})
.then(response => response.json())
.then(data => {
  console.log('IP:', data.ip);
  console.log('Browser:', data.browser);
  console.log('OS:', data.os);
});
```

### Android (Java/Kotlin)
```java
OkHttpClient client = new OkHttpClient();
Request request = new Request.Builder()
    .url("http://localhost:8080/api/detect/simple")
    .addHeader("X-API-Key", "android_9876543210fedcba")
    .build();

client.newCall(request).enqueue(new Callback() {
    @Override
    public void onResponse(Call call, Response response) throws IOException {
        // Handle response
    }
});
```

### Python
```python
import requests

response = requests.get(
    'http://localhost:8080/api/detect/simple',
    headers={'X-API-Key': 'web_1234567890abcdef'}
)

data = response.json()
print(f"IP: {data['ip']}")
print(f"Browser: {data['browser']}")
```

## 🧪 Run Tests

```bash
python test_api.py
```

## 📊 Monitor Performance

```bash
curl -H "X-API-Key: web_1234567890abcdef" \
     http://localhost:8080/api/stats
```

## 🛠️ Management

### Docker Commands
```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Update and restart
docker-compose up -d --build
```

### Environment Variables
```bash
# Development
export ENVIRONMENT=development
export API_DEBUG=true

# Production
export ENVIRONMENT=production
export REDIS_ENABLED=true
export RATE_LIMIT_ENABLED=true
```

## 🚨 Troubleshooting

### API not responding
```bash
# Check if service is running
docker-compose ps

# Check logs
docker-compose logs api

# Check health
curl http://localhost:8080/api/health
```

### Permission denied
```bash
# Make deploy script executable
chmod +x deploy.sh
```

### Port already in use
```bash
# Stop existing services
docker-compose down

# Or change port in docker-compose.yml
```

## 📈 Performance Tips

1. **Use caching**: The API automatically caches results
2. **Use simple endpoint**: `/api/detect/simple` for basic needs
3. **Monitor stats**: Check `/api/stats` regularly
4. **Use Redis**: For production deployments

## 🔒 Security

1. **Change API keys**: Update in `config.py` or environment variables
2. **Use HTTPS**: In production
3. **Rate limiting**: Enabled by default
4. **Input validation**: All inputs are validated

## 📞 Support

- **Documentation**: See `README.md`
- **Performance**: See `PERFORMANCE.md`
- **Tests**: Run `python test_api.py`
- **Issues**: Check logs with `docker-compose logs`

---

**🎯 You're ready to go!** Your high-performance IP and browser detection API is now running and ready to handle requests from your web frontend and Android app.