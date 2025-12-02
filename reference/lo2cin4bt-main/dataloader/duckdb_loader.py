import duckdb
import pandas as pd
from typing import Optional, Tuple
from rich.console import Console
from rich.panel import Panel
from .base_loader import AbstractDataLoader

console = Console()

class DuckDBLoader(AbstractDataLoader):
    def __init__(self):
        super().__init__()
        self.db_path = r"c:\SP_lab_Projects\sp_lab_v9_1.1\data\taifex.db"
        self.symbol = None

    def load(self) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Load data from DuckDB
        Returns: (DataFrame, frequency)
        """
        try:
            con = duckdb.connect(self.db_path)
            
            # Step 1: Select Symbol
            # Get list of symbols (top 20 by count to avoid clutter)
            # Or just let user type it?
            # Let's list major ones like TX, MTX, TE, TF
            
            # Query distinct symbols and their counts
            print("Fetching available symbols...")
            sym_df = con.execute("""
                SELECT Symbol, COUNT(*) as Count 
                FROM futures_data 
                GROUP BY Symbol 
                ORDER BY Count DESC 
                LIMIT 20
            """).fetchdf()
            
            console.print(Panel(
                sym_df.to_string(index=False),
                title="[bold #dbac30]Top 20 Symbols[/bold #dbac30]",
                border_style="#dbac30"
            ))
            
            while True:
                console.print("[bold #dbac30]Enter Symbol (e.g., TX):[/bold #dbac30]")
                symbol = input().strip().upper()
                if not symbol:
                    continue
                
                # Check if symbol exists
                count = con.execute("SELECT COUNT(*) FROM futures_data WHERE Symbol = ?", [symbol]).fetchone()[0]
                if count == 0:
                    console.print(f"[red]Symbol {symbol} not found![/red]")
                    continue
                
                self.symbol = symbol
                break
            
            # Step 2: Select Date Range (Optional)
            console.print("[bold #dbac30]Enter Start Year (YYYY) [Enter for all]:[/bold #dbac30]")
            start_year = input().strip()
            
            query = "SELECT * FROM futures_data WHERE Symbol = ?"
            params = [self.symbol]
            
            if start_year:
                query += " AND Date >= ?"
                params.append(f"{start_year}/01/01")
                
            # Step 3: Load Data
            print(f"Loading data for {self.symbol}...")
            df = con.execute(query, params).fetchdf()
            
            con.close()
            
            if df.empty:
                self.show_error("No data found for the selected criteria.")
                return None, None
                
            # Standardize columns
            # Our DB columns are already English: Date, Open, High, Low, Close, Volume
            # But AbstractDataLoader expects 'Time' instead of 'Date'
            df.rename(columns={'Date': 'Time'}, inplace=True)
            
            # Convert Time to datetime
            df['Time'] = pd.to_datetime(df['Time'])
            
            # Sort by Time
            df.sort_values('Time', inplace=True)
            df.reset_index(drop=True, inplace=True)
            
            # Set frequency (Daily data)
            frequency = "1d"
            
            return df, frequency

        except Exception as e:
            self.show_error(f"Error loading from DuckDB: {e}")
            return None, None
