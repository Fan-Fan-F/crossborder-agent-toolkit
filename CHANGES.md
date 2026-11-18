# 改动说明 CHANGES — crossborder-agent-toolkit

本项目为基于原项目 `heqiangdiao-wq/AI-Cross-Border-Ecommerce-Agent-Toolkit` 思路进行的全新独立实现（B 路线：只借鉴 SOP 方法论与业务逻辑设计，代码 100% 独立重写）。

---

## 一、架构升级与功能改进点

1. **确定性算术与严密边界拦截（SOP 1: 定价与多 SKU 测算）**
   - 彻底将提示词升级为具备完整数学反推能力的定价计算引擎 `PricingCalculator`，支持单件保本平衡价、目标净利率对应售价、盈亏平衡 ROAS（$1/\text{毛利率}$）以及不同净利率底线下的促销优惠券最大发放空间测算。
   - 实现多 SKU 四角色梯度矩阵规划器 `SkuMatrixPlanner`（引流款 Traffic、主推款 Hero、高配款 High-End、配件组合款 Bundle），提供价格倒挂与过低毛利风控诊断。
   - 增加数学边界防护：采购成本必须大于 0，各项变动费率总和 $\ge 100\%$ 时坚决阻断计算并报错。

2. **生产级 Listing 质量与多平台合规质检（SOP 2: 内容合规与参数溯源）**
   - 建立面向 Shopee（120 字符）、Mercado Livre（60 字符）、Amazon（200 字符）等跨境主流平台的硬性规则库与字符计数引擎（解决西语/葡语拉美重音字符 Unicode 长度计算问题）。
   - 实现前置高权重区（前 20-30 字符）核心搜索词覆盖度评分机制。
   - 建立双层合规防护网 `ComplianceGuard`：品牌侵权词（Apple, Nike, Xiaomi, Dyson 等）硬拦截与绝对化虚假宣传词（melhor do mercado, 100% original, 治愈承诺等）分级预警。
   - 首创参数一致性溯源校验器 `SpecConsistencyChecker`：从生成文本中提取功率、电池容量、速度、承重等数值参数，与商家真实规格表严格比对，拦截 AI 幻觉和虚假参数标注。

3. **逆向四阶段广告漏斗诊断与 P0/P1/P2 动作引擎（SOP 3: 广告漏斗决策）**
   - 严格遵循 SOP 运营规范：漏斗必须按照“曝光 $\to$ 点击（CTR $\ge 3\%$）$\to$ 加购（加购率 $\ge 8\%$）$\to$ 转化（CVR $\ge 1\%$）$\to$ 成本与 ROAS”单向逆推病因，杜绝“转化差直接盲目调出价”。
   - 提供除零防崩保护与小样本期判定，支持读取 CSV 与 JSON 广告数据报表。
   - 自动生成结构化分级行动清单：P0 紧急止血（高花无转化立即关停/否定）、P1 素材与详情页修补（换主图、发券、调价）、P2 扩量放量（健康高 ROI 词加预算）；并根据目标 ACOS 与转化率反算最大可承受 CPC 出价上限。

4. **端到端闭环流水线与生产级 CLI 工具链**
   - 实现 `CrossborderPipeline`，将“定价模型（产出保本 ROAS）$\to$ Listing 合规质检 $\to$ 投后漏斗数据复盘”完整闭环串联。
   - 提供标准命令行工具 `crossborder-toolkit`，包含 `pricing`、`listing`、`ad`、`pipeline` 四个功能子命令，支持人类可读的终端格式与机器可读的 JSON 格式输出。

---

## 二、自测记录

### 1. 自动化单元测试
- **测试命令**：
  ```bash
  python3 -m unittest discover -s tests -v
  ```
- **第 1 轮自测情况**：
  - 运行 18 个测试用例，17 项通过，1 项失败：
    - 失败用例：`test_spec_consistency_unverified (test_listing.TestListingValidator.test_spec_consistency_unverified)`
    - 失败原因：子字符串比对逻辑漏洞，导致规格表中的 `500w` 误将文本中的 `1500w` 视作子串命中。
  - 修复动作：修改 `SpecConsistencyChecker.verify`，提取参数值与物理单位进行严密的精确匹配比对。
- **第 2 轮自测情况**：
  - 18 个测试全部通过（0 failure, 0 error），耗时 0.004 秒：
    - `test_metrics_calculation`: PASS
    - `test_p0_action_generation`: PASS
    - `test_stage_1_pre_click`: PASS
    - `test_stage_2_detail_page`: PASS
    - `test_stage_3_decision_making`: PASS
    - `test_stage_4_cost_inefficient`: PASS
    - `test_stage_5_healthy`: PASS
    - `test_compliance_brand_and_exaggerated_claims`: PASS
    - `test_mercadolivre_title_length_exceeded`: PASS
    - `test_shopee_valid_listing`: PASS
    - `test_spec_consistency_unverified`: PASS
    - `test_end_to_end_pipeline`: PASS
    - `test_fixed_price_back_calculation`: PASS
    - `test_invalid_excessive_rates`: PASS
    - `test_invalid_negative_cost`: PASS
    - `test_shopee_pricing`: PASS
    - `test_sku_matrix_planning`: PASS
    - `test_sku_matrix_unhealthy_hierarchy`: PASS

### 2. 包安装与命令行实机测试
- **安装测试命令**：
  ```bash
  pip install --break-system-packages -e .
  ```
  - 结果：成功构建 wheel 并完成本地可编辑安装，成功注册 `crossborder-toolkit` 命令。

- **CLI 定价命令测试**：
  ```bash
  crossborder-toolkit pricing --cost 100 --shipping 15 --packaging 5 --platform shopee --target-margin 0.25
  ```
  - 结果：成功计算建议售价 $240.00，保本售价 $160.00，保本 ROAS 3.33，并输出 4 档优惠券折让空间。

- **CLI Listing 质检测试（合规与违规双向校验）**：
  ```bash
  crossborder-toolkit listing --platform shopee --title "Patinete Elétrico Dobrável 500W Bateria 10.4Ah Autonomia 30km Preto Adulto" --specs examples/spec_patinete.json --keywords "Patinete Elétrico,500W"
  ```
  - 结果：通过校验，状态 PASS，得分 100/100。
  ```bash
  crossborder-toolkit listing --platform mercadolivre --title "Patinete Elétrico Xiaomi Apple 100% original Dobrável 500W Bateria 10.4Ah Autonomia 30km Preto Adulto" --desc "Super scooter atinge 80km/h com motor de 1500W e peso máximo 120kg." --specs examples/spec_patinete.json
  ```
  - 结果：成功阻断，状态 FAIL，得分 0/100；精确拦截超限 41 字符、品牌词 xiaomi/apple、虚假词 100% original，以及未溯源虚构参数 80km/h 和 1500w。

- **CLI 广告漏斗诊断测试**：
  ```bash
  crossborder-toolkit ad --file examples/ad_report_sample.csv --breakeven-roas 2.5
  ```
  - 结果：成功诊断 5 个关键词/广告组，识别整体 ROAS 2.64（盈利），产出包含 1 项 P0 紧急停投、2 项 P1 主图优化、2 项 P2 放量加预算的结构化执行清单。

- **CLI 端到端流水线测试**：
  ```bash
  crossborder-toolkit pipeline --cost 120 --shipping 15 --platform shopee --target-margin 0.25 --title "Patinete Elétrico Dobrável 500W Bateria 10.4Ah Autonomia 30km Preto Adulto" --desc "Patinete com motor potente de 500W e bateria 10.4Ah." --keywords "Patinete Elétrico,500W" --ad-file examples/ad_report_sample.csv
  ```
  - 结果：顺利串联定价、Listing 质检与广告诊断，输出综合健康度报告。

### 3. 环境与依赖说明
- 纯 Python 3.9+ 标准库驱动，无第三方重型数据库或外部网络依赖，测试完全在本地脱机运行通过。
