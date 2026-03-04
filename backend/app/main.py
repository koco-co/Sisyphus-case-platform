from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import projects, cases, config, vectors, generation, documents

app = FastAPI(
    title="Sisyphus API",
    description="测试用例生成平台 API",
    version="0.1.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(projects.router)
app.include_router(cases.router)
app.include_router(config.router)
app.include_router(vectors.router)
app.include_router(generation.router)
app.include_router(documents.router)


@app.get("/")
async def root():
    return {
        "message": "Sisyphus 测试用例生成平台 API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
