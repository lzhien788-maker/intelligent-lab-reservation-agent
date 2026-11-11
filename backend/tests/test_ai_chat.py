"""
AI 对话接口 /api/ai/chat 连通性测试
------------------------------------------------
前置：后端服务已启动（默认 http://127.0.0.1:8000）
运行：
    cd backend
    ./.venv/Scripts/python.exe tests/test_ai_chat.py
    # 换端口： ./.venv/Scripts/python.exe tests/test_ai_chat.py http://127.0.0.1:8012
说明：会真实调用一次大模型（消耗少量 token），并把 return 内容打印出来。
"""
import sys
import os
import json
import urllib.request
import urllib.error

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8000"
PASS, FAIL = [], []


def check(ok, msg):
    (PASS if ok else FAIL).append(msg)
    print(("  [PASS] " if ok else "  [FAIL] ") + msg)


def post(body, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(
        BASE + "/api/ai/chat",
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw}
    except Exception as e:
        return None, {"raw": f"{type(e).__name__}: {e}"}


def main():
    try:
        from app.database import SessionLocal
        from app.models.user import User
        from app.utils.jwt import create_access_token
    except Exception as e:
        print("导入项目模块失败（是不是依赖没装/虚拟环境没激活？）：", e)
        sys.exit(1)

    db = SessionLocal()
    user = db.query(User).filter(User.status == 1).first()
    db.close()
    if not user:
        print("数据库里没有可用用户，先注册一个再测")
        sys.exit(1)
    token = create_access_token(user.id)
    print(f"目标地址：{BASE}")
    print(f"测试账号：id={user.id} username={user.username} role={user.role}\n")

    # 1 正常单轮
    print("----- 1) 正常单轮对话 -----")
    status, body = post({"messages": [{"role": "user", "content": "你好，预约实验室要走什么流程？"}]}, token)
    print("  HTTP", status, "->", json.dumps(body, ensure_ascii=False)[:300])
    check(status == 200 and body.get("code") == 200, "接口返回 200")
    data = body.get("data") or {}
    check(data.get("role") == "assistant", "返回角色是 assistant")
    check(bool((data.get("content") or "").strip()), "返回内容非空")
    check("预约" in (data.get("content") or ""), "回答没有跑题（提到了预约）")

    # 2 多轮历史
    print("\n----- 2) 多轮历史 -----")
    status, body = post({"messages": [
        {"role": "user", "content": "预约需要审核吗？"},
        {"role": "assistant", "content": "需要，提交后是待审核状态。"},
        {"role": "user", "content": "那我可以在哪里看状态？"},
    ]}, token)
    print("  HTTP", status, "->", json.dumps(body, ensure_ascii=False)[:300])
    check(status == 200 and (body.get("data") or {}).get("content"), "多轮对话正常返回")

    # 3 空 messages
    print("\n----- 3) messages 为空（期望业务错误） -----")
    status, body = post({"messages": []}, token)
    print("  HTTP", status, "->", json.dumps(body, ensure_ascii=False)[:200])
    check(body.get("code") == 500 and "对话内容为空" in body.get("message", ""), "空数组被拦截并提示")

    # 4 全空白内容
    print("\n----- 4) 内容全空白（期望业务错误） -----")
    status, body = post({"messages": [{"role": "user", "content": "   "}]}, token)
    print("  HTTP", status, "->", json.dumps(body, ensure_ascii=False)[:200])
    check(body.get("code") == 500, "空白内容被拦截")

    # 5 无 token
    print("\n----- 5) 不带 token（期望 401） -----")
    status, body = post({"messages": [{"role": "user", "content": "你好"}]})
    print("  HTTP", status, "->", json.dumps(body, ensure_ascii=False)[:200])
    check(status == 401, "鉴权生效，未登录访问被拒")

    # 6 参数缺失
    print("\n----- 6) 缺 messages 字段（期望 422） -----")
    status, body = post({"msg": "你好"}, token)
    print("  HTTP", status, "->", json.dumps(body, ensure_ascii=False)[:200])
    check(status == 422, "参数校验生效")

    print(f"\n===== 汇总：通过 {len(PASS)}，失败 {len(FAIL)} =====")
    for f in FAIL:
        print("  失败项：", f)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
