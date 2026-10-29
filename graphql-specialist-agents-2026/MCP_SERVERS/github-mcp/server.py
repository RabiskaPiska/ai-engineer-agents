"""github-mcp — reference MCP server exposing GitHub REST read operations.

Tools:
    get_repo(owner, repo)                     -> repo metadata dict
    get_file_contents(owner, repo, path)      -> file metadata + decoded content
    search_repositories(query)                -> repository search results

Auth: GitHub token is read ONLY from the ``GH_TOKEN`` environment variable
(never a literal). The token is optional: unauthenticated requests work but
are heavily rate-limited by GitHub.

Errors are returned as friendly dicts ({"error": ..., "status": ...}) instead
of raising, so an MCP client always gets structured JSON back.
"""

import base64
import os
from typing import Any

import httpx

try:  # mcp 1.x (SPEC baseline)
    from mcp.server.fastmcp import FastMCP
except ImportError:  # mcp 2.x renamed FastMCP -> MCPServer
    from mcp.server.mcpserver import MCPServer as FastMCP

mcp = FastMCP("github-mcp")

_GITHUB_API = "https://api.github.com"


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "github-mcp (GraphQL Specialist Agent Pack)",
    }
    token = os.environ.get("GH_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _friendly_http_error(action: str, response: httpx.Response) -> dict[str, Any]:
    """Map a GitHub REST error response to a friendly, honest dict."""
    hints = {
        401: "GH_TOKEN is set but rejected — check the token value/expiry.",
        403: "Rate limited or forbidden. With no GH_TOKEN, GitHub allows only "
        "~60 requests/hour per IP; set GH_TOKEN to raise the limit.",
        404: "Not found — check owner/repo/path spelling and token scopes "
        "(private repos need a token with repo access).",
        422: "GitHub rejected the request parameters as invalid.",
    }
    try:
        detail = response.json().get("message", "")
    except ValueError:
        detail = response.text[:300]
    return {
        "error": f"GitHub API returned HTTP {response.status_code} while {action}.",
        "status": response.status_code,
        "detail": detail,
        "hint": hints.get(response.status_code),
    }


@mcp.tool()
def get_repo(owner: str, repo: str) -> dict[str, Any]:
    """Fetch metadata for a GitHub repository (GET /repos/{owner}/{repo}).

    Returns the repository JSON (name, description, stars, forks, default
    branch, pushed_at, ...) or a friendly error dict on failure.
    """
    if not owner or not repo:
        return {"error": "Both 'owner' and 'repo' are required."}
    url = f"{_GITHUB_API}/repos/{owner.strip('/')}/{repo.strip('/')}"
    try:
        resp = httpx.get(url, headers=_headers(), timeout=30.0, follow_redirects=True)
    except httpx.HTTPError as exc:
        return {"error": f"Network error while fetching repo {owner}/{repo}: {exc!r}"}
    if resp.status_code != 200:
        return _friendly_http_error(f"fetching repo {owner}/{repo}", resp)
    return resp.json()


@mcp.tool()
def get_file_contents(owner: str, repo: str, path: str) -> dict[str, Any]:
    """Fetch a file's contents from a GitHub repo (GET /repos/{owner}/{repo}/contents/{path}).

    Returns {"path", "name", "sha", "size", "content", "encoding", "html_url"}.
    Text content is base64-decoded into 'content'; binary files report
    encoding 'base64' with the raw base64 payload. Directories return a
    listing under 'items'. Friendly error dict on failure.
    """
    if not owner or not repo or not path:
        return {"error": "'owner', 'repo' and 'path' are all required."}
    path = path.lstrip("/")
    url = f"{_GITHUB_API}/repos/{owner.strip('/')}/{repo.strip('/')}/contents/{path}"
    try:
        resp = httpx.get(url, headers=_headers(), timeout=30.0, follow_redirects=True)
    except httpx.HTTPError as exc:
        return {"error": f"Network error while fetching {owner}/{repo}/{path}: {exc!r}"}
    if resp.status_code != 200:
        return _friendly_http_error(f"fetching {owner}/{repo}/{path}", resp)
    data = resp.json()
    if isinstance(data, list):  # directory listing
        return {
            "path": path,
            "type": "dir",
            "items": [
                {
                    "name": item.get("name"),
                    "type": item.get("type"),
                    "path": item.get("path"),
                    "size": item.get("size"),
                }
                for item in data
            ],
        }
    result = {
        "path": data.get("path"),
        "name": data.get("name"),
        "sha": data.get("sha"),
        "size": data.get("size"),
        "html_url": data.get("html_url"),
        "encoding": data.get("encoding"),
        "content": data.get("content"),
    }
    if data.get("encoding") == "base64" and isinstance(result["content"], str):
        try:
            result["content"] = base64.b64decode(result["content"]).decode("utf-8")
            result["encoding"] = "utf-8"
        except (UnicodeDecodeError, ValueError):
            # binary content: keep the base64 payload, say so honestly
            result["encoding"] = "base64"
    return result


@mcp.tool()
def search_repositories(query: str, per_page: int = 10) -> dict[str, Any]:
    """Search GitHub repositories (GET /search/repositories?q=<query>).

    'query' is a raw GitHub search expression, e.g.
    'graphql security language:python stars:>100'.
    Returns {"total_count", "items": [{name, full_name, html_url, description,
    stargazers_count, pushed_at}]} (capped at 'per_page', max 100).
    """
    if not query.strip():
        return {"error": "'query' must be a non-empty GitHub search expression."}
    per_page = max(1, min(int(per_page), 100))
    try:
        resp = httpx.get(
            f"{_GITHUB_API}/search/repositories",
            headers=_headers(),
            params={"q": query, "per_page": per_page},
            timeout=30.0,
            follow_redirects=True,
        )
    except httpx.HTTPError as exc:
        return {"error": f"Network error while searching repositories: {exc!r}"}
    if resp.status_code != 200:
        return _friendly_http_error("searching repositories", resp)
    data = resp.json()
    return {
        "total_count": data.get("total_count", 0),
        "items": [
            {
                "name": item.get("name"),
                "full_name": item.get("full_name"),
                "html_url": item.get("html_url"),
                "description": item.get("description"),
                "stargazers_count": item.get("stargazers_count"),
                "pushed_at": item.get("pushed_at"),
            }
            for item in data.get("items", [])
        ],
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
