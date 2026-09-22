import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import json
from datetime import datetime
from typing import Any, List, Tuple, Optional
from logger import logger
from src.ai.observability.engine import DiagnosticEngine
from apps.windows.telemetry.models import AnomalyItem
from src.rag.user_workspace_rag import user_workspace_rag_manager

class DataResearchEngine(DiagnosticEngine):
    """
    Движок для проведения статистического анализа данных и генерации отчетов с ИИ-интерпретацией и RAG-памятью.
    """
    def __init__(self, user_id: int = 0, chat_model: Any = None):
        super().__init__(chat_model=chat_model)
        self.user_id = user_id
        self.rag_collection_id = "research_reports"
        self.data = None
        self.report_dir = os.path.join(os.path.dirname(__file__), "tmp", "reports")
        os.makedirs(self.report_dir, exist_ok=True)
        self._ensure_rag_collection()
        logger.debug(f"DataResearchEngine initialized for user {user_id}. Reports dir: {self.report_dir}")

    def _ensure_rag_collection(self):
        """Гарантирует существование RAG-коллекции для отчетов."""
        if not user_workspace_rag_manager.get_collection(self.user_id, self.rag_collection_id):
            user_workspace_rag_manager.create_collection(
                self.user_id,
                name="Research Reports",
                description="Архив автоматических отчетов по статистическим исследованиям данных."
            )
            logger.info(f"Created RAG collection '{self.rag_collection_id}'")

    def _save_report_to_rag(self, file_path: str, report: dict):
        """Сохраняет отчет в RAG-индекс."""
        filename = os.path.basename(file_path)
        question = f"Исследование данных: {filename} от {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Очищаем отчет перед сохранением (убираем пути к файлам из визуализаций)
        report_to_save = report.copy()
        report_to_save["visualizations"] = [v.get("title") for v in report.get("visualizations", [])]

        user_workspace_rag_manager.add_qa_entry(
            user_id=self.user_id,
            rag_id=self.rag_collection_id,
            question=question,
            answer=json.dumps(report_to_save, ensure_ascii=False),
            meta={"file_path": file_path, "is_research": True}
        )

    def _get_historical_context(self, file_path: str) -> str:
        """Ищет исторические отчеты по данному файлу."""
        filename = os.path.basename(file_path)
        results = user_workspace_rag_manager.search_collection(
            self.user_id, self.rag_collection_id, query=filename, top_k=2
        )
        if not results:
            return ""
        
        context = "Исторические исследования по этому файлу:\n"
        for res in results:
            context += f"- {res['text']}\n"
        return context

    def load_data(self, file_path: str) -> bool:
        """Загрузка данных из CSV файла."""
        try:
            self.data = pd.read_csv(file_path)
            logger.debug(f"Data loaded from {file_path}.")
            return True
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return False

    def evaluate_heuristics(self, data: Any = None) -> Tuple[int, List[AnomalyItem], List[str]]:
        """
        Поиск статистических аномалий (выбросы, корреляции).
        
        Returns:
            Tuple[int, List[AnomalyItem], List[str]]: Оценка здоровья, список аномалий, рекомендации.
        """
        if self.data is None:
            return 0, [AnomalyItem(severity="high", description="Data not loaded")], ["Load data first"]
        
        anomalies = []
        recommendations = []
        score = 100

        # Поиск пропущенных значений
        missing_count = self.data.isnull().sum().sum()
        if missing_count > 0:
            score -= 20
            anomalies.append(AnomalyItem(severity="medium", description=f"Found {missing_count} missing values"))
            recommendations.append("Consider imputing or dropping missing values")

        # Поиск выбросов (простой метод 3-х сигм для примера)
        numerical_df = self.data.select_dtypes(include=['number'])
        if not numerical_df.empty:
            outliers = (numerical_df > numerical_df.mean() + 3 * numerical_df.std()).sum().sum()
            if outliers > 0:
                score -= 10
                anomalies.append(AnomalyItem(severity="low", description=f"Found {outliers} potential outliers"))
                recommendations.append("Investigate outliers for data quality issues")

        return max(0, score), anomalies, recommendations

    async def run_full_research(self, file_path: str) -> dict:
        """
        Проведение полного исследования данных: загрузка, эвристики, RAG-контекст и ИИ-диагностика.
        """
        if not self.load_data(file_path):
            return {"error": "Failed to load data"}

        # ИИ-диагностика (вызов метода из DiagnosticEngine)
        diagnostic_report = await self.diagnose(self.data)
        
        # Получение истории
        history = self._get_historical_context(file_path)

        report = {
            "statistics": self.data.describe().to_dict(),
            "ai_report": diagnostic_report.model_dump(),
            "historical_context": history,
            "visualizations": []
        }

        # Генерация визуализаций
        numerical_df = self.data.select_dtypes(include=['number'])
        if not numerical_df.empty:
            corr_path = os.path.join(self.report_dir, "correlation.png")
            plt.figure(figsize=(10, 8))
            sns.heatmap(numerical_df.corr(), annot=True, cmap='coolwarm')
            plt.title('Тепловая карта корреляции')
            plt.savefig(corr_path)
            plt.close()
            report["visualizations"].append({"title": "Correlation Matrix", "path": corr_path})

        # Сохранение в RAG
        self._save_report_to_rag(file_path, report)

        logger.debug("Full research completed with AI interpretation and RAG save.")
        return report
