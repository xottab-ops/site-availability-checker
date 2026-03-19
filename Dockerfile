FROM python:3.13-slim

WORKDIR /app

# Системные зависимости для Playwright + Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Установка uv
RUN pip install --no-cache-dir uv

# Копируем файлы зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости проекта (без dev)
RUN uv sync --frozen --no-dev

# Устанавливаем Chromium вместе со всеми системными зависимостями
RUN uv run playwright install --with-deps chromium

# Копируем исходный код
COPY . .

# Создаём директории для логов и скриншотов
RUN mkdir -p logs screenshots

CMD ["uv", "run", "python", "main.py"]
