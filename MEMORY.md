# AetherVerse Project Memory Index

Last updated: 2026-06-26

## Project Memories

- [Headless Check-in Investigation](.agents/memory/headless-punchcard.md) — Direction 1: Full reverse-engineering, network debugging, and final conclusion (API shut down by Tencent)

## Architecture

- [Architecture](.agents/wiki/Architecture.md) — System topology, ports, and component overview
- [Cloud Server Access & Ops](.agents/wiki/CloudServer.md) — ⭐ 云端服务器 SSH 连接凭据 + Docker 拓扑 + 常用运维命令速查（操作云端先看这）
- [NewAPI Gateway](.agents/wiki/NewAPI.md) — Gateway configuration, database, and administration
- [Local Proxy](.agents/wiki/LocalProxy.md) — Request translation, stream sanitization, keyword replacement, check-in APIs
- [Punchcard](.agents/wiki/Checkin.md) — Automated check-in scripts (GUI + attempted API)

## Raw Sources

- [User Requests](.agents/raw/UserRequests.md) — Chronological history of all user requests
- [Original Proxy Code](.agents/raw/OriginalProxyCode.md) — Notes on the original Node.js backup codebase
- [一键整合功能](.agents/memory/one-click-integration.md) — 账号OAuth登录/粘贴ck_ key→自动写channels表;代码改完未跑通,卡在local_proxy重启后dashboard 404(疑多进程残留),交接重点

## Handoff / 交付日志

- [Patina 风格首页重构](.agents/handoff/HANDOFF_patina_frontend.md) — ⭐ 已通过 Footer JS 注入完成 UI 重构。已实现自包含 Patina 风格落地页（支持多模型展示、快速接入指引、FAQ 折叠和一键复制基址），且不破坏管理员微信自动打卡侧边栏。
- [sui.io 搬运落地页](.agents/memory/aetherverse-landing-sui-port.md) — ⭐ 真搬运 sui.io（官方 CSS/GSAP/Slater/Lenis + 文字改 AetherVerse）。已修 Lenis/Weglot/CSS 挂载/自用模式 bug；卡点：未登录 / 不渲染 Footer
