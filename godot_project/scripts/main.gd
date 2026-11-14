extends Control

const SERVER_URL = "http://127.0.0.1:5000"

onready var http = $HTTPRequest
onready var session_label = $VBoxContainer/SessionLabel
onready var state_label = $VBoxContainer/StateLabel
onready var event_label = $VBoxContainer/EventLabel
onready var player_stats = $VBoxContainer/PlayerStats
onready var economy_label = $VBoxContainer/EconomyLabel
onready var asset_container = $VBoxContainer/AssetContainer
onready var liability_container = $VBoxContainer/LiabilityContainer
onready var start_button = $VBoxContainer/ButtonRow1/StartButton
onready var step_button = $VBoxContainer/ButtonRow1/StepButton
onready var invest_button = $VBoxContainer/ButtonRow2/InvestButton
onready var rental_button = $VBoxContainer/ButtonRow2/RentalButton
onready var loan_button = $VBoxContainer/ButtonRow2/LoanButton
onready var asset_details_button = $VBoxContainer/ButtonRow2/AssetDetailsButton
onready var sell_asset_button = $VBoxContainer/ButtonRow2/SellAssetButton
onready var save_button = $VBoxContainer/ButtonRow3/SaveButton
onready var load_button = $VBoxContainer/ButtonRow3/LoadButton
onready var confirm_dialog = $VBoxContainer/ConfirmDialog

var session_id = ""
var session_token = ""
var selected_asset_name = ""

func _ready():
    start_button.pressed.connect(_on_start_pressed)
    step_button.pressed.connect(_on_step_pressed)
    invest_button.pressed.connect(_on_invest_pressed)
    rental_button.pressed.connect(_on_rental_pressed)
    loan_button.pressed.connect(_on_loan_pressed)
    asset_details_button.pressed.connect(_on_asset_details_pressed)
    sell_asset_button.pressed.connect(_on_sell_asset_pressed)
    save_button.pressed.connect(_on_save_pressed)
    load_button.pressed.connect(_on_load_pressed)
    confirm_dialog.connect("confirmed", Callable(self, "_on_confirmed_sell"))

func _on_start_pressed():
    _post_json("/session", {"profile": {"region": "tier2", "education": "graduate"}})

func _on_step_pressed():
    _post_json("/step", {"months": 1})

func _on_invest_pressed():
    _post_json("/action", {"type": "invest_market", "symbol": "NIFTY_IND", "amount": 20000})

func _on_rental_pressed():
    _post_json("/action", {"type": "buy_rental", "amount": 50000})

func _on_loan_pressed():
    _post_json("/action", {"type": "take_loan", "amount": 100000})

func _on_save_pressed():
    _post_json("/save", {})

func _on_load_pressed():
    _post_json("/load", {})

func _post_json(path: String, payload: Dictionary):
    if session_id != "" and path != "/session":
        payload["session_id"] = session_id
    var json_data = JSON.print(payload)
    var headers = ["Content-Type: application/json"]
    if session_token != "":
        headers.append("X-Session-Token: " + session_token)
    var err = http.request(SERVER_URL + path, headers, json_data.to_utf8(), HTTPClient.METHOD_POST)
    if err != OK:
        state_label.text = "Request error: %d" % err

func _on_http_request_request_completed(result, response_code, headers, body):
    var text = body.get_string_from_utf8()
    if response_code != 200:
        state_label.text = "HTTP error %d: %s" % [response_code, text]
        return

    var parse = JSON.parse_string(text)
    if parse.error != OK:
        state_label.text = "Response parse error: %s" % parse.error
        return

    var response = parse.result
    if response.has("error"):
        state_label.text = "Server error: %s" % response["error"]
        return

    if response.has("session_id"):
        session_id = response["session_id"]
        session_label.text = "Session: %s" % session_id
    if response.has("token"):
        session_token = response["token"]
        state_label.text = "Session token acquired"

    # preview response: show proceeds and ask for confirmation
    if response.has("proceeds"):
        var p = response["proceeds"]
        var nm = response.has("asset") and response["asset"].get("name", selected_asset_name) or selected_asset_name
        confirm_dialog.dialog_text = "Sell '%s' for ₹%s?" % [nm, str(p)]
        confirm_dialog.popup_centered()
        return

    if response.has("player"):
        _update_state(response["player"], response.get("economy", {}), response.get("events", []), response.get("status", ""), response)
        return

    if response.has("status"):
        state_label.text = "Status: %s" % response["status"]
        return

    state_label.text = "Unexpected response"

func _update_state(player: Dictionary, economy: Dictionary, events: Array, status: String, raw_response: Dictionary) -> void:
    player_stats.text = "Player: %s | Cash: ₹%s | Net Worth: ₹%s | Income: ₹%s/mo | Expenses: ₹%s/mo" % [player.get("name", "?"), str(player.get("cash", 0)), str(player.get("net_worth", 0)), str(player.get("monthly_income", 0)), str(player.get("expenses", 0))]
    economy_label.text = "Economy: Inflation %s | Rate %s | Stock %s | Real Estate %s" % [str(economy.get("inflation", 0.0)), str(economy.get("interest_rate", 0.0)), str(economy.get("stock_index", 0.0)), str(economy.get("real_estate_index", 0.0))]
    state_label.text = status != "" ? status : "State updated"

    if events.size() > 0:
        var latest = events[events.size() - 1]
        event_label.text = latest.get("event_text", "Month processed.")
    elif raw_response.has("event_text"):
        event_label.text = raw_response["event_text"]
    else:
        event_label.text = "Event log updated."

    _populate_table(asset_container, player.get("assets", []), true)
    _populate_table(liability_container, player.get("liabilities", []), false)

func _populate_table(container: Node, items: Array, is_asset: bool) -> void:
    for child in container.get_children():
        child.queue_free()
    if items.empty():
        var blank = Label.new()
        blank.text = is_asset ? "No assets yet." : "No liabilities yet."
        container.add_child(blank)
        return

    for item in items:
        if is_asset:
            var btn = Button.new()
            btn.text = "%s [%s] - ₹%s | Cashflow ₹%s/mo" % [item.get("name", ""), item.get("asset_type", ""), str(item.get("value", 0)), str(item.get("monthly_cashflow", 0))]
            btn.set_meta("asset_name", item.get("name", ""))
            btn.pressed.connect(Callable(self, "_on_asset_button_pressed"), [btn])
            container.add_child(btn)
        else:
            var label = Label.new()
            label.text = "%s [%s] - Remaining ₹%s | Payment ₹%s/mo" % [item.get("name", ""), item.get("liability_type", ""), str(item.get("principal", 0)), str(item.get("monthly_payment", 0))]
            container.add_child(label)

func _on_asset_details_pressed():
    if selected_asset_name == "":
        state_label.text = "Select an asset first (click one)."
        return
    state_label.text = "Selected asset: %s" % selected_asset_name

func _on_sell_asset_pressed():
    if selected_asset_name == "":
        state_label.text = "Select an asset first to sell."
        return
    # request server-side preview of proceeds before confirming
    _post_json("/action/preview", {"name": selected_asset_name})

func _on_confirmed_sell():
    if session_id == "":
        state_label.text = "No active session"
        return
    _post_json("/action", {"type": "sell_asset", "name": selected_asset_name})

func _on_asset_button_pressed(btn: Button) -> void:
    selected_asset_name = btn.get_meta("asset_name")
    state_label.text = "Selected: %s" % selected_asset_name
