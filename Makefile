PYTHON ?= python
ROOT := $(CURDIR)

.PHONY: setup test ingest update-corpus quotes packs avatar-slice avatar-workspace founder-memory avatar-report avatar mechanisms landers ads audit

setup:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest -q

ingest:
	$(PYTHON) scripts/ingest_arcticshift.py \
		--submissions data/raw/tinnitus/tinnitus_submissions.jsonl \
		--comments data/raw/tinnitus/tinnitus_comments.jsonl \
		--sqlite data/intermediate/reddit.db \
		--threads-jsonl data/threads/threads.jsonl \
		--threads-md-dir data/threads/md \
		--manifest data/threads/thread_index.csv

update-corpus:
	$(PYTHON) scripts/update_research_corpus.py

quotes:
	$(PYTHON) scripts/extract_quote_candidates.py \
		--threads data/threads/threads.jsonl \
		--threads data/threads/orphan_threads.jsonl \
		--out data/evidence/quote_candidates.jsonl

packs:
	$(PYTHON) scripts/build_research_packs.py \
		--threads data/threads/threads.jsonl \
		--out-dir data/packs \
		--manifest data/packs/pack_manifest.csv \
		--max-threads 25 \
		--max-chars 120000 \
		--max-comments-per-thread 80

avatar-slice:
	$(PYTHON) scripts/build_avatar_state_slice.py \
		--config configs/avatar_states/jaw_clenching_nighttime_spike.json \
		--threads data/threads/threads.jsonl \
		--threads data/threads/orphan_threads.jsonl \
		--out-threads data/avatar_states/jaw_clenching_nighttime_spike/threads.jsonl \
		--out-manifest data/avatar_states/jaw_clenching_nighttime_spike/thread_index.csv \
		--out-report data/avatar_states/jaw_clenching_nighttime_spike/report.json

avatar-workspace:
	$(PYTHON) scripts/build_avatar_workspace.py \
		--config configs/avatar_states/jaw_clenching_nighttime_spike.json

founder-memory:
	$(PYTHON) scripts/refresh_founder_memory.py \
		--workspace data/avatar_states/jaw_clenching_nighttime_spike \
		--config configs/avatar_states/jaw_clenching_nighttime_spike.json

avatar-report:
	$(PYTHON) scripts/build_avatar_report.py \
		--workspace data/avatar_states/jaw_clenching_nighttime_spike \
		--config configs/avatar_states/jaw_clenching_nighttime_spike.json \
		--sections-dir outputs/report_sections \
		--report-state outputs/report_state.json \
		--pattern-ledger outputs/pattern_ledger.json \
		--compiled-body-out outputs/founder_report_body.md

avatar:
	bash bin/avatar-dossier.sh

mechanisms:
	bash bin/mechanism-lab.sh

landers:
	bash bin/lander-angles.sh

ads:
	bash bin/ad-angle-bank.sh

audit:
	bash bin/compliance-audit.sh
