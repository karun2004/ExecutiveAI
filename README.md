# MACH-1 v3 — AI Company Operating System

One-command AI company that runs on your laptop. Zero monthly cost.

## What It Does

MACH-1 is a **6-team AI company** managed by a CEO agent:

| Team | Job | Primary Model |
|------|-----|---------------|
| **CEO** | Creates plans, assigns tasks, monitors everything | Groq Llama 3.3 70B |
| **Content** (OpenClaw) | Blogs, social posts, video scripts | Groq → Mistral → Ollama |
| **Coding** | Builds projects from descriptions | Codestral → Groq → Ollama |
| **DevOps** | Code review, git push, health monitoring | Mistral Large → Groq |
| **Marketing** | Social strategy, engagement optimization | Groq → Mistral |
| **Sales** | Outreach drafts, lead generation | Mistral Large → Groq |

## Quick Start

```bash
# 1. Clone and setup
chmod +x setup.sh && ./setup.sh

# 2. Add your API keys
nano .env

# 3. Start
sudo systemctl start mach1 mach1-dashboard

# 4. Open dashboard
firefox http://localhost:5000
```

## Architecture

```
mach-1/
├── main.py              # Master process (CEO + scheduler)
├── dashboard/app.py     # Flask dashboard (separate service)
├── agents/
│   ├── ceo.py           # CEO agent (controls all teams)
│   ├── content_team.py  # Content generation (OpenClaw)
│   ├── coding_team.py   # Project builder
│   ├── devops_team.py   # Code review, git, health
│   ├── marketing_team.py# Social media strategy
│   ├── sales_team.py    # Outreach drafts
│   └── rss_scraper.py   # RSS topic fetcher
├── config/settings.py   # All configuration
├── utils/
│   ├── database.py      # SQLite (9 tables, 8 indexes)
│   ├── router.py        # API router with fallback chains
│   ├── notify.py        # ntfy.sh push notifications
│   └── logger.py        # Rotating log files
├── setup.sh             # One-command installer
├── .env.example         # Config template
└── requirements.txt     # Python deps (flask, requests, dotenv)
```

## Daily Workflow

1. Open dashboard → CEO proposes a plan
2. You approve/modify/reject the plan
3. CEO assigns tasks to 5 teams
4. Teams work (using LLM APIs with automatic fallback)
5. Review content → one-click copy to post
6. Review outreach → approve before sending
7. Review projects → push to GitHub

## Free Tier Budget

- **Groq**: 1000 req/day (primary workhorse)
- **Mistral**: ~86K req/day theoretical (code + chat)
- **Ollama**: Unlimited (local, slower)
- **Google Gemini**: 250 req/day (emergency only)

## Transfer to New Machine

```bash
# On old machine
tar czf mach1-backup.tar.gz mach-1/

# On new machine
tar xzf mach1-backup.tar.gz
cd mach-1 && ./setup.sh
```
