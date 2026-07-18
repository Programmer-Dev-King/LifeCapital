Windows setup (Python + virtualenv + Godot + run tests)

1) Install Python 3.11+ (Windows installer) and check `python --version`.
2) Open PowerShell and create a virtual environment in the project folder:

```powershell
cd "C:\path\to\LifeCapital"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3) Install Python dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

4) Run unit tests:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

5) Run the backend server (for Godot UI):

```powershell
python backend\app.py
```

6) Open the Godot editor (download Godot 4.x stable from godotengine.org) and open the folder `godot_project/`.
   - Run the `scenes/main.tscn` scene to use the UI and connect to the backend at `http://127.0.0.1:5000`.

8) New endpoints
- The backend exposes a preview endpoint `/action/preview` (POST) which returns server-side computed proceeds for a proposed `sell_asset` so the client can show confirmation before executing the sale.
- Admin CLI: create users with `python backend/admin.py create_user <username> <password>` and list users with `python backend/admin.py list_users`.

7) Run CLI prototype:

```powershell
python main.py
```

Notes
- If you run into permission issues running the PowerShell activation script, use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in an elevated PowerShell.
- This repo already includes a lightweight Flask backend and Godot scaffold; the core engine lives inside `engine/`.
