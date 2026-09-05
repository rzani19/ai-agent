# AI Agent / Vibe Coding — Project Context

## Tentang Project Ini
Playground + portfolio untuk belajar AI Agent dan Vibe Coding. Prinsip: **practical > theory**, build while learning. AI (Claude Code) menulis code, saya (user) memahami architecture dan logic-nya. Jangan biarkan saya mengetik boilerplate manual kalau Claude Code bisa mengerjakannya.

**PENTING — kalibrasi tujuan**: Saya ingin bisa membangun AI Agent secara efektif & efisien dengan bantuan AI (vibe coding). Saya **BUKAN** ingin jadi deep programmer/coder. Implikasinya:
- Penjelasan cukup level konsep (apa yang berubah, kenapa, 1-2 kalimat) — jangan bedah kode baris demi baris kecuali saya minta.
- Automated testing (pytest) justru PENTING — itu cara saya percaya hasil kerja tanpa harus baca/paham detail implementasi tiap kali.
- Fokus keputusan: apakah ini aman, apakah ini kerja, apakah arsitekturnya masuk akal — bukan penguasaan sintaks Python.
- Tetap jaga 1 task at a time + git checkpoint, tapi jangan asumsikan saya mau ngerti tiap baris diff.

Tujuan akhir: bisa merancang & mengarahkan AI Agent project dari ide → working product → portfolio, dengan coding agent sebagai eksekutor utama.

## Environment
- **OS**: Windows + WSL2, Ubuntu 26.04.1 LTS (kernel 6.18.33.2-microsoft-standard-WSL2)
- **Hardware**: Lenovo Legion 5i, i7, RTX 4060 Laptop (8GB VRAM), 32GB RAM, 1TB SSD — pertimbangkan ini untuk semua rekomendasi model/tool lokal, jangan yang terlalu berat tanpa manfaat jelas.
- **Docker**: Docker Desktop Windows + WSL2 integration
- **Git**: 2.53.0
- **Python system**: 3.14.4 — **jangan diubah**, project pakai Python 3.12 via `uv`
- **uv**: 0.12.10, venv di `~/projects/ai-agent/.venv`, Python 3.12.14
- **Node**: via NVM 0.40.3 → Node v24.20.0, npm 11.19.0
- **Ollama**: berjalan lokal, model `qwen3:8b` (~5.2GB), SDK `ollama==0.6.2`

## Project Location
`~/projects/ai-agent` — Git sudah di-init. **Jangan reset/delete/overwrite destructive** tanpa menjelaskan dulu. Git selalu jadi safety checkpoint (commit sebelum perubahan besar).

`.env` mungkin berisi secret — jangan pernah minta saya paste isinya.

## Stack
**Sudah dipakai**: Python, uv, pytest, tool registry manual, Ollama (qwen3:8b) + Claude API (Haiku 4.5) sebagai dual LLM backend
**Target berikutnya**: structured output → MCP → LangGraph
**Nanti (backend/deploy)**: FastAPI, PostgreSQL, Docker, VPS
**Nanti (RAG, kalau perlu)**: Chroma / Qdrant / pgvector

Prinsip: **one primary tool per category** kecuali ada alasan kuat untuk nambah. Jangan pasang LangGraph/CrewAI/framework berat sebelum fundamental agent dipahami manual. Jangan install banyak subscription/tool/SaaS tanpa alasan jelas — TAPI spending kecil (API pay-as-you-go, subscription murah) boleh kalau itu jelas mempercepat progress/hasil project, selama tetap pilih tier termurah yang cukup.

## LLM Backend Strategy
Tetap pakai Ollama (qwen3:8b) sebagai satu-satunya backend untuk sekarang — upgrade ke Claude API sempat dipertimbangkan tapi payment API belum bisa diproses (kendala kartu). Kalau nanti payment-nya kepecahin (misal pakai virtual card), boleh dicoba lagi. Untuk sekarang, keterbatasan tool-calling qwen3:8b disiasati lewat prompting/kode, bukan ganti model.

## Cara Kerja yang Saya Mau
1 task → implement → test → saya pahami → next task. Jangan kasih 10 langkah sekaligus. Kalau ada beberapa opsi, pilihkan **satu** rekomendasi utama + alasan singkat — jangan bikin saya milih dari banyak opsi.

Untuk setiap perubahan penting, ikuti urutan ini:
1. Jelaskan singkat apa yang mau diubah
2. Jelaskan alasan architectural-nya
3. Implementasikan
4. Jalankan test
5. Laporkan hasil test
6. Tunjukkan perubahan penting kalau perlu

Sebelum kerjakan task baru: inspect repo dulu (struktur, file terkait, git status) sebelum ubah apapun. Jangan langsung massive refactor.

## Gaya Komunikasi
Bahasa Indonesia santai dan jelas, seperti mentor/senior dev. Hindari: overengineering, teori panjang tanpa diminta, terlalu banyak pilihan sekaligus, install framework sebelum dibutuhkan.

## Roadmap Singkat
- **Phase 0** (mostly done): environment setup
- **Phase 1**: Python fundamentals sambil build (nggak perlu selesaikan course dulu)
- **Phase 2** (current focus): Vibe Coding — pakai Claude Code efektif
- **Phase 3**: LLM engineering (tool calling, structured output, context management)
- **Phase 4**: AI Agent manual (tool registry, agent loop, state/memory, error handling, RAG, MCP)
- **Phase 5**: Framework (LangGraph, dst) — setelah paham manual implementation-nya
- **Phase 6**: Real portfolio projects
- **Phase 7**: Monetization

## Known Technical Debt (per commit terakhir)
- Tool execution masih hard-coded, belum ada tool registry proper
- `calculate` tool pakai `eval()` — perlu diganti, tapi bukan cuma ganti 1 baris, ini masuk ke perbaikan architecture agent secara umum
- Belum ada: robust error handling, proper agent loop, state/memory, RAG, MCP, production architecture, testing yang solid

## Status Saat Ini — Strategic Pause (penting, baca sebelum saran fitur baru)
Sudah ada tool `get_crypto_price` (CoinGecko) dan `get_stock_price` (Alpha Vantage), keduanya jalan & ter-test. TAPI: sedang PAUSE dulu nambah tool finansial baru (forex, news, technical indicator, dll) dan JANGAN bikin `journal_entry`/trading journal tool dulu.

Alasan: sedang validasi manual (tanpa kode) selama 1-2 minggu apakah proses "thesis → decision → journal → review" beneran ngebantu kualitas keputusan trading/investing saya. Kalau belum tervalidasi, coding lebih jauh ke arah ini cuma mindahin proses yang belum kebukti berguna ke kode. Kalau nanti saya bilang "eksperimen manual berhasil, lanjut", baru boleh bantu bikin `journal_entry` tool atau nambah data source lain — sampai saat itu, kalau saya minta task financial-tools baru, tanyakan dulu apakah eksperimen manualnya sudah selesai/berhasil.
