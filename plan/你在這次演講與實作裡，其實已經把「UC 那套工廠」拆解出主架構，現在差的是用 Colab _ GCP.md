<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# 你在這次演講與實作裡，其實已經把「UC 那套工廠」拆解出主架構，現在差的是用 Colab / GCP 做出一個縮小版、日頻版本。下面整理成「他們在做什麼」＋「你目前做到哪裡」＋「接下來在 Colab/GCP 可以怎麼走」。


***

## UC 的平台與進步方向（你聽到的重點）

- 他們強調的是「平台驅動」：從 Quant 1.0 的單一策略與人工經驗，到 Quant 2.0 的資料平台與回測系統，再到 Quant 2.5–3.0 導入 AI 因子、大量 GPU、雲端，讓因子 throughput 大幅增加。[1][2]
- 回測系統目標是能在 tick 級完整 replay 4.5 年市場，從「一筆一筆重播要跑 20 多天」優化到「工程化系統＋多執行緒＋CUDA 後，只要幾分鐘」，這樣每天早上開盤前就能把新條件全部測完。[2]
- 他們自建 Domain‑specific Runtime Library（DRL）：把常見運算（均線、相關矩陣、各種技術指標）抽成 API，加上三層快取（原始資料、表達式、dataset），實測讓 MA20 算法加速 30 倍、相關矩陣加速 400 倍，避免每個研究員各寫一份慢又容易有 bug 的 code。[3][1]
- 硬體上有自有 GPU 叢集（如數百～上千張 A100 / H200）再加 AWS，專門用來：在像 Alpha158/360 這種高維資料集上訓練大量模型、做自動因子挖掘、海量回測與強化學習實驗，目標是每月可以測數百～上千個新因子組合。[4][5][1]

***

## 你現在在 Colab 已經做到的事情

- 你已經在 Colab 成功安裝 Qlib，下載官方 `cn_data` 日資料，並用 `D.features` 把 CSI300 的 `$close` 拉出來，這等同於連上他們的「資料層」但用的是公開日頻資料。[6][7]
- 你用 5 日報酬當簡單訊號，套 Qlib 的 `TopkDropoutStrategy` 做 Top‑K 選股，透過 `backtest_daily` 完成 2017–2020 的日回測，拿到每日報表 `report` 和持股矩陣 `positions`。[8]
- 接著用 `risk_analysis` 算出：含成本年化超額報酬約 6.6%、information ratio 約 0.86、最大回撤約 -9%，這就是一份簡化版的「策略體檢表」——跟 UC Demo4 那張 Sharpe / Max Drawdown 表本質上一樣，只是頻率與標的不同。[9][10]

換句話說，你已經把「資料層 → 策略層 → 回測層 → 風險分析」這條管線在日資料上跑通了，只是現在訊號很簡單（5 日動能），還沒接上真正的 Alpha158/360 或你關心的台股 / 台指資料。

***

## 在 Colab 上可以做到的「UC 縮小版」

不靠 A100、只用 Colab CPU + 日 K，其實可以復刻 70% 的方法論：

- 資料層：
    - 用 FinMind 把台股日 K、財報、三大法人拉進一張標準表（`date, stock_id, open, high, low, close, volume, factor` 再加幾個基本面欄位），Schema 參考 Qlib 的要求即可。[7][11]
    - 把這張表存成 SQLite / Parquet，等於你的「本地 Data Platform」，Colab 掛 Google Drive 就能讀寫。
- 因子層（對應 Alpha158/360 思想）：
    - 先挑 10–20 個你「有直覺、看得懂」的因子：動能（3/6/12 個月）、波動度、價值（E/P、B/P）、量異常、價格遠離均線、法人買超等，這些都能用日資料實現，結構類似 Alpha158 裡的價量特徵。[5][12]
    - 用大模型幫你把論文因子翻成數學公式 + Pandas／SQL 步驟，再在 Colab 上算出因子矩陣，然後用剛跑過的 Qlib 回測流程驗證 IC 與分組報酬。
- 回測與風險層：
    - 延續你剛才的 TopK pipeline：把 `pred_score` 換成「某個因子值」或「多因子模型的預測分數」，一樣用 `backtest_daily + risk_analysis`，就能快速得到年化報酬、IR、MDD 等指標。
    - 這一層其實就是 UC 投影片中「Case Study：從 paper 因子 → 台股驗證 → 小金額實測 → 每日／每週監控」的日線版本，只是你回測的是 5～10 年日資料，而不是 4.5 年 tick。
- AI / LLM 協助（自動因子挖掘「輕量版」）：
    - 從 UC 投影片與你錄的逐字稿可以看到，他們也強調用論文、機器學習模型產生大量候選因子，再做嚴格驗證。[2]
    - 在你的架構裡，可以讓大模型負責：讀 paper → 產生候選因子公式 → 轉成 SQL/Pandas → 產生多版本設定檔（rebalance 週期、持股數、成本假設），再交給 Colab 的 Qlib pipeline 自動跑一輪；最後再由大模型幫你摘要哪幾個因子在台股有效。

***

## 什麼時候需要 GCP / GPU，怎麼用才值得

你現階段用 Colab CPU 跑日資料，已經足以涵蓋：台股日 K、50 檔股票、10 年歷史、數十個因子與 TopK 回測，不會有速度瓶頸。[13][4]
考慮 GCP / GPU 的合理時機是：

- 你開始引入「分鐘級資料」或「上百檔股票的 1 分鐘 K」、且要做多策略回測時，Colab CPU 會變得很慢，這時可以在 GCP 開一台有 T4 / L4 的 VM 或 Vertex Notebook，專門跑回測。
- 你想用深度學習模型（LSTM、Transformer、TFT 等）直接吃 Alpha158/自製因子矩陣做預測，再用 Qlib 的 `Model` 介面整合到回測流程，這類模型在 GPU 上會比 CPU 快數十倍。[14][5]
- 你真的要做「自動因子挖掘＋遺傳演算法」這類會同時訓練上百個模型的實驗，GPU + GCP 的好處是可以長時間穩定跑，不受 Colab 斷線限制。

就算上 GCP，也可以沿用現在這套：

- 資料存在 GCS / BigQuery；
- 計算用 Qlib + PyTorch/LightGBM；
- 結果寫回 SQLite / Postgres；
- 大模型依舊由你本機或雲端 API 提供。

***

## 對你來說的下一步建議

- 先把「今天在 Qlib 上跑通的範例」改成台股日資料（用 FinMind），確認 `D.features / backtest_daily / risk_analysis` 在你自己資料上能跑。
- 接著按 UC 的路線，選一篇你感興趣的因子論文（或 UC 投影片中的 Demo 因子），請大模型幫你翻成數學公式與 Colab 公式，實際做一個「Case Study：paper 因子在台股 5 年日線上的表現」。
- 全程都先用日資料與 CPU，等真的覺得「算太慢」再考慮 GCP / GPU；這樣你保留 UC 那套的核心精神（平台化、因子工廠、風險優先），但成本與複雜度都壓在適合個人投資者的等級。

我們繼續剛剛的討論，還有這些研究在後續交易可以帶來什麼樣子的變化，還有後續該怎麼利用研究的成果交易

這些研究的直接影響，是把你從「看盤＋經驗」的交易方式，拉到「平台驅動、指標驅動」的決策流程；接下來只要多走幾步，Colab 上那條 Qlib 管線就可以變成你每日/每週實際下單的核心引擎。你會從「偶爾用回測參考一下」變成「所有部位變動都有事先定義好的因子、規則與風險指標支撐」。[^1_1][^1_2]

***

## 會對你的交易帶來哪些變化

- 從「單筆 idea」變成「組合＋風險」思維：每個新策略都會先經過 Qlib 的回測與 `risk_analysis`，你看的是年化報酬、IR、MDD，而不是只看幾筆漂亮交易，久了你的習慣會變成「先問組合風險能不能接受」。[^1_3][^1_1]
- 從「盤中臨時決定」變成「例行流程」：每天或每週固定時間，先更新資料→算因子→生成排名和目標持股→得到一份 trade list，再依照規則執行，減少情緒化進出場。這種「例行 routine → 產生下一輪信號」的設計其實就是 Qlib online serving 文件在做的事，只是你用日頻版本。[^1_2]
- 從「策略好像有用」變成「持續監控＋淘汰」：你可以把 IC、IR、rolling drawdown 做成簡單表或圖，定期檢查某個因子/策略是否開始衰退，必要時降權或下架，這跟近期很多 Alpha158 等因子研究強調的 alpha decay 監控是一樣的精神。[^1_4][^1_1]

***

## 怎麼把研究管線接到實盤流程

可以把你現在的 Qlib Notebook 想成「研究版」，目標是把它拆成一個穩定的「日常信號管線」：

1. 資料 \& 因子更新：每天收盤後，Colab（或之後 GCP）腳本自動抓 FinMind/其他來源的台股日 K＋財報/籌碼，寫進 SQLite/Parquet，然後依照你定義好的公式算出 10–20 個因子並存進 `factors.db`。[^1_5][^1_1]
2. 產生預測分數 `pred_score`：可以是
    - 單一排序因子（例如 6 個月動能、E/P 反轉分數）
    - 多因子線性組合
    - 之後在 GPU 上訓練的 ML 模型預測分數（吃 Alpha158 風格特徵）
然後餵進你已經熟悉的 `TopkDropoutStrategy + backtest_daily` 那一套，只是這次是「今天要 rebalance 的實際持股建議」。[^1_6][^1_1]
3. 輸出 trade list：由程式輸出一個簡單表格：`date, stock_id, target_weight, current_weight, diff, side`，這一張就是你隔天開盤前的「下單指令」，先手動照單調整，未來可以再考慮接券商 API 做半自動。這種「研究→信號→下單」的 workflow 與典型 quant R\&D→production 流程是一致的。[^1_7][^1_3]

***

## 實際操作路線：先變成「研究驅動的人工交易」

結合你現在的條件（Colab、有限時間、偏日頻），比較合理的演進是三階段，而不是一次就全自動：

- 第 1 階段：研究驅動人工交易
    - 每週固定跑一次 Qlib 管線，產出「下週 TopK 名單＋建議權重」，你只用小部分資金（例如總資金的 10–20%）照表調整，其他部位還是照原本習慣操作。
    - 同時持續記錄「實盤績效 vs 回測預期」，看滑價、手續費、可成交量對日線因子策略影響多大，這段時間當成「live out-of-sample」。[^1_1][^1_3]
- 第 2 階段：半自動組合管理
    - 等你對因子表現有信心後，把「目標持股＋權重」規則寫死：例如「每月第 1 個交易日 rebalance、最多 10 檔、單檔不超過 15%、產業權重不超過 40%」。
    - Colab/GCP 腳本負責每天更新資料和計算信號，你只在預定的 rebalance 日把 trade list 匯出 CSV，然後用券商工具/簡單腳本一次送單，實際操作時間壓到幾分鐘內。這就是很多量化平台強調「從研究環境到前台決策的順暢移轉」。[^1_1][^1_7]
- 第 3 階段：多策略資金配置
    - 當你累積了數個有統計優勢的策略（例如：價值型、動能型、低波動、指數增強），可以額外做一層「策略層資金分配」：根據各策略近期 IR、drawdown、相關係數決定每個 bucket 配多少資金。
    - 這一層也可以用 Qlib 或簡單 Python 腳本做資產配置優化，本質上類似專業 quant 使用整合平台來同時管理多個模型與執行器。[^1_1][^1_7]

***

## 用平台把「風險優先」落實在實盤

你現在已經看得到年化超額報酬、IR、最大回撤，下一步是把這些數字變成具體管控規則，真的綁在交易上：

- 在研究端：對每個策略固定輸出一份「風險體檢表」，指標格式統一（年化、IR、MDD、換手率、最大連虧天數），方便你橫向比較與挑選要上實盤的策略。這和很多量化平台把「alpha、風險模型、執行」整合一條龍的做法一致，只是你用的是日頻縮小版。[^1_8][^1_1]
- 在實盤端：預先定義幾條硬規則，例如「策略 rolling 12 個月 MDD 超過 -15% 就減半資金」、「rolling IR 跌破 0 就暫停加碼」、「單日成交金額不超過近 20 日平均成交量的 10%」，讓「什麼時候縮手」不用臨時想，而是回測中就設計好。這種有明確風險閾值的治理，也是近期很多 R\&D→live trading 框架強調的一環。[^1_9][^1_7]

***

## 接下來可以做的三件具體事

- 把現在 CSI300 的 Qlib Notebook 完整「搬到台股」，讓 `D.features / backtest_daily / risk_analysis` 在你的 FinMind/本地資料庫上穩定跑一輪；這會是第一個真正「可以每天/每週重複執行」的台股管線。[^1_5][^1_1]
- 選一個你直覺最強的因子（例如 6 或 12 個月動能、E/P 反轉或法人買超），做一個「paper 因子在台股日資料上的 Case Study」，然後把回測規則直接轉成「小資金實盤規則」，開始第 1 階段的「研究驅動人工交易」。[^1_3][^1_1]
- 同時設計一個最簡版的「每日/每週流程清單」：什麼時候更新資料、什麼時候重跑 Notebook、怎麼輸出 trade list、什麼條件要減碼/停機，先手寫出來，再慢慢自動化。這樣你的 Colab/GCP 研究就會真正變成一個小而完整的「個人 UC 工廠」。[^1_2][^1_1]

如果你願意，下一步可以一起把「第 1 階段」具體化：例如挑一個因子＋一個台股標的範圍，直接寫出「實盤規則草稿」（頻率、持股上限、風險線），再回頭看需要補哪些研究。
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_16][^1_17][^1_18][^1_19][^1_20][^1_21][^1_22][^1_23][^1_24][^1_25][^1_26]</span>

<div align="center">⁂</div>

[^1_1]: https://blog.csdn.net/D1237890/article/details/153350533

[^1_2]: https://qlib.readthedocs.io/en/v0.9.2/component/online.html

[^1_3]: interests.finance_tools.qlib

[^1_4]: interests.machine_learning_tools.qlib

[^1_5]: https://help.darwinex.com/quant-workflow-algorithmic-trading-strategy-rd-in-python

[^1_6]: projects.quant_strategy_roadmap

[^1_7]: https://arxiv.org/html/2502.16789v1

[^1_8]: https://www.finlab.tw/qlib-intro/

[^1_9]: interests.finance.quantitative_investing

[^1_10]: tools.workflow_automation

[^1_11]: https://github.com/microsoft/qlib

[^1_12]: https://www.thegoldensource.com/quant-research-development/

[^1_13]: interests.quantitative_trading

[^1_14]: https://www.factset.com/solutions/quantitative-research

[^1_15]: https://openreview.net/pdf/b552ab06d347a31887bbd9310d0e372405a60755.pdf

[^1_16]: https://www.youtube.com/watch?v=MFIV_OHaRx0

[^1_17]: https://www.facebook.com/will.fans/posts/微軟推出-qlib-框架一套以-ai-導向的量化交易平台讓你以-ai-為名自由創作自己的程式交易策略如果有賺錢記得跟我說-/3927349217294193/

[^1_18]: https://www.blog.brightcoding.dev/2025/08/24/veighna-a-python-platform-for-algorithmic-and-ai-powered-trading/

[^1_19]: https://www.reddit.com/r/learnmachinelearning/comments/kh9k5l/intro_to_microsofts_qlib_easily_code_practical/

[^1_20]: https://www.youtube.com/watch?v=_zeYJ-p8ZQo

[^1_21]: https://blog.csdn.net/m0_59164304/article/details/144788762

[^1_22]: https://www.reddit.com/r/quant/comments/14bwr4f/quantitative_researchers_what_do_you_actually_do/

[^1_23]: https://github.com/Floxym/financial-chat-Finance-NLP-Chatbots

[^1_24]: https://raw.githubusercontent.com/vnpy/vnpy/master/README_ENG.md

[^1_25]: https://www.interaction-design.org/literature/article/how-to-fit-quantitative-research-into-the-project-lifecycle

[^1_26]: https://www.sciencedirect.com/science/article/abs/pii/S0926580508000265


---

# 好，把所有內容整理好，我後續要交給其他ai團隊，討論，

下面是整理給「其他 AI 團隊」看的說明稿，涵蓋：整體目標、UC 方法論抽象版、你目前做到哪裡、縮小版平台設計、以及如何接到實際交易與分階段目標。

***

## 目標：個人版 UC 因子工廠（日頻）

- 目標不是複製 UC 的 tick 級超大叢集，而是做一個「日頻、台股為主」的縮小版工廠：同樣有資料層、因子層、回測層、風險層與執行流程，但所有東西都跑在 Colab / GCP + 日 K 上即可。[^2_4][^2_7]
- 平台核心能力：
    - 能穩定取得台股日資料（價量＋財報＋籌碼），並以標準 schema 儲存。
    - 能快速定義與計算一批因子（類 Alpha158/360 思想），並在統一的回測框架中跑 IC / 分組報酬 / TopK 策略。
    - 能把回測結果轉成「實際可執行的持股建議與風險體檢表」，支援後續自動化或半自動化交易。[^2_1][^2_5]

***

## UC / Qlib 方法論的抽象版規格

- 平台驅動思維：從「單一策略＋人工經驗」升級為「資料平台＋回測系統＋因子工廠」，再進一步導入 ML / 深度學習與 GPU 做大規模因子挖掘與模型訓練，提高單位時間可測試的因子數量與策略組合數量。[^2_7][^2_8]
- 工程化回測與 DRL 思想：
    - 回測層要支援高速重播歷史資料、統一交易規則與成本模型，讓研究員可以反覆驗證不同因子與策略，而不是每人各寫一份 ad‑hoc script。[^2_4][^2_7]
    - 以 domain‑specific runtime library 方式把均線、相關矩陣、技術指標與常見運算抽象成 API，配合快取與向量化計算，避免每個人重算與踩同樣的 bug；Qlib/FinLab 都朝這個方向實作（例如 Alpha158/360 這類預算好的特徵庫）。[^2_5][^2_1]
- 雲端與 GPU 的角色：在專業場景用於高維特徵（Alpha158/360）上的 ML/深度學習訓練、自動因子搜索與大量回測；在本案中先以 CPU + 日資料為主，只有在需要深度模型或分鐘級回測時才遷移到 GCP GPU。[^2_8][^2_7]

***

## 目前已完成的研究管線（使用者現況）

- 使用者已在 Colab 成功安裝 Qlib，使用官方 `cn_data` 日資料，並透過 `D.features` 讀取指數成分股的收盤價等特徵，等同於已經串上 Qlib 的標準資料層與資料服務介面。[^2_7][^2_4]
- 已完成一個基於「5 日報酬」的簡單 TopK 選股策略：
    - 用 5 日報酬作為單一信號，配合 Qlib 的 `TopkDropoutStrategy` 跑 2017–2020 日頻回測，成功產出每日損益報表與持股矩陣。
    - 透過 `risk_analysis` 取得含成本的年化超額報酬、IR、最大回撤等指標，形成類似 UC demo 中 Sharpe / Max Drawdown 的風險體檢表，證明「資料層 → 策略層 → 回測層 → 風險分析」這條管線在日資料上已跑通。[^2_7][^2_4]
- 差異在於：
    - 目前訊號仍是非常簡化的動能（5 日），尚未引入 Alpha158/360 風格的多維因子，也尚未切換到台股資料。
    - 研究成果尚未系統化地接到「日常產 signal → 生成 trade list → 實盤執行」的固定流程。[^2_7]

***

## 縮小版平台：AI 團隊預期要實作的模組

1. 資料層（Data Platform，日頻）
    - 資料來源：優先使用 FinMind 或類似 API，取得台股日 K、三大法人、融資融券、財報與基本面指標；必要時也可加入自建資料（例如自算技術指標）。[^2_1][^2_5]
    - 統一 schema：建議使用寬表或長表格式，例如 `date, stock_id, open, high, low, close, volume, turnover, margin, foreign, eps, roe, ...`，並寫入 SQLite / Parquet，掛載在 Google Drive 或 GCS 供 Colab/GCP 使用。[^2_1][^2_5]
    - 工具需求：需要一組穩定的「更新腳本」與簡單監控（錯誤重試、缺值處理、log），確保每日/每週能自動更新資料而不依賴手動操作。
2. 因子層（Factor Library，Alpha158/360 思想的日頻版本）
    - 先實作 10–20 個「有經濟直覺、計算簡單、完全基於日資料」的因子，範例：
        - 價量類：不同視窗的動能（3/6/12 個月）、波動度、成交量異常、價格相對均線乖離。
        - 基本面與價值：E/P、B/P、ROE、ROA、營收成長等可從公開財報推得的比率。
        - 籌碼類：外資/投信/自營商買超佔成交量比例、連續買超天數等。[^2_1][^2_5]
    - 技術要求：
        - 以向量化 Pandas / NumPy / SQL 或參考 Qlib/FinLab 的實作風格，封裝成可重複利用的因子計算 API，避免每個 Notebook 重寫。
        - 輸出標準化的「因子矩陣」（index: date, columns: stock_id, value: 因子值），方便進入回測與 IC 分析。
3. 回測與風險層（Backtest \& Risk Analytics）
    - 對接 Qlib 的日頻回測：將上述因子或其組合映射為 `pred_score`，透過固定策略模板（如 TopK / 分組多空 / 行業中性等）跑長期日頻回測，輸出：
        - 累積報酬曲線與年化/年化超額報酬。
        - Information Ratio / Sharpe、最大回撤、勝率、換手率等標準指標。
        - 因子 IC、Q1–Q5 分組報酬與 t‑stat，用於判斷因子是否具預測力。[^2_5][^2_7][^2_4]
    - 風險治理規則：
        - 為每個策略輸出統一格式的「風險體檢表」（同一組指標），方便比較與篩選。
        - 預先定義實盤風控閾值，例如 rolling 12 個月 MDD、rolling IR 等，一旦超過閾值就標記策略需降權或停用。
4. AI / LLM 協作層（輕量版自動因子挖掘）
    - LLM 任務：
        - 讀論文或簡報內容，萃取出明確的因子定義（數學公式與口語解釋）。
        - 依照本平台的資料 schema，自動生成對應的 Pandas/SQL 因子計算流程與回測設定（rebalance 週期、持股數、成本假設等）。[^2_1][^2_8][^2_5]
    - 自動化流程：
        - 接收「候選因子描述」→ 產生多個 parameterization（不同視窗、不同標準化方法）→ 寫入回測隊列 → 由 Qlib pipeline 自動批次跑完。
        - 最後由 LLM 對「各候選因子在台股的 IC / 回測結果」做結構化摘要，標記值得進一步研究或上實盤的因子。

***

## 與實際交易接軌與分階段目標

1. 交易流程設計（研究 → 信號 → trade list）
    - 每日/每週流程：
        - 收盤後自動更新資料與因子矩陣。
        - 跑一次選定策略群的回測/信號生成（實務上可以只生成「最新一期 signal」，不必每天全回測）。
        - 產生包含 `date, stock_id, target_weight, current_weight, diff, side` 的 trade list，作為隔日開盤前的實際調整依據。[^2_6][^2_7][^2_5]
    - 實作形式：
        - 第 1 階段由人手動依 trade list 下單（研究驅動人工交易）。
        - 後續可接台灣券商 API 或以 CSV 匯入券商工具，升級為半自動/全自動。
2. 三階段落地路線（AI 團隊可對應的里程碑）
    - 階段 1：研究驅動人工交易
        - 目標：讓使用者每週能穩定跑出「TopK 名單＋建議權重」，用小部位（資金的 10–20%）實測，對照回測與實盤差異（滑價、流動性）。
        - 任務重點：資料與因子計算穩定、回測與風險表格式統一、trade list 產出流程順手。
    - 階段 2：半自動組合管理
        - 目標：固定 rebalance 規則（月/雙週），由系統自動產出調整單與紀錄交易日誌，使用者只需審核與一次性送單。
        - 任務重點：策略配置規則寫死（持股數上限、單檔上限、產業集中度限制），並將多策略資金分配簡單化（例如固定權重或基於最近 1 年 IR/風險調整）。[^2_10][^2_5]
    - 階段 3：多策略與風控儀表板
        - 目標：同時管理多個風格（動能、價值、低波等），以簡易儀表板呈現各策略最新 IR、MDD、相關係數與實盤/回測偏離度，支援策略下架與資金再分配決策。
        - 任務重點：集中化的績效與風險監控模組、策略生命週期管理（上架、觀察、停用），以及與 LLM 報告的整合。

如果你願意，下一步可以直接把這份說明當作需求文件，請 AI 團隊先幫你明確切出「資料層腳本」與「因子庫 v1（10–20 個因子）」兩個模組，再決定要先支援哪一個交易階段（多數情況下，會先完成「階段 1：研究驅動人工交易」）。
<span style="display:none">[^2_11][^2_12][^2_13][^2_14][^2_15][^2_16][^2_17][^2_2][^2_3][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://www.finlab.tw/qlib-finlab-implementation-source-code/

[^2_2]: https://lazyinwork.com/2025/05/30/ai量化投資啟航！qlib入門指南，新手也能學，時間不/

[^2_3]: https://www.facebook.com/100091229471511/posts/qlib-在-finlab-的應用提升台股選股效率最近台股中小型股表現低迷但研究的動力卻不能因此停滯這次我們深入整合了-microsoft-開源的量化工具庫-q/523524230698555/

[^2_4]: https://blog.csdn.net/qq_57309855/article/details/141850287

[^2_5]: https://2023meowmiles.com/finlab-完全攻略：用-ai-和-python-打造你的台股量化交易系統/

[^2_6]: https://www.youtube.com/watch?v=5MzV_4aId-k

[^2_7]: https://www.cnblogs.com/sljsz/p/14629526.html

[^2_8]: https://github.com/huzhe007/learn-qlib

[^2_9]: https://www.youtube.com/watch?v=W2_LnUtlgk8

[^2_10]: https://www.thegoldensource.com/quant-research-development/

[^2_11]: interests.finance_tools.qlib

[^2_12]: interests.machine_learning_tools.qlib

[^2_13]: interests.computing_hardware.gpu_colab

[^2_14]: interests.quantitative_trading

[^2_15]: projects.quant_strategy_roadmap

[^2_16]: tools.workflow_automation

[^2_17]: interests.finance.quantitative_investing

