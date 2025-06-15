#!/bin/bash

# Build knowledge base
echo "Building knowledge base..."
python build_agent.py --pdf_dir ./research_papers --index_name physics_papers

# Evaluate model
echo "Evaluating model..."
python evaluate_model.py --test_data ./test_data.test_data.json --index_name physics_papers

echo "Process completed!"