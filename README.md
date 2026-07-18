<div align="center">
   <img src="Demo.gif" alt="Project Demo" width="600"/>
</div>

# LifeCapital — Financial Freedom Game Engine (Prototype)

A dual financial simulation prototype built in Python featuring:
1. **Financial Simulator** — India-specific income, asset, expense tracking with market dynamics
2. **Cashflow Game** — Rat Race board game + Fast Track escape with 50+ Indian financial cards

Both games include Flask backend persistence, session management, and token-based auth.

---

## 🚀 Quick Start

1. Open PowerShell and navigate to the repo:

```powershell
cd "C:\path\to\LifeCapital"
```

2. Create and activate virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

4. Set up environment variables:

```powershell
copy .env.example .env
```

5. Run the backend server:

```powershell
python backend\app.py
```

6. To play **Cashflow Game CLI**:

```powershell
python -m engine.cashflow_cli --profession startup --region tier2
```

7. Or open `godot_project/` in Godot 4.x and run `scenes/main.tscn` for Financial Simulator UI.

---

## 🎮 Two Games Included

### 1. Financial Simulator
**Classic LifeCapital engine** — month-by-month financial decisions with Indian economy.
- Build assets (stocks, rental properties, businesses, ETFs)
- Manage liabilities (loans, credit cards)
- Experience Indian events (festivals, monsoons, GST changes, job loss)
- Track net worth and passive income over 36+ months

**API Routes:**
- `POST /auth/login` — create a session
- `POST /action` — invest, buy rental, take loan, sell asset
- `POST /step` — advance one or more months
- `GET /state` — fetch current player state
- `POST /save`, `POST /load` — save/load game to JSON

### 2. Cashflow Game (New)
**Rat Race → Fast Track escape gameplay** — true board game mechanics.
- Roll dice and land on board spaces (Payday, Deals, Doodads, Market, Baby, Downsized, Charity)
- Draw deal cards and decide: buy small opportunities or big investments
- Handle unexpected doodads (medical bills, weddings, tuition hikes)
- Escape condition: `Passive Income > Total Expenses` → enter **Fast Track**
- Fast Track win: buy your Dream (₹250k) OR accumulate ₹50k/month passive income

**Card Decks (50+ Indian cards):**
- **Small Deals** (12 cards) — SIPs, mutual funds, chit funds, small shops
- **Big Deals** (12 cards) — DDA flats, commercial spaces, farms, franchises
- **Doodads** (15 cards) — Diwali shopping, medical emergencies, wedding costs, tuition hikes
- **Market Cards** (20 cards) — Sensex surge, gold rally, property corrections, recession

**API Routes (Cashflow):**
- `POST /cashflow/start` — create a new Cashflow game session
- `POST /cashflow/turn` — roll dice and take a turn
- `POST /cashflow/deal` — accept/reject a deal card
- `POST /cashflow/escape` — enter Fast Track if escape condition met
- `POST /cashflow/sell` — sell an asset for cash
- `GET /cashflow/decks` — view all card descriptions for UI reference

---

## 📊 Features

- **Dual Game Engines** — Financial Simulator and Cashflow board game
- **SQLite Persistence** — Session storage, credentials, game state
- **Token-Based Auth** — Secure session tokens with 24-hour expiry
- **Indian Economic Model** — Regional income multipliers, tax slabs, GST, subsidies, monsoon shocks
- **Card System** — 50+ culturally relevant financial products and events
- **Turn-Based Logic** — Deterministic financial calculations, dice rolling, card drawing
- **Godot UI** — Asset/liability visualization for Financial Simulator
- **CLI Interface** — Interactive Cashflow game playable in terminal

---

## 🧪 Testing

Run all unit tests:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Tests cover:
- Financial Simulator (income, expenses, asset growth, event handling)
- Cashflow Engine (escape condition, bankruptcy, asset selling)
- Authentication and session persistence
- Save/load functionality

---

## 🔐 Authentication

- Default admin user: username `admin`, password `admin`
- Set `LIFECAP_ADMIN_PW` and `LIFECAP_SALT` in `.env` before production
- Create additional users:

```powershell
python backend\admin.py create_user <username> <password>
```

- Tokens expire after 24 hours; use `/auth/refresh` to extend
- Use `/auth/logout` to destroy a session

---

## 📝 Environment Variables

Copy `.env.example` to `.env` and customize:

```
LIFECAP_ADMIN_PW=admin
LIFECAP_SALT=please_change_to_secure_random
```

---

## 📂 Project Structure

```
.
├── backend/
│   ├── app.py                    # Flask backend (LifeCapital + Cashflow routes)
│   └── admin.py                  # User management CLI
├── engine/
│   ├── cashflow.py               # Cashflow game engine (Rat Race + Fast Track)
│   ├── cashflow_cli.py           # Interactive CLI for Cashflow game
│   ├── cashflow_indian_decks.py  # 50+ Indian-flavored card decks
│   ├── game_manager.py           # Financial Simulator game logic
│   ├── economy.py                # Economy state and dynamics
│   ├── player.py                 # Player financial model
│   ├── assets.py                 # Asset and Liability classes
│   ├── market.py                 # Stock/ETF market manager
│   ├── events.py                 # Random events (festivals, crashes, etc.)
│   ├── india_data.py             # Regional data, tax slabs, subsidies
│   └── save_system.py            # JSON save/load for games
├── tests/
│   ├── test_auth.py              # Auth and session tests
│   ├── test_actions.py           # Action and sell preview tests
│   ├── test_cashflow_engine.py   # Cashflow engine tests
│   └── test_core.py              # Simulation tests
├── godot_project/                # Godot 4.x UI (Financial Simulator only)
├── data/                         # CSV data (salaries, GST, subsidies)
├── .vscode/                      # VS Code tasks and extensions
├── requirements.txt              # Python dependencies
├── README.md                     # This file
└── SETUP.md                      # Detailed setup guide
```

---

## 🎯 Gameplay Walkthrough

### Financial Simulator
1. Choose profession and region
2. Start simulation (36 months default)
3. Each month:
   - Earn salary + passive income
   - Pay expenses, taxes, loan payments
   - Choose action: invest market, buy rental, take loan, sell asset
   - Random event occurs (festival bonus, job loss, monsoon damage, etc.)
   - Assets grow/shrink based on market and economy
4. Win condition: Build enough passive income to sustain lifestyle

### Cashflow Game
1. Choose profession (IAS, CA, Clerk, Startup founder, Farmer)
2. Roll die, move around board
3. Land on space:
   - **Payday** → collect monthly cashflow
   - **Deal** → draw small/big deal card, decide to buy
   - **Doodad** → pay unexpected expense
   - **Market** → asset values change
   - **Baby** → add child, increase monthly expenses
   - **Downsized** → lose job, lose 2 turns
   - **Charity** → donate for social good
4. **Escape Rat Race:** When `Passive Income > Total Expenses`, enter Fast Track
5. **Win Fast Track:** Buy Dream (₹250k) OR reach ₹50k/month passive income

---

## 🛠️ Development Commands

**Run backend (port 5000):**
```powershell
python backend\app.py
```

**Run Cashflow game (CLI):**
```powershell
python -m engine.cashflow_cli --profession startup --region tier2 --seed 42
```

**Run all tests:**
```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

**Run specific test:**
```powershell
python -m unittest tests.test_cashflow_engine.CashflowEngineTests.test_escape_condition_and_fast_track_entry
```

**Create new user:**
```powershell
python backend\admin.py create_user john_doe password123
```

---

## 🚢 Production Deployment Checklist

- [ ] Change `LIFECAP_ADMIN_PW` to strong password
- [ ] Generate and set `LIFECAP_SALT` to 32-char random string
- [ ] Move `lifecycle_sessions.db` to secure location with regular backups
- [ ] Enable HTTPS for `/auth/login`, `/auth/refresh`, `/auth/logout`
- [ ] Rate-limit login attempts to prevent brute force
- [ ] Use PostgreSQL instead of SQLite for multi-server setup
- [ ] Add request logging and error monitoring
- [ ] Test game balance with larger player base
- [ ] Document card probabilities and drop rates

---

## 📚 Documentation

- **SETUP.md** — Detailed environment setup guide
- **engine/cashflow.py** — Game engine docstrings and class definitions
- **engine/cashflow_indian_decks.py** — Card deck specifications and scenarios
- **README.md** — This file (high-level overview)

---

## 🤝 Contributing

- Add new Indian card scenarios to `cashflow_indian_decks.py`
- Improve AI decision-making in `ai_manager.py`
- Extend economy model with seasonal trends
- Build frontend UI (React, Vue, Flutter, etc.)
- Translate cards and UI to regional languages

---

## 📖 Next Steps

1. **Play & Feedback** — Test both games, provide balance feedback
2. **UI Enhancement** — Build richer Godot/web UI for card visualization
3. **Multiplayer** — Add turn-based multiplayer using WebSockets
4. **Analytics** — Track player decisions, win rates, common failure modes
5. **Localization** — Translate to Hindi, Tamil, Telugu, Kannada, etc.
6. **Mobile App** — React Native or Flutter client
7. **Economy Tuning** — Balance card values based on player data

---

## 📄 License & Attribution

Inspired by the original Cashflow board game (Robert Kiyosaki). This prototype adds Indian economic realism, Rat Race/Fast Track mechanics, and playable backend integration.

**Author:** Dev  
**Version:** 0.1.0 (Prototype)  
**Last Updated:** June 2026

