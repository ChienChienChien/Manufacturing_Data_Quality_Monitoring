# 製造資料品質監控平台｜架構圖

## 上線期間架構

```mermaid
flowchart TB
    A["製造系統：生產、原料、採購資料"]
    B["資訊單位資料轉檔"]
    C["資料倉儲：BOM 關鍵資料表"]
    D["資料品質檢查引擎：完整性、欄位、空值、新鮮度"]
    E["品質紀錄：摘要、明細、異常證據"]
    F["Power BI：品質狀態與歷史明細"]
    G["Power Automate／Teams：異常通知與協作處理"]
    H["BOM 運算平台"]

    A --> B
    B --> C
    C --> H
    C --> D
    D --> E
    E --> F
    F --> G
    D -. "事前預警與事後定位" .-> H
```

## 各層職責

| 層級 | 主要職責 |
|---|---|
| 製造系統 | 產生 BOM 所需的生產、原料及採購資料 |
| 資訊單位資料轉檔 | 將來源資料定期寫入資料倉儲 |
| 資料倉儲 | 提供 BOM 與其他分析系統使用的整合資料表 |
| 資料品質檢查引擎 | 依排程與設定檔執行表格及欄位規則 |
| 品質紀錄 | 保存資料表摘要與每項規則的明細結果 |
| Power BI | 集中呈現正常、警告、歷史與異常細節 |
| Power Automate／Teams | 將異常轉換成可被相關單位處理的通知 |
| BOM 運算平台 | 使用資料倉儲內容進行 BOM 計算 |

## 品質檢查流程

```mermaid
stateDiagram-v2
    state "等待排程" as Wait
    state "選取資料表" as Select
    state "載入規則" as Load
    state "執行檢查" as Check
    state "保存結果" as Store
    state "更新儀表板" as Refresh
    state "發送異常通知" as Notify
    state "正常完成" as Complete

    [*] --> Wait
    Wait --> Select: 到達監控時段
    Select --> Load: 取得資料表設定
    Load --> Check: 套用品質規則
    Check --> Store: 保存摘要與明細
    Store --> Refresh: 更新監控狀態
    Refresh --> Complete: 全部檢查通過
    Refresh --> Notify: 發現異常
    Notify --> Complete: 通知相關單位
    Complete --> [*]
```

## 品質紀錄模型

```mermaid
flowchart LR
    A["檢查批次"] --> B["資料表摘要"]
    A --> C["規則明細"]
    B --> D["正常／警告"]
    C --> E["欄位與規則"]
    C --> F["異常筆數或觀察值"]
```

摘要紀錄支援儀表板與通知；規則明細則保留問題定位需要的欄位、檢查類型、異常數量與實際值。

## 架構演進

```mermaid
flowchart TB
    subgraph Before[原架構]
        A["製造系統"] --> B["資料轉檔"]
        B --> C["資料倉儲"]
        C --> D["BOM"]
        C --> E["品質監控"]
    end

    subgraph Target[演進架構]
        F["製造系統源頭資料"] --> G["BOM"]
        H["少數仍需轉檔的資料"] --> I["必要品質監控"]
    end

    Before -. "逐步改造" .-> Target
```

平台逐步退場並不代表專案失敗，而是上游架構改善後，原本為轉檔風險建立的控制層已不再需要完整保留。

## 圖示說明

- 實線箭頭代表主要資料或流程方向。
- 虛線箭頭代表監控回饋或架構演進。
- 所有資料來源、資料表及系統名稱均已去識別化。

