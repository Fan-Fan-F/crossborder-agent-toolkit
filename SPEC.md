# 功能规格说明书 SPEC — crossborder-agent-toolkit

本项目为跨境电商运营智能体工具箱（Cross-Border Ecommerce Agent Toolkit）的全新重写实现（B 路线：只借鉴原项目 SOP 思路与业务逻辑设计，代码 100% 独立编写）。

---

## 一、借鉴原项目的核心思路与功能清单

原项目（`heqiangdiao-wq/AI-Cross-Border-Ecommerce-Agent-Toolkit`）将跨境电商日常运营 SOP（基于拉美 Shopee、Mercado Livre 等主流平台）拆解为 7 个 Agent 模块。但原项目以提示词和文档模板为主，可执行工具零散且缺乏严密的数据输入输出校验。

本项目选取原项目中**最核心、最需要确定性算法与规则校验的 3 条核心运营 SOP**，落地为具备生产级可用性、高鲁棒性校验、支持 CLI 与 Python API 调用的确定性工具箱：

1. **SOP 1: 产品定价与多 SKU 利润测算引擎（Pricing & SKU Strategy Engine）**
   - 对应原项目：`02_Product_Strategy_Agent`（定价模型、费率核算、SKU 四角色矩阵）。
   - 目标：摆脱“拍脑袋定价”，通过严密的公式反算保本价、目标售价、税后净利与券额余量，并对 SKU 结构进行健康度核验。
2. **SOP 2: Listing 标题与文案合规质检引擎（Listing Compliance & Content Validator）**
   - 对应原项目：`03_Listing_Creative_Agent`（平台标题规则、违禁词扫描、参数溯源）。
   - 目标：针对 Shopee、Mercado Livre、Amazon 等平台的硬性字段限制（如 UTF-8 字符长度）、绝对化宣传与侵权禁用词进行硬性拦截，并对文案中的数字参数与规格表进行一致性溯源校验。
3. **SOP 3: 广告漏斗诊断与动作决策引擎（Ad Funnel Diagnostics & Action Engine）**
   - 对应原项目：`06_Advertising_Optimization_Agent`（漏斗诊断、盈亏平衡 ROAS、P0/P1/P2 动作分级）。
   - 目标：依照“曝光 → 点击 → 加购 → 转化”严格漏斗顺序，对广告表现进行逐层病因定性，自动产出带优先级的止血、修补、放量动作清单与出价调整建议。

---

## 二、SOP 1 规格说明：产品定价与多 SKU 利润测算引擎

### 1. 业务场景
跨境电商卖家在 Shopee、Mercado Livre、Amazon 上架时，需要综合考虑采购成本、头程/尾程运费、仓储费、平台佣金、广告费率、退货损耗率以及综合税务。若定价过低会导致“单量大但亏本”，定价过高则失去竞争力；多 SKU 时容易出现价格倒挂或毛利结构不合理。

### 2. 输入定义 (Input)
支持单品测算与多 SKU 矩阵测算：
- `cost` (float, 必须 > 0): 单件采购成本。
- `shipping` (float, 必须 >= 0, 默认 0.0): 包含头程与尾程预估物流成本。
- `packaging` (float, 必须 >= 0, 默认 0.0): 包装与固定仓储杂费。
- `platform` (str, 选填: `shopee`, `mercadolivre`, `amazon`, `custom`): 预设平台费率模板。
- `commission_rate` (float, [0, 1), 选填): 平台佣金率（若指定 platform 则使用预设值，如 Shopee 14%、Mercado Livre 16%）。
- `ad_rate` (float, [0, 1), 默认 0.05): 预估广告成本占销售额比例（如 5%）。
- `return_rate` (float, [0, 1), 默认 0.02): 退货与售后损耗率（如 2%）。
- `tax_rate` (float, [0, 1), 默认 0.0): 综合税率或发票税率（如巴西站税费）。
- `target_margin` (float, [0, 1), 选填): 目标净利润率（例如大件 30%，小件 25%）。
- `target_price` (float, 选填): 指定测试销售价（与 target_margin 二选一，指定售价时将反算实际净利率）。
- `skus` (list of dict, 矩阵模式): 包含多 SKU 角色定义：
  - `role`: `traffic` (引流款), `hero` (主推款), `high_end` (高配款), `bundle` (配件组合款)。
  - `cost`: 独立采购成本。
  - `addon_price`: 加价幅度或建议加价。

### 3. 输出定义 (Output)
- `target_price` (float): 建议零售价。
  $$Price = \frac{Cost + Shipping + Packaging}{1 - (Commission + AdRate + ReturnRate + TaxRate + TargetMargin)}$$
- `breakeven_price` (float): 保本保底售价（即净利润为 0 时的最低售价）。
- `breakeven_roas` (float): 广告盈亏平衡 ROAS（$1 / 毛利率$）。
- `net_profit` (float): 在目标售价下的单件净利润金额。
- `net_margin` (float): 实际净利率。
- `voucher_buffer` (dict): 在不同利润保留底线下，允许开具的最大平台优惠券/折扣券金额与百分比。
- `sku_matrix` (list of dict, 矩阵模式): 各 SKU 的价格阶梯、毛利对比、以及健康度建议（如引流款是否亏损过多、高配款利润是否充足）。

### 4. 校验规则 (Validation Rules)
1. 费用与成本值校验：`cost > 0`，`shipping >= 0`，`packaging >= 0`，不能为负数或非数值。
2. 费率区间与有效性校验：各项费率必须属于 `[0, 1)`。
3. 费率总和守卫：
   $$\sum Rate = Commission + AdRate + ReturnRate + TaxRate + TargetMargin$$
   如果 $\sum Rate \ge 1.0$，系统必须直接拒绝计算并抛出明确错误提示（例如：“费率与利润目标总和达到或超过 100%，数学上无法实现正向售价”）。
4. SKU 价格结构规则检查：
   - 引流款价格必须严格低于主推款；
   - 高配款价格必须高于主推款；
   - 若引流款毛利率为负，给出黄色风险提示（亏损引流需限制预算）。

---

## 三、SOP 2 规格说明：Listing 标题与文案合规质检引擎

### 1. 业务场景
跨境平台对于商品 Listing 有严格的字符上限和合规要求。例如 Shopee 标题上限 120 字符、Mercado Livre 上限 60 字符；使用绝对化宣传用语（如 "melhor", "100%", "garantido"）或侵权品牌词（如 "Apple", "Nike", "Xiaomi"）会遭平台下架或限流。此外，AI 编写详情文案时经常“虚构技术参数”，必须与产品真实规格表严格一致。

### 2. 输入定义 (Input)
- `platform` (str, 必填: `shopee`, `mercadolivre`, `amazon`): 目标平台。
- `title` (str, 必填): 待检测的商品标题（支持英文、葡萄牙文、西班牙文、中文）。
- `description` (str, 选填): 待检测的商品详情页文案。
- `spec_table` (dict, 选填): 真实技术规格表（键值对，如 `{"potencia": "500W", "bateria": "10.4Ah", "peso_maximo": "120kg"}`）。
- `core_keywords` (list of str, 选填): 必须覆盖的核心搜索词。
- `custom_forbidden` (list of str, 选填): 商家自选追加的禁用词/品牌词。

### 3. 输出定义 (Output)
- `passed` (bool): 整体是否通过（无严重阻断项）。
- `score` (int, 0-100): 综合质量与合规评分。
- `title_check` (dict):
  - `char_count`: 真实字符长度（准确处理拉美重音字符如 `ã`, `ç`, `é`，字符计数而非字节计数）。
  - `max_allowed`: 平台允许最大字符数。
  - `is_length_valid`: 是否超限。
  - `front_30_chars`: 前 30 字符截取展示。
  - `core_keywords_covered`: 核心词在前 30 字符内以及整标题内的命中情况。
- `compliance_issues` (list of dict):
  - `severity`: `ERROR` (违规禁用词/严重超限), `WARNING` (疑似夸大宣传/次要建议).
  - `issue_type`: `FORBIDDEN_BRAND` (品牌侵权), `EXAGGERATED_CLAIM` (虚假夸大词), `LENGTH_OVERFLOW` (长度超限).
  - `matched_text`: 命中的词或文本片段。
  - `message`: 修复建议。
- `spec_traceability` (dict):
  - `extracted_specs`: 从文本中自动提取的技术参数（如数值+单位：`500W`, `36V`, `120kg`）。
  - `verified_specs`: 成功在 `spec_table` 溯源的参数列表。
  - `unverified_specs`: 未在规格表登记、存在 AI 虚构风险的数值警示列表。

### 4. 校验规则 (Validation Rules)
1. 平台长度硬拦截：Shopee > 120 字符、Mercado Livre > 60 字符、Amazon > 200 字符，直接判为 `ERROR` 并导致 `passed = False`。
2. 禁用词硬拦截：预置常见侵权品牌词库（Apple, Samsung, Xiaomi, Nike 等）及违禁绝对化词库（melhor do mercado, 100% garantido, cura milagrosa 等），命中任何一项直接标红报错。
3. 参数可溯源原则：正文中出现的任何物理数值（功率 W、容量 Ah/mAh、电压 V、承重 kg 等），若与传入的 `spec_table` 数值不一致或完全未登记，系统记入 `unverified_specs` 并扣除质量分。

---

## 四、SOP 3 规格说明：广告漏斗诊断与动作决策引擎

### 1. 业务场景
跨境电商日常广告运营中，卖家往往缺乏科学的漏斗拆解能力，一遇亏损就盲目关停广告或乱降出价。根据 SOP 标准操作程序，必须按照“曝光 → 点击 → 加购 → 转化”的层级顺序自上而下排查病因，区分素材问题、详情页问题与定价问题，并针对性输出 P0（紧急止血）、P1（素材优化与修补）、P2（放量扩充）动作。

### 2. 输入定义 (Input)
- `ad_data` (list of dict 或 CSV 文件路径): 广告报表数据，单条数据字段包括：
  - `ad_id` / `campaign_name` (str): 广告标识或推广关键词。
  - `impressions` (int, >= 0): 曝光数。
  - `clicks` (int, >= 0): 点击数。
  - `add_to_cart` (int, >= 0): 加购数。
  - `orders` (int, >= 0): 成交订单数。
  - `spend` (float, >= 0.0): 广告消耗金额。
  - `revenue` (float, >= 0.0): 广告引导 GMV 金额。
- `breakeven_roas` (float, 必填 > 0): 产品的保本盈亏平衡 ROAS（可由 SOP 1 产出联动）。
- `benchmarks` (dict, 选填，有默认标准):
  - `min_ctr`: 点击率健康线（默认 0.03 即 3%）。
  - `min_cart_rate`: 点击加购率健康线（默认 0.08 即 8%）。
  - `min_cvr`: 加购转化率健康线（默认 0.01 即 1%）。
  - `high_spend_threshold`: 高消耗无转化报警阈值（默认 50.0 或由客单价反算）。

### 3. 输出定义 (Output)
- `summary` (dict): 整体消耗、销售额、整体 CTR、加购率、CVR、整体 ROAS 与盈亏状态。
- `diagnoses` (list of dict): 每个广告组/关键词的明细诊断：
  - `metrics`: 计算出实测 CTR, Cart_Rate, CVR, CPC, CPA, ROAS, ACOS。
  - `stage`: 漏斗卡点环节：
    - `STAGE_1_PRE_CLICK`: 有曝光无点击（CTR 不足），病因在主图、标题或前置价格标。
    - `STAGE_2_DETAIL_PAGE`: 有点击无加购（加购率不足），病因在详情页、SKU 选项或规格展示。
    - `STAGE_3_DECISION_MAKING`: 有加购无转化（转化率不足），病因在最终决策环节（优惠券、运费、评价、买家信心）。
    - `STAGE_4_COST_INEFFICIENT`: 漏斗各级均健康，但 ROAS 低于盈亏线，病因在竞价出价过高或词匹配太泛。
    - `STAGE_HEALTHY`: 表现优秀，ROAS 高于盈亏线。
- `actions` (list of dict): 分级行动建议：
  - `P0_EMERGENCY`: 立即暂停/否定亏损词（高花费 0 转化、ROAS 严重低于盈亏线）。
  - `P1_OPTIMIZATION`: 素材与转化调整（如修改主图测试 CTR、补充详情页痛点、发放限时优惠券拉高转化率、适度调降出价）。
  - `P2_EXPANSION`: 放量放大（ROAS 表现优秀、出价合理，建议加预算提排名）。
- `max_cpc_recommendations` (dict): 根据目标 ROAS 与转化率反算的最大可承受 CPC 竞价上限建议。

### 4. 校验规则 (Validation Rules)
1. 漏斗顺位判定不可跳步：必须严格按照 CTR -> 加购率 -> 转化率 -> ROAS 的先后顺位判定问题，避免在 CTR 未达标时误调出价。
2. 零除防崩与鲁棒性：曝光为 0、点击为 0、花费为 0 等异常情况必须优雅处理，不得触发除零异常（ZeroDivisionError）。
3. 严格数据格式校验：所有数值字段必须为非负数，缺失关键字段时返回清晰校验提示。

---

## 五、模块化架构与 CLI / Python API 规划

全新代码采用清晰、标准、无外部沉重依赖的 Python 纯工程结构（支持 Python 3.9+，核心仅使用 Python 标准库，确保在任何标准 Python 环境下一键即装即跑）：

```text
crossborder-agent-toolkit/
├── crossborder_toolkit/
│   ├── __init__.py
│   ├── cli.py                     # 统一命令行入口
│   ├── pricing/                   # SOP 1: 定价与多 SKU 测算
│   │   ├── __init__.py
│   │   ├── calculator.py          # 定价核心算术与反算
│   │   ├── platforms.py           # 平台预设费率库 (Shopee, Mercado Livre, Amazon)
│   │   └── sku_matrix.py          # 多 SKU 角色梯度规划
│   ├── listing/                   # SOP 2: Listing 合规与质检
│   │   ├── __init__.py
│   │   ├── validator.py           # 字符数校验、核心词覆盖
│   │   ├── compliance.py          # 禁用词、品牌词、侵权词检测
│   │   └── spec_checker.py        # 文本数值提取与规格表一致性溯源
│   ├── advertising/               # SOP 3: 广告漏斗诊断与决策
│   │   ├── __init__.py
│   │   ├── diagnostic.py          # 四阶段漏斗判定算法
│   │   ├── action_planner.py      # P0/P1/P2 动作分级生成器
│   │   └── bid_optimizer.py       # 保本 ROAS 与最大承受 CPC 算术
│   └── pipeline.py                # 跨 SOP 串联与工作流运行器
├── tests/                         # 完整自动化测试套件
│   ├── __init__.py
│   ├── test_pricing.py
│   ├── test_listing.py
│   ├── test_advertising.py
│   └── test_pipeline.py
├── pyproject.toml                 # 现代标准打包配置
├── setup.py                       # 兼容 pip install -e . 安装
├── SPEC.md                        # 本规格说明书
├── CHANGES.md                     # 改动与自测记录
├── LICENSE                        # 原项目 MIT License
├── PROVENANCE.md                  # 来源记录文件
├── TASK.md                        # 任务单
└── README.md                      # 中英双语文档与快速上手指南
```
