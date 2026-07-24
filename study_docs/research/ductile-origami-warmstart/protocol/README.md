# Protocol Artifact Status

> ⚠️ **HISTORICAL M00 PROTOTYPE／DO NOT EXECUTE AS ACTIVE CONTRACT**

本目錄現有 `experiment-contract.yaml`、`protocol-lock.json`、schemas與registries是 legacy M00 prototype artifacts。

它們：

- 仍指向 legacy `M00` design與 `M00.*` criteria；
- 即使 `protocol-lock.json` 寫有 `lock_state: locked`，也**不代表**通過現行 S00；
- 不可原地改名成 active stage-gated contract；
- 不可作為 S00／S10 已完成的證據；
- 只可作 [S00 design](../designs/staged/s00-evidence-contract-lineage-observability-design.md) 的 migration input。

Active authorities：

- [Research charter](../../surrogate-dse-plan.md)
- [Stage-gated experiment plan](../../ductile-origami-warmstart-experiment-plan.md)
- [Milestone design index](../designs/README.md)

S00 必須建立新的 contract／schema version、重新驗證 observer neutrality、checkpoint parity、lineage與artifact reconciliation，再產生新的 active lock。為保留歷史可追溯性，本目錄現有locked artifacts不直接覆寫。
