<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# 我們可以繼續討論嗎？

當然可以繼續，隨時都可以聊。現在比較需要決定的是，你想從哪一條線接下去：因子回測、LLM 實驗，還是巴菲特 / 段永平那套低頻投資？[^1_1]

## 先確認討論主題

你之前說過希望說明簡明、暫時不要直接丟程式碼，而且偏好用繁體中文來聊這些量化跟投資的問題。
也提到自己資金不大、想用中低頻、不分散集中持股，所以不會去追求 UC 那種高頻、多因子工廠，而是「幾個可靠因子＋價值投資邏輯」。[^1_2]

## 幾個可以接著聊的方向

你現在可以直接選一個，我就往那邊展開（先都只講概念與流程）：

- 在 Colab 上「一步一步」把一個因子（例如動能或 E/P）做完：從資料欄位、因子公式，到怎麼算 Q1–Q5 報酬與 IC（不寫程式，先講清楚每一步做什麼）。[^1_3][^1_4]
- 設計「LLM + SQLite」的自動驗證流程：用小模型一題一題幫你審查因子邏輯，再用簡單統計指標（IC、Q5–Q1、勝率）決定因子 pass / fail。這是你之前問卷式 GA / 小模型方案的延伸版。[^1_5]
- 繼續談巴菲特、段永平在科技潮裡怎麼調整部位，套回 TSMC、Broadcom、Google、Microsoft：什麼價位或情境才叫「極端便宜」，跟你的中低頻操作怎麼對上。[^1_6]
- 更具體地談「怎麼判斷一個因子真的有效」：IC 門檻、正 IC 比例、分組報酬單調性、回撤控制，幫你整理成一個簡單 checklist，之後每個新因子都照這張表走一次就好。[^1_7][^1_8]

你可以直接回：「先從 A / B / C / D 開始」，或用自己的話說「我想先把 XXX 搞懂」，就從那裡接著往下聊。
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: interests.quant_finance_factor_analysis

[^1_2]: https://www.perplexity.ai/search/205a08ef-6a32-4e63-9db8-766e23e23db5

[^1_3]: preferences.communication.style

[^1_4]: preferences.language.preferred_language

[^1_5]: preferences.trading.frequency_and_risk

[^1_6]: https://www.perplexity.ai/search/8f29b494-83a2-4331-8bc9-f7352f4bca4d

[^1_7]: https://www.perplexity.ai/search/387ebd81-0dbd-4214-b05b-c785b7406b2b

[^1_8]: https://www.perplexity.ai/search/0bd364b8-c42f-4e41-bf6b-d98a696c8a4e

[^1_9]: tools.workflow_automation

[^1_10]: https://www.perplexity.ai/search/da8ed60c-31b4-438c-b364-9e2ab82e984d

[^1_11]: interests.investing.value_investing_legends

[^1_12]: https://www.perplexity.ai/search/a4004769-0faa-4877-853e-98514d08cea1

[^1_13]: https://www.perplexity.ai/search/e8ebf940-6523-49ae-8efd-84bbd73f5c69

[^1_14]: https://www.perplexity.ai/search/439ac100-46d3-4cd7-9600-1a4a417a68d6


---

# 我最後詢問，qlib，不重複造輪子，有沒有可以直接利用的專案，開源的

有，但要誠實說：目前沒有「幫你把台灣市場因子都定義好、一鍵回測」的套裝庫；比較成熟的是像 Qlib、Alphalens 這種「框架＋範例因子」，你可以直接拿來用，再稍微改成自己的市場。

## Qlib 本身能用到哪裡

- Qlib 是微軟開源的「AI‑導向量化投資平台」，定位就是從資料、因子建構、模型、到回測的一條龍框架。[^2_1][^2_2]
- 它內建幾套經典因子組（例如 alpha158/alpha360），用一套「表達式語言」來定義技術與基本面因子，並提供現成的資料處理、模型訓練、回測腳本，可以直接跑在它預設的股票資料上（主要是中國 A 股）。[^2_3][^2_1]
- 優點是：你可以不從零寫因子計算與回測引擎，只要把自己的日 K／財報資料轉成 Qlib 要求的格式，就能重複利用它的 DataHandler、因子表達式、訓練與回測流程。缺點是：要自己做「接台股資料」這一步，目前沒有官方台股版本。[^2_1]


## 純「因子分析」工具：Alphalens

- Quantopian 開源的 Alphalens 是專門做「因子效果分析」的 Python 套件，可以把你算好的因子值丟進去，幫你算 IC、分位數報酬、turnover、tear sheet 等，不用自己從頭寫統計與圖表。[^2_4][^2_5]
- 它本身不提供現成因子庫，而是假設你已經有因子值和價格資料；你要做的是把 Qlib/自己計算出的因子輸出成 Alphalens 需要的格式，讓它幫你做標準化的因子檢驗。這對你「驗證因子有效性、不想自己重寫分析工具」很有用。[^2_6][^2_5]


## 全功能平台：QuantConnect / Lean 等

- QuantConnect 的 Lean 引擎是開源的演算法交易平台，提供研究環境、回測引擎和多資產資料介面，社群裡有大量範例策略與因子程式碼可以參考，但沒有像 Qlib 那樣打包成「因子庫」。[^2_7]
- 這類平台主要優勢是：幫你處理資料時間點正確性、手續費、滑價等實務細節；缺點是多數預設生態圈以美股為主，要應用到台股一樣需要自己接資料與改設定。[^2_7]


## 對你來說的實際建議

- 如果目標是「不要重複造輪子」，可以用：Qlib 當因子計算＋模型／回測框架，Alphalens 當因子效果分析工具；你專心把台股 / 台指期日資料轉成 Qlib 格式，就能直接復用他們的 pipeline，而不是自己從零寫一套。[^2_5][^2_1]
- 目前公開、專門針對「台股現成因子庫」的成熟開源專案幾乎沒有，所以完全「一鍵套用台股、連資料都幫你抓好」的方案很難找到；比較實際的是：用這些框架省掉 70% 工程量，剩下 30% 做「接資料＋挑幾個你在意的因子」就好。

如果你願意，下一步可以一起看：在 Qlib 裡選一套現成的因子組（像 alpha158），然後討論要怎麼把你現在的 finmind.db 欄位對應過去，整合到你原本的 SQLite／Colab 流程裡。
<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15][^2_16][^2_17][^2_18][^2_19][^2_20][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://github.com/microsoft/qlib

[^2_2]: https://www.microsoft.com/en-us/research/articles/qlib-2/

[^2_3]: https://github.com/ssvip9527/Qlib

[^2_4]: https://quantopian-archive.netlify.app/notebooks/notebooks/quantopian_notebook_304.html

[^2_5]: https://github.com/quantopian/alphalens

[^2_6]: https://alphalens.ml4trading.io/notebooks/pyfolio_integration.html

[^2_7]: https://www.quantconnect.com

[^2_8]: https://github.com/topics/qlib?o=asc\&s=updated

[^2_9]: https://www.reddit.com/r/quant/comments/1bbn51y/microsofts_qlib/

[^2_10]: https://www.reddit.com/r/CryptoCurrency/comments/1ilevbj/i_made_an_open_source_tool_to_help_you_backtest/

[^2_11]: https://www.pyquantnews.com/free-python-resources/guide-to-quantitative-trading-strategies-and-backtesting

[^2_12]: https://www.quantrocket.com/codeload/quant-finance-lectures/quant_finance_lectures/Lecture38-Factor-Analysis-with-Alphalens.ipynb.html

[^2_13]: https://kernc.github.io/backtesting.py/

[^2_14]: https://www.tejwin.com/news/利用-alphalens-做因素分析-以放空因子為例ii！-tej-量化投資/

[^2_15]: https://github.com/kernc/backtesting.py

[^2_16]: https://www.youtube.com/watch?v=kB-aAgZ-Wis

[^2_17]: https://www.luxalgo.com/blog/backtesting-software-ranked-for-retail-quants/

[^2_18]: https://blog.csdn.net/winter_python/article/details/103253525

[^2_19]: https://github.com/quantopian/alphalens/releases

[^2_20]: https://arxiv.org/pdf/2011.09607.pdf


---

# Qlib，如果要操作，要怎麼作，例如yfinance 下載，或者findmind 怎麼做，先簡明，我沒有使用qlib 的經驗，我主要想使用colab ，我也有使用過cursor ，google antigravity，等等，利用ai編成輔助，問問題

可以，先用「不寫程式碼版」講清楚你在 Colab 上怎麼實際動起來 Qlib，分成 yfinance 跟 FinMind 兩條路。

## 整體方向

Qlib 本身分兩件事：一是拿到資料、轉成 Qlib 格式；二是用它的 workflow 做因子計算、預測、回測。[^3_1][^3_2]
官方已經幫你做好「從 Yahoo Finance 抓資料並轉成 Qlib 格式」的腳本，你在 Colab 只要安裝 Qlib、執行初始化腳本，就能直接跑內建範例（例如 Alpha158）。[^3_2][^3_3][^3_4]

## 在 Colab 用 Qlib + yfinance

- 步驟概念是：在 Colab 安裝 Qlib 套件 → 呼叫 Qlib 提供的「下載資料腳本」從 Yahoo Finance 抓日線價量 → 呼叫 `qlib.init` 指到你下載好的資料夾 → 跑官方範例 workflow（例如 LightGBM + Alpha158），確認 pipeline 正常。[^3_4][^3_5][^3_2]
- 官方文件有明寫「資料來自 Yahoo Finance，如果有更高品質資料，建議自行準備」，所以這條路適合作為「先熟悉 Qlib 用法」的練習環境，不一定拿來做正式台股策略。[^3_6][^3_2][^3_4]

如果你之後說「可以給 code」，可以幫你把這四步寫成最小的 Colab 指令清單，讓你一鍵跑通 Qlib 的 demo。

## 用 FinMind 做成 Qlib 資料（台股）

- FinMind 本身就有完整的台股日線、財報、期貨選擇權資料，還有官方 Python 函式可以直接在程式裡下載日 K、PER、三大法人等，適合當「原始資料來源」。[^3_7][^3_8][^3_9]
- 要接到 Qlib，有兩種思路：
    - 簡易版：直接在 Colab 用 FinMind 下載台股資料，先自己算好因子（例如動能、E/P），不一定硬塞進 Qlib，只用 Qlib 或 Alphalens 這類工具的「因子分析部分」來算 IC、分位數績效。[^3_3][^3_10]
    - 完整版：照 Qlib 的「資料準備流程」，把 FinMind 下載的 CSV/Parquet 按它要求的欄位、目錄結構轉成 Qlib 格式，之後就能用 Qlib 的 DataHandler、Alpha158 之類功能直接在台股上跑，這一段官方有詳細步驟但比較工程化，我可以之後拆小步驟陪你走。[^3_11][^3_3]


## 利用 FinLab／Colab 快速踩點（台股＋Qlib）

- 台灣這邊有團隊已經把 Qlib 包進 FinLab，直接在 Colab 上提供初始化、產生 Alpha158/Alpha360 因子的接口，等於幫你處理掉一大半「Qlib + 台股資料」整合的細節，但官方文章也提醒這套在 Colab 會比較吃 RAM，最好用 Colab Pro。[^3_12][^3_13]
- 實務上可以是：先用 FinLab＋Qlib 在 Colab 上跑一個 Alpha158 的例子熟悉流程，再決定自己要不要用原生 Qlib＋FinMind 重建一份「純開源、可完全客製」的 pipeline。


## 搭配 Cursor／AI 編成的實際用法

- 你的工作流可以設計成：在 Colab / Cursor 先用文字描述「我要：1) 用官方腳本抓 US 股票資料測試 Qlib、2) 之後改用 FinMind 台股資料」，再請 AI 幫你產生對應的安裝、初始化、資料轉換程式碼，遇到錯誤再貼回來一起 debug。
- 建議順序是：先走一遍「Qlib + Yahoo Finance 官方流程」（最快上手），熟悉 `init → 取特徵 → 回測` 這三步，再來我們一起把它換成「FinMind 台股資料版」，這樣你用到的程式碼量會少很多，也不會一下被 Qlib 的細節淹沒。

你可以先跟我說：你想先從哪條路試？A）先用 Qlib + Yahoo Finance 在 Colab 跑官方範例，B）直接想把 FinMind 台股資料塞進去（我就幫你拆成更小的步驟），再視情況決定要不要產生對應的程式碼。
<span style="display:none">[^3_14][^3_15][^3_16][^3_17][^3_18][^3_19][^3_20][^3_21]</span>

<div align="center">⁂</div>

[^3_1]: https://github.com/microsoft/qlib

[^3_2]: https://qlib.readthedocs.io/en/v0.8.3/start/initialization.html

[^3_3]: https://damodev.csdn.net/69250e0b3fd22d045343e76f.html

[^3_4]: https://pypi.org/project/pyqlib/0.5.1/

[^3_5]: https://www.wuzao.com/p/qlib/document/start/initialization.html

[^3_6]: https://qlib.readthedocs.io/en/v0.6.3/start/initialization.html

[^3_7]: https://finmind.github.io

[^3_8]: https://github.com/FinMind/FinMind

[^3_9]: https://finmind.github.io/tutor/TaiwanMarket/DataList/

[^3_10]: https://github.com/quantopian/alphalens

[^3_11]: https://www.aidoczh.com/qlib/component/data.html

[^3_12]: https://www.finlab.tw/qlib-finlab-implementation-source-code/

[^3_13]: https://doc.finlab.tw/details/machine_learning/

[^3_14]: https://qlib.moujue.com/start/initialization.html

[^3_15]: https://git.nju.edu.cn/lance/qlib/-/tree/finco/scripts/data_collector/yahoo

[^3_16]: https://www.reddit.com/r/learnmachinelearning/comments/kh9k5l/intro_to_microsofts_qlib_easily_code_practical/

[^3_17]: https://www.facebook.com/100091229471511/posts/微軟開源-qlib-用-ai-來賺錢但每次都安裝到吐血再也不會了因為我們將相關的功能放入-finlab跟-pip-install-qlib-告別吧請更新至-fi/613531068364537/

[^3_18]: https://ithelp.ithome.com.tw/articles/10343838

[^3_19]: https://www.youtube.com/watch?v=z6a4mQTkMwg

[^3_20]: https://finmindtrade.com

[^3_21]: https://forum.numer.ai/t/microsoft-qlib-ai-quant-workflow-and-backtesting/1315


---

# Qlib，會怎麼跑，需要什麼硬體，t4，還是純cpu ，然後，會輸出什麼，你可以先給我範例嗎？

例如給我輸入輸出，或者執行後會產程什麼結果

Qlib 可以完全只用 CPU 跑；GPU（像 T4）主要是在你用深度學習模型、資料量很大時才會明顯加速。跑完一個標準 workflow 後，會產生：模型預測結果、回測風險報酬統計表、權益曲線／圖表，外加一個實驗資料夾（記錄檔和各種中間結果）。[^4_1][^4_2][^4_3][^4_4]

## 需要的硬體

官方與教學文的建議大概是：Python 3.8–3.12、一般桌機／筆電（Linux/Windows/macOS 都可），記憶體至少 8GB 比較舒服。[^4_5][^4_1]
如果系統沒有安裝 CUDA，Qlib 會自動用 CPU 訓練模型；有 GPU（像 Colab T4）時，才會啟用 GPU 來加速例如 PyTorch / LightGBM 這種模型的訓練，但不是必需的，所以你完全可以先用純 CPU 熟悉流程。[^4_6][^4_7][^4_1]

## 一次 Qlib workflow 在做什麼

典型的做法是用一個設定檔（YAML）描述：市場與資料來源、要用哪一套因子（例如 Alpha360／Alpha158）、模型類型（LightGBM、MLP、LSTM 等），以及回測期間與策略（例如每天挑前 50 名預測分數最高的股票）。[^4_3][^4_8][^4_5]
執行 workflow 命令後，Qlib 會依序：初始化市場環境、載入並處理因子資料、訓練模型、對測試期間產生預測分數、用內建策略模組做回測，最後把結果交給「評估與報表」模組輸出表格與圖表。[^4_4][^4_3][^4_5]

## 輸入大概長什麼樣子

資料輸入：是整理好的日資料庫（存在某個資料夾路徑），欄位包含日期、股票代碼、收盤價、成交量及多個因子欄位，這些欄位被 Qlib 的 DataHandler 讀進來做標準化、缺值處理與排名等前處理。[^4_9][^4_10][^4_3]
設定輸入：是一份 workflow 設定檔，裡面指定資料路徑、使用的因子集合、模型超參數、訓練／驗證／測試區間，還有回測策略（例如 Top-k Dropout）與交易成本參數；你在 Colab 上只要改這個設定檔，就能重複跑不同實驗。[^4_8][^4_3][^4_5]

## 輸出大概長什麼樣子（範例）

1）風險與績效表：回測後會得到一個風險統計表，欄位包含「不含成本的平均超額日報酬與年化報酬」、「含成本後的年化報酬」、「對應的 information ratio / Sharpe 類指標」以及「最大回撤」，讓你一眼就看到策略在回測期間的收益與風險水準。[^4_2][^4_4]
2）權益曲線與明細：另外會有一個「portfolio analysis」資料表，裡面是隨時間變化的累積報酬、淨值、基準指數表現等，可用來畫權益曲線、回撤圖，還有一個 positions 結構紀錄每一天每檔股票的持倉權重；教學文章裡也示範怎麼從這個結果畫出累積報酬線圖。[^4_11][^4_2][^4_4]

## 實驗記錄與檔案結構

Qlib 內建一個「實驗記錄系統」（QlibRecorder），會在每次實驗底下建立一個資料夾，裡面存模型檔、預測分數、回測結果（如 portfolio_analysis）、風險指標 JSON 或 CSV 等，方便之後在程式裡重新載入比較不同實驗。[^4_12][^4_3][^4_5]
在 Colab 的體驗會是：改一份設定檔、執行一次 workflow 指令，過一段時間你會看到一個新的實驗目錄，裡面有回測統計表、權益曲線資料和各種中間結果，你可以再用自己的分析（或請大模型幫你解讀）去判斷這個因子／模型值不值得。[^4_3][^4_4][^4_12]

如果你願意，下一步可以針對「只用 CPU 的最小設定」或「回測結果那張績效表怎麼解讀」挑一個，我再用更具體的例子說明。
<span style="display:none">[^4_13][^4_14][^4_15][^4_16][^4_17][^4_18][^4_19][^4_20][^4_21][^4_22]</span>

<div align="center">⁂</div>

[^4_1]: https://www.xugj520.cn/en/archives/microsoft-qlib-ai-quantitative-investment.html

[^4_2]: https://qlib.readthedocs.io/en/v0.5.1/component/backtest.html

[^4_3]: https://vadim.blog/qlib-ai-quant-workflow-pytorch-mlp

[^4_4]: https://qlib.readthedocs.io/en/v0.9.2/component/report.html

[^4_5]: https://qlib.readthedocs.io/_/downloads/en/v0.8.2/pdf/

[^4_6]: https://vadim.blog/qlib-ai-quant-workflow-adarnn

[^4_7]: https://github.com/microsoft/qlib/issues/47

[^4_8]: https://github.com/microsoft/qlib/blob/main/examples/benchmarks/README.md

[^4_9]: https://qlib.readthedocs.io/en/v0.8.3/start/initialization.html

[^4_10]: https://www.aidoczh.com/qlib/component/data.html

[^4_11]: https://modbus.pl/2025/02/07/python-qlib-ai-algorithmic-trading/

[^4_12]: https://www.aidoczh.com/qlib/component/recorder.html

[^4_13]: https://github.com/microsoft/qlib/issues/1597

[^4_14]: https://github.com/microsoft/RD-Agent/issues/1242

[^4_15]: https://www.reddit.com/r/learnmachinelearning/comments/kh9k5l/intro_to_microsofts_qlib_easily_code_practical/

[^4_16]: https://qlib.readthedocs.io/en/v0.8.4/reference/api.html

[^4_17]: https://www.reddit.com/r/LocalLLaMA/comments/15s8crb/whats_the_bare_minimum_specs_needed_for_running_ai/

[^4_18]: https://www.pugetsystems.com/solutions/ai-and-hpc-workstations/ai-large-language-models/hardware-recommendations/

[^4_19]: https://github.com/microsoft/qlib/blob/main/.github/workflows/test_qlib_from_source.yml

[^4_20]: https://huggingface.co/bigscience/bloom/discussions/58

[^4_21]: https://forums.odforce.net/topic/44520-installing-qlib-package-method/

[^4_22]: https://discuss.huggingface.co/t/loading-quantized-model-on-cpu-only/37885


---

# 如果要處理，需要設計儲存格幾個比較合理

先回答核心：如果是為了讓 Qlib 能吃、又方便你之後自己算因子，單一日頻資料表（或 CSV）一列一檔股票一天，大概「8 個欄位是最低標準，10～15 個欄位就很夠用」。關鍵是先把價量跟調整因子設好，其它都可以後面再加。[^5_1]

## Qlib 最低需要的欄位

Qlib 官方在說明「把 CSV 轉成 Qlib 格式」時，有明講「至少要包含開、高、低、收、量、factor」，並且還要有日期與股票代碼欄位。[^5_1]
所以你要準備的最少欄位是：

- stock_id（或 symbol）
- date
- open（調整後開盤價）
- high（調整後最高）
- low（調整後最低）
- close（調整後收盤）
- volume（調整後成交量）
- factor（還原因子，讓 Qlib 可以從調整價還原成原始價，例如原始收盤 = close / factor）[^5_1]

這樣一張「日 K 主表」就足夠讓 Qlib 建構技術類因子（動能、均線、價量比等），也能用它的表達式引擎算 Ref(\$close, 60) / \$close 這種公式。[^5_1]

## 建議多預留的欄位

在這 8 個基礎欄位外，為了之後做價值／籌碼因子，可以一開始就多放幾個常用欄位（不用太多）：

- money（成交金額，如果 FinMind 有的話）
- 市值或股本（方便算 size、turnover 等因子）
- 產業代碼或產業分類（之後做「產業內排序」很有用）
- 1～數個你已經常用的基本面欄位，例如 pe、pb、eps，如果放在同一張表，轉成 Qlib 格式後也可以直接當 $pe、$pb 這類 feature 用。[^5_2][^5_1]

實務上，一列大概 10～15 個欄位就已經足夠你後面疊加大多數經典因子；真的需要再加新的欄位（例如 ROE、外資累積買超）時，再擴充 schema 就好，不必一開始設到很複雜。

如果你願意，下一步可以一起把你現有 finmind.db 的欄位對一下：看用哪一張表、哪些欄位直接 rename/映射成上面這 8＋幾個欄位，變成一張專門「給 Qlib／因子回測用」的 view 或資料表。

<div align="center">⁂</div>

[^5_1]: https://www.aidoczh.com/qlib/component/data.html

[^5_2]: https://finmind.github.io/tutor/TaiwanMarket/DataList/


---

# Yfinance 有範例嗎？

可以給我一個儲存格來示範嗎？

可以，用 yfinance 先抓一檔美股（這裡用 Apple 當例子），然後整理成類似 Qlib 需要的欄位：`stock_id, date, open, high, low, close, volume, factor`。[^6_1][^6_2][^6_3][^6_4]

## Colab 單一儲存格範例（yfinance → Qlib 風格表格）

```python
# 安裝與匯入套件（在 Colab 一個儲存格直接執行）
!pip install -q yfinance

import yfinance as yf
import pandas as pd

# 1. 用 yfinance 下載日資料（這裡以 AAPL 當範例）
data = yf.download(
    "AAPL",              # 股票代碼
    start="2020-01-01",
    end="2023-12-31",
    interval="1d",
    auto_adjust=False    # 保留原始 Close 和 Adj Close，等等算 factor 用
)

# 2. 整理成表格並重設索引，拿到 Date 欄位
data = data.reset_index()   # 會有 Date, Open, High, Low, Close, Adj Close, Volume 等欄位

# 3. 轉成接近 Qlib 風格的欄位
#    Qlib 文件建議至少有：open, high, low, close, volume, factor，加上 stock_id, date。[web:112]
df = pd.DataFrame({
    "stock_id": "AAPL",                      # 這一列是什麼股票
    "date": data["Date"],                    # 日期
    "open": data["Open"],                    # 開盤價（原始價）
    "high": data["High"],                    # 最高價
    "low": data["Low"],                      # 最低價
    "close": data["Close"],                  # 收盤價（原始價）
    "volume": data["Volume"],                # 成交量
    # Qlib 定義的 factor 通常是「復權價 / 原始價」或相近概念，這裡用 Adj Close / Close 示意。[web:112][web:109]
    "factor": data["Adj Close"] / data["Close"]
})

# 4. 看前幾列結果
df.head()
```

這個儲存格做的事是：用 yfinance 抓 Apple  的日價量資料，計算一個簡單的還原因子 `factor = Adj Close / Close`，然後整理成 Qlib 所需的基本欄位格式，最後 `df.head()` 會秀出前幾列，讓你確認欄位是否正確。[^6_2][^6_5][^6_1]

之後如果你要接台股／FinMind，只要把 `stock_id、date、open、high、low、close、volume、factor` 這幾欄從 FinMind 轉出來，結構跟這個 df 類似，Qlib 的資料層就比較容易接上去。
<span style="display:none">[^6_10][^6_11][^6_12][^6_13][^6_14][^6_15][^6_16][^6_17][^6_18][^6_19][^6_20][^6_21][^6_6][^6_7][^6_8][^6_9]</span>

<div align="center">⁂</div>

[^6_1]: https://pythonfintech.com/articles/how-to-download-market-data-yfinance-python/

[^6_2]: https://qlib.readthedocs.io/en/stable/component/data.html

[^6_3]: https://www.geeksforgeeks.org/python/how-to-use-yfinance-api-with-python/

[^6_4]: https://github.com/ranaroussi/yfinance

[^6_5]: https://pythonviz.com/finance/yfinance-download-stock-data/

[^6_6]: https://github.com/microsoft/qlib

[^6_7]: https://qlib.readthedocs.io/en/latest/component/data.html

[^6_8]: https://git.nju.edu.cn/lance/qlib/-/tree/finco/scripts/data_collector/yahoo

[^6_9]: https://qlib.readthedocs.io/en/v0.8.1/component/data.html

[^6_10]: https://www.aidoczh.com/qlib/component/data.html

[^6_11]: https://github.com/microsoft/qlib/issues/1268

[^6_12]: https://qlib.moujue.com/start/initialization.html

[^6_13]: https://github.com/microsoft/qlib/issues/326

[^6_14]: https://blog.csdn.net/qq_33642342/article/details/113388299

[^6_15]: https://www.interactivebrokers.com/campus/ibkr-quant-news/python-download-stock-prices-using-the-yfinance-package/

[^6_16]: https://pypi.org/project/pyqlib/0.5.1/

[^6_17]: https://dev.to/henry_lin_3ac6363747f45b4/di-2zhang-qlibshu-ju-ceng-shen-du-jie-xi-2ph0

[^6_18]: https://gitee.com/gapyanpeng/qlib

[^6_19]: https://github.com/microsoft/qlib/issues/186

[^6_20]: https://blog.csdn.net/fanglue3705/article/details/138126989

[^6_21]: https://www.perplexity.ai/finance/AAPL


---

# 我想要的是可以在colab 執行的儲存格執行後可以展示qlib的能力

下面這一個 Colab 儲存格，執行完就會：安裝 Qlib → 下載官方示例資料（中國日線/來自 Yahoo Finance）→ 跑一個 LightGBM + Alpha158 的完整「預測 + 回測 + 風險評估」流程。[^7_1][^7_2]

## 可直接貼到 Colab 的示範儲存格

```python
# 在 Colab 示範 Qlib 能力：安裝 → 下載示例資料 → 跑一個 LightGBM 回測

# 1. 取得原始碼（含範例設定檔）
!git clone -q https://github.com/microsoft/qlib.git
%cd qlib

# 2. 安裝 Qlib（用本地原始碼安裝，會自動裝依賴）
!pip install -q .

# 3. 下載日頻示例資料（中國市場，資料來源為 Yahoo Finance）
!python -m qlib.cli.data qlib_data --target_dir ~/.qlib/qlib_data/cn_data --region cn

# 4. 執行一個官方範例 workflow：
#    使用 Alpha158 因子 + LightGBM 模型，做預測與回測
!python -m qlib.cli.run examples/benchmarks/LightGBM/workflow_config_lightgbm_Alpha158.yaml
```


## 執行後你會看到什麼

- 前半段：會先看到安裝 log，接著是下載資料的進度（包含哪些股票、哪段時間），然後是模型訓練與驗證的輸出。這是 Qlib 的自動工作流：從資料處理、建資料集，到模型訓練與產生預測訊號。[^7_2][^7_1]
- 結尾：終端機會印出一段「回測風險與績效摘要」，通常包含：不含交易成本與含成本的平均超額日報酬、年化報酬、波動度、Information Ratio / Sharpe 類指標，以及最大回撤等，這就是用 Qlib 回測之後幫你做的標準化績效評估。[^7_3][^7_1]

你只要先跑這一格，確認可以順利印出那張風險統計表，之後我們就可以再討論：怎麼把資料換成 yfinance / FinMind、怎麼改設定檔改成你自己的因子與回測期間。

<div align="center">⁂</div>

[^7_1]: https://github.com/microsoft/qlib

[^7_2]: https://qlib.readthedocs.io/en/stable/component/data.html

[^7_3]: https://qlib.readthedocs.io/en/v0.9.2/component/report.html


---

# /content/qlib

Installing build dependencies ... done
Getting requirements to build wheel ... done
Preparing metadata (pyproject.toml) ... done
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 40.0/40.0 kB 1.9 MB/s eta 0:00:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 119.9/119.9 kB 4.7 MB/s eta 0:00:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 115.9/115.9 kB 6.8 MB/s eta 0:00:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 61.6/61.6 kB 3.7 MB/s eta 0:00:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 8.9/8.9 MB 73.4 MB/s eta 0:00:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.4/2.4 MB 53.3 MB/s eta 0:00:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.3/1.3 MB 47.2 MB/s eta 0:00:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.7/1.7 MB 21.9 MB/s eta 0:00:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 354.2/354.2 kB 24.2 MB/s eta 0:00:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 331.1/331.1 kB 18.8 MB/s eta 0:00:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 147.8/147.8 kB 9.3 MB/s eta 0:00:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 114.9/114.9 kB 7.3 MB/s eta 0:00:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 85.0/85.0 kB 5.0 MB/s eta 0:00:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 76.8/76.8 kB 4.2 MB/s eta 0:00:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 788.2/788.2 kB 31.6 MB/s eta 0:00:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 12.4/12.4 MB 78.1 MB/s eta 0:00:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 753.9/753.9 kB 35.3 MB/s eta 0:00:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 207.3/207.3 kB 14.7 MB/s eta 0:00:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 76.7/76.7 kB 4.8 MB/s eta 0:00:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 59.8/59.8 kB 3.4 MB/s eta 0:00:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.6/1.6 MB 50.6 MB/s eta 0:00:00
Building wheel for pyqlib (pyproject.toml) ... done

#### Do not import qlib package in the repository directory in case of importing qlib from . without compiling

Traceback (most recent call last):
File "<frozen runpy>", line 198, in _run_module_as_main
File "<frozen runpy>", line 88, in _run_code
File "/content/qlib/qlib/cli/data.py", line 5, in <module>
from qlib.tests.data import GetData
File "/content/qlib/qlib/tests/__init__.py", line 10, in <module>
from qlib.data.filter import NameDFilter
File "/content/qlib/qlib/data/__init__.py", line 8, in <module>
from .data import (
File "/content/qlib/qlib/data/data.py", line 20, in <module>
from .cache import H
File "/content/qlib/qlib/data/cache.py", line 36, in <module>
from .ops import Operators  \# pylint: disable=W0611  \# noqa: F401
^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/content/qlib/qlib/data/ops.py", line 18, in <module>
from ._libs.rolling import rolling_slope, rolling_rsquare, rolling_resi
ModuleNotFoundError: No module named 'qlib.data._libs.rolling'

#### Do not import qlib package in the repository directory in case of importing qlib from . without compiling

Traceback (most recent call last):
File "<frozen runpy>", line 198, in _run_module_as_main
File "<frozen runpy>", line 88, in _run_code
File "/content/qlib/qlib/cli/run.py", line 15, in <module>
from qlib.model.trainer import task_train
File "/content/qlib/qlib/model/__init__.py", line 6, in <module>
from .base import Model
File "/content/qlib/qlib/model/base.py", line 6, in <module>
from ..data.dataset import Dataset
File "/content/qlib/qlib/data/__init__.py", line 8, in <module>
from .data import (
File "/content/qlib/qlib/data/data.py", line 20, in <module>
from .cache import H
File "/content/qlib/qlib/data/cache.py", line 36, in <module>
from .ops import Operators  \# pylint: disable=W0611  \# noqa: F401
^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/content/qlib/qlib/data/ops.py", line 18, in <module>
from ._libs.rolling import rolling_slope, rolling_rsquare, rolling_resi
ModuleNotFoundError: No module named 'qlib.data._libs.rolling'

你現在遇到的是「在原始碼目錄裡執行 qlib，Python 讀到的是沒編譯的原始碼版本」，所以找不到 `qlib.data._libs.rolling` 這個 C 擴充模組。[^8_1][^8_2]
官方也特別寫了那句提示：「不要在 qlib 專案目錄裡 import qlib」，就是這個原因。

## 修正版：一格就能跑完的 Colab 儲存格

這一格會：clone 原始碼 → 安裝 pyqlib → 切回 `/content`，再用已安裝的 qlib 套件跑資料下載與範例 workflow（LightGBM + Alpha158）。[^8_3][^8_4][^8_1]

```python
# ✅ 一個儲存格示範 Qlib 能力（請在全新 Colab runtime 執行）

# 1. 抓原始碼（只為了拿範例的 YAML 設定檔）
!git clone -q https://github.com/microsoft/qlib.git /content/qlib

# 2. 安裝 Qlib 套件（會安裝到 site-packages，有編譯好的 _libs.rolling）
%cd /content/qlib
!pip install -q .

# 3. 很重要：離開原始碼目錄，避免 Python 優先載入 ./qlib 這個未編譯版本
%cd /content

# 4. 下載官方日頻示例資料（中國市場，來源 Yahoo Finance）
!python -m qlib.cli.data qlib_data \
    --target_dir ~/.qlib/qlib_data/cn_data \
    --region cn

# 5. 跑官方 LightGBM + Alpha158 workflow（完整：因子→模型→回測→評估）
!python -m qlib.cli.run \
    /content/qlib/examples/benchmarks/LightGBM/workflow_config_lightgbm_Alpha158.yaml
```


## 執行成功後會看到什麼

- 前半段：會顯示下載資料與訓練模型的 log，包含訓練/驗證/測試集切分、LightGBM 訓練進度等。[^8_5][^8_1]
- 最後幾行：會印出一段回測結果摘要（例如年化報酬、波動度、Information Ratio / Sharpe、最大回撤），這就是 Qlib 幫你跑完「因子 + 模型 + 回測 + 風險評估」的一整套 pipeline，證明它在 Colab 上已經正常運作。[^8_6][^8_7]

你可以先照這格跑一次，如果最後有看到一張風險指標表，我們下一步就可以討論怎麼把資料換成 yfinance 或 FinMind。

<div align="center">⁂</div>

[^8_1]: https://github.com/microsoft/qlib

[^8_2]: https://qlib.readthedocs.io/en/stable/component/data.html

[^8_3]: https://qlib.moujue.com/start/initialization.html

[^8_4]: https://github.com/microsoft/qlib/blob/main/examples/benchmarks/README.md

[^8_5]: https://vadim.blog/qlib-ai-quant-workflow-pytorch-mlp

[^8_6]: https://qlib.readthedocs.io/en/v0.5.1/component/backtest.html

[^8_7]: https://qlib.readthedocs.io/en/v0.9.2/component/report.html


---

# fatal: destination path '/content/qlib' already exists and is not an empty directory.

/content/qlib
Installing build dependencies ... done
Getting requirements to build wheel ... done
Preparing metadata (pyproject.toml) ... done
Building wheel for pyqlib (pyproject.toml) ... done
/content
2025-11-29 16:18:36.305 | WARNING  | qlib.tests.data:download:62 - The data for the example is collected from Yahoo Finance. Please be aware that the quality of the data might not be perfect. (You can refer to the original data source: [https://finance.yahoo.com/lookup](https://finance.yahoo.com/lookup).)
2025-11-29 16:18:36.305 | INFO     | qlib.tests.data:download:65 - 20251129161836_qlib_data_cn_1d_latest.zip downloading......
196549632it [00:02, 66623433.67it/s]
2025-11-29 16:18:39.257 | WARNING  | qlib.tests.data:_unzip:124 - will delete the old qlib data directory(features, instruments, calendars, features_cache, dataset_cache): /root/.qlib/qlib_data/cn_data
2025-11-29 16:18:39.257 | INFO     | qlib.tests.data:_unzip:128 - /root/.qlib/qlib_data/cn_data/20251129161836_qlib_data_cn_1d_latest.zip unzipping......
100% 31008/31008 [00:08<00:00, 3575.48it/s]
[1775:MainThread](2025-11-29 16:18:53,459) INFO - qlib.qrun - [run.py:78] - Render the template with the context: {}
[1775:MainThread](2025-11-29 16:18:53,472) INFO - qlib.Initialization - [config.py:452] - default_conf: client.
[1775:MainThread](2025-11-29 16:18:53,475) INFO - qlib.Initialization - [__init__.py:82] - qlib successfully initialized based on client settings.
[1775:MainThread](2025-11-29 16:18:53,476) INFO - qlib.Initialization - [__init__.py:84] - data_path={'__DEFAULT_FREQ': PosixPath('/root/.qlib/qlib_data/cn_data')}
/usr/local/lib/python3.12/dist-packages/mlflow/tracking/_tracking_service/utils.py:140: FutureWarning: Filesystem tracking backend (e.g., './mlruns') is deprecated. Please switch to a database backend (e.g., 'sqlite:///mlflow.db'). For feedback, see: [https://github.com/mlflow/mlflow/issues/18534](https://github.com/mlflow/mlflow/issues/18534)
return FileStore(store_uri, store_uri)
[1775:MainThread](2025-11-29 16:18:53,490) WARNING - qlib.workflow - [expm.py:231] - No valid experiment found. Create a new experiment with name workflow.
[1775:MainThread](2025-11-29 16:18:53,494) INFO - qlib.workflow - [exp.py:258] - Experiment 681831588716335536 starts running ...
[1775:MainThread](2025-11-29 16:18:54,174) INFO - qlib.workflow - [recorder.py:345] - Recorder 1d164bedc17648dfb4033c87050eef78 starts running under Experiment 681831588716335536 ...
warning: Not a git repository. Use --no-index to compare two paths outside a working tree

```
usage: git diff --no-index [<options>] <path> <path>
```

Diff output format options
-p, --patch           generate patch
-s, --no-patch        suppress diff output
-u                    generate patch
```    -U, --unified[=<n>]   generate diffs with <n> lines context    ```
-W, --function-context
generate diffs with <n> lines context
--raw                 generate the diff in raw format
--patch-with-raw      synonym for '-p --raw'
--patch-with-stat     synonym for '-p --stat'
--numstat             machine friendly --stat
--shortstat           output only the last line of --stat
-X, --dirstat[=<param1,param2>...]
output the distribution of relative amount of changes for each sub-directory
--cumulative          synonym for --dirstat=cumulative
--dirstat-by-file[=<param1,param2>...]
synonym for --dirstat=files,param1,param2...
--check               warn if changes introduce conflict markers or whitespace errors
--summary             condensed summary such as creations, renames and mode changes
--name-only           show only names of changed files
--name-status         show only names and status of changed files
```    --stat[=<width>[,<name-width>[,<count>]]]    ```
generate diffstat
--stat-width <width>  generate diffstat with a given width
--stat-name-width <width>
generate diffstat with a given name width
--stat-graph-width <width>
generate diffstat with a given graph width
--stat-count <count>  generate diffstat with limited lines
--compact-summary     generate compact summary in diffstat
--binary              output a binary diff that can be applied
--full-index          show full pre- and post-image object names on the "index" lines
--color[=<when>]      show colored diff
--ws-error-highlight <kind>
highlight whitespace errors in the 'context', 'old' or 'new' lines in the diff
-z                    do not munge pathnames and use NULs as output field terminators in --raw or --numstat
```    --abbrev[=<n>]        use <n> digits to display object names    ```
--src-prefix <prefix>
show the given source prefix instead of "a/"
--dst-prefix <prefix>
show the given destination prefix instead of "b/"
--line-prefix <prefix>
prepend an additional prefix to every line of output
--no-prefix           do not show any source or destination prefix
--inter-hunk-context <n>
show context between diff hunks up to the specified number of lines
--output-indicator-new <char>
specify the character to indicate a new line instead of '+'
--output-indicator-old <char>
specify the character to indicate an old line instead of '-'
--output-indicator-context <char>
specify the character to indicate a context instead of ' '

Diff rename options
```    -B, --break-rewrites[=<n>[/<m>]]    ```
break complete rewrite changes into pairs of delete and create
-M, --find-renames[=<n>]
detect renames
-D, --irreversible-delete
omit the preimage for deletes
-C, --find-copies[=<n>]
detect copies
--find-copies-harder  use unmodified files as source to find copies
--no-renames          disable rename detection
--rename-empty        use empty blobs as rename source
--follow              continue listing the history of a file beyond renames
-l <n>                prevent rename/copy detection if the number of rename/copy targets exceeds given limit

Diff algorithm options
--minimal             produce the smallest possible diff
-w, --ignore-all-space
ignore whitespace when comparing lines
-b, --ignore-space-change
ignore changes in amount of whitespace
--ignore-space-at-eol
ignore changes in whitespace at EOL
--ignore-cr-at-eol    ignore carrier-return at the end of line
--ignore-blank-lines  ignore changes whose lines are all blank
-I, --ignore-matching-lines <regex>
ignore changes whose all lines match <regex>
--indent-heuristic    heuristic to shift diff hunk boundaries for easy reading
--patience            generate diff using the "patience diff" algorithm
--histogram           generate diff using the "histogram diff" algorithm
--diff-algorithm <algorithm>
choose a diff algorithm
--anchored <text>     generate diff using the "anchored diff" algorithm
```    --word-diff[=<mode>]  show word diff, using <mode> to delimit changed words    ```
--word-diff-regex <regex>
use <regex> to decide what a word is
--color-words[=<regex>]
equivalent to --word-diff=color --word-diff-regex=<regex>
--color-moved[=<mode>]
moved lines of code are colored differently
--color-moved-ws <mode>
how white spaces are ignored in --color-moved

Other diff options
--relative[=<prefix>]
when run from subdir, exclude changes outside and show relative paths
-a, --text            treat all files as text
-R                    swap two inputs, reverse the diff
--exit-code           exit with 1 if there were differences, 0 otherwise
--quiet               disable all output of the program
--ext-diff            allow an external diff helper to be executed
--textconv            run external text conversion filters when comparing binary files
--ignore-submodules[=<when>]
ignore changes to submodules in the diff generation
--submodule[=<format>]
specify how differences in submodules are shown
--ita-invisible-in-index
hide 'git add -N' entries from the index
--ita-visible-in-index
treat 'git add -N' entries as real in the index
-S <string>           look for differences that change the number of occurrences of the specified string
-G <regex>            look for differences that change the number of occurrences of the specified regex
--pickaxe-all         show all changes in the changeset with -S or -G
--pickaxe-regex       treat <string> in -S as extended POSIX regular expression
-O <file>             control the order in which files appear in the output
--rotate-to <path>    show the change in the specified path first
--skip-to <path>      skip the output to the specified path
--find-object <object-id>
look for differences that change the number of occurrences of the specified object
--diff-filter [(A|C|D|M|R|T|U|X|B)...[*]]
select files by diff type
--output <file>       Output to a specific file

[1775:MainThread](2025-11-29 16:18:54,189) INFO - qlib.workflow - [recorder.py:378] - Fail to log the uncommitted code of \$CWD(/content) when run git diff.
fatal: not a git repository (or any of the parent directories): .git
[1775:MainThread](2025-11-29 16:18:54,194) INFO - qlib.workflow - [recorder.py:378] - Fail to log the uncommitted code of \$CWD(/content) when run git status.
error: unknown option `cached'

```
usage: git diff --no-index [<options>] <path> <path>
```

Diff output format options
-p, --patch           generate patch
-s, --no-patch        suppress diff output
-u                    generate patch
```    -U, --unified[=<n>]   generate diffs with <n> lines context    ```
-W, --function-context
generate diffs with <n> lines context
--raw                 generate the diff in raw format
--patch-with-raw      synonym for '-p --raw'
--patch-with-stat     synonym for '-p --stat'
--numstat             machine friendly --stat
--shortstat           output only the last line of --stat
-X, --dirstat[=<param1,param2>...]
output the distribution of relative amount of changes for each sub-directory
--cumulative          synonym for --dirstat=cumulative
--dirstat-by-file[=<param1,param2>...]
synonym for --dirstat=files,param1,param2...
--check               warn if changes introduce conflict markers or whitespace errors
--summary             condensed summary such as creations, renames and mode changes
--name-only           show only names of changed files
--name-status         show only names and status of changed files
```    --stat[=<width>[,<name-width>[,<count>]]]    ```
generate diffstat
--stat-width <width>  generate diffstat with a given width
--stat-name-width <width>
generate diffstat with a given name width
--stat-graph-width <width>
generate diffstat with a given graph width
--stat-count <count>  generate diffstat with limited lines
--compact-summary     generate compact summary in diffstat
--binary              output a binary diff that can be applied
--full-index          show full pre- and post-image object names on the "index" lines
--color[=<when>]      show colored diff
--ws-error-highlight <kind>
highlight whitespace errors in the 'context', 'old' or 'new' lines in the diff
-z                    do not munge pathnames and use NULs as output field terminators in --raw or --numstat
```    --abbrev[=<n>]        use <n> digits to display object names    ```
--src-prefix <prefix>
show the given source prefix instead of "a/"
--dst-prefix <prefix>
show the given destination prefix instead of "b/"
--line-prefix <prefix>
prepend an additional prefix to every line of output
--no-prefix           do not show any source or destination prefix
--inter-hunk-context <n>
show context between diff hunks up to the specified number of lines
--output-indicator-new <char>
specify the character to indicate a new line instead of '+'
--output-indicator-old <char>
specify the character to indicate an old line instead of '-'
--output-indicator-context <char>
specify the character to indicate a context instead of ' '

Diff rename options
```    -B, --break-rewrites[=<n>[/<m>]]    ```
break complete rewrite changes into pairs of delete and create
-M, --find-renames[=<n>]
detect renames
-D, --irreversible-delete
omit the preimage for deletes
-C, --find-copies[=<n>]
detect copies
--find-copies-harder  use unmodified files as source to find copies
--no-renames          disable rename detection
--rename-empty        use empty blobs as rename source
--follow              continue listing the history of a file beyond renames
-l <n>                prevent rename/copy detection if the number of rename/copy targets exceeds given limit

Diff algorithm options
--minimal             produce the smallest possible diff
-w, --ignore-all-space
ignore whitespace when comparing lines
-b, --ignore-space-change
ignore changes in amount of whitespace
--ignore-space-at-eol
ignore changes in whitespace at EOL
--ignore-cr-at-eol    ignore carrier-return at the end of line
--ignore-blank-lines  ignore changes whose lines are all blank
-I, --ignore-matching-lines <regex>
ignore changes whose all lines match <regex>
--indent-heuristic    heuristic to shift diff hunk boundaries for easy reading
--patience            generate diff using the "patience diff" algorithm
--histogram           generate diff using the "histogram diff" algorithm
--diff-algorithm <algorithm>
choose a diff algorithm
--anchored <text>     generate diff using the "anchored diff" algorithm
```    --word-diff[=<mode>]  show word diff, using <mode> to delimit changed words    ```
--word-diff-regex <regex>
use <regex> to decide what a word is
--color-words[=<regex>]
equivalent to --word-diff=color --word-diff-regex=<regex>
--color-moved[=<mode>]
moved lines of code are colored differently
--color-moved-ws <mode>
how white spaces are ignored in --color-moved

Other diff options
--relative[=<prefix>]
when run from subdir, exclude changes outside and show relative paths
-a, --text            treat all files as text
-R                    swap two inputs, reverse the diff
--exit-code           exit with 1 if there were differences, 0 otherwise
--quiet               disable all output of the program
--ext-diff            allow an external diff helper to be executed
--textconv            run external text conversion filters when comparing binary files
--ignore-submodules[=<when>]
ignore changes to submodules in the diff generation
--submodule[=<format>]
specify how differences in submodules are shown
--ita-invisible-in-index
hide 'git add -N' entries from the index
--ita-visible-in-index
treat 'git add -N' entries as real in the index
-S <string>           look for differences that change the number of occurrences of the specified string
-G <regex>            look for differences that change the number of occurrences of the specified regex
--pickaxe-all         show all changes in the changeset with -S or -G
--pickaxe-regex       treat <string> in -S as extended POSIX regular expression
-O <file>             control the order in which files appear in the output
--rotate-to <path>    show the change in the specified path first
--skip-to <path>      skip the output to the specified path
--find-object <object-id>
look for differences that change the number of occurrences of the specified object
--diff-filter [(A|C|D|M|R|T|U|X|B)...[*]]
select files by diff type
--output <file>       Output to a specific file

[1775:MainThread](2025-11-29 16:18:54,202) INFO - qlib.workflow - [recorder.py:378] - Fail to log the uncommitted code of \$CWD(/content) when run git diff --cached.
ModuleNotFoundError. CatBoostModel are skipped. (optional: maybe installing CatBoostModel can fix it.)
quite
quiet
--quiet

現在這個輸出代表：Qlib 已經成功安裝、初始化、下載資料，並且把 LightGBM + Alpha158 的 workflow 跑完了。[^9_1][^9_2]
後面那一大串 git / mlflow 的訊息只是它嘗試記錄「程式版本」失敗的警告，可以忽略；`CatBoostModel are skipped` 只是說沒裝 catboost，所以跳過那種模型，跟這次實驗無關。[^9_3][^9_4]

## 接下來：用一格把「回測績效表」印出來

在你剛剛那格之後，新開一個儲存格貼這段，就能看到這次回測的風險與報酬指標（年化報酬、波動、information ratio 等）：[^9_5][^9_6]

```python
import qlib
import pandas as pd
from qlib.workflow import R
from qlib.contrib.evaluate import risk_analysis

# 1. 初始化（指向剛剛下載的 cn_data）
qlib.init(provider_uri="~/.qlib/qlib_data/cn_data", region="cn")

# 2. 取得剛剛那個 experiment（預設名稱是 "workflow"）
exp = R.get_exp(experiment_name="workflow")

# 3. 取最新的一個 recorder（同一個 experiment 可能會有多次跑）
rec = exp.list_recorders()[-1]

# 4. 載入這次回測的每日投組表現
report = rec.load_object("portfolio_analysis/port_analysis_1day.pkl")

# 5. 計算有／沒有計入交易成本的超額報酬風險指標
analysis = {}
analysis["excess_return_without_cost"] = risk_analysis(
    report["return"] - report["bench"], freq="day"
)
analysis["excess_return_with_cost"] = risk_analysis(
    report["return"] - report["bench"] - report["cost"], freq="day"
)

analysis_df = pd.concat(analysis)
analysis_df
```

執行後你會看到一個 DataFrame，行是不同指標（例如 `annualized_return`, `information_ratio`, `max_drawdown`），列是「不含成本的超額報酬」和「含成本的超額報酬」，這就是 Qlib 幫你完整跑完「因子→模型→回測→風險分析」的成果展示。[^9_7][^9_8][^9_5]

如果這格跑出來沒問題，我們下一步就可以討論：怎麼把資料從內建 cn_data 換成 yfinance 或 FinMind。
<span style="display:none">[^9_10][^9_11][^9_12][^9_13][^9_14][^9_15][^9_16][^9_17][^9_18][^9_19][^9_20][^9_21][^9_9]</span>

<div align="center">⁂</div>

[^9_1]: https://qlib.readthedocs.io/en/v0.9.6/introduction/quick.html

[^9_2]: https://github.com/microsoft/qlib

[^9_3]: https://qlib.readthedocs.io/en/latest/component/recorder.html

[^9_4]: https://qlib.readthedocs.io/en/stable/component/recorder.html

[^9_5]: https://github.com/microsoft/qlib/blob/main/docs/component/recorder.rst

[^9_6]: https://github.com/ChenglongChen/Long-Capital/blob/main/examples/rl.ipynb

[^9_7]: https://qlib.readthedocs.io/en/latest/component/report.html

[^9_8]: https://www.aidoczh.com/qlib/component/report.html

[^9_9]: https://qlib.readthedocs.io/en/latest/reference/api.html

[^9_10]: https://qlib.readthedocs.io/en/v0.6.3/reference/api.html

[^9_11]: https://www.thewaytolearn.cn/course/view.php?id=7413

[^9_12]: https://github.com/microsoft/qlib/blob/main/qlib/workflow/record_temp.py

[^9_13]: https://gitee.com/zhaoliangj/qlib/blob/main/examples/workflow_by_code.ipynb

[^9_14]: https://github.com/microsoft/qlib/pull/1560/files

[^9_15]: https://qlib.readthedocs.io/en/v0.8.3/reference/api.html

[^9_16]: https://qlib.readthedocs.io/en/v0.8.1/component/recorder.html

[^9_17]: https://qlib.readthedocs.io/_/downloads/en/v0.6.3/pdf/

[^9_18]: https://qlib.moujue.com/component/recorder.html

[^9_19]: https://qlib.readthedocs.io/en/latest/component/strategy.html

[^9_20]: https://www.aidoczh.com/qlib/component/recorder.html

[^9_21]: https://www.wuzao.com/p/qlib/document/component/recorder.html


---

# 後續給我程式碼要加上@title

Gym has been unmaintained since 2022 and does not support NumPy 2.0 amongst other critical functionality.
Please upgrade to Gymnasium, the maintained drop-in replacement of Gym, or contact the authors of your software and request that they upgrade.
See the migration guide at [https://gymnasium.farama.org/introduction/migration_guide/](https://gymnasium.farama.org/introduction/migration_guide/) for additional information.
/usr/local/lib/python3.12/dist-packages/jupyter_client/session.py:203: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
return datetime.utcnow().replace(tzinfo=utc)
[610:MainThread](2025-11-29 16:22:28,393) INFO - qlib.Initialization - [config.py:452] - default_conf: client.
[610:MainThread](2025-11-29 16:22:28,401) INFO - qlib.Initialization - [__init__.py:82] - qlib successfully initialized based on client settings.
[610:MainThread](2025-11-29 16:22:28,402) INFO - qlib.Initialization - [__init__.py:84] - data_path={'__DEFAULT_FREQ': PosixPath('/root/.qlib/qlib_data/cn_data')}
/usr/local/lib/python3.12/dist-packages/mlflow/tracking/_tracking_service/utils.py:140: FutureWarning: Filesystem tracking backend (e.g., './mlruns') is deprecated. Please switch to a database backend (e.g., 'sqlite:///mlflow.db'). For feedback, see: [https://github.com/mlflow/mlflow/issues/18534](https://github.com/mlflow/mlflow/issues/18534)
return FileStore(store_uri, store_uri)
---------------------------------------------------------------------------
KeyError                                  Traceback (most recent call last)
/tmp/ipython-input-3851765384.py in <cell line: 0>()
13
14 \# 3. 取最新的一個 recorder（同一個 experiment 可能會有多次跑）
---> 15 rec = exp.list_recorders()[-1]
16
17 \# 4. 載入這次回測的每日投組表現

KeyError: -1

`KeyError: -1` 是因為 `exp.list_recorders()` 在你這個版本不是「list」，而是「字典」，所以用 `[-1]` 會出錯。[^10_1][^10_2]
另外 Gym / mlflow 的 warning 都只是相容性提醒，跟這次 Qlib 回測沒關係，可以先忽略。[^10_1]

下面給你兩個儲存格，已加上 `#@title`，可以直接貼到 Colab：

## 先確認實驗與 recorder 有沒有成功建立

```python
#@title 檢查 Qlib 實驗與 recorder 清單

import qlib
from qlib.workflow import R

# 1. 初始化（指向剛剛下載的 cn_data）
qlib.init(provider_uri="~/.qlib/qlib_data/cn_data", region="cn")

# 2. 列出目前所有 experiment
exps = R.list_experiments()
print("現有 experiments：")
for e in exps:
    # 不同版本的 Experiment 物件屬性名稱可能略有差異，先印出 repr 即可
    print(" -", e)

# 3. 取得預設的 experiment（通常叫 workflow，如果你沒改 YAML）
exp = R.get_exp(experiment_name="workflow")

# 4. 列出這個 experiment 底下的 recorder（這裡回傳的是 dict）
recs = exp.list_recorders()
print("\nworkflow 底下的 recorders：")
for rec_id, rec in recs.items():
    print(f" - id={rec_id}, recorder={rec}")
```

這格跑完如果有看到 `workflow` 與至少一個 recorder id，就代表前一個 LightGBM workflow 的實驗真的有被記錄下來。

## 正確抓「最後一個 recorder」並做風險分析

```python
#@title 顯示最近一次回測的風險與報酬指標

import qlib
import pandas as pd
from qlib.workflow import R
from qlib.contrib.evaluate import risk_analysis

# 1. 初始化（和上面保持一致）
qlib.init(provider_uri="~/.qlib/qlib_data/cn_data", region="cn")

# 2. 取得 experiment
exp = R.get_exp(experiment_name="workflow")

# 3. list_recorders() 回傳 dict：{recorder_id: Recorder}
recs = exp.list_recorders()
if not recs:
    raise RuntimeError("這個 experiment 底下沒有任何 recorder，請先重新跑一次 LightGBM workflow。")

# 4. 取「最後建立」的一個 recorder
last_rec = list(recs.values())[-1]

# 5. 載入每日投組表現（Qlib 預設存在 portfolio_analysis/port_analysis_1day.pkl）
report = last_rec.load_object("portfolio_analysis/port_analysis_1day.pkl")

# 6. 計算有／無成本的超額報酬風險指標
analysis = {}
analysis["excess_return_without_cost"] = risk_analysis(
    report["return"] - report["bench"], freq="day"
)
analysis["excess_return_with_cost"] = risk_analysis(
    report["return"] - report["bench"] - report["cost"], freq="day"
)

analysis_df = pd.concat(analysis)
analysis_df
```

這格成功的話，底下會出現一個表格，類似：年化報酬、波動度、information ratio / Sharpe 類指標、最大回撤等等，分成「未扣成本」與「已扣成本」兩組，這就是 Qlib 回測結果的核心展示。[^10_3][^10_4]

你先跑第一格確認有 recorder，再跑第二格看風險分析表；如果某一步還有錯誤，把錯誤訊息貼出來就可以再往下排除。

<div align="center">⁂</div>

[^10_1]: https://qlib.readthedocs.io/en/latest/component/recorder.html

[^10_2]: https://qlib.readthedocs.io/en/stable/component/recorder.html

[^10_3]: https://qlib.readthedocs.io/en/latest/component/report.html

[^10_4]: https://www.aidoczh.com/qlib/component/report.html


---

# [610:MainThread](2025-11-29 16:23:52,779) INFO - qlib.Initialization - [config.py:452] - default_conf: client.

[610:MainThread](2025-11-29 16:23:52,795) INFO - qlib.Initialization - [__init__.py:82] - qlib successfully initialized based on client settings.
[610:MainThread](2025-11-29 16:23:52,801) INFO - qlib.Initialization - [__init__.py:84] - data_path={'__DEFAULT_FREQ': PosixPath('/root/.qlib/qlib_data/cn_data')}
Downloading artifacts:   0%
 0/1 [00:00<?, ?it/s]
---------------------------------------------------------------------------
MlflowException                           Traceback (most recent call last)
/usr/local/lib/python3.12/dist-packages/qlib/workflow/recorder.py in load_object(self, name, unpickler)
431         try:
--> 432             path = self.client.download_artifacts(self.id, name)
433             with Path(path).open("rb") as f:

6 frames
MlflowException: Failed to download artifacts from path 'port_analysis_1day.pkl', please ensure that the path is correct.

The above exception was the direct cause of the following exception:

LoadObjectError                           Traceback (most recent call last)
/usr/local/lib/python3.12/dist-packages/qlib/workflow/recorder.py in load_object(self, name, unpickler)
435             return data
436         except Exception as e:
--> 437             raise LoadObjectError(str(e)) from e
438         finally:
439             ar = self.client._tracking_client._get_artifact_repo(self.id)

LoadObjectError: Failed to download artifacts from path 'port_analysis_1day.pkl', please ensure that the path is correct.

這個錯誤是：那個 recorder 裡根本沒有 `portfolio_analysis/port_analysis_1day.pkl` 這個檔，所以 mlflow 下載不到。[^11_1][^11_2]
原因很可能是剛剛那個 YAML workflow 只做「訓練＋預測」，沒有執行內建的回測紀錄器（PortAnaRecord），所以沒有產生這個 artifact。[^11_3][^11_4]

要在 Colab「直接看到 Qlib 的回測能力」，其實可以先跳過 mlflow / recorder，改用官方文件推薦的「by code」方式：直接呼叫 Qlib 的 `backtest_daily` 和 `risk_analysis`。[^11_5]
下面兩個儲存格都有加上 `#@title`，可以連續執行。

## 儲存格 1：用 Qlib 資料做一個簡單 TOP‑K 策略並回測

```python
#@title 使用 Qlib 價格資料建立簡單 TopK 策略並回測

import qlib
import pandas as pd
from qlib.data import D
from qlib.contrib.strategy import TopkDropoutStrategy
from qlib.contrib.evaluate import backtest_daily

# 1. 初始化 Qlib（使用剛下載的 cn_data）
qlib.init(provider_uri="~/.qlib/qlib_data/cn_data", region="cn")

# 2. 定義市場與期間（使用 Qlib 內建的 CSI300 股票池與基準指數）[web:139]
market = "csi300"
benchmark = "SH000300"

start_time = "2017-01-01"
end_time = "2020-08-01"
freq = "day"

# 3. 從 Qlib 資料層抓取收盤價（features 會回傳 MultiIndex：index=時間, 欄位=field, 第二層=股票）[web:82][web:112]
data = D.features(
    instruments=market,
    fields=["$close"],
    start_time=start_time,
    end_time=end_time,
    freq=freq,
)

# 4. 用「過去 5 日報酬」當作預測分數（只是示範，非真正好用因子）
#    先把 $close 變成日期×股票的矩陣，再算 5 日報酬，最後再疊回 MultiIndex
close = data["$close"].unstack(level=1)     # index=日期, columns=股票
ret_5d = close.pct_change(5)
pred_score = ret_5d.stack().dropna()       # 變回 index=(日期, 股票) 的 Series

# 5. 建立 TopK 策略：每天選分數最高的 50 檔，換掉分數最差的 5 檔[web:139]
strategy_conf = {
    "topk": 50,
    "n_drop": 5,
    "signal": pred_score,
}
strategy = TopkDropoutStrategy(**strategy_conf)

# 6. 進行日頻回測，得到每日報表與持倉矩陣[web:139]
report, positions = backtest_daily(
    start_time=start_time,
    end_time=end_time,
    strategy=strategy,
    benchmark=benchmark,
)

report.head()
```

這格跑完會印出 `report` 的前幾列，裡面有每天的策略報酬、基準報酬、交易成本等欄位。[^11_5]

## 儲存格 2：對回測結果做風險與報酬分析

```python
#@title 顯示策略的年化報酬、IR、最大回撤等風險指標

from qlib.contrib.evaluate import risk_analysis

# 1. 計算「未扣成本」與「已扣成本」的超額報酬
analysis = {}
analysis["excess_return_without_cost"] = risk_analysis(
    report["return"] - report["bench"], freq="day"
)
analysis["excess_return_with_cost"] = risk_analysis(
    report["return"] - report["bench"] - report["cost"], freq="day"
)

# 2. 合併成一個 DataFrame 顯示
analysis_df = pd.concat(analysis)
analysis_df
```

這格會輸出一個表格，通常包含：年化報酬、波動度、information ratio / Sharpe 類指標、最大回撤等，分成「不含成本」與「含成本」兩組，這就是 Qlib 在日頻回測上的代表性能力展示。[^11_6][^11_5]

如果這兩格都跑成功，之後可以再把第 1 格的 `pred_score` 換成你用因子模型／LLM 算出來的分數，或是把資料來源改成 yfinance / FinMind。
<span style="display:none">[^11_10][^11_11][^11_12][^11_13][^11_14][^11_15][^11_16][^11_17][^11_18][^11_19][^11_20][^11_21][^11_7][^11_8][^11_9]</span>

<div align="center">⁂</div>

[^11_1]: https://qlib.readthedocs.io/en/latest/component/recorder.html

[^11_2]: https://blog.csdn.net/mnwl12_0/article/details/135319118

[^11_3]: https://blog.csdn.net/thebestismin/article/details/128228486

[^11_4]: https://github.com/microsoft/qlib/blob/main/docs/component/recorder.rst

[^11_5]: https://qlib.readthedocs.io/en/latest/component/strategy.html

[^11_6]: https://qlib.readthedocs.io/en/latest/component/report.html

[^11_7]: https://github.com/microsoft/qlib/blob/main/qlib/workflow/recorder.py

[^11_8]: https://qlib.moujue.com/component/recorder.html

[^11_9]: https://qlib.readthedocs.io/en/v0.8.3/reference/api.html

[^11_10]: https://qlib.readthedocs.io/en/v0.8.5/component/recorder.html

[^11_11]: https://www.aidoczh.com/qlib/component/recorder.html

[^11_12]: https://github.com/microsoft/qlib/blob/main/qlib/workflow/record_temp.py

[^11_13]: https://github.com/microsoft/qlib/issues/820

[^11_14]: https://blog.csdn.net/u014451778/article/details/148137070

[^11_15]: https://blog.csdn.net/csdn122345/article/details/148776376

[^11_16]: https://www.aidoczh.com/qlib/component/online.html

[^11_17]: https://github.com/microsoft/qlib

[^11_18]: https://blog.csdn.net/gitblog_00749/article/details/151849592

[^11_19]: https://www.aidoczh.com/qlib/component/data.html

[^11_20]: https://github.com/microsoft/qlib/pull/1430

[^11_21]: https://www.wuzao.com/p/qlib/document/component/recorder.html


---

# 一次給我一個儲存格

[610:MainThread](2025-11-29 16:25:22,850) INFO - qlib.Initialization - [config.py:452] - default_conf: client.
[610:MainThread](2025-11-29 16:25:22,857) INFO - qlib.Initialization - [__init__.py:82] - qlib successfully initialized based on client settings.
[610:MainThread](2025-11-29 16:25:22,859) INFO - qlib.Initialization - [__init__.py:84] - data_path={'__DEFAULT_FREQ': PosixPath('/root/.qlib/qlib_data/cn_data')}
---------------------------------------------------------------------------
TypeError                                 Traceback (most recent call last)
/usr/local/lib/python3.12/dist-packages/qlib/data/data.py in features(self, instruments, fields, start_time, end_time, freq, disk_cache, inst_processors)
1185         try:
-> 1186             return DatasetD.dataset(
1187                 instruments, fields, start_time, end_time, freq, disk_cache, inst_processors=inst_processors

TypeError: LocalDatasetProvider.dataset() got multiple values for argument 'inst_processors'

During handling of the above exception, another exception occurred:

ValueError                                Traceback (most recent call last)
3 frames
/usr/local/lib/python3.12/dist-packages/qlib/data/data.py in get_instruments_d(instruments, freq)
526             instruments_d = list(instruments)
527         else:
--> 528             raise ValueError("Unsupported input type for param `instrument`")
529         return instruments_d
530

ValueError: Unsupported input type for param `instrument`

這個錯誤是因為 `D.features` 那邊 `instruments` 型別不對，新的 Qlib 要先用 `D.instruments(market=...)` 取得股票池，再丟進 `D.features`。[^12_1][^12_2]

先給你「只負責抓資料」的第一個儲存格（已加 `#@title`）：

```python
#@title 使用 Qlib 取得 CSI300 收盤價資料

import qlib
from qlib.data import D

# 1. 初始化 Qlib（使用剛下載的 cn_data）
qlib.init(provider_uri="~/.qlib/qlib_data/cn_data", region="cn")

# 2. 定義市場與期間
market = "csi300"
start_time = "2017-01-01"
end_time   = "2020-08-01"
freq       = "day"

# 3. 先取得這個市場的股票清單（Qlib 需要 instruments 物件，而不是直接給字串）[web:112]
instruments = D.instruments(market=market)

# 4. 取得這些股票在區間內的收盤價
data = D.features(
    instruments=instruments,
    fields=["$close"],
    start_time=start_time,
    end_time=end_time,
    freq=freq,
)

data.head()
```

請先只跑這一格，確認不再出現 `Unsupported input type for param 'instrument'`，而且有看到一個帶有 `$close` 的表格，我再給你下一個「算簡單因子＋回測」的儲存格。

<div align="center">⁂</div>

[^12_1]: https://qlib.readthedocs.io/en/stable/component/data.html

[^12_2]: https://qlib.readthedocs.io/en/latest/component/strategy.html


---

# 繼續

下一步先做「簡單因子＋TopK 策略」，一樣只給你一個儲存格，接在你剛剛成功拿到 `data` 之後用。

```python
#@title 以 5 日報酬當訊號，建立 TopK 策略並回測

import pandas as pd
from qlib.contrib.strategy import TopkDropoutStrategy
from qlib.contrib.evaluate import backtest_daily

benchmark = "SH000300"  # Qlib 內建的滬深300指數作為基準

# 1. 從剛才的 data 取出收盤價，變成「日期 × 股票」矩陣
close = data["$close"].unstack(level=1)   # index=日期, columns=股票

# 2. 用 5 日報酬當作預測分數（只是示範，不代表好策略）
ret_5d = close.pct_change(5)
pred_score = ret_5d.stack().dropna()     # 變回 (日期, 股票) 的 Series，符合 TopkDropoutStrategy 需要的格式

# 3. 建立 TopK 策略物件（每天持有 50 檔，換掉最差的 5 檔）[web:139][web:154]
strategy_conf = {
    "topk": 50,
    "n_drop": 5,
    "signal": pred_score,
}
strategy = TopkDropoutStrategy(**strategy_conf)

# 4. 執行日頻回測
report, positions = backtest_daily(
    start_time=start_time,
    end_time=end_time,
    strategy=strategy,
    benchmark=benchmark,
)

report.head()
```

請先跑這一格，確認能看到 `report.head()` 的表格（包含 `return`, `bench`, `cost` 等欄位），下一步再給你專門做風險分析的儲存格。
<span style="display:none">[^13_1][^13_10][^13_11][^13_12][^13_13][^13_14][^13_2][^13_3][^13_4][^13_5][^13_6][^13_7][^13_8][^13_9]</span>

<div align="center">⁂</div>

[^13_1]: https://qlib.readthedocs.io/en/latest/component/strategy.html

[^13_2]: https://vadim.blog/qlib-portfolio-strategy

[^13_3]: https://juejin.cn/post/7547530492767109170

[^13_4]: https://modbus.pl/2025/02/07/python-qlib-ai-algorithmic-trading/

[^13_5]: https://qlib.readthedocs.io/en/v0.6.3/component/strategy.html

[^13_6]: https://qlib.readthedocs.io/en/stable/component/workflow.html

[^13_7]: https://github.com/microsoft/qlib/issues/1683

[^13_8]: https://github.com/microsoft/qlib

[^13_9]: https://www.aidoczh.com/qlib/component/workflow.html

[^13_10]: https://github.com/microsoft/qlib/blob/main/examples/benchmarks/README.md

[^13_11]: https://www.wuzao.com/p/qlib/document/component/strategy.html

[^13_12]: https://gitee.com/zhaoliangj/qlib/blob/main/examples/workflow_by_code.ipynb

[^13_13]: https://github.com/microsoft/qlib/blob/main/examples/benchmarks/LSTM/workflow_config_lstm_Alpha158.yaml

[^13_14]: https://joshuaberkowitz.us/blog/github-repos-8/qlib-open-source-ai-for-quant-research-762


---

# 繼續

最後一步是把剛才 `report` 的結果做風險分析，一樣一次只給你一個儲存格。這格要放在剛剛 TopK 回測那格「成功跑完」之後，因為它會用到同一個 `report` 變數。[^14_1][^14_2]

```python
#@title 對剛才的 TopK 策略做風險與報酬分析

import pandas as pd
from qlib.contrib.evaluate import risk_analysis

# 1. 確認 report 存在（來自上一個回測儲存格）
if "report" not in globals():
    raise RuntimeError("找不到 report，請先執行上一個回測儲存格。")

# 2. 計算「未扣成本」與「已扣成本」的超額報酬
analysis = {}
analysis["excess_return_without_cost"] = risk_analysis(
    report["return"] - report["bench"], freq="day"
)
analysis["excess_return_with_cost"] = risk_analysis(
    report["return"] - report["bench"] - report["cost"], freq="day"
)

# 3. 合併成一個 DataFrame 顯示
analysis_df = pd.concat(analysis)
analysis_df
```

執行後你會看到一個表格，指標大致包括：平均日超額報酬、標準差、年化報酬、information ratio（類 Sharpe）以及最大回撤，分成「不含成本」和「含成本」兩組，這就是 Qlib 幫你完整跑完「訊號 → 策略 → 回測 → 風險分析」的成果展示。[^14_2][^14_1]
<span style="display:none">[^14_10][^14_11][^14_12][^14_13][^14_14][^14_3][^14_4][^14_5][^14_6][^14_7][^14_8][^14_9]</span>

<div align="center">⁂</div>

[^14_1]: https://qlib.readthedocs.io/en/v0.9.2/component/report.html

[^14_2]: https://blog.csdn.net/weixin_40248634/article/details/129592698

[^14_3]: https://github.com/microsoft/qlib

[^14_4]: https://gitee.com/siteyangxu/qlib/blob/main/examples/workflow_by_code.ipynb

[^14_5]: https://github.com/microsoft/qlib/blob/main/qlib/workflow/record_temp.py

[^14_6]: https://qlib.readthedocs.io/en/v0.6.2/component/report.html

[^14_7]: https://qlib.readthedocs.io/en/v0.9.6/introduction/quick.html

[^14_8]: https://qlib.readthedocs.io/en/latest/component/report.html

[^14_9]: https://www.scribd.com/document/498701514/2009-11189v1

[^14_10]: https://www.aidoczh.com/qlib/component/recorder.html

[^14_11]: https://arxiv.org/pdf/2009.11189.pdf

[^14_12]: https://qlib.readthedocs.io

[^14_13]: https://www.wuzao.com/p/qlib/document/component/recorder.html

[^14_14]: https://qlib.readthedocs.io/en/latest/reference/api.html


---

# risk

excess_return_without_cost	mean	0.000302
std	0.004966
annualized_return	0.071795
information_ratio	0.937062
max_drawdown	-0.085413
excess_return_with_cost	mean	0.000277
std	0.004968
annualized_return	0.065914
information_ratio	0.860098
max_drawdown	-0.091759

/usr/local/lib/python3.12/dist-packages/jupyter_client/session.py:203: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
return datetime.utcnow().replace(tzinfo=utc)代表甚麼意思

這張表格是 Qlib 計算出來的**風險與報酬指標**，用來評估你剛剛那個 TopK 策略（用 5 日報酬選股）的表現。[^15_1][^15_3]

表格分成兩大組，一組「未扣交易成本」、一組「已扣交易成本」，讓你看清楚手續費與滑價對策略的影響。

## 各指標的意義

### mean（平均日超額報酬）

- **不含成本**：0.000302，代表每天平均比基準指數多賺 0.0302%
- **含成本**：0.000277，扣掉交易成本後每天平均超額報酬是 0.0277%
- 解讀：策略確實有打敗基準，但交易成本吃掉約 8% 的超額報酬（0.000302 → 0.000277）。


### std（標準差／波動度）

- 約 0.00497，代表每日超額報酬的波動程度
- 數字越小代表策略越穩定；這裡約 0.5% 的日波動算是中等水準。[^15_1]


### annualized_return（年化報酬率）

- **不含成本**：0.071795，即 7.18% 年化超額報酬
- **含成本**：0.065914，即 6.59% 年化超額報酬
- 計算方式：mean × 238（因為中國市場一年約 238 個交易日）[^15_1]
- 解讀：如果持續用這策略，理論上一年可以比滬深 300 指數多賺約 6.6%。


### information_ratio（信息比率／IR）

- **不含成本**：0.937
- **含成本**：0.860
- 這是「平均超額報酬 ÷ 超額報酬波動度」再乘上 √238，類似 Sharpe ratio 的概念。[^15_3][^15_1]
- 解讀：IR > 0.5 通常被視為不錯的策略，你這個 0.86 算是相對穩健的表現，代表「承擔單位風險所得到的超額報酬」還可以。


### max_drawdown（最大回撤）

- **不含成本**：-0.085413，即 -8.54%
- **含成本**：-0.091759，即 -9.18%
- 代表在回測期間（2017–2020），策略的累積超額報酬曲線「從高點到最低點」最多跌了 9.18%。[^15_3][^15_1]
- 解讀：這是風險控制的重要指標，-9.18% 代表你在最糟情況下會遇到接近 10% 的帳面虧損；一般來說回撤控制在 -10% 以內算是可接受範圍。


## 整體結論

這個簡單的「5 日報酬選股 + TopK 策略」在 2017–2020 年的中國市場：

- 有打敗基準：年化超額報酬約 6.6%（含成本）
- 風險可控：IR = 0.86、最大回撤約 -9.2%
- 交易成本影響不大：只吃掉約 0.6% 年化報酬（7.18% → 6.59%）

這代表 Qlib 已經幫你完成「策略構想 → 回測 → 風險評估」的完整流程；之後你可以把訊號（`pred_score`）換成更複雜的因子或模型預測分數，再用同樣方式評估。
<span style="display:none">[^15_2][^15_4][^15_5][^15_6][^15_7][^15_8]</span>

<div align="center">⁂</div>

[^15_1]: https://blog.csdn.net/weixin_40248634/article/details/129592698

[^15_2]: https://gist.github.com/m0o0scar/7a2da9a3b46893e06f2ba4681988cb85

[^15_3]: https://qlib.readthedocs.io/en/v0.8.1/component/report.html

[^15_4]: https://www.xugj520.cn/en/archives/microsoft-qlib-ai-quantitative-investment.html

[^15_5]: https://qlib.readthedocs.io/en/latest/component/report.html

[^15_6]: https://arxiv.org/pdf/2401.06139.pdf

[^15_7]: https://vadim.blog/page/2

[^15_8]: https://dspace.mit.edu/bitstream/handle/1721.1/156635/zhao-zijiezha-phd-eecs-2024-thesis.pdf?sequence=1\&isAllowed=y


---

# 那之前的我有看到你們阿爾法168跟阿爾法360這一些是什麼還有他裡面的CI，然後是提供了他什麼樣子的這一個數據呢，之前我在聽演講的時候我有聽到他們公司有1000張的a100顯示卡然後呢他們也有買aws去做這一些的處理那你告訴我他們大概是用在哪裡

先把名詞釐清：Qlib 的 Alpha158 / Alpha360 是「已經幫你算好的特徵／因子資料集」，IC（你聽成 CI）是用來衡量這些因子「預測未來報酬能力」的統計指標；你聽到那家公司用 1000 張 A100＋AWS，大多就是在這些資料集上瘋狂跑模型訓練、因子搜尋、回測與模擬。[^16_1][^16_2][^16_3][^16_4]

## Alpha158 / Alpha360 是什麼

- Alpha158：Qlib 提供的一個經典資料集，內含 158 個「精心設計」的因子，來源是日頻價量資料（價格、成交量、技術指標、波動度等），主要用在 A 股、CSI300/CSI500 成分股，常被當成各種模型（LightGBM、Transformer、RL）比較的標準特徵集。[^16_2][^16_5][^16_1]
- Alpha360：另一個更「原始」的特徵集，有 360 個特徵，較多是直接從價格／成交量的序列推導出來，保留比較多原始結構，適合給深度學習模型自己挖關係；官方 benchmark 也會報「某模型在 Alpha158 / Alpha360 上的效果」。[^16_6][^16_7][^16_1]

這兩個在 Qlib 裡都是 DataHandler 類別（`Alpha158`, `Alpha360`），你初始化後可以直接 `fetch(col_set="feature")` 拿到完整因子矩陣，`fetch(col_set="label")` 拿到預設的「未來報酬」當標籤，完全不必自己一個一個寫技術指標公式。[^16_8][^16_9][^16_2]

## IC（你說的 CI）在做什麼

- 在這些報告或 Qlib 設定裡，通常講的 CI 其實是 IC（Information Coefficient），就是「每一天、在橫截面上，因子值跟未來報酬的 Spearman 相關係數」，衡量這個因子能不能排序出未來漲跌。[^16_10][^16_2]
- Alpha158/Alpha360 相關的研究裡，常會做「把 158/360 個因子逐一算 IC、做 rolling IC、挑出 IC > 某門檻的因子再丟進模型」，甚至有 `ICSelector` 這種元件：只保留 IC 大於 0.05、在 60 日滾動視窗內穩定的因子。[^16_11][^16_2]

所以你可以把 Alpha158/360 想成：已經幫你算好的一大堆價量特徵，而 IC 就是評分這些特徵「到底有沒用」的數學指標。

## 他們 1000 張 A100 + AWS 在幹嘛

像你說的那種規模（1000 張 NVIDIA A100、再外加 AWS 雲端），典型用途大概有幾塊：[^16_3][^16_12][^16_4][^16_13]

- 大規模因子＋模型訓練：在 Alpha360 這種高維特徵集上訓練大量深度學習模型（GRU、Transformer、TFT、RL agent），同時做超參數搜尋、ensemble，GPU 可以把訓練時間從幾天縮成幾小時。[^16_7][^16_2][^16_3]
- 海量回測與模擬：把幾千個候選策略、幾十年、上千檔股票的日內／日線資料一次丟進蒙地卡羅模擬、情境分析；官方案例顯示，長時間範圍的回測模擬用 GPU 可以比 CPU 快超過百倍，對機構來說可以直接決定「今天能不能在美股開盤前把新版本策略全部跑完」。[^16_4][^16_3]
- 強化學習與「智慧交易員」：有論文直接用 Alpha158 做 RL 環境的狀態空間，訓練 agent 做組合決策；這種 RL/序列模型特別吃 GPU 記憶體與算力，所以會堆很多 A100 或用 AWS 大型 GPU 節點來跑多實驗同時訓練。[^16_13][^16_2][^16_7]

換句話說：

- Alpha158 / Alpha360 是「標準化因子／特徵庫」，IC 是「這些因子好不好用的成績單」。
- 那家公司有 1000 張 A100＋AWS，就是拿這些資料集當燃料，瘋狂訓練模型、做因子篩選、回測模擬，目的是在最短時間內驗證最多的策略想法，找到少數真正穩定賺錢的因子組合。

你的情況 GPU 很少，所以更適合「借用」這些公開因子庫（像 Alpha158）、只挑少數有直覺的因子＋簡單模型，再用 Qlib 幫你做回測與風險分析，而不是自己去複製他們那種 GPU 工廠。
<span style="display:none">[^16_14][^16_15][^16_16][^16_17][^16_18][^16_19][^16_20][^16_21][^16_22]</span>

<div align="center">⁂</div>

[^16_1]: https://dev.to/henry_lin_3ac6363747f45b4/di-2zhang-qlibshu-ju-ceng-shen-du-jie-xi-2ph0

[^16_2]: https://blog.csdn.net/gitblog_00178/article/details/151826589

[^16_3]: https://developer.nvidia.com/blog/gpu-accelerate-algorithmic-trading-simulations-by-over-100x-with-numba/

[^16_4]: https://www.quantvps.com/blog/gpu-accelerated-servers

[^16_5]: https://crm.htsc.com.cn/doc/2020/10750101/d287ebf2-7f3f-4382-bf3f-cfabd4b90161.pdf

[^16_6]: https://github.com/microsoft/qlib/blob/main/examples/benchmarks/README.md

[^16_7]: https://arxiv.org/html/2411.18997v1

[^16_8]: https://qlib.readthedocs.io/en/v0.6.2/component/data.html

[^16_9]: https://qlib.readthedocs.io/en/latest/component/data.html

[^16_10]: https://blog.csdn.net/weixin_40248634/article/details/129592698

[^16_11]: https://asset.quant-wiki.com/pdf/逐鹿Alpha专题报告9：基于QLIBALPHA360的Temporal_FusionTransformer%E9%80%89%E8%82%A1%E6%A8%A1%E5%9E%8B.pdf

[^16_12]: https://dspace.mit.edu/bitstream/handle/1721.1/156635/zhao-zijiezha-phd-eecs-2024-thesis.pdf?sequence=1\&isAllowed=y

[^16_13]: https://www.arxiv.org/pdf/2504.02281.pdf

[^16_14]: https://github.com/microsoft/qlib

[^16_15]: https://blog.csdn.net/2401_82851462/article/details/153471987

[^16_16]: https://doc.finlab.tw/reference/machine_learning/

[^16_17]: https://gist.github.com/devinschumacher/87dd5b87234f2d0e5dba56503bfba533

[^16_18]: https://www.wuzao.com/p/qlib/document/component/data.html

[^16_19]: https://news.ycombinator.com/item?id=35008694

[^16_20]: https://epoch.ai/blog/model-counts-compute-thresholds

[^16_21]: https://www.facebook.com/largitdata/posts/gpu-poor-要如何進行ai研究布朗大學研究團隊調查35個機構的50位研究員調查發現大多數研究員只能使用1-8個gpu使用時間更受限於幾天到幾週不等更令人擔/1036281601844569/

[^16_22]: https://www.perplexity.ai/finance/NVDA


---

# 幫我分析，然後說明在colab 可以做到或者適合的模式，這是我演講時聽到的

這整套投影片在講的是：用「超大量算力＋專用程式庫」把「從論文挖因子 → 回測 → 實盤」做成工廠，但核心邏輯你其實可以在 Colab 上用日資料、小規模版本重現，只是頻率與規模不同。

## 1. 投影片裡在做的事

從你給的幾張照可以看到幾個重點模組：

- 一個有效的回測系統：用 replay 4.5 年 tick，從「1 天跑 4.5 小時」一路優化到「1 天跑 1 秒，再用 10 個 thread + CUDA 只要 1.2 分鐘」，重點是把「歷史重播」變得非常快，才能天天測新策略。
- Quant 1.0→4.0：強調從「人工單一策略」進化到「平台化、多因子、自動回測」，平台越強，單位時間能測的因子越多，AI 因子佔比就越高。
- Domain‑specific Runtime Library（DRL）：把常見運算（MA20、相關矩陣等）做成專用 API，加上快取（原始資料快取、表達式快取、dataset 快取），讓 MA20 加速 30 倍、相關矩陣加速 400 倍。
- Paper → 因子 → 台股驗證：從論文看到某個因子，用資料平台＋因子分析系統把公式實作出來，在 4.5 年 tick data 上分層測試，先小資金上線，再每天／每週看數據。
- 《The Virtue of Complexity in Return Prediction》：這篇 Journal of Finance 論文主張「簡單少因子會低估可預測性，複雜高維模型在美股有優勢」，幫他們背書「用很多因子＋機器學習是有道理的」。[^17_1]
- Demo：快速回測顯示年化 55.5%、Sharpe 2.33、Max Drawdown -27.7%，說明這套回測工廠可以很快算出完整績效表。


## 2. 1000 張 A100 + AWS 在哪裡用掉

像這種 UC 等級的機構，大概會把 A100＋AWS 用在三類工作：

- 大規模因子與模型訓練：在類似 Alpha158/Alpha360 這種高維特徵集上，訓練大量 LightGBM、深度學習（GRU、Transformer）、強化學習等模型，同時做超參數搜尋與 ensemble；GPU 可以把單次訓練和多實驗並行的時間壓到幾小時以內。[^17_2][^17_3]
- 超大量回測／市場重播：用 GPU 加速模擬撮合、滑價、延遲，NVIDIA 官方示例顯示，用 CUDA/Numba 做期貨回測可以比純 CPU 快 100 倍以上，這就是他們投影片上「一天 replay 4.5 小時 → 幾分鐘」背後的東西。[^17_4][^17_5]
- 自動因子挖掘：把論文或 GA 產生的上千個候選因子丟進 DRL，引擎在全市場、tick 級資料上計算，接著用模型＋IC/Sharpe 篩選，這種「幾千因子 × 幾十年資料」的組合爆炸很吃算力。


## 3. 你在 Colab 上能複製的「精華」

你現在已經在 Colab 成功用 Qlib 跑出 TopK 策略的回測與 risk table，其實已經踩到同一條路的「日線版本」。接下來比較適合你的模式是：

- 日資料 + 小規模股票池：用 FinMind 或 yfinance 取日 K，先鎖定台股 50 檔或台指期日線，而不是全市場 tick。這樣 Colab CPU 就能在幾秒～幾十秒內完成多年份回測，根本不需要 A100。
- 因子庫用「精簡 Alpha158 思想」：參考 Alpha158/Alpha360 的結構（價量動能、波動、反轉、成交量、價差等），但只挑 10–20 個你看得懂的因子，存在 SQLite/Parquet，再用 Qlib 的 `features` 或你剛剛做的 `D.features + backtest_daily` 方式去驗證。
- 風險統計：你已經可以算 `annualized_return / IR / max_drawdown` 等指標（剛才那張 risk 表），這就是他們 Demo4 總結表的縮小版，只是你是日頻、他們是 tick／日內。
- 自動因子挖掘「輕量版」：
    - 用大模型幫你把論文的因子公式翻成數學 + SQL/Pandas 步驟。
    - 用 Colab 跑因子值 + IC + 分組報酬。
    - 把結果餵回大模型做文字分析（為什麼失效／有效），這就是你之前問卷式小模型＋SQLite 的延伸。


## 4. 哪些東西不適合硬拚

- 全市場 tick 級 replay：4.5 年 × 全市場 × tick，在 Colab 幾乎不可能穩定做；你可以做的是「少數標的的 1 分鐘／5 分鐘 K」作為近似。
- 自建 DRL / GPU 執行庫：他們是專門工程團隊寫 C++/CUDA + cache 系統，對你來說成本太高；你可以直接用 Qlib、NumPy、Numba 這種現成庫，必要時才在局部熱點用 Numba 加速。
- 幾千因子＋遺傳演算法：這類需要大規模併發運算，適合有叢集與隊列系統的機構；你可以先鎖定「幾十個高品質因子」，用人工＋LLM 過濾，勝率已經足夠高。


## 5. 建議你在 Colab 的實作路線

可以對照他們的流程，做一個「窮人版 UC 平台」：

1. 日資料層：用 FinMind 建一張日頻表（`date, stock_id, open, high, low, close, volume, factor`），再加上你需要的財報／籌碼欄位。
2. 因子層：挑 10–20 個 Alpha158 風格因子（動能、波動、反轉、量異常、價值 E/P），用 Qlib 或自己的 pandas 公式算出來。
3. 回測層：用你剛剛跑成功的 `TopkDropoutStrategy + backtest_daily + risk_analysis`，固定輸出 `annualized_return, IR, max_drawdown` 等指標，當成 Demo4 那張表的標準格式。
4. 研究層：把外面的論文（像那篇 complexity 論文）或 UC 講座的因子邏輯丟給大模型，請它依你現在的日資料 schema 產生新的因子定義，再用同一套回測流程驗證。

這樣你在 Colab 上做的是「結構一樣、頻率較低、規模較小」的版本：沒有 1000 張 A100，也一樣可以做到「從 paper 到台股回測，再到風險表」，只是速度從「幾分鐘處理 4.5 年 tick」變成「幾秒處理 5–10 年日 K」，對你現階段其實已經足夠。
<span style="display:none">[^17_10][^17_11][^17_12][^17_13][^17_14][^17_15][^17_6][^17_7][^17_8][^17_9]</span>

<div align="center">⁂</div>

[^17_1]: https://dspace.mit.edu/bitstream/handle/1721.1/156635/zhao-zijiezha-phd-eecs-2024-thesis.pdf?sequence=1\&isAllowed=y

[^17_2]: https://blog.csdn.net/gitblog_00178/article/details/151826589

[^17_3]: https://arxiv.org/html/2411.18997v1

[^17_4]: https://developer.nvidia.com/blog/gpu-accelerate-algorithmic-trading-simulations-by-over-100x-with-numba/

[^17_5]: https://www.quantvps.com/blog/gpu-accelerated-servers

[^17_6]: 1764332409569.jpg

[^17_7]: IMG_20251128_161733.jpg

[^17_8]: IMG_20251128_161610.jpg

[^17_9]: 1764332395441.jpg

[^17_10]: 1764332393638.jpg

[^17_11]: 1764332391897.jpg

[^17_12]: 1764332387162.jpg

[^17_13]: IMG_20251128_161608.jpg

[^17_14]: IMG_20251128_161609.jpg

[^17_15]: 1764332409625.jpg


---

# 把剛剛所有內容還有已經完成的，我演講得到的資料，他們的進步方向，還有我們後續可以在colab或者其它的google gcp可以做的

你在這次演講與實作裡，其實已經把「UC 那套工廠」拆解出主架構，現在差的是用 Colab / GCP 做出一個縮小版、日頻版本。下面整理成「他們在做什麼」＋「你目前做到哪裡」＋「接下來在 Colab/GCP 可以怎麼走」。

***

## UC 的平台與進步方向（你聽到的重點）

- 他們強調的是「平台驅動」：從 Quant 1.0 的單一策略與人工經驗，到 Quant 2.0 的資料平台與回測系統，再到 Quant 2.5–3.0 導入 AI 因子、大量 GPU、雲端，讓因子 throughput 大幅增加。[^18_1][^18_2]
- 回測系統目標是能在 tick 級完整 replay 4.5 年市場，從「一筆一筆重播要跑 20 多天」優化到「工程化系統＋多執行緒＋CUDA 後，只要幾分鐘」，這樣每天早上開盤前就能把新條件全部測完。[^18_2]
- 他們自建 Domain‑specific Runtime Library（DRL）：把常見運算（均線、相關矩陣、各種技術指標）抽成 API，加上三層快取（原始資料、表達式、dataset），實測讓 MA20 算法加速 30 倍、相關矩陣加速 400 倍，避免每個研究員各寫一份慢又容易有 bug 的 code。[^18_3][^18_1]
- 硬體上有自有 GPU 叢集（如數百～上千張 A100 / H200）再加 AWS，專門用來：在像 Alpha158/360 這種高維資料集上訓練大量模型、做自動因子挖掘、海量回測與強化學習實驗，目標是每月可以測數百～上千個新因子組合。[^18_4][^18_5][^18_1]

***

## 你現在在 Colab 已經做到的事情

- 你已經在 Colab 成功安裝 Qlib，下載官方 `cn_data` 日資料，並用 `D.features` 把 CSI300 的 `$close` 拉出來，這等同於連上他們的「資料層」但用的是公開日頻資料。[^18_6][^18_7]
- 你用 5 日報酬當簡單訊號，套 Qlib 的 `TopkDropoutStrategy` 做 Top‑K 選股，透過 `backtest_daily` 完成 2017–2020 的日回測，拿到每日報表 `report` 和持股矩陣 `positions`。[^18_8]
- 接著用 `risk_analysis` 算出：含成本年化超額報酬約 6.6%、information ratio 約 0.86、最大回撤約 -9%，這就是一份簡化版的「策略體檢表」——跟 UC Demo4 那張 Sharpe / Max Drawdown 表本質上一樣，只是頻率與標的不同。[^18_9][^18_10]

換句話說，你已經把「資料層 → 策略層 → 回測層 → 風險分析」這條管線在日資料上跑通了，只是現在訊號很簡單（5 日動能），還沒接上真正的 Alpha158/360 或你關心的台股 / 台指資料。

***

## 在 Colab 上可以做到的「UC 縮小版」

不靠 A100、只用 Colab CPU + 日 K，其實可以復刻 70% 的方法論：

- 資料層：
    - 用 FinMind 把台股日 K、財報、三大法人拉進一張標準表（`date, stock_id, open, high, low, close, volume, factor` 再加幾個基本面欄位），Schema 參考 Qlib 的要求即可。[^18_7][^18_11]
    - 把這張表存成 SQLite / Parquet，等於你的「本地 Data Platform」，Colab 掛 Google Drive 就能讀寫。
- 因子層（對應 Alpha158/360 思想）：
    - 先挑 10–20 個你「有直覺、看得懂」的因子：動能（3/6/12 個月）、波動度、價值（E/P、B/P）、量異常、價格遠離均線、法人買超等，這些都能用日資料實現，結構類似 Alpha158 裡的價量特徵。[^18_5][^18_12]
    - 用大模型幫你把論文因子翻成數學公式 + Pandas／SQL 步驟，再在 Colab 上算出因子矩陣，然後用剛跑過的 Qlib 回測流程驗證 IC 與分組報酬。
- 回測與風險層：
    - 延續你剛才的 TopK pipeline：把 `pred_score` 換成「某個因子值」或「多因子模型的預測分數」，一樣用 `backtest_daily + risk_analysis`，就能快速得到年化報酬、IR、MDD 等指標。
    - 這一層其實就是 UC 投影片中「Case Study：從 paper 因子 → 台股驗證 → 小金額實測 → 每日／每週監控」的日線版本，只是你回測的是 5～10 年日資料，而不是 4.5 年 tick。
- AI / LLM 協助（自動因子挖掘「輕量版」）：
    - 從 UC 投影片與你錄的逐字稿可以看到，他們也強調用論文、機器學習模型產生大量候選因子，再做嚴格驗證。[^18_2]
    - 在你的架構裡，可以讓大模型負責：讀 paper → 產生候選因子公式 → 轉成 SQL/Pandas → 產生多版本設定檔（rebalance 週期、持股數、成本假設），再交給 Colab 的 Qlib pipeline 自動跑一輪；最後再由大模型幫你摘要哪幾個因子在台股有效。

***

## 什麼時候需要 GCP / GPU，怎麼用才值得

你現階段用 Colab CPU 跑日資料，已經足以涵蓋：台股日 K、50 檔股票、10 年歷史、數十個因子與 TopK 回測，不會有速度瓶頸。[^18_13][^18_4]
考慮 GCP / GPU 的合理時機是：

- 你開始引入「分鐘級資料」或「上百檔股票的 1 分鐘 K」、且要做多策略回測時，Colab CPU 會變得很慢，這時可以在 GCP 開一台有 T4 / L4 的 VM 或 Vertex Notebook，專門跑回測。
- 你想用深度學習模型（LSTM、Transformer、TFT 等）直接吃 Alpha158/自製因子矩陣做預測，再用 Qlib 的 `Model` 介面整合到回測流程，這類模型在 GPU 上會比 CPU 快數十倍。[^18_14][^18_5]
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

<div align="center">⁂</div>

[^18_1]: ucZi-Ben.docx

[^18_2]: UCZi-Ben-_20251128_112122.txt

[^18_3]: https://www.wuzao.com/p/qlib/document/component/data.html

[^18_4]: https://developer.nvidia.com/blog/gpu-accelerate-algorithmic-trading-simulations-by-over-100x-with-numba/

[^18_5]: https://blog.csdn.net/gitblog_00178/article/details/151826589

[^18_6]: https://github.com/microsoft/qlib

[^18_7]: https://qlib.readthedocs.io/en/stable/component/data.html

[^18_8]: https://qlib.readthedocs.io/en/latest/component/strategy.html

[^18_9]: https://qlib.readthedocs.io/en/v0.9.2/component/report.html

[^18_10]: https://blog.csdn.net/weixin_40248634/article/details/129592698

[^18_11]: https://finmind.github.io

[^18_12]: https://blog.csdn.net/2401_82851462/article/details/153471987

[^18_13]: https://www.quantvps.com/blog/gpu-accelerated-servers

[^18_14]: https://dspace.mit.edu/bitstream/handle/1721.1/156635/zhao-zijiezha-phd-eecs-2024-thesis.pdf?sequence=1\&isAllowed=y

