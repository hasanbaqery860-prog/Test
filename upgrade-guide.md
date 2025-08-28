# Zitadel Upgrade Guide: v2.42.0 to v2.55.1+

This guide helps you upgrade Zitadel from v2.42.0 to v2.55.1 or later to enable HTTP SMS provider support.

## Why Upgrade?

### v2.42.0 Limitations
- Only Twilio SMS provider supported
- No HTTP/webhook SMS provider support
- Limited customization options

### v2.55.1+ Benefits
- Native HTTP SMS provider support
- Multiple SMS provider integrations
- Custom webhook endpoints
- Better flexibility and control

## Pre-Upgrade Checklist

- [ ] **Backup your Zitadel instance**
  ```bash
  # For PostgreSQL
  pg_dump -h localhost -U zitadel -d zitadel > zitadel_backup_$(date +%Y%m%d).sql
  
  # For CockroachDB
  cockroach dump zitadel --insecure > zitadel_backup_$(date +%Y%m%d).sql
  ```

- [ ] **Document current configuration**
  ```bash
  # Save current environment variables
  docker inspect zitadel | jq '.[0].Config.Env' > zitadel_env_backup.json
  
  # Save current config files
  cp -r /path/to/zitadel/config ./zitadel_config_backup/
  ```

- [ ] **Check compatibility**
  - Review [Zitadel release notes](https://github.com/zitadel/zitadel/releases)
  - Check for breaking changes between versions
  - Verify database migration requirements

- [ ] **Plan downtime window**
  - Notify users about maintenance
  - Schedule during low-traffic period

## Upgrade Steps

### Step 1: Stop Current Instance

```bash
# Docker Compose
docker-compose down

# Docker
docker stop zitadel

# Kubernetes
kubectl scale deployment zitadel --replicas=0
```

### Step 2: Update Zitadel Version

#### Docker Compose
```yaml
# docker-compose.yml
services:
  zitadel:
    image: ghcr.io/zitadel/zitadel:v2.55.1  # Update from v2.42.0
```

#### Kubernetes
```yaml
# deployment.yaml
spec:
  containers:
  - name: zitadel
    image: ghcr.io/zitadel/zitadel:v2.55.1  # Update from v2.42.0
```

### Step 3: Run Database Migrations

Zitadel usually handles migrations automatically, but verify:

```bash
# Check migration status
docker run --rm \
  -e DATABASE_URL="postgres://user:pass@host:5432/zitadel" \
  ghcr.io/zitadel/zitadel:v2.55.1 \
  migrate status

# Run migrations if needed
docker run --rm \
  -e DATABASE_URL="postgres://user:pass@host:5432/zitadel" \
  ghcr.io/zitadel/zitadel:v2.55.1 \
  migrate up
```

### Step 4: Start Updated Instance

```bash
# Docker Compose
docker-compose up -d

# Docker
docker start zitadel

# Kubernetes
kubectl scale deployment zitadel --replicas=1
```

### Step 5: Verify Upgrade

```bash
# Check version
curl https://your-zitadel-domain.com/admin/v1/healthz

# Check logs
docker logs zitadel | tail -50

# Test login
curl -I https://your-zitadel-domain.com
```

## Post-Upgrade: Configure HTTP SMS Provider

### 1. Create HTTP SMS Provider

```bash
curl -L 'https://$ZITADEL_DOMAIN/admin/v1/sms/http' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -H 'Authorization: Bearer $TOKEN' \
  -d '{
    "endpoint": "https://your-webhook.com/send",
    "description": "Custom HTTP SMS Provider"
  }'
```

### 2. Activate Provider

```bash
curl -L 'https://$ZITADEL_DOMAIN/admin/v1/sms/$PROVIDER_ID/_activate' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -H 'Authorization: Bearer $TOKEN' \
  -d '{}'
```

### 3. Test SMS Functionality

Send a test SMS to verify the configuration works correctly.

## Rollback Plan

If issues occur, rollback to v2.42.0:

### 1. Stop Current Instance
```bash
docker-compose down
```

### 2. Restore Database Backup
```bash
# PostgreSQL
psql -h localhost -U zitadel -d zitadel < zitadel_backup_20240101.sql

# CockroachDB
cockroach sql --insecure < zitadel_backup_20240101.sql
```

### 3. Revert to v2.42.0
```yaml
# docker-compose.yml
services:
  zitadel:
    image: ghcr.io/zitadel/zitadel:v2.42.0  # Revert version
```

### 4. Start Previous Version
```bash
docker-compose up -d
```

## Migration from Twilio Proxy to Native HTTP

If you were using the Twilio proxy workaround in v2.42.0:

1. **Deploy your webhook server** (use the provided `sms-webhook-example.py`)
2. **Create HTTP SMS provider** in Zitadel v2.55.1+
3. **Update configuration** to point to your webhook
4. **Test thoroughly** before removing the proxy
5. **Decommission the Twilio proxy**

## Troubleshooting

### Common Issues

1. **"Method not allowed" error**
   - Ensure you're on v2.55.1 or later
   - Check API endpoint URL is correct

2. **Database migration fails**
   - Check database connectivity
   - Verify database user permissions
   - Review migration logs

3. **SMS not sending after upgrade**
   - Verify provider configuration
   - Check webhook connectivity
   - Review Zitadel logs

### Getting Help

- [Zitadel Documentation](https://zitadel.com/docs)
- [GitHub Issues](https://github.com/zitadel/zitadel/issues)
- [Community Forum](https://github.com/zitadel/zitadel/discussions)

## Version Comparison

| Feature | v2.42.0 | v2.55.1+ |
|---------|---------|----------|
| Twilio SMS | ✅ | ✅ |
| HTTP SMS Providers | ❌ | ✅ |
| Webhook Support | ❌ | ✅ |
| Custom SMS Templates | Limited | Enhanced |
| Provider Management API | ❌ | ✅ |

## Best Practices

1. **Always backup before upgrading**
2. **Test in staging environment first**
3. **Monitor logs during and after upgrade**
4. **Have a rollback plan ready**
5. **Document any custom configurations**

## Conclusion

Upgrading from v2.42.0 to v2.55.1+ enables powerful SMS provider flexibility. While the upgrade process is generally smooth, proper planning and testing ensure a successful migration.