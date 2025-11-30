import qlib
from qlib.constant import REG_CN
from qlib.utils import init_instance_by_config
from qlib.workflow import R
from qlib.workflow.record_temp import SignalRecord, PortAnaRecord
import sys
from pathlib import Path
import yaml

def run_example():
    # 設定資料路徑
    provider_uri = str(Path("data/qlib_data/cn_data").absolute())
    qlib.init(provider_uri=provider_uri, region=REG_CN)

    # 簡單的設定檔
    config = {
        "market": "csi300",
        "benchmark": "SH000300",
        "data_handler_config": {
            "start_time": "2020-01-01",
            "end_time": "2020-12-31",
            "fit_start_time": "2020-01-01",
            "fit_end_time": "2020-06-30",
            "instruments": "csi300",
        },
        "task": {
            "model": {
                "class": "LGBModel",
                "module_path": "qlib.contrib.model.gbdt",
                "kwargs": {
                    "loss": "mse",
                    "colsample_bytree": 0.8879,
                    "learning_rate": 0.0421,
                    "subsample": 0.8789,
                    "lambda_l1": 205.6999,
                    "lambda_l2": 580.9768,
                    "max_depth": 8,
                    "num_leaves": 210,
                    "num_threads": 20,
                },
            },
            "dataset": {
                "class": "DatasetH",
                "module_path": "qlib.data.dataset",
                "kwargs": {
                    "handler": {
                        "class": "Alpha158",
                        "module_path": "qlib.contrib.data.handler",
                        "kwargs": {
                            "start_time": "2020-01-01",
                            "end_time": "2020-12-31",
                            "fit_start_time": "2020-01-01",
                            "fit_end_time": "2020-06-30",
                            "instruments": "csi300",
                        },
                    },
                    "segments": {
                        "train": ["2020-01-01", "2020-06-30"],
                        "valid": ["2020-07-01", "2020-09-30"],
                        "test": ["2020-10-01", "2020-12-31"],
                    },
                },
            },
            "record": [
                {
                    "class": "SignalRecord",
                    "module_path": "qlib.workflow.record_temp",
                    "kwargs": {"model": "<MODEL>", "dataset": "<DATASET>"},
                },
                {
                    "class": "PortAnaRecord",
                    "module_path": "qlib.workflow.record_temp",
                    "kwargs": {
                        "model": "<MODEL>",
                        "dataset": "<DATASET>",
                        "strategy": {
                            "class": "TopkDropoutStrategy",
                            "module_path": "qlib.contrib.strategy.strategy",
                            "kwargs": {
                                "model": "<MODEL>",
                                "dataset": "<DATASET>",
                                "topk": 50,
                                "n_drop": 5,
                            },
                        },
                        "backtest": {
                            "start_time": "2020-10-01",
                            "end_time": "2020-12-31",
                            "account": 100000000,
                            "benchmark": "SH000300",
                            "exchange_kwargs": {
                                "limit_threshold": 0.095,
                                "deal_price": "close",
                                "open_cost": 0.0005,
                                "close_cost": 0.0015,
                                "min_cost": 5,
                            },
                        },
                    },
                },
            ],
        },
    }

    # 執行 Workflow
    with R.start(experiment_name="alpha158_example"):
        # init_instance_by_config 會自動訓練並回傳 model
        model = init_instance_by_config(config["task"]["model"])
        dataset = init_instance_by_config(config["task"]["dataset"])
        
        # 訓練
        model.fit(dataset)
        
        # 預測與記錄
        recorder = R.get_recorder()
        R.save_objects(**{"params.pkl": config})
        
        # 執行 Record (包含回測)
        # 注意: 這裡簡化流程，直接呼叫 Record 的 generate 方法
        # 實際 Qlib 流程可能更複雜，這裡只做最小驗證
        
        label_df = dataset.prepare("test", col_set=["label"], data_key=DataHandlerLP.DK_L)
        pred_df = model.predict(dataset)
        
        print("預測完成，前 5 筆結果：")
        print(pred_df.head())

if __name__ == "__main__":
    run_example()
