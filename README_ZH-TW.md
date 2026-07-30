[English](README.md) | **繁體中文**

# 資料品質監控平台

本專案建立一套自動化資料品質監控與異常告警機制，針對資料倉儲（Data Warehouse）之資料進入報表、分析模型與決策流程前的時效性、完整性及基本結構進行檢核。

透過每日自動執行、集中監控與即時通知，將過去依賴使用者回報的被動排查模式，轉為主動發現與快速定位，降低異常資料持續影響下游分析與決策的風險。

本案例實際應用於製造資料，支援 [最低成本 BOM 資料與決策平台](https://github.com/ChienChienChien/BOM_Management_Platform/blob/main/README_ZH-TW.md) 與 [原料庫存推估與庫存告警系統](https://github.com/ChienChienChien/Material_Forecasting_System/blob/master/README_ZH-TW.md)；檢核架構亦可依不同資料表與使用情境設定規則，延伸至其他資料來源及分析流程。

## 目的

資料倉儲（Data Warehouse）每日接收來自大型系統（例如MES, SAP）的資料，然而資料傳輸的過程中，容易發生以下問題導致資料延遲、缺漏或不完整：

- 來源系統與資料倉儲的效能問題
- 資料庫鎖定或查詢效能問題
- 來源系統的資料表規格修改
- 轉檔程式異常

本專案以監控的角度，透過每日自動檢核、集中監控與異常通知，讓有問題的資料能在影響下游分析運用前被發現，提升決策資料的可信度。

## 成果與作法

### 1. 建立資料檢核規則

| 檢核面向 | 檢核內容 | 管理目的 |
|---|---|---|
| 時效性 | 資料表是否於每日預期時間完成更新 | 避免下游系統使用過期資料 |
| 完整性 | 資料表是否為空 | 辨識資料缺漏或轉檔不完整 |
| 基本結構 | 必要欄位是否存在 | 提前發現來源結構異動造成的流程風險 |

### 2. 將資料檢核轉為每日自動化流程

檢核程式部署於 Windows Server，由 Windows 工作排程器於每天上午 8 點自動觸發。Python 使用 Great Expectations 執行資料品質檢核，將整體結果與各項規則明細寫入 SQL Server，並供 Power BI 更新監控畫面。

透過自動檢核與集中呈現，資料品質管理不再依賴人工逐一確認；維護人員可以從歷史紀錄快速掌握異常資料表、發生時間與未通過的規則，縮短問題確認與定位所需的時間。

### 3. 從使用者回報轉為主動異常通知

當 SQL Server 新增一筆狀態為 `Warning` 的檢核結果時，Power Automate 會自動將異常發布至 Teams，讓報表使用者與維護人員及早掌握問題。

維護人員收到異常通知後，可再由 Power BI 上的資料異常監控表 （如下圖）中查詢檢核明細，確定問題再聯繫 IT 或相關系統負責人處理。

<table>
  <tr>
    <td align="center" width="100%">
      <img src="docs/images/data-quality-warning.png" alt="資料品質 Warning 紀錄與檢核明細" width="900"><br>
    </td>
  </tr>
</table>

> Warning 範例：上方呈現異常歷史紀錄，下方保留單次檢核的規則結果與明細，協助維護人員快速確認異常來源。

## 架構

```mermaid
flowchart TB
    A["資料倉儲"] --> C["Python/Great Expectations<br/>資料品質檢核"]
    C --> D["SQL Server<br/>檢核摘要與規則明細"]
    D --> E["Power BI<br/>監控與歷史追蹤"]
    D --> F["Power Automate<br/>監聽新增紀錄"]
    F --> G{"狀態為 Warning？"}
    G -->|是| H["Teams<br/>異常通知"]
```

## 技術

| 類別 | 技術 | 用途 |
|---|---|---|
| 檢核程式 | Python、Great Expectations | 執行資料時效性、完整性與基本結構規則 |
| 資料儲存 | SQL Server | 儲存檢核摘要、規則明細與歷史紀錄 |
| 視覺化 | Power BI | 集中呈現異常狀態與檢核結果 |
| 流程通知 | Power Automate、Microsoft Teams | 依 `Warning` 紀錄觸發並發布異常通知 |
| 執行環境 | Windows Server、Windows 工作排程器 | 每日自動執行檢核流程 |
