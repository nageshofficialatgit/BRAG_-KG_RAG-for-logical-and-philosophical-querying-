import shutil
import os

files_map = {
    "orchestrator": [
        "query_classifier.py", "cot_generator.py", "search_orchestrator.py",
        "context_synthesizer.py", "answer_generator.py",
        "confidence_scorer_enhanced.py", "confidence_scorer.py"
    ],
    "knowledge": [
        "kg_service.py", "rag_service.py", "philosophy_kg_transformer.py",
        "philosophy_search_enhancer.py", "reference_service.py"
    ],
    "tools": [
        "web_crawler_service.py", "image_service.py", "robots_parser.py"
    ],
    "core": [
        "llm_service.py", "prompt_loader.py", "output_processor.py",
        "conversation_memory_service.py"
    ]
}

base = os.path.join(os.getcwd(), "backend", "services")
print(f"Base dir: {base}")

for dest, files in files_map.items():
    for f in files:
        src = os.path.join(base, f)
        dst = os.path.join(base, dest, f)
        if os.path.exists(src):
            try:
                shutil.move(src, dst)
                print(f"Moved {src} to {dst}")
            except Exception as e:
                print(f"Error moving {src}: {e}")
        else:
            print(f"Source not found: {src}")
