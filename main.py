import os
import time
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from audit import audit_logger
from auth import rbac
from rag import get_retrieval_chain

# 解决部分 Windows 环境下 OpenMP 重复加载导致的报错
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(
    title="基于 RAG 的企业内部制度问答系统",
    description="毕业设计演示系统",
    version="1.0",
)

security = HTTPBearer()


class Query(BaseModel):
    input: str
    detailed: bool


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌。"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    """解析当前请求中的用户身份。"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    return TokenData(username=username)


@app.post("/login", response_model=Token, summary="用户登录")
def login(login_data: LoginRequest):
    """登录并返回 Bearer Token。"""
    if not rbac.authenticate(login_data.username, login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": login_data.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/question", summary="知识库问答")
def answer_question(
    query: Query,
    current_user: TokenData = Depends(get_current_user),
):
    """基于知识库回答用户问题。"""
    start_time = time.time()

    try:
        chain = get_retrieval_chain(username=current_user.username)
        output = chain.invoke({"input": query.input})

        execution_time = time.time() - start_time
        audit_logger.log_query(
            username=current_user.username,
            query=query.input,
            response=output["answer"],
            status="success",
            execution_time=execution_time,
        )

        if query.detailed:
            return output
        return output["answer"]
    except Exception as exc:
        import traceback

        error_traceback = traceback.format_exc()
        print(f"Error in answer_question: {error_traceback}")

        execution_time = time.time() - start_time
        audit_logger.log_query(
            username=current_user.username,
            query=query.input,
            response=str(exc),
            status="failed",
            execution_time=execution_time,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your request: {exc}",
        ) from exc


@app.get("/", response_class=HTMLResponse, summary="系统首页")
def home():
    return """
    <html>
    <head>
        <meta charset="utf-8" />
        <title>企业内部制度问答系统</title>
    </head>
    <body>
        <h1>基于 RAG 的企业内部制度问答系统</h1>
        <p>毕业设计演示系统</p>
        <p>接口文档地址：</p>
        <a href="/docs">进入接口文档页面</a>
        <p>使用说明：</p>
        <ul>
            <li>1. 先调用 /login 获取访问令牌</li>
            <li>2. 在 /question 接口中使用 Bearer Token 进行认证</li>
            <li>3. 发送问题后即可获得知识库回答</li>
        </ul>
    </body>
    </html>
    """


@app.get("/logs", summary="获取审计日志")
def get_audit_logs(
    limit: int = 100,
    current_user: TokenData = Depends(get_current_user),
):
    """仅管理员和 HR 可查看审计日志。"""
    if not rbac.has_permission(current_user.username, "write_logs"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access audit logs",
        )
    return audit_logger.get_logs(limit=limit)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
