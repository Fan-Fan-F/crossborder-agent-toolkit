"""Command-line interface (CLI) for crossborder-agent-toolkit."""

import argparse
import json
import sys
from typing import List, Optional

from .pricing import PricingCalculator, SkuMatrixPlanner, SkuItem
from .listing import ListingValidator, ComplianceGuard
from .advertising import AdFunnelDiagnostic, AdActionPlanner, AdRecord
from .pipeline import CrossborderPipeline


def setup_pricing_parser(subparsers):
    p = subparsers.add_parser("pricing", help="Calculate unit price, breakeven, ROAS, and coupon buffer.")
    p.add_argument("--cost", type=float, required=True, help="Procurement cost per unit")
    p.add_argument("--shipping", type=float, default=0.0, help="Freight cost per unit (default: 0.0)")
    p.add_argument("--packaging", type=float, default=0.0, help="Packaging and warehouse fee per unit (default: 0.0)")
    p.add_argument("--platform", type=str, default="shopee", help="Platform preset: shopee, mercadolivre, amazon, custom")
    p.add_argument("--commission", type=float, default=None, help="Commission rate (e.g. 0.14 for 14%%)")
    p.add_argument("--ad-rate", type=float, default=None, help="Ad spend ratio (e.g. 0.05 for 5%%)")
    p.add_argument("--tax-rate", type=float, default=None, help="Local tax ratio (e.g. 0.04 for 4%%)")
    p.add_argument("--target-margin", type=float, default=None, help="Target net margin (e.g. 0.25 for 25%%)")
    p.add_argument("--target-price", type=float, default=None, help="Specified test selling price")
    p.add_argument("--json", action="store_true", help="Output raw JSON format")


def setup_listing_parser(subparsers):
    p = subparsers.add_parser("listing", help="Validate listing title, character limit, and policy compliance.")
    p.add_argument("--platform", type=str, default="shopee", help="Target platform (shopee, mercadolivre, amazon)")
    p.add_argument("--title", type=str, required=True, help="Product title to validate")
    p.add_argument("--desc", type=str, default="", help="Product description text")
    p.add_argument("--specs", type=str, default=None, help="JSON string or path to JSON/spec file")
    p.add_argument("--keywords", type=str, default="", help="Comma-separated core keywords to check")
    p.add_argument("--forbidden", type=str, default="", help="Comma-separated additional forbidden words")
    p.add_argument("--json", action="store_true", help="Output raw JSON format")


def setup_ad_parser(subparsers):
    p = subparsers.add_parser("ad", help="Diagnose advertising funnel and generate P0/P1/P2 action plan.")
    p.add_argument("--file", type=str, required=True, help="Path to ad report CSV or JSON file")
    p.add_argument("--breakeven-roas", type=float, default=2.5, help="Product breakeven ROAS (default: 2.5)")
    p.add_argument("--min-ctr", type=float, default=0.03, help="Healthy CTR threshold (default: 0.03)")
    p.add_argument("--min-cart-rate", type=float, default=0.08, help="Healthy Cart Rate threshold (default: 0.08)")
    p.add_argument("--min-cvr", type=float, default=0.01, help="Healthy CVR threshold (default: 0.01)")
    p.add_argument("--json", action="store_true", help="Output raw JSON format")


def setup_pipeline_parser(subparsers):
    p = subparsers.add_parser("pipeline", help="Run end-to-end pricing -> listing -> ad operational pipeline.")
    p.add_argument("--cost", type=float, required=True, help="Procurement cost")
    p.add_argument("--platform", type=str, default="shopee", help="Platform preset")
    p.add_argument("--shipping", type=float, default=0.0, help="Shipping cost")
    p.add_argument("--target-margin", type=float, default=0.25, help="Target net margin")
    p.add_argument("--title", type=str, required=True, help="Listing title")
    p.add_argument("--desc", type=str, default="", help="Listing description")
    p.add_argument("--keywords", type=str, default="", help="Comma-separated keywords")
    p.add_argument("--ad-file", type=str, default=None, help="Optional ad report JSON/CSV path")
    p.add_argument("--json", action="store_true", help="Output raw JSON format")


def handle_pricing(args):
    try:
        res = PricingCalculator.calculate(
            cost=args.cost,
            shipping=args.shipping,
            packaging=args.packaging,
            platform=args.platform,
            commission_rate=args.commission,
            ad_rate=args.ad_rate,
            tax_rate=args.tax_rate,
            target_margin=args.target_margin,
            target_price=args.target_price,
        )
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)

    if args.json:
        print(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
        return

    print("=" * 60)
    print(f"💰 定价与毛利测算报告 [{res.platform.upper()}]")
    print("=" * 60)
    print(f"• 基础成本 (Cost + Ship + Pack): {res.cost:.2f} + {res.shipping:.2f} + {res.packaging:.2f} = {res.total_fixed_cost:.2f}")
    print(f"• 变动费率总和: {res.total_variable_rate * 100:.2f}% (佣金 {res.commission_rate*100:.1f}% / 广告 {res.ad_rate*100:.1f}% / 退货 {res.return_rate*100:.1f}% / 税 {res.tax_rate*100:.1f}%)")
    print(f"• 建议销售价: ${res.target_price:.2f}")
    print(f"• 保本保底售价: ${res.breakeven_price:.2f}")
    print(f"• 单件预估净利: ${res.net_profit:.2f} (净利率: {res.net_margin * 100:.2f}%)")
    print(f"• 保本 ROAS: {res.breakeven_roas:.2f}")
    print("\n🎟️ 优惠券/促销余量空间:")
    for k, v in res.voucher_buffers.items():
        print(f"  - 保留 {k.replace('keep_', '').replace('_margin', '')} 净利: 最大可打 {v['max_discount_pct']}% 折 (折后价: ${v['discounted_price']:.2f})")
    print("=" * 60)


def handle_listing(args):
    specs = {}
    if args.specs:
        try:
            if args.specs.startswith("{"):
                specs = json.loads(args.specs)
            else:
                with open(args.specs, "r", encoding="utf-8") as f:
                    specs = json.load(f)
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to load specs: {e}\n")

    forbidden_list = [w.strip() for w in args.forbidden.split(",") if w.strip()]
    core_kw_list = [w.strip() for w in args.keywords.split(",") if w.strip()]

    guard = ComplianceGuard(custom_forbidden=forbidden_list)
    validator = ListingValidator(compliance_guard=guard)

    res = validator.validate(
        platform=args.platform,
        title=args.title,
        description=args.desc,
        spec_table=specs,
        core_keywords=core_kw_list,
    )

    if args.json:
        print(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
        return

    print("=" * 60)
    print(f"📋 Listing 质检与合规报告 [{res.platform.upper()}] - 状态: {res.status} (得分: {res.score}/100)")
    print("=" * 60)
    print(f"• 标题字符数: {res.title_char_count} / {res.max_title_chars} (有效: {'✅' if res.is_title_length_valid else '❌'})")
    print(f"• 前 {res.front_weight_chars} 字符高权重区: \"{res.front_weight_text}\"")
    if core_kw_list:
        print(f"• 前置核心词命中: {res.core_keywords_in_front or '无'}")
        if res.missing_core_keywords:
            print(f"• 遗漏核心词: {res.missing_core_keywords}")

    if res.compliance_violations:
        print("\n⚠️ 合规与品牌词违规:")
        for v in res.compliance_violations:
            print(f"  [{v.severity}] {v.category}: 命中 '{v.matched_word}' -> {v.recommendation}")

    if res.spec_report.unverified_specs:
        print("\n🔍 参数溯源风险 (可疑虚标):")
        for u in res.spec_report.unverified_specs:
            print(f"  - 数值 '{u}' 未在产品规格表中找到依据")

    if res.actionable_feedback:
        print("\n💡 优化建议:")
        for fb in res.actionable_feedback:
            print(f"  • {fb}")
    print("=" * 60)


def load_ad_records(file_path: str) -> List[AdRecord]:
    records = []
    if file_path.endswith(".json"):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    records.append(AdRecord.from_dict(item))
            elif isinstance(data, dict):
                records.append(AdRecord.from_dict(data))
    else:
        # Simple CSV parser
        import csv
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(AdRecord.from_dict(row))
    return records


def handle_ad(args):
    try:
        records = load_ad_records(args.file)
    except Exception as e:
        sys.stderr.write(f"Error loading ad file '{args.file}': {e}\n")
        sys.exit(1)

    if not records:
        sys.stderr.write(f"Error: No ad records found in '{args.file}'\n")
        sys.exit(1)

    diag_engine = AdFunnelDiagnostic(
        min_ctr=args.min_ctr,
        min_cart_rate=args.min_cart_rate,
        min_cvr=args.min_cvr,
    )
    summary = diag_engine.diagnose_batch(records, breakeven_roas=args.breakeven_roas)

    planner = AdActionPlanner()
    actions = planner.plan_actions(summary.diagnoses, breakeven_roas=args.breakeven_roas)

    if args.json:
        out = {
            "summary": summary.to_dict(),
            "actions": [a.to_dict() for a in actions],
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return

    print("=" * 60)
    print(f"📊 广告漏斗诊断与优化报告 (总花费: ${summary.total_spend:.2f} | GMV: ${summary.total_revenue:.2f})")
    print(f"• 整体 ROAS: {summary.overall_roas:.2f} (保本线: {summary.breakeven_roas:.2f} - {'✅ 盈利' if summary.profitable else '❌ 亏损'})")
    print(f"• 整体漏斗: CTR {summary.overall_ctr*100:.2f}% -> 加购率 {summary.overall_cart_rate*100:.2f}% -> CVR {summary.overall_cvr*100:.2f}%")
    print(f"• 诊断分布: {summary.stage_counts}")
    print("=" * 60)

    print("\n🎯 执行动作清单 (按优先级排序):")
    for act in actions:
        print(f"• [{act.priority}] {act.target_ad_id} -> {act.action_type}")
        print(f"  原因: {act.reason}")
        print(f"  步骤: {act.recommended_step}\n")


def handle_pipeline(args):
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    ad_records = None
    if args.ad_file:
        try:
            records = load_ad_records(args.ad_file)
            ad_records = [r.__dict__ for r in records]
        except Exception as e:
            sys.stderr.write(f"Warning: Failed loading ad-file: {e}\n")

    pipe = CrossborderPipeline()
    res = pipe.run(
        cost=args.cost,
        platform=args.platform,
        shipping=args.shipping,
        target_margin=args.target_margin,
        title=args.title,
        description=args.desc,
        core_keywords=keywords,
        ad_records=ad_records,
    )

    if args.json:
        print(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
        return

    print("=" * 65)
    print(f"🚀 跨境电商运营闭环工作流运行报告 [综合健康度: {res.overall_health}]")
    print("=" * 65)
    print(f"1. 定价核算: 成本 ${res.pricing_result.total_fixed_cost:.2f} -> 建议售价 ${res.pricing_result.target_price:.2f} (保本 ROAS {res.pricing_result.breakeven_roas:.2f})")
    print(f"2. Listing 质检: 状态 {res.listing_result.status} (得分 {res.listing_result.score}/100, 长度 {res.listing_result.title_char_count}/{res.listing_result.max_title_chars})")
    if res.ad_summary:
        print(f"3. 广告投后: 诊断词数 {len(res.ad_summary.diagnoses)}，产生 {len(res.recommended_actions)} 项动作")
        for a in res.recommended_actions[:3]:
            print(f"   - [{a.priority}] {a.target_ad_id}: {a.action_type}")
    print("=" * 65)


def main():
    parser = argparse.ArgumentParser(
        prog="crossborder-toolkit",
        description="Cross-border Ecommerce Agent Toolkit CLI — Pricing, Listing QC, and Ad Funnel Diagnostics.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available commands")

    setup_pricing_parser(subparsers)
    setup_listing_parser(subparsers)
    setup_ad_parser(subparsers)
    setup_pipeline_parser(subparsers)

    args = parser.parse_args()
    if not args.subcommand:
        parser.print_help()
        sys.exit(0)

    if args.subcommand == "pricing":
        handle_pricing(args)
    elif args.subcommand == "listing":
        handle_listing(args)
    elif args.subcommand == "ad":
        handle_ad(args)
    elif args.subcommand == "pipeline":
        handle_pipeline(args)


if __name__ == "__main__":
    main()
