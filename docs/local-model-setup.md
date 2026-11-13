# Optional local-model workflows

The autonomous studio supports an optional local Ollama-compatible model. This path is separate from paid API inference.

## Safety and defaults

- Local inference is disabled unless `STUDIO_LOCAL_LLM_ENABLED=true` is explicitly set.
- The endpoint must be a literal loopback IP, normally `http://127.0.0.1:11434`. Remote hosts and `localhost` names are rejected.
- The studio does not download models. Install Ollama and download a model yourself before running anything.
- No API key or paid provider is used by this path. The client reports an API cost of €0.
- The command requires `--approve-local-run`; the scheduled GitHub Actions workflow does not call it.
- Specialist outputs are drafts and the workflow stops at `review_required`. It does not publish, contact people or spend money.
- Do not place passwords, API keys, access tokens or other secrets in workflow JSON.

## Prepare the local model

1. Install Ollama using its official installer for your operating system.
2. Start the Ollama service.
3. Download a model that is compatible with your machine. The studio will not choose or download one automatically.
4. Confirm the exact installed model name with `ollama list`.

## Configure the local run

From the repository root, set the local opt-in and the exact installed model name:

```bash
export STUDIO_LOCAL_LLM_ENABLED=true
export STUDIO_LOCAL_LLM_BASE_URL=http://127.0.0.1:11434
export STUDIO_LOCAL_LLM_MODEL='YOUR_INSTALLED_MODEL_NAME'
```

Edit `data/local_workflow.example.json` or create your own JSON file. A workflow contains 1–6 specialist tasks and a JSON object called `context`. Use only information you are comfortable sending to the local model.

Run it manually:

```bash
python -m agent.local_runner \
  --workflow data/local_workflow.example.json \
  --workflow-id my-first-local-run \
  --approve-local-run
```

The workflow ID is used for checkpoint recovery. Use a new ID when you want a fresh workflow rather than resuming previous specialist outputs.

## What the result means

A successful run ends in `review_required`, not in publication or automatic acceptance. Inspect the specialist drafts and checkpoint file under `data/agent_checkpoints/` before deciding what to do next.

This local path has automated tests using mocked HTTP responses. Those tests do not prove that a particular model is installed, fast enough or good at reasoning on your hardware.
