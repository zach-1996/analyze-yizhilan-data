# 一枝兰数据分析 Skill

通过已连接的一枝兰或九枝兰 MCP，将自然语言问题转换为只读查询，并输出有数据证据的投放与招生分析。

## 功能

- 广告投放、招生转化、学校与渠道表现、素材和定制报表分析。
- 指标业务语义映射，区分招生人数、招生点数、报名量和线索。
- 公历同比、显式环比、农历同比及相对日期计算。
- 地域归属核验、完整分页、数据完整性检查和异常分析。
- 用户确认后的本机 MCP 绑定与指纹校验。

## 安装

将本仓库下载后，把包含 `SKILL.md` 的整个目录命名为 `analyze-yizhilan-data`，放到本机的 `$CODEX_HOME/skills/` 下。未设置 `CODEX_HOME` 时，使用用户目录下的 `.codex/skills/`。

重新打开 Codex 会话以加载技能。使用前需要已连接且有访问权限的一枝兰或九枝兰 MCP；本仓库不提供数据源账号、连接地址或访问凭据。首次分析时按技能提示确认数据源。

## 使用示例

```text
使用 $analyze-yizhilan-data 分析一枝兰 2026 年 8 月各学校的招生人数，并与去年同期比较。
```

```text
使用 $analyze-yizhilan-data 分析九枝兰 2026 年 8 月各渠道的投放效果，说明数据口径和完整性。
```

## 文件结构

```text
SKILL.md
agents/openai.yaml
references/analysis-and-reporting.md
references/business-semantics.md
references/tool-routing.md
scripts/compare_dates.py
scripts/mcp_binding.py
```

两个辅助脚本使用 Python 3.10 或更高版本，无第三方 Python 依赖。可通过 `python scripts/compare_dates.py --help` 和 `python scripts/mcp_binding.py --help` 查看用法。

本机 MCP 绑定保存于 `$CODEX_HOME/state/analyze-yizhilan-data/`，不属于共享技能；不要将绑定状态、凭据或业务查询结果提交到仓库。

## 第三方声明

`scripts/compare_dates.py` 的农历换算表和算法改编自 wolfhong/LunarCalendar，文件内保留了原 MIT 许可证和版权声明。该声明适用于相应第三方代码，不代表整个仓库被另行授予相同许可证。
