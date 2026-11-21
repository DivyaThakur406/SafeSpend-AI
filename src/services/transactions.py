"""
Transaction Analytics and Data Processing.
"""
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime

from src.database.db_manager import db


class TransactionService:
    @staticmethod
    def get_enriched_transactions(user_id: int = 1, limit: int = 100) -> pd.DataFrame:
        df = db.get_transactions(user_id, limit=limit)
        if df.empty:
            return df
        df["date_formatted"] = pd.to_datetime(df["date"]).dt.strftime("%d %b %Y")
        return df

    @staticmethod
    def get_category_breakdown(user_id: int = 1) -> pd.DataFrame:
        df = db.get_transactions(user_id)
        if df.empty:
            return pd.DataFrame(columns=["category", "total_amount", "count", "percentage"])
        
        expense_df = df[df["type"] == "expense"]
        if expense_df.empty:
            return pd.DataFrame(columns=["category", "total_amount", "count", "percentage"])
        
        grouped = expense_df.groupby("category").agg(
            total_amount=("amount", "sum"),
            count=("id", "count")
        ).reset_index()

        total_expense = grouped["total_amount"].sum()
        grouped["percentage"] = (grouped["total_amount"] / total_expense * 100).round(1)
        grouped = grouped.sort_values(by="total_amount", ascending=False)
        return grouped

    @staticmethod
    def get_upi_app_breakdown(user_id: int = 1) -> pd.DataFrame:
        df = db.get_transactions(user_id)
        if df.empty:
            return pd.DataFrame(columns=["upi_app", "total_amount", "count"])
        
        expense_df = df[df["type"] == "expense"]
        grouped = expense_df.groupby("upi_app").agg(
            total_amount=("amount", "sum"),
            count=("id", "count")
        ).reset_index()
        grouped = grouped.sort_values(by="total_amount", ascending=False)
        return grouped

    @staticmethod
    def get_daily_spending_trend(user_id: int = 1) -> pd.DataFrame:
        df = db.get_transactions(user_id)
        if df.empty:
            return pd.DataFrame(columns=["date", "amount"])
        
        expense_df = df[df["type"] == "expense"].copy()
        expense_df["date"] = pd.to_datetime(expense_df["date"])
        daily = expense_df.groupby("date")["amount"].sum().reset_index()
        daily = daily.sort_values(by="date")
        return daily
