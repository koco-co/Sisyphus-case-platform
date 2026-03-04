# Sisyphus Backend

测试用例生成平台后端服务。

## 开发环境设置

```bash
# 使用 uv 安装依赖
uv sync

# 复制环境变量
cp .env.example .env

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 运行测试

```bash
uv run pytest
```
