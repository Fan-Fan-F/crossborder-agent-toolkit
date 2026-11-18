# Cross-Border Ecommerce Agent Toolkit (跨境电商运营智能体工具箱)

> 纯 Python 生产级跨境电商运营智能体可执行工具箱：定价与多 SKU 毛利测算、Listing 平台合规质检与参数溯源、四阶段广告漏斗逆向诊断与 P0/P1/P2 动作决策。  
> Production-grade Python toolkit for cross-border ecommerce operations: pricing & multi-SKU margin analysis, listing compliance & spec traceability, and 4-stage reverse ad funnel diagnostics.

---

## 中文文档 (Chinese)

### 一、功能与原思路的关系

原项目以提示词和文档模板为主，提出将跨境电商日常运营 SOP（Shopee、Mercado Livre、Amazon 等平台）拆解为 Agent 的理念。本项目为 **B 路线（按思路重写）**，保留原项目核心业务洞察，将原本停留在文本提示词层面的经验规则升级为具备严密输入输出校验与确定性算法的工程化 Python 工具箱：

1. **SOP 1: 产品定价与多 SKU 利润测算引擎 (`crossborder_toolkit.pricing`)**
   - **与原思路关系**：原项目依靠提示词让大模型估算定价，容易产生算术幻觉；本项目实现严密的数学反推模型。
   - **核心功能**：
     - 反算建议零售价、保本保底价（Break-even Price）、广告保本 ROAS（$1/\text{毛利率}$）以及税后净利。
     - 计算在保留 15%、10%、5% 等不同净利底线下，允许开具的最大店铺优惠券折让空间。
     - 支持多 SKU 四角色梯度规划（引流款 Traffic、主推款 Hero、高配款 High-End、配件组合款 Bundle），自动校验引流款价格倒挂与毛利过低风险。
     - 严格校验费率边界：费率总和 $\ge 100\%$ 时坚决阻断计算。

2. **SOP 2: Listing 标题与文案合规质检引擎 (`crossborder_toolkit.listing`)**
   - **与原思路关系**：原项目依赖人眼比对或文本自检表；本项目实现基于平台规则的自动化质检。
   - **核心功能**：
     - 精确 Unicode 字符计算（正确识别葡语 `ã`, `ç`, `é` 等重音符号，杜绝平台字符超限被拒）。
     - 支持 Shopee（120 字符）、Mercado Livre（60 字符）、Amazon（200 字符）等各平台硬限制。
     - 前置 20-30 字符高权重搜索词覆盖度评分。
     - 侵权品牌词库（Apple, Xiaomi, Dyson, Nike 等）与夸大宣传词库（melhor do mercado, 100% original 等）自动扫描拦截。
     - **参数一致性溯源校验**：自动提取正文中的功率（W）、电池（Ah/mAh）、速度（km/h）、承重（kg）等物理参数，与商家真实规格表严格对账，防止 AI 虚构夸大参数。

3. **SOP 3: 广告漏斗逆向诊断与动作决策引擎 (`crossborder_toolkit.advertising`)**
   - **与原思路关系**：原项目提出逆向漏斗概念；本项目将其工程化为可直接读取 CSV/JSON 报表的决策引擎。
   - **核心功能**：
     - 严格遵循“曝光 $\to$ 点击（CTR $\ge 3\%$）$\to$ 加购（加购率 $\ge 8\%$）$\to$ 转化（CVR $\ge 1\%$）$\to$ ROAS”的漏斗诊断逻辑，杜绝在点击率不足时盲目调出价。
     - 自动定性病因：点击前问题（主图/标题）、详情页承接问题、决策临门一脚问题、出价过高问题。
     - 自动输出结构化动作清单：
       - `P0_EMERGENCY`（紧急止血）：高花费 0 转化、严重亏损词立即关停/否定；
       - `P1_OPTIMIZATION`（素材与详情优化）：主图优化、增加促销券、下调出价；
       - `P2_EXPANSION`（放量扩张）：健康高 ROI 词加预算扩量。
     - 基于目标 ACOS 与转化率反算最大可承受 CPC 出价上限。

4. **端到端闭环串联与 CLI 工具 (`crossborder_toolkit.pipeline`, `crossborder_toolkit.cli`)**
   - 提供串联“定价保本 ROAS $\to$ Listing 质检 $\to$ 广告投后复盘”的一键工作流。
   - 提供标准命令行接口 `crossborder-toolkit`，支持交互式终端输出与 JSON 输出。

---

### 二、快速开始

#### 1. 环境准备与安装
本项目基于纯 Python 标准库构建，无外部重量级依赖，支持 Python 3.9+。

```bash
# 克隆仓库后在根目录安装
pip install -e .

# 或无需安装直接使用 Python 模块运行
python3 -m crossborder_toolkit.cli --help
```

#### 2. 命令行调用示例

##### 测算单品定价与优惠券余量 (Pricing)
```bash
crossborder-toolkit pricing \
  --cost 100 \
  --shipping 15 \
  --packaging 5 \
  --platform shopee \
  --target-margin 0.25
```

##### Listing 标题与合规质检 (Listing Quality & Compliance)
```bash
crossborder-toolkit listing \
  --platform shopee \
  --title "Patinete Elétrico Dobrável 500W Bateria 10.4Ah Autonomia 30km Preto Adulto" \
  --desc "Patinete com motor potente de 500W e bateria de 10.4Ah com alcance de 30km e peso máximo 120kg." \
  --specs examples/spec_patinete.json \
  --keywords "Patinete Elétrico,500W"
```

##### 广告漏斗数据复盘与生成动作清单 (Ad Diagnostics)
```bash
crossborder-toolkit ad \
  --file examples/ad_report_sample.csv \
  --breakeven-roas 2.5
```

##### 端到端闭环运营流水线 (Pipeline)
```bash
crossborder-toolkit pipeline \
  --cost 120 \
  --shipping 15 \
  --platform shopee \
  --target-margin 0.25 \
  --title "Patinete Elétrico Dobrável 500W Bateria 10.4Ah Autonomia 30km" \
  --keywords "Patinete Elétrico" \
  --ad-file examples/ad_report_sample.csv
```

#### 3. Python API 代码调用示例

```python
from crossborder_toolkit import PricingCalculator, ListingValidator, AdFunnelDiagnostic, AdRecord

# 1. 计算定价与保本 ROAS
pricing = PricingCalculator.calculate(
    cost=80.0,
    shipping=12.0,
    platform="shopee",
    target_margin=0.25,
)
print(f"建议售价: ${pricing.target_price}, 保本 ROAS: {pricing.breakeven_roas}")

# 2. 检验 Listing 合规与参数
validator = ListingValidator()
result = validator.validate(
    platform="shopee",
    title="Patinete Elétrico 500W Dobrável Adulto",
    spec_table={"potencia": "500W"},
    core_keywords=["Patinete Elétrico"],
)
print(f"合规得分: {result.score}, 状态: {result.status}")
```

#### 4. 运行自动化测试
```bash
python3 -m unittest discover -s tests -v
```

---

### 三、来源与致谢

本项目受 [AI-Cross-Border-Ecommerce-Agent-Toolkit](https://github.com/heqiangdiao-wq/AI-Cross-Border-Ecommerce-Agent-Toolkit) 启发重写，代码全部新写，原项目由 heqiangdiao-wq 以 MIT 许可证开源。

---

### 四、许可证

本项目沿用 MIT 许可证，全文见根目录 [LICENSE](./LICENSE)。

---

## English Documentation

### I. Features and Relation to Original Concept

The original project provided prompts and markdown templates for cross-border ecommerce SOPs. This repository is a **Route B rewrite (concept-driven reimplementation)**: we retained the core domain methodology while transforming prompts into a production-grade, executable Python toolkit with rigorous mathematical validations:

1. **SOP 1: Pricing & Multi-SKU Margin Engine (`crossborder_toolkit.pricing`)**
   - Precise back-calculation of target selling prices, breakeven prices, breakeven ROAS ($1 / \text{margin}$), and net profit.
   - Buffer calculation for coupons and promotion discounts while protecting minimum net margins (15%, 10%, 5%).
   - Multi-SKU portfolio planner (Traffic, Hero, High-End, Bundle) validating pricing hierarchy and loss-leader boundaries.
   - Robust fee boundary guard blocking invalid configurations ($\sum \text{fees} \ge 100\%$).

2. **SOP 2: Listing Compliance & Spec Traceability Validator (`crossborder_toolkit.listing`)**
   - Exact Unicode character length tracking for Shopee (120 chars), Mercado Livre (60 chars), and Amazon (200 chars).
   - High-weighting front character (first 20-30 chars) core keyword density score.
   - Real-time scanner for unauthorized brand trademarks (Apple, Xiaomi, Dyson, Nike, etc.) and deceptive claims (e.g., "100% original", "melhor do mercado").
   - Spec consistency engine extracting numeric specifications from text and verifying them against authentic product spec sheets to eliminate AI hallucinations.

3. **SOP 3: 4-Stage Ad Funnel Diagnostic & Action Planner (`crossborder_toolkit.advertising`)**
   - Reverse funnel diagnostic framework: Impressions $\to$ Clicks (CTR $\ge 3\%$) $\to$ Cart Additions (Cart Rate $\ge 8\%$) $\to$ Conversions (CVR $\ge 1\%$) $\to$ ROAS.
   - Categorized root-cause identification: Pre-click creative defects, detail page drop-offs, checkout hesitation, or cost inefficiency.
   - Actionable P0/P1/P2 task generation: P0 Emergency pause for zero-conversion money pits, P1 creative/voucher remedies, and P2 budget scaling for high-ROAS keywords.
   - Maximum allowable CPC ceiling calculator derived from target ACOS and conversion rates.

4. **Closed-Loop Pipeline & CLI (`crossborder_toolkit.pipeline`, `crossborder_toolkit.cli`)**
   - Unified operational workflow linking pricing models, listing quality verification, and ad performance reviews.
   - CLI utility `crossborder-toolkit` supporting human-readable terminal visuals and raw JSON output.

---

### II. Quick Start

#### 1. Installation
The toolkit uses the Python standard library with no external dependencies (Python 3.9+ supported).

```bash
pip install -e .
```

#### 2. CLI Usage Examples

```bash
# Pricing & margin analysis
crossborder-toolkit pricing --cost 100 --shipping 15 --platform shopee --target-margin 0.25

# Listing quality & compliance inspection
crossborder-toolkit listing --platform shopee \
  --title "Patinete Elétrico Dobrável 500W Bateria 10.4Ah Autonomia 30km Preto Adulto" \
  --specs examples/spec_patinete.json \
  --keywords "Patinete Elétrico,500W"

# Ad funnel diagnosis & P0/P1/P2 actions
crossborder-toolkit ad --file examples/ad_report_sample.csv --breakeven-roas 2.5

# End-to-end closed-loop pipeline
crossborder-toolkit pipeline --cost 120 --shipping 15 --platform shopee --target-margin 0.25 \
  --title "Patinete Elétrico Dobrável 500W Bateria 10.4Ah" \
  --ad-file examples/ad_report_sample.csv
```

#### 3. Run Automated Tests
```bash
python3 -m unittest discover -s tests -v
```

---

### III. Provenance and Acknowledgments

This project is a rewrite inspired by [AI-Cross-Border-Ecommerce-Agent-Toolkit](https://github.com/heqiangdiao-wq/AI-Cross-Border-Ecommerce-Agent-Toolkit). All code is newly implemented from scratch. The original project was open-sourced by [heqiangdiao-wq](https://github.com/heqiangdiao-wq) under the MIT License.

---

### IV. License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for the full license text.
