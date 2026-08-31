# colab

Google Colab notebooks for running AI Breadboard experiments in a cloud environment without local setup.

## Files

- `RAG_Media_Colab.ipynb` — Notebook for building and querying a RAG (Retrieval-Augmented Generation) index over a media library using FAISS and Gemini embeddings

## Usage

Open the notebook directly in Google Colab:

1. Upload `RAG_Media_Colab.ipynb` to [colab.research.google.com](https://colab.research.google.com)
2. Set your `GEMINI_API_KEY` in the Colab secrets panel
3. Run all cells sequentially

## Dependencies

- `google-generativeai`
- `faiss-cpu`
- `sentence-transformers`
