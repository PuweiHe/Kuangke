"""
监控任务运行器

驱动完整的监控流程：数据查询 -> 规则检查 -> 结果处理 -> 通知
是风险监控系统的顶层调度入口

支持三种执行模式：
1. 全量监控：执行所有风险类型的监控
2. 按风险类型：执行指定风险类型的监控
3. 按监控ID：执行指定的监控指标
"""

import importlib
import inspect
from pathlib import Path

from typing import Any, Dict, List, Optional
from loguru import logger

from dao.risk_types_dao import RiskTypesDAO
from dao.monitor_config_dao import MonitorConfigDAO
from models.monitor_rule_config import MonitorRuleConfig
from utils.date_utils import normalize_business_date


# ============================================================
# 监控ID -> (模块路径, 类名) 精确映射（优先使用）
# 新增监控指标时，在此处添加映射即可
# ============================================================
MONITOR_ID_MAP = {
    # === black_white / Infrastructure.py ===
    "BW-IF-0001": ("monitors.black_white.Infrastructure", "REITSInvestmentScopeMonitor"),
    "BW-IF-0002": ("monitors.black_white.Infrastructure", "FVOCIFundPoolMonitor"),
    "BW-IF-0003": ("monitors.black_white.Infrastructure", "FVOCIStockPoolMonitor"),
    "BW-IF-0004": ("monitors.black_white.Infrastructure", "FVOCIFundInvestExitMonitor"),
    "BW-IF-0005": ("monitors.black_white.Infrastructure", "FVOCIFundBuySellMonitor"),
    # === black_white / investment_constraints.py ===
    "BW-IC-0001": ("monitors.black_white.investment_constraints", "BanSoyaMonitor"),
    "BW-IC-0002": ("monitors.black_white.investment_constraints", "StockInvestmentScopeMonitor"),
    "BW-IC-0003": ("monitors.black_white.investment_constraints", "SubordinatedBondWhitelistMonitor"),
    "BW-IC-0004": ("monitors.black_white.investment_constraints", "RealEstateIndustryBanMonitor"),
    "BW-IC-0005": ("monitors.black_white.investment_constraints", "TargetWhitelistMonitor"),
    "BW-IC-0006": ("monitors.black_white.investment_constraints", "WhitelistInvestmentScopeMonitor"),
    # === black_white / trade_constraint.py ===
    "BW-TC-0001": ("monitors.black_white.trade_constraint", "TradeCounterpartyConstraint"),
    # === rating / fiexd_income_constraint.py ===
    "RG-FI-0001": ("monitors.rating.fiexd_income_constraint", "BondIssuerAndDebtCreditRatingMonitor"),
    "RG-FI-0002": ("monitors.rating.fiexd_income_constraint", "BBBRatedBondRatioMonitor"),
    "RG-FI-0003": ("monitors.rating.fiexd_income_constraint", "BBBRatedBondMonitor"),
    "RG-FI-0004": ("monitors.rating.fiexd_income_constraint", "AMinusRatedBondRatioMonitor"),
    # === rating / risk_rating_constraint.py ===
    "RG-RC-0001": ("monitors.rating.risk_rating_constraint", "BondIssuerExternalRatingMonitor"),
    "RG-RC-0002": ("monitors.rating.risk_rating_constraint", "EnterpriseBondRatingMonitor"),
    "RG-RC-0003": ("monitors.rating.risk_rating_constraint", "InternalEnterpriseBondRatingMonitor"),
    "RG-RC-0004": ("monitors.rating.risk_rating_constraint", "UrbanInvestmentBondRegionMonitor"),
    "RG-RC-0005": ("monitors.rating.risk_rating_constraint", "DebtInvestmentPlanRatingMonitor"),
    "RG-RC-0006": ("monitors.rating.risk_rating_constraint", "InfrastructureRealEstateTrustRatingMonitor"),
    # === investment_ratio_amount / liability_evaluation.py ===
    "IRA-SC-0001": ("monitors.investment_ratio_amount.liability_evaluation", "SingleAssetCumulativeInvestmentAmountMonitor"),
    # === investment_amount / asset_constraints.py ===
    "IA-AC-0001": ("monitors.investment_amount.asset_constraints", "EquityStockMarketValueMonitor"),
    # === investment_amount / investment_constraints.py ===
    "IA-IC-0001": ("monitors.investment_amount.investment_constraints", "BondInvestmentQuotaMonitor"),
    "IA-IC-0002": ("monitors.investment_amount.investment_constraints", "StockInvestmentQuotaMonitor"),
    "IA-IC-0003": ("monitors.investment_amount.investment_constraints", "MultiProductInfrastructureQuotaMonitor"),
    "IA-IC-0004": ("monitors.investment_amount.investment_constraints", "TotalInvestmentAmountMonitor"),
    "IA-IC-0005": ("monitors.investment_amount.investment_constraints", "SingleBondInvestmentAmountMonitor"),
    "IA-IC-0006": ("monitors.investment_amount.investment_constraints", "SingleStockInvestmentAmountMonitor"),
    # === investment_amount / product_scale_constraints.py ===
    "IA-PS-0001": ("monitors.investment_amount.product_scale_constraints", "FixedIncomeScaleMonitor"),
    "IA-PS-0002": ("monitors.investment_amount.product_scale_constraints", "StockScaleMonitor"),
    # === duration / duration.py ===
    "DR-EX-0001": ("monitors.duration.duration", "FixedIncomeScaleDurationMonitor"),
    "DR-EX-0002": ("monitors.duration.duration", "FixedIncomeAssetBondDurationMonitor"),
    "DR-DEMO-0003": ("monitors.duration.duration", "FixedIncomeAssetDurationMonitor"),
    # === financial_yield / asset_constraints.py ===
    "FY-AC-0001": ("monitors.financial_yield.asset_constraints", "EquityComprehensiveYieldMonitor"),
    "FY-AC-0002": ("monitors.financial_yield.asset_constraints", "FixedIncomeComprehensiveYieldMonitor"),
    # === financial_yield / investment_objective.py ===
    "FY-IO-0001": ("monitors.financial_yield.investment_objective", "FixedIncomeSpecialAccountYieldMonitor"),
    "FY-IO-0002": ("monitors.financial_yield.investment_objective", "EquitySpecialAccountYieldMonitor"),
    "FY-IO-0003": ("monitors.financial_yield.investment_objective", "TrustPlanYieldTargetMonitor"),
    "FY-IO-0004": ("monitors.financial_yield.investment_objective", "ABSYieldTargetMonitor"),
    "FY-IO-0005": ("monitors.financial_yield.investment_objective", "WealthProductAnnualYieldTargetMonitor"),
    "FY-IO-0006": ("monitors.financial_yield.investment_objective", "InfrastructureFundYieldTargetMonitor"),
    "FY-IO-0007": ("monitors.financial_yield.investment_objective", "DebtPlanYieldTargetMonitor"),
    # === financial_yield / return_objective.py ===
    "FY-RO-0001": ("monitors.financial_yield.return_objective", "FixedIncomeYieldMonitor"),
    "FY-RO-0002": ("monitors.financial_yield.return_objective", "FixedIncomeNonStdLiquidityYieldMonitor"),
    "FY-RO-0003": ("monitors.financial_yield.return_objective", "StockYieldMonitor"),
    "FY-RO-0004": ("monitors.financial_yield.return_objective", "FinancialYieldMonitor"),
    # === financial_yield / single_asset.py ===
    "FY-SA-0001": ("monitors.financial_yield.single_asset", "SingleAssetMonitor"),
    # === investment_ratio / account_classify_constraint.py ===
    "IR-AC-0001": ("monitors.investment_ratio.account_classify_constraint", "AmortizedCostBondMonitor"),
    "IR-AC-0002": ("monitors.investment_ratio.account_classify_constraint", "FVOCIInfrastructureBuySellMonitor"),
    "IR-IA-0001": ("monitors.investment_ratio.income_asset_constraint", "SingleIndustryConcentrationMonitor"),
    "IR-IA-0002": ("monitors.investment_ratio.income_asset_constraint", "SingleBondHoldingRatioMonitor"),
    "IR-IA-0003": ("monitors.investment_ratio.income_asset_constraint", "SingleBondIssueScaleRatioMonitor"),
    "IR-RC-0001": ("monitors.investment_ratio.investment_ratio_constraint", "BondHoldingScaleRatioMonitor"),
    "IR-RC-0002": ("monitors.investment_ratio.investment_ratio_constraint", "StockHoldingScaleRatioMonitor"),
    "IR-RC-0003": ("monitors.investment_ratio.investment_ratio_constraint", "FinancialProductHoldingScaleRatioMonitor"),
    "IR-RC-0004": ("monitors.investment_ratio.investment_ratio_constraint", "InfrastructureFundHoldingScaleRatioMonitor"),
    "IR-RC-0005": ("monitors.investment_ratio.investment_ratio_constraint", "BondEntrustedInvestmentRatioMonitor"),
    "IR-RC-0006": ("monitors.investment_ratio.investment_ratio_constraint", "StockEntrustedInvestmentRatioMonitor"),
    "IR-RC-0007": ("monitors.investment_ratio.investment_ratio_constraint", "FinancialProductInvestmentRatioMonitor"),
    "IR-RC-0008": ("monitors.investment_ratio.investment_ratio_constraint", "InfrastructureFundInvestmentRatioMonitor"),
    "IR-RC-0009": ("monitors.investment_ratio.investment_ratio_constraint", "AccountLeverageRatioMonitor"),
    "IR-RC-0010": ("monitors.investment_ratio.investment_ratio_constraint", "AssetClassInvestmentRatioMonitor"),
    "IR-TC-0001": ("monitors.investment_ratio.trade_counterparty_constraint", "SingleBondBalanceRatioMonitor"),
}

# ============================================================
# 监控类型 -> 模块路径 模糊映射（备用）
# 当 monitor_id 不在 MONITOR_ID_MAP 中时，通过类型加载模块并自动匹配
# ============================================================
MONITOR_TYPE_MAP = {
    "白名单/黑名单": [
        "monitors.black_white.Infrastructure",
        "monitors.black_white.investment_constraints",
        "monitors.black_white.trade_constraint",
    ],
    "评级": [
        "monitors.rating.fiexd_income_constraint",
        "monitors.rating.risk_rating_constraint",
    ],
    "投资金额": [
        "monitors.investment_amount.asset_constraints",
        "monitors.investment_amount.investment_constraints",
    ],
    "投资额度监控": [
        "monitors.investment_amount.investment_constraints",
        "monitors.investment_amount.product_scale_constraints",
    ],
    "投资比例金额": [
        "monitors.investment_ratio_amount.liability_evaluation",
    ],
    "久期": [
        "monitors.duration.duration",
    ],
    "财务收益率指标": [
        "monitors.financial_yield.asset_constraints",
    ],
    "投资比例": [
        "monitors.investment_ratio.account_classify_constraint",
        "monitors.investment_ratio.income_asset_constraint",
        "monitors.investment_ratio.investment_ratio_constraint",
        "monitors.investment_ratio.trade_counterparty_constraint",
    ],
    "投资比例监控": [
        "monitors.investment_ratio.account_classify_constraint",
        "monitors.investment_ratio.income_asset_constraint",
        "monitors.investment_ratio.investment_ratio_constraint",
        "monitors.investment_ratio.trade_counterparty_constraint",
    ],
}


class MonitorRunner:
    """
    监控任务运行器

    支持多种执行模式：
    - 全量监控：执行所有启用的监控指标
    - 按风险类型：执行指定风险类型的监控
    - 按监控ID：执行指定的单个监控指标

    从数据获取到结果存储的完整链路
    """

    def __init__(self):
        self.risk_types_dao = RiskTypesDAO()
        self.monitor_config_dao = MonitorConfigDAO()
        self._discovered_monitor_classes = None

        logger.info("MonitorRunner 初始化完成")

    def run(self, biz_date: str, dimension: Optional[str] = None) -> Dict[str, Any]:
        """
        执行指定日期的全量监控

        获取所有启用的监控配置，逐个执行

        Parameters
        ----------
        biz_date : str
            业务日期，格式：YYYYMMDD
        dimension : str, optional
            维度代码，如果不指定则执行所有维度

        Returns
        -------
        dict
            监控结果摘要，包含每个监控指标的执行结果
        """
        biz_date = normalize_business_date(biz_date)
        logger.info(f"开始执行全量监控，业务日期: {biz_date}")

        try:
            if self.monitor_config_dao.get_snapshot_count(biz_date) == 0:
                return {"status": "no_data", "biz_date": biz_date, "total_count": 0}
            # 1. 获取所有启用的监控配置
            logger.debug("准备查询监控配置...")
            configs = self.monitor_config_dao.get_trust_dimension_config(dimension=dimension)

            logger.info(f"获取到 {len(configs)} 个启用的监控指标")
            if not configs:
                logger.warning("没有启用的监控指标")
                return {"status": "no_config", "biz_date": biz_date}

            # 2. 逐个执行监控指标
            results = []
            success_count = 0
            fail_count = 0

            for config in configs:
                try:
                    logger.debug(f"开始处理监控配置: {config.monitor_id} - {config.monitor_title}  执行维度: {config.trust_dimension}")
                    result = self._execute_single_monitor(
                        monitor_id=config.monitor_id,
                        biz_date=biz_date,
                        dimension=config.trust_dimension,
                        config = config
                    )

                    logger.debug(f"监控 {config.monitor_id}, 维度: {config.trust_dimension} 执行完成, 状态: {result.get('status')}")
                    results.append(result)

                    if result.get("status") == "success":
                        success_count += 1
                    else:
                        fail_count += 1

                except Exception as e:
                    logger.error(f"执行监控指标 {config.monitor_id} 失败: {e}")
                    fail_count += 1
                    results.append({
                        "monitor_id": config.monitor_id,
                        "status": "error",
                        "error": str(e)
                    })

            logger.info(f"全量监控完成: 成功 {success_count}, 失败 {fail_count}, 总计 {len(configs)}")

            return {
                "status": "completed",
                "biz_date": biz_date,
                "total_count": len(configs),
                "success_count": success_count,
                "fail_count": fail_count,
                "results": results,
            }

        except Exception as e:
            logger.error(f"全量监控执行失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"status": "error", "biz_date": biz_date, "error": str(e)}

    def run_by_monitor_id(self, monitor_id: str, biz_date: str, dimension: Optional[str] = None) -> Dict[str, Any]:
        """
        执行指定的单个监控指标

        Parameters
        ----------
        monitor_id : str
            监控指标ID，如: "BW-RB-0001"
        biz_date : str
            业务日期，格式：YYYYMMDD
        dimension : str, optional
            维度代码，如果不指定则从配置中获取

        Returns
        -------
        dict
            监控执行结果
        """
        biz_date = normalize_business_date(biz_date)
        logger.info(f"开始执行监控指标: {monitor_id}, 业务日期: {biz_date}")

        try:
            if self.monitor_config_dao.get_snapshot_count(biz_date) == 0:
                return {"status": "no_data", "monitor_id": monitor_id, "biz_date": biz_date}
            # 1. 获取监控配置
            configs = self.monitor_config_dao.get_trust_dimension_config(
                monitor_id=monitor_id, dimension=dimension
            )
            if len(configs) == 0:
                logger.error(f"监控指标配置不存在: {monitor_id}")
                return {
                    "status": "not_found",
                    "monitor_id": monitor_id,
                    "biz_date": biz_date,
                    "error": f"监控指标 {monitor_id} 不存在或未启用"
                }

            # 2. 通过监控指标获得多个委托维度执行
            results = []
            for config in configs:
                result = self._execute_single_monitor(
                    monitor_id=monitor_id,
                    biz_date=biz_date,
                    dimension=config.trust_dimension,
                    config=config
                )
                results.append(result)

            logger.info(f"监控指标 {monitor_id} 执行完成: {results[-1].get('status')}")
            return results[-1]

        except Exception as e:
            logger.error(f"执行监控指标 {monitor_id} 失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "monitor_id": monitor_id,
                "biz_date": biz_date,
                "error": str(e)
            }

    def _execute_single_monitor(self, monitor_id: str, biz_date: str, dimension: str, config: Any = None) -> Dict[str, Any]:
        """
        执行单个监控指标的核心逻辑

        根据 monitor_type 动态加载对应的监控类并执行

        Parameters
        ----------
        monitor_id : str
            监控指标ID
        biz_date : str
            业务日期
        dimension : str
            维度代码

        Returns
        -------
        dict
            执行结果
        """
        try:
            # 1. 获取监控配置
            if not config:
                config = self.monitor_config_dao.get_monitor_config_by_id(monitor_id)

            if not config:
                return {
                    "monitor_id": monitor_id,
                    "status": "not_found",
                    "error": "配置不存在"
                }

            monitor_type = config.monitor_type
            logger.debug(f"监控类型: {monitor_type}, 监控项: {config.monitor_item}")

            # 2. 根据 monitor_type 或 monitor_id 加载对应的监控类
            monitor_instance = self._load_monitor_class(monitor_type, monitor_id)
            if not monitor_instance:
                return {
                    "monitor_id": monitor_id,
                    "status": "error",
                    "error": f"不支持的监控类型: {monitor_type}"
                }

            # 3. 执行监控
            result = monitor_instance.execute(
                biz_date=biz_date,
                monitor_id=monitor_id,
                dimension=dimension,
                config=config
            )

            # 4. 处理结果
            if isinstance(result, dict) and "status" in result:
                return {"monitor_id": monitor_id, **result}
            if isinstance(result, list):
                return {
                    "monitor_id": monitor_id,
                    "status": "success",
                    "data_count": len(result),
                    "results": [r.to_dict() if hasattr(r, 'to_dict') else r for r in result]
                }
            elif hasattr(result, 'to_dict'):
                return {
                    "monitor_id": monitor_id,
                    "status": "success",
                    "data_count": 1,
                    "results": [result.to_dict()]
                }
            else:
                return {
                    "monitor_id": monitor_id,
                    "status": "success",
                    "data_count": 0,
                    "results": []
                }

        except Exception as e:
            logger.error(f"执行监控指标 {monitor_id} 异常: {e}")
            return {
                "monitor_id": monitor_id,
                "status": "error",
                "error": str(e)
            }

    def _discover_monitors(self) -> Dict[str, type]:
        """Discover monitor classes once and instantiate a fresh object for each run."""
        from monitors.monitor_base import MonitorBase
        discovered = {}
        root = Path(__file__).parent
        for source in root.rglob("*.py"):
            module_name = "monitors." + ".".join(source.relative_to(root).with_suffix("").parts)
            if module_name.endswith((".monitor_base", ".monitor_runner")):
                continue
            try:
                module = importlib.import_module(module_name)
            except ImportError as exc:
                logger.warning(f"Skipping unavailable monitor module {module_name}: {exc}")
                continue
            for _, cls in inspect.getmembers(module, inspect.isclass):
                if cls is MonitorBase or not issubclass(cls, MonitorBase):
                    continue
                if cls.__module__ != module.__name__:
                    continue
                try:
                    monitor_id = getattr(cls(), "monitor_id", None)
                except Exception as exc:
                    logger.warning(f"Could not initialize monitor {cls.__name__}: {exc}")
                    continue
                if monitor_id:
                    discovered[monitor_id] = cls
        return discovered

    def _load_monitor_class(self, monitor_type: str, monitor_id: str = None):
        """
        根据监控类型动态加载对应的监控类实例

        Parameters
        ----------
        monitor_type : str
            监控类型，如: "白名单/黑名单", "投资金额" 等
        monitor_id : str, optional
            监控指标ID，用于精确定位具体的监控类

        Returns
        -------
        MonitorBase or None
            监控类实例，如果类型不支持则返回 None
        """
        try:
            if self._discovered_monitor_classes is None:
                self._discovered_monitor_classes = self._discover_monitors()


            # 优先使用 monitor_id 精确匹配（全局 MONITOR_ID_MAP）
            if monitor_id and monitor_id in MONITOR_ID_MAP:
                module_path, class_name = MONITOR_ID_MAP[monitor_id]
                logger.debug(f"使用 MONITOR_ID_MAP: {monitor_id} -> {module_path}.{class_name}")

                module = importlib.import_module(module_path)
                monitor_class = getattr(module, class_name, None)
                if not monitor_class:
                    logger.error(f"模块 {module_path} 中未找到类 {class_name}")
                    return None

                logger.info(f"成功加载监控类: {class_name} (monitor_id={monitor_id})")
                return monitor_class()

            if monitor_id in self._discovered_monitor_classes:
                return self._discovered_monitor_classes[monitor_id]()

            # 备用方案：使用 monitor_type 模糊匹配（全局 MONITOR_TYPE_MAP）
            if monitor_type not in MONITOR_TYPE_MAP:
                logger.warning(f"监控类型 '{monitor_type}' 尚未在 MONITOR_TYPE_MAP 中配置")
                return None

            module_paths = MONITOR_TYPE_MAP[monitor_type]
            logger.debug(f"使用 MONITOR_TYPE_MAP: {monitor_type} -> {module_paths}")

            # 遍历所有关联模块，查找匹配的监控类
            for module_path in module_paths:
                module = importlib.import_module(module_path)

                for name in dir(module):
                    obj = getattr(module, name)
                    if (hasattr(obj, '__bases__') and
                        any(base.__name__ == 'MonitorBase' for base in obj.__bases__) and
                        obj.__name__ != 'MonitorBase'):

                        if monitor_id:
                            temp_instance = obj()
                            if hasattr(temp_instance, 'monitor_id') and temp_instance.monitor_id == monitor_id:
                                logger.info(f"成功加载监控类: {name} (monitor_id={monitor_id})")
                                return temp_instance
                        else:
                            logger.info(f"成功加载监控类: {name}")
                            return obj()

            logger.error(f"在类型 '{monitor_type}' 的所有模块中均未找到监控类")
            return None

        except Exception as e:
            logger.error(f"加载监控类失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def run_by_monitor_type(self, monitor_type: str, biz_date: str, dimension: Optional[str] = None) -> Dict[str, Any]:
        """
        执行指定监控类型的所有指标

        Parameters
        ----------
        monitor_type : str
            监控类型，如: "black_white", "investment_amount" 等
        biz_date : str
            业务日期
        dimension : str, optional
            维度代码

        Returns
        -------
        dict
            监控结果摘要
        """
        biz_date = normalize_business_date(biz_date)
        logger.info(f"开始执行监控类型: {monitor_type}, 业务日期: {biz_date}")

        try:
            if self.monitor_config_dao.get_snapshot_count(biz_date) == 0:
                return {"status": "no_data", "monitor_type": monitor_type, "biz_date": biz_date}
            # 1. 获取该类型下所有启用的监控配置
            configs = self.monitor_config_dao.get_monitor_configs()
            type_configs = [c for c in configs if c.monitor_type == monitor_type]

            if not type_configs:
                logger.warning(f"监控类型 {monitor_type} 没有启用的指标")
                return {
                    "status": "no_config",
                    "monitor_type": monitor_type,
                    "biz_date": biz_date
                }

            logger.info(f"找到 {len(type_configs)} 个 {monitor_type} 类型的监控指标")

            # 2. 逐个执行
            results = []
            success_count = 0
            fail_count = 0

            for config in type_configs:
                try:
                    # 确定维度：从数据库获取受托维度列表
                    trust_dimensions = []
                    if dimension:
                        # 如果指定了维度，只执行该维度
                        trust_dimensions = [dimension]
                    else:
                        # 从数据库中获取该监控指标的所有受托维度
                        dimension_datas = self.monitor_config_dao.get_trust_dimension_by_monitor_id(config.monitor_id)
                        trust_dimensions = [item["trust_dimension"] for item in dimension_datas]

                        # 如果数据库中没有配置维度，使用默认值
                        if not trust_dimensions:
                            trust_dimensions = [config.dimension_code]

                    logger.debug(f"监控指标 {config.monitor_id} 执行维度: {trust_dimensions}")

                    # 循环执行每个维度
                    for dim in trust_dimensions:
                        result = self._execute_single_monitor(
                            monitor_id=config.monitor_id,
                            biz_date=biz_date,
                            dimension=dim,
                            config=config,
                        )
                        results.append(result)

                        if result.get("status") == "success":
                            success_count += 1
                        else:
                            fail_count += 1

                except Exception as e:
                    logger.error(f"执行 {config.monitor_id} 失败: {e}")
                    fail_count += 1

            logger.info(f"监控类型 {monitor_type} 执行完成: 成功 {success_count}, 失败 {fail_count}")

            return {
                "status": "completed",
                "monitor_type": monitor_type,
                "biz_date": biz_date,
                "total_count": len(type_configs),
                "success_count": success_count,
                "fail_count": fail_count,
                "results": results,
            }

        except Exception as e:
            logger.error(f"执行监控类型 {monitor_type} 失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "monitor_type": monitor_type,
                "biz_date": biz_date,
                "error": str(e)
            }
