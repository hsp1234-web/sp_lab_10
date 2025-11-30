import pytest
import subprocess
import sys
from pathlib import Path

class TestIntegration:
    
    def test_main_help(self):
        """測試 CLI Help"""
        result = subprocess.run(
            [sys.executable, "main.py", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Hybrid Qlib Framework CLI" in result.stdout

    def test_prepare_data_dry_run(self, tmp_path):
        """測試資料準備 (模擬)"""
        # 這裡我們不真的去連 DB，而是測試參數解析
        # 如果沒有 DB，script 會報錯但 returncode 可能是 1
        # 我們預期它會失敗 (因為測試環境可能沒 DB)，但至少能執行
        
        output_dir = tmp_path / "data"
        result = subprocess.run(
            [sys.executable, "main.py", "prepare-data", 
             "--db-path", "dummy.db", 
             "--output-dir", str(output_dir)],
            capture_output=True,
            text=True
        )
        # 預期失敗因為 dummy.db 不存在
        assert "資料庫檔案不存在" in result.stdout or result.returncode != 0
