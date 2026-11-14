# Cashflow Game API Reference

Quick guide for integrating the Cashflow game into Godot or other frontends.

---

## Base URL

```
http://localhost:5000
```

All requests should include the session token in either the header or request body.

---

## Authentication

### Session Token

Returned from `/cashflow/start`. Pass in subsequent requests via:
- **Header:** `X-Session-Token: <token>`
- **Body:** `{ "token": "<token>" }`

Use the header rather than putting the token in a URL. Tokens expire after 24 hours and are stored as hashes.

---

## Endpoints

### 1. Start New Game

```http
POST /cashflow/start
Content-Type: application/json

{
  "profession": "startup",        // Required: startup, ias, ca, clerk, kisan
  "region": "tier2",              // Optional: metro, tier1, tier2, tier3 (default: tier2)
  "seed": null                     // Optional: for reproducible random events
}
```

**Response (200):**
```json
{
  "status": "started",
  "session_id": "uuid",
  "token": "hex_token",
  "game": {
    "player": {
      "name": "Startup",
      "salary": 30000,
      "other_expenses": 15000,
      "children": 0,
      "child_cost_per_month": 0,
      "cash": 10000,
      "position": 0,
      "assets": [],
      "liabilities": [],
      "on_fast_track": false,
      "bankrupt": false,
      "owns_dream": false
    },
    "board_state": {
      "rat_race_position": 0,
      "fast_track_position": -1,
      "total_passive_income": 0,
      "total_expenses": 15000,
      "net_worth": 10000
    }
  }
}
```

---

### 2. Take Turn

```http
POST /cashflow/turn?session_id=uuid
X-Session-Token: token
Content-Type: application/json
```

**Response (200):**
```json
{
  "status": "turn_complete",
  "rolled": 4,                           // Dice result (1-6 on Rat Race, 2-12 on Fast Track)
  "space": "PAYDAY",                     // Space name
  "event": "Collected monthly cashflow", // Description
  "entered_fast_track": false,           // True if just escaped Rat Race
  "win": false,                          // True if won game
  "bankrupt": false,                     // True if player lost
  "game": { /* updated game state */ },
  "session_id": "uuid"
}
```

**Possible spaces:**
- Rat Race: `PAYDAY`, `SMALL_DEAL`, `BIG_DEAL`, `MARKET`, `DOODAD`, `BABY`, `DOWNSIZED`, `CHARITY`
- Fast Track: `CASHFLOW_DAY`, `FT_BUSINESS`, `DREAM`, `CHARITY`, `TAX_AUDIT`, `LAWSUIT`, `DIVORCE`

---

### 3. Accept/Reject Deal Card

After landing on `SMALL_DEAL` or `BIG_DEAL`, a card appears. Player chooses to accept or reject.

```http
POST /cashflow/deal?session_id=uuid
X-Session-Token: token
Content-Type: application/json

{
  "deal_name": "Nifty SIP",  // Exact card name from decks
  "accept": true             // true to buy, false to skip
}
```

**Response (200):**
```json
{
  "status": "deal_applied",
  "event": "Purchased Nifty SIP for ₹6,000",
  "game": { /* updated game state */ },
  "session_id": "uuid"
}
```

---

### 4. Enter Fast Track (Escape)

Automatically triggered when escape condition is met (`passive_income > total_expenses`), but can also be called explicitly.

```http
POST /cashflow/escape?session_id=uuid
X-Session-Token: token
Content-Type: application/json
```

**Response (200):**
```json
{
  "status": "escape_attempted",
  "event": "Entered Fast Track!",
  "on_fast_track": true,
  "game": { /* updated game state */ },
  "session_id": "uuid"
}
```

---

### 5. Sell Asset

Player can sell any asset for cash (typically to cover negative cashflow or buy deals).

```http
POST /cashflow/sell?session_id=uuid
X-Session-Token: token
Content-Type: application/json

{
  "asset_name": "Nifty SIP"  // Exact asset name
}
```

**Response (200):**
```json
{
  "status": "asset_sold",
  "event": "Sold Nifty SIP for ₹5,400 (90% of value)",
  "game": { /* updated game state */ },
  "session_id": "uuid"
}
```

---

### 6. Get Card Decks (Reference)

Retrieve all card descriptions for UI display (no auth required).

```http
GET /cashflow/decks
```

**Response (200):**
```json
{
  "small_deals": [
    {
      "name": "Nifty SIP",
      "description": "Systematic Investment Plan in Nifty 50 index",
      "cost": 6000
    },
    // ... 11 more small deals
  ],
  "big_deals": [
    {
      "name": "DDA Flat",
      "description": "Government housing with rental potential",
      "cost": 85000
    },
    // ... 11 more big deals
  ],
  "doodads": [
    {
      "description": "Diwali Festival Shopping",
      "cost": 15000
    },
    // ... 14 more doodads
  ],
  "markets": [
    {
      "description": "Sensex Surge! +20%",
      "affects": "stock"
    },
    // ... 19 more market cards
  ]
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "no session",
  "session_id": null
}
```

### 404 Not Found
```json
{
  "error": "deal not found",
  "session_id": "uuid"
}
```

### 401 Unauthorized
Invalid or expired token:
```json
{
  "error": "unauthorized"
}
```

---

## Game State Object

Returned from `/cashflow/turn`, `/cashflow/deal`, `/cashflow/escape`, `/cashflow/sell`:

```json
{
  "player": {
    "name": "Startup",
    "salary": 30000,
    "other_expenses": 15000,
    "children": 1,
    "child_cost_per_month": 2500,
    "cash": 8500,
    "position": 3,
    "assets": [
      {
        "name": "Nifty SIP",
        "asset_type": "stock",
        "value": 6000,
        "cashflow": 150,
        "purchase_price": 6000,
        "down_payment": null,
        "notes": "Monthly returns"
      }
    ],
    "liabilities": [],
    "on_fast_track": false,
    "bankrupt": false,
    "owns_dream": false
  },
  "board_state": {
    "rat_race_position": 3,
    "fast_track_position": -1,
    "total_passive_income": 150,
    "total_expenses": 17500,
    "net_worth": 14500
  },
  "available_cards": {
    "small_deals": ["Nifty SIP", "Midcap Fund", ...],
    "big_deals": ["DDA Flat", "Retail Shop", ...],
    "doodads": ["Diwali Shopping", "Medical Bill", ...]
  }
}
```

---

## Example Flow (Godot GDScript)

```gdscript
# Start game
var response = await http_post("/cashflow/start", {
  "profession": "startup",
  "region": "tier2"
})
session_id = response["session_id"]
token = response["token"]

# Game loop
while not response["game"]["player"]["bankrupt"] and not response["game"]["player"]["owns_dream"]:
  # Take turn
  response = await http_post("/cashflow/turn", {
    "session_id": session_id,
    "token": token
  })
  
  var space = response["space"]
  print("Rolled %d, landed on %s" % [response["rolled"], space])
  
  # Handle card if deal space
  if space in ["SMALL_DEAL", "BIG_DEAL"]:
    var card = response.get("card")
    if card:
      var accept = await ask_user_dialog(card["description"], "Buy?")
      response = await http_post("/cashflow/deal", {
        "session_id": session_id,
        "token": token,
        "deal_name": card["name"],
        "accept": accept
      })
  
  # Check escape condition
  if response["entered_fast_track"]:
    print("Escaped to Fast Track!")
  
  # Check win
  if response["win"]:
    print("You won!")
    break

print("Game over!")
```

---

## Card Deck Details

### Small Deals (₹4.5k–₹8k cost, ₹100–₹210/mo cashflow)

| Name | Cost | Monthly CF | Type |
|------|------|----------|------|
| Nifty SIP | ₹6,000 | ₹150 | Stock |
| Midcap Fund | ₹5,000 | ₹140 | Stock |
| PPF | ₹5,000 | ₹125 | Scheme |
| Senior Citizen Savings | ₹7,000 | ₹210 | Scheme |
| Sukanya Samriddhi | ₹6,000 | ₹140 | Scheme |
| Tea Stall | ₹5,000 DP | ₹400 | Business |
| Coaching Center | ₹8,000 DP | ₹600 | Business |
| Small Shop | ₹6,500 DP | ₹500 | Business |
| Chit Fund | ₹4,500 | ₹110 | Scheme |
| Corporate Bonds | ₹7,500 | ₹187 | Bond |
| Sovereign Gold Bond | ₹5,000 | ₹100 | Bond |

### Big Deals (₹85k–₹160k cost, ₹3k–₹6.8k/mo cashflow)

| Name | Cost | Monthly CF | Type |
|------|------|----------|------|
| DDA Flat | ₹85,000 DP | ₹3,200 | Real Estate |
| Builder Floor | ₹120,000 DP | ₹4,500 | Real Estate |
| Gated Apartment | ₹100,000 DP | ₹4,200 | Real Estate |
| Retail Shop | ₹95,000 DP | ₹3,800 | Business |
| Warehouse | ₹110,000 DP | ₹4,800 | Business |
| Organic Farm | ₹90,000 DP | ₹3,200 | Agriculture |
| Dairy Farm | ₹85,000 DP | ₹3,100 | Agriculture |
| Tech Startup | ₹150,000 DP | ₹6,200 | Business |
| Hotel/Resort | ₹140,000 DP | ₹5,800 | Business |
| Fitness Center | ₹120,000 DP | ₹5,000 | Business |
| Education Institute | ₹130,000 DP | ₹5,500 | Business |
| Logistics Company | ₹160,000 DP | ₹6,800 | Business |

### Doodads (Unexpected Expenses)

| Event | Cost | Duration |
|-------|------|----------|
| Diwali Shopping | ₹15,000 | One-time |
| Wedding | ₹35,000 | One-time |
| Medical Emergency | ₹50,000 | One-time |
| House Renovation | ₹20,000 | One-time |
| Vehicle Purchase | ₹12,000 | One-time |
| Gadgets | ₹18,000 | One-time |
| Travel | ₹25,000 | One-time |
| Charity Donation | ₹8,000 | One-time |
| Laptop/Computer | ₹55,000 | One-time |
| Health Checkup | ₹7,000 | One-time |
| School Tuition | +₹2,500 | Monthly |
| House Rent Increase | +₹3,000 | Monthly |
| Tuition Cost | +₹1,800 | Monthly |
| Loan EMI | +₹4,000 | Monthly |
| Insurance Premium | +₹1,200 | Monthly |

### Market Cards (Asset Value Multipliers)

| Event | Affect | Multiplier |
|-------|--------|-----------|
| Sensex Surge | Stock | +20% |
| Gold Rally | Precious | +25% |
| FD Maturity | Bonds | +10% |
| Real Estate Boom | Real Estate | +18% |
| Agricultural Growth | Agriculture | +22% |
| Business Expansion | Business | +15% |
| GST Reduction | All | +12% |
| Property Spike (Sell) | Real Estate | +20% |
| Stock Split | Stock | +8% |
| Stock Crash | Stock | -15% |
| Real Estate Correction | Real Estate | -12% |
| Gold Dip | Precious | -8% |
| Agricultural Collapse | Agriculture | -25% |
| Business Slowdown | Business | -18% |
| Dollar Collapse | Exports | -10% |
| Property Deflation | Real Estate | -15% |
| Market Consolidation | All | +1% |
| Rate Steady | All | 1.0× |
| Market Stabilization | All | +3% |

---

## Win Conditions

1. **Rat Race Escape:** `Passive Income > Total Monthly Expenses`
   - Automatically triggers Fast Track entry
   - Reset position, enter Fast Track board

2. **Fast Track Win:**
   - **Option A:** Buy your Dream (₹250,000 asset)
   - **Option B:** Accumulate ₹50,000/month passive income

3. **Lose Conditions:**
   - Cash goes negative and can't liquidate enough assets
   - Bankruptcy declared

---

## Technical Notes

- All currency values in **Indian Rupees (₹)**
- Dice rolls:
  - Rat Race: 1d6 (move 1–6 spaces)
  - Fast Track: 2d6 (move 2–12 spaces)
- Asset selling: proceeds at 90% of purchase value
- Tax: calculated on total income (salary + cashflow) using Indian tax slabs
- Session persistence: SQLite-backed auto-save on each action
- No real-time multiplayer (turn-based only)

---

## Troubleshooting

**Session expired:**
```json
{
  "error": "no session"
}
```
→ Call `/cashflow/start` to create a new session

**Deal card not found:**
```json
{
  "error": "deal not found"
}
```
→ Check exact card name against `/cashflow/decks` response

**Negative cash after doodad:**
→ Call `/cashflow/sell` to liquidate assets at 90% value

**Token mismatch:**
→ Ensure same token from `/cashflow/start` is used in all subsequent requests

---

## Next Steps

- [ ] Godot scene for Cashflow board visualization
- [ ] Multiplayer turn-based mode (P2P or server relay)
- [ ] Card animation and audio feedback
- [ ] Statistics tracking (wins, bankruptcies, common cards)
- [ ] Difficulty levels (Easy = slow expenses, Hard = aggressive doodads)
- [ ] Export/import game state as JSON
- [ ] Replay system for recorded games
