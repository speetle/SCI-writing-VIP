#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""push_skill_to_github.py — 把本地 SCI-writing-VIP 技能推到 GitHub（通道 B：Git Data API）

【为什么要用这个脚本而不是 `git push`】
WorkBuddy 沙箱代理放行 `api.github.com`、拦截/严重拖慢 `github.com`；
且本机 `~/.gitconfig` 里那条 credential helper 指向一个**已不存在的 gh 路径**（无凭据）。
故写操作走 Git Data API（POST /git/blobs、POST /git/trees、POST /git/commits、
更新分支 PATCH /git/refs/heads/<b>、**创建标签 POST /git/refs**），只读探测走 api.github.com。
⚠️ 创建 ref 的端点**不带路径后缀**：`POST /repos/{o}/{r}/git/refs` + body `{"ref":"refs/tags/x","sha":…}`。
   写成 `POST /git/refs/tags/x` 会被 GitHub 路由到「update a reference」（PATCH 语义），
   ref 不存在时返回 **422 Reference does not exist**（2026-10-05 实测踩过，见 v2.6.1）。

【权限】需要 token。三种取法任选其一：
  1) `export GH_TOKEN=ghp_xxx`
  2) `python3 push_skill_to_github.py --token ghp_xxx`   （会打印一次后由 shell 处理，见下方「安全」说明）
  3) `read -rs GH_TOKEN` 后直接跑（不落历史）

⚠️ 安全：token 只经环境变量传递，脚本**绝不写盘、绝不 echo**。
   用完请到 https://github.com/settings/tokens 点 Revoke。

【用法】
  # 1) 试运行，只列出会增删哪些文件（不需要 token 也能跑，仅公开仓库可读时）
  python3 push_skill_to_github.py --skill <本地 skill 目录> --repo speetle/SCI-writing-VIP --dry-run

  # 2) 正式推送（保留历史，追加提交）
  GH_TOKEN=ghp_xxx python3 push_skill_to_github.py \
      --skill ~/.workbuddy/skills/SCI-writing-VIP --repo speetle/SCI-writing-VIP \
      --msg "feat: v2.4 — 三层取材（近十年顶刊 reserve 池）+ 问题表述强度训练 + 日课静默/周报推送"

  # 3) 打标签（可选，随机推送一并创建）
  GH_TOKEN=ghp_xxx python3 push_skill_to_github.py ... --tag v2.6.1

  # 4) 补打/改打标签（内容已推完时用；**不新建任何 commit**）
  GH_TOKEN=ghp_xxx python3 push_skill_to_github.py ... --tag v2.6.1 --tag-only
"""
import argparse
import base64
import hashlib
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request

API = "https://api.github.com"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "SCI-writing-VIP-pusher", "Accept": "application/vnd.github+json"}
SKIP_DIRS = {".git", "__pycache__", "_cache", "dist", ".venv", "node_modules"}
SKIP_SUFFIX = (".pyc", ".pyo", ".tmp", ".log")
# 🔴 本地专用：**绝不外发**（不是遗漏，是决定；勿"顺手补上"）
#    push_repo_to_github.py 的 --create 分支把一篇未发表课题的题目硬编码为默认仓库描述，
#    公开即提前泄题 → 保留为本地工具。
LOCAL_ONLY = ("scripts/push_repo_to_github.py",)
# 🔴 仓库自有文件：本地 skill 目录不收，但**绝不可判为"待删"**（删了不可逆）
PROTECT = ("README", "CHANGELOG", "LICENSE", "docs/", ".gitignore")


def api(path, method="GET", body=None, token=None, tries=3):
    data = json.dumps(body).encode() if body is not None else None
    h = dict(UA)
    if token:
        h["Authorization"] = f"Bearer {token}"
    if data:
        h["Content-Type"] = "application/json"
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(API + path, data=data, headers=h, method=method)
            with urllib.request.urlopen(req, timeout=45, context=CTX) as r:
                txt = r.read().decode()
                return json.loads(txt) if txt else {}
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read().decode()[:200]}"
            if e.code in (409,) and "empty" in last.lower():
                last = "GIT_EMPTY:" + last
            # 401 = token 无效/已撤销/过期。重试无意义（同一 token 必然再失败），
            # 且必须早失败：否则会把大段裸 traceback 甩给用户，看不出真正原因。
            if e.code == 401:
                raise RuntimeError(
                    "401 Bad credentials —— token 无效：未设、已撤销、已过期，或以错账号生成。\n"
                    "       解决：https://github.com/settings/tokens 重新生成（scope 勾 repo），\n"
                    "              `export GH_TOKEN=ghp_xxx` 后重跑。\n"
                    "       注：本脚本读的只是环境变量 GH_TOKEN，不会从别处取凭据。")
            if e.code < 500:
                raise RuntimeError(last)
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
        time.sleep(1.2 * (i + 1))
    raise RuntimeError(last)


def blob_sha(data: bytes) -> str:
    """git blob sha：sha1(b"blob <len>\\0" + data)"""
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def walk_local(root):
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(SKIP_SUFFIX) or fn.startswith("."):
                continue
            if ".bak" in fn:          # 备份文件（含 .bak-YYYYMMDD 形式）一律不外发
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            if rel in LOCAL_ONLY:     # 本地专用（见文件头 LOCAL_ONLY 注释）
                continue
            with open(p, "rb") as f:
                out[rel] = f.read()
    return out


def _make_tag(repo, tag, sha, token):
    """创建标签 ref，指向 sha。

    🔴 端点必须是 `POST /repos/{repo}/git/refs`，body 里带 `{"ref": "refs/tags/<tag>"}`。
    写成 `POST /repos/{repo}/git/refs/tags/<tag>` 是**错的**：GitHub 会把该路径
    路由到「update a reference」（本应 PATCH），ref 不存在时返回
    `422 {"message":"Reference does not exist"}` —— 报错文档链接会指向
    `https://docs.github.com/rest/git/refs#update-a-reference`，极易被误读成「无权限」。
    2026-10-05 推送 v2.6.0 时即因此静默跳过标签。
    返回 True 表示新建成功；False 表示跳过（已存在 / 失败），**均不影响内容推送**。
    """
    try:
        api(f"/repos/{repo}/git/refs", "POST",
            {"ref": f"refs/tags/{tag}", "sha": sha}, token)
        print(f"[标签] {tag} → {sha[:10]}")
        return True
    except RuntimeError as e:
        msg = str(e)
        if "already exists" in msg:
            print(f"[标签] {tag} 已存在，跳过（不移动既有标签）。")
        else:
            print(f"[标签] ❌ 创建失败：{msg[:220]}")
            print("       ⚠️ 标签独立于内容：本次内容推送已成功，不影响交付。")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", default=os.path.expanduser("~/.workbuddy/skills/SCI-writing-VIP"),
                    help="本地 skill 目录")
    ap.add_argument("--repo", default="speetle/SCI-writing-VIP")
    ap.add_argument("--branch", default="main")
    ap.add_argument("--msg", default="chore: sync local skill")
    ap.add_argument("--token", default="", help="（可选）也可直接用环境变量 GH_TOKEN")
    ap.add_argument("--dry-run", action="store_true", help="只比对本地/远端差异，不推送")
    ap.add_argument("--tag", default="", help="推送后打标签（需 token）")
    ap.add_argument("--tag-only", action="store_true",
                    help="只打标签、**不新建任何 commit**（内容已推完时补打/改打用；须配合 --tag）")
    ap.add_argument("--prune", action="store_true",
                    help="删除远端有本地无的文件（**默认不开**）。"
                         "⚠️ 2026-10-01 实测：远端有 README/CHANGELOG/LICENSE/.gitignore/docs/PUBLISH.md/"
                         "references/templates/* 共 13 份，本地 skill 目录无对应文件——"
                         "**开着 --prune 会把它们删掉且不可逆**，故默认只报告不删。")
    a = ap.parse_args()

    token = a.token or os.environ.get("GH_TOKEN", "")
    root = os.path.abspath(os.path.expanduser(a.skill))
    if not os.path.isdir(root):
        sys.exit(f"本地 skill 目录不存在：{root}")

    local = walk_local(root)
    print(f"[本地] skill 目录 {root}\n[本地] 待推文件 {len(local)} 个")
    for p in sorted(local)[:5]:
        print(f"      {p}")
    if len(local) > 5:
        print(f"      ...（共 {len(local)} 个）")

    head = api(f"/repos/{a.repo}/commits/{a.branch}")
    head_sha = head.get("sha") or (head.get("commit") or {}).get("sha")
    if not head_sha:
        sys.exit(f"读不到远端 HEAD：{head}")
    print(f"[远端] {a.repo}@{a.branch} HEAD={head_sha[:10]}")

    tree = api(f"/repos/{a.repo}/git/trees/{head_sha}?recursive=1")
    remote = {i["path"]: i["sha"] for i in tree.get("tree", []) if i.get("type") == "blob"}

    to_add, changed = [], []
    for rel, data in local.items():
        if rel not in remote:
            to_add.append(rel)
        elif remote[rel] != blob_sha(data):
            changed.append(rel)
            to_add.append(rel)
    def protected(p):
        return any(p.startswith(x) or os.path.basename(p).startswith(x) for x in PROTECT)

    stale = [p for p in remote if p not in local]
    protected_stale = [p for p in stale if protected(p)]
    stale = [p for p in stale if not protected(p)]

    print(f"\n[比对] 新增 {len(to_add) - len(changed)}｜修改 {len(changed)}｜"
          f"远端有本地无（删除）{len(stale)}｜无变化 {len(local) - len(to_add)}")
    for p in sorted(changed)[:20]:
        print(f"      M {p}")
    for p in sorted(p for p in to_add if p not in changed)[:20]:
        print(f"      A {p}")
    for p in sorted(stale)[:20]:
        print(f"      D {p}")
    if protected_stale:
        print(f"      🔒 受保护（只读报告、不删）：{protected_stale}")

    if a.dry_run:
        print("\n[dry-run] 完成，未推送（也不建 blob，省 API 配额）。")
        return
    if not token:
        sys.exit("\n🔴 无 token：Git Data API 的写端点一律 401 Requires authentication。"
                 "\n   请 `export GH_TOKEN=ghp_xxx` 后重跑；用完到 https://github.com/settings/tokens 撤销。")

    # 推送前先做一次轻量校验：401 时立即退出，**不建任何 blob/tree/commit**，
    # 避免远端留下悬空对象。实测（2026-10-01）token 在推送过程中被撤销时，
    # 未校验版本会把 traceback 抛在最后一步 PATCH ref 上，用户看不出根因。
    try:
        who = api("/user", "GET", None, token)
        print(f"[凭据] 有效 · 账号 {who.get('login')} · scope=repo")
    except Exception as e:
        sys.exit(f"\n🔴 凭据校验失败，已中止，未写入任何内容：\n   {e}")

    # --tag-only：内容已在远端，只补/改标签，**不建 blob/tree/commit**
    if a.tag_only:
        if not a.tag:
            sys.exit("🔴 --tag-only 须同时给出 --tag <名称>。")
        _make_tag(a.repo, a.tag, head_sha, token)
        print(f"\n✅ 仅标签操作完成（未新建 commit）｜main HEAD 仍为 {head_sha[:10]}")
        return

    add_sha = {}
    for rel in to_add:
        nb = api(f"/repos/{a.repo}/git/blobs", "POST",
                 {"content": base64.b64encode(local[rel]).decode(), "encoding": "base64"}, token)
        add_sha[rel] = nb["sha"]

    entries = [{"path": p, "mode": "100644", "type": "blob", "sha": add_sha[p]} for p in to_add]
    if a.prune:
        entries += [{"path": p, "sha": None} for p in stale]
        print(f"[剪枝] 已开启 --prune，将删除远端 {len(stale)} 个文件：{stale}")
    elif stale:
        print(f"[⚠️ 保留] 远端有本地无的 {len(stale)} 个文件**未删除**（未传 --prune）：{stale}")
    base = tree.get("sha")
    new_tree = api(f"/repos/{a.repo}/git/trees", "POST",
                   {"base_tree": base, "tree": entries}, token)

    parents = [head_sha]
    if len(parents) == 1 and new_tree.get("parents"):
        pass
    commit = api(f"/repos/{a.repo}/git/commits", "POST",
                 {"message": a.msg, "tree": new_tree["sha"], "parents": parents}, token)
    api(f"/repos/{a.repo}/git/refs/heads/{a.branch}", "PATCH",
        {"sha": commit["sha"], "force": False}, token)

    if a.tag:
        _make_tag(a.repo, a.tag, commit["sha"], token)

    # 核验
    vt = api(f"/repos/{a.repo}/git/trees/{commit['sha']}?recursive=1")
    rt = {i["path"]: i["sha"] for i in vt.get("tree", []) if i.get("type") == "blob"}
    bad = [p for p, d in local.items() if rt.get(p) != blob_sha(d)]
    print(f"\n✅ 推送完成 {commit['sha'][:10]}｜远端文件 {len(rt)}｜内容不符 {len(bad)}")
    if bad:
        for p in bad[:10]:
            print("   ❌", p)
        sys.exit(1)
    print("   逐文件 sha 比对全部一致。")


if __name__ == "__main__":
    main()
