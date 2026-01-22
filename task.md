# Task: Refactoring and Enhancing Orchestration System

## Status
- [ ] Refactor Directory Structure
    - [ ] Create `backend/services/orchestrator/`
    - [ ] Create `backend/services/knowledge/`
    - [ ] Create `backend/services/tools/`
    - [ ] Create `backend/services/core/`
    - [ ] Move files to appropriate directories
    - [ ] Update imports in all files (using `find` and `sed` or equivalent)

## Orchestration Enhancements
- [ ] Enhance `CoTGeneratorService`
    - [ ] Implement dynamic prompting based on `QueryType` (Analytical vs Factual)
    - [ ] Add explicit validation/critique step in reasoning generation
- [ ] Enhance `SearchOrchestratorService`
    - [ ] Integrate `langchain_community.utilities.SearxSearchWrapper`
    - [ ] Implement "Iterative Search": If initial results are poor, refine terms and retry (max 1 retry)
- [ ] Enhance `AnswerGeneratorService`
    - [ ] Add self-critique/reflection loop before returning final answer (optional, based on complexity)

## Verification
- [ ] Verify `backend/main.py` imports work after refactor
- [ ] Test `POST /api/orchestrate/search` with improved components
