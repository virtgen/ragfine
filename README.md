# .ragfine — Perfect AI starts here.
Framework that helps you **build, evaluate, and refine** RAG component in generative AI pipelines with surgical precision.  
> Developed by [IncubeAI](https://github.com/incubeai) — founded by [Artur Bak](https://github.com/virtgen).

---

## 🧠 What is .ragfine?

.ragfine is a modular framework that helps you **build, evaluate, and refine** RAG component
or any other AI pipeline.  
It automatically analyzes retrieval quality, semantic coherence, prompt strategy, and response alignment — helping your AI reason more clearly.

---

## ✨ Features
- 🔍 Retrieval Diagnostics — detect irrelevant or missing chunks.  
- 🧩 Embedding Alignment — optimize vector representations for semantic precision.  
- 🧠 Prompt Refinement — evaluate and fine-tune query templates dynamically.  
- 📈 Performance Tracking — continuous feedback on retrieval + generation quality.  

---

## 🚀 Quick Start
```bash
pip install ragfine
ragfine analyze --config config.yaml

## Local Tests
```bash
poetry install --with dev

make install        # install dev deps via Poetry
make test           # run all tests
make coverage       # with coverage report
make lint           # static checks
make format         # format code (black + isort)
make clean          # remove caches

