# 📚 AI Breadboard: ספר לימוד לארכיטקטורת AI, RAG ו-Fine-Tuning

> **לוח פיתוח אינטראקטיבי (Breadboard) לחוקרים ומפתחי מערכות בינה מלאכותית**

---

## 💡 מניפסט «AI Breadboard»

בהנדסת אלקטרוניקה, **לוח פיתוח (Breadboard)** הוא כלי יסוד המאפשר לחבר רכיבים (טרנזיסטורים, מיקרו-בקרים, חיישנים) ללא הלחמה, לבדוק אותות בנקודות בקרה ולשנות את מבנה המעגל במהירות.

פרויקט **`aibreadboard`** מביא את הגישה הזו לעולם ה-AI:
1. **לוח פיתוח פתוח (Open Breadboard Testbench):** הרצה ישירה, שקופה ומהירה על המחשב המקומי (FastAPI, Python venv, ONNX DirectML) עם גישה ישירה לכל רכיב.
2. **אפיק מודלים אחיד:** חיבור כל מודל – מ-Google Gemini בענן ועד מודלים מקומיים קלים (SLMs) – תחת ממשק אחוד `UnifiedChatModel`.
3. **שקיפות מלאה:** גישה ישירה לחישוב וקטורים (Embeddings), דירוג דמיון קוסינוס ואימון נתונים.
4. **מעבדת RAG ו-Fine-Tuning:** אופטימיזציה של מודלים עם Microsoft Olive, המרת משקלים ב-ONNX ואימון מהיר ב-LoRA/QLoRA.
5. **מערכת מיומנויות (Skills):** הרחבה מודולרית של סוכנים לפי דרישה דרך קובצי `SKILL.md`.

---

## 🧭 פרקי הספר

| פרק | נושא |
|---|---|
| [**פרק 1**](../../en/book/ch01_philosophy.md) | פילוסופיית No-Docker והגדרת סביבת העבודה |
| [**פרק 2**](../../en/book/ch02_orchestration.md) | ניתוב מודלים ועמידות בפני תקלות (UnifiedChatModel & ModelManager) |
| [**פרק 3**](../../en/book/ch03_local_inference.md) | הרצת מודלים מקומית והאצת DirectML על גבי כל כרטיס מסך |
| [**פרק 4**](../../en/book/ch04_rag_architecture.md) | ארכיטקטורת RAG, מתמטיקה של וקטורים ואינדקס FAISS |
| [**פרק 5**](../../en/book/ch05_optimization_finetuning.md) | אופטימיזציית מודלים (Microsoft Olive), המרת ONNX ו-Fine-Tuning |
| [**פרק 6**](../../en/book/ch06_agents_and_mcp.md) | סוכני ReAct, פרוטוקול MCP וממשק קולי |
| [**פרק 7**](../../en/book/ch07_skills_management.md) | יצירה וניהול מיומנויות (Skills) עבור מודלים וסוכנים |
| [**פרק 8**](../../en/book/ch08_laboratory_practicum.md) | 10 מעבדות מעשיות על גבי לוח הפיתוח |
