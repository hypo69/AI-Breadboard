# Деплоймент

## Локальный деплойment

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка окружения

```bash
cp .env.example .env
# Отредактируйте .env файл
```

### 3. Запуск

```bash
python main.py
```

## Docker деплойment

### 1. Создание Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3000

CMD ["python", "main.py"]
```

### 2. Сборка образа

```bash
docker build -t ai-assistant .
```

### 3. Запуск

```bash
docker run -p 3000:3000 -v $(pwd):/app ai-assistant
```

## Продакшен деплойment

### 1. Настройка nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### 2. Настройка systemd

```bash
sudo nano /etc/systemd/system/ai-assistant.service
```

```ini
[Unit]
Description=ai-assistant Server
After=network.target

[Service]
User=your_user
WorkingDirectory=/path/to/ai-assistant
ExecStart=/path/to/ai-assistant/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ai-assistant
sudo systemctl start ai-assistant
```

## Kubernetes

### 1. deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-assistant
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-assistant
  template:
    metadata:
      labels:
        app: ai-assistant
    spec:
      containers:
      - name: ai-assistant
        image: ai-assistant:latest
        ports:
        - containerPort: 3000
        env:
        - name: GEMINI_API_KEY_NAMES
          valueFrom:
            secretKeyRef:
              name: gemini-secrets
              key: api-key
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: gemini-secrets
              key: jwt-secret
```

### 2. service.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ai-assistant
spec:
  selector:
    app: ai-assistant
  ports:
  - port: 80
    targetPort: 3000
  type: LoadBalancer
```

## CI/CD

### GitHub Actions workflow

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: pip install -r requirements.txt
    
    - name: Run tests
      run: pytest
    
    - name: Deploy
      run: |
        # Your deployment script
```

---

[← Development](development.md) | [← Назад в меню](../index.md)