# Two-court tournament results synchronisation

This optional feature lets Windows 11 and Raspberry Pi 5 scoring computers
operate independently while a third computer maintains one combined results
CSV. It uses Python's standard HTTP library, with **one remote writer** rather
than two courts concurrently editing a shared CSV over SMB.

## Files and ownership

| Computer | Original draw | Results |
| --- | --- | --- |
| Court 1 (even games) | Local Tournament_Draw.csv | Local Tournament_Results.csv |
| Court 2 (odd games) | Identical local Tournament_Draw.csv | Independent local Tournament_Results.csv |
| Results computer | Identical Tournament_Draw.csv | Combined Tournament_Results.csv |

The draw must be **byte-for-byte identical** on all three machines. Do not edit
its game numbers, teams or schedule during a tournament. The court and server
both refuse to merge against a changed draw.

The courts do **not** mount or edit the third computer's CSV. They send one
completed game at a time to a Python service. An SMB share is unnecessary for
uploading results, though you can separately share the folder for read-only
viewing.

## Safety rules

- Each court's complete result is saved **locally first**, independent of the
  network. Network failure cannot block normal game progression.
- A background worker retries after ten seconds when offline. It also wakes
  immediately after a local export or when **Sync Now** is pressed. The
  networking code never touches Tk widgets or runs on the timer thread.
- The results server processes one game write at a time under a lock. It
  stages a complete replacement CSV, then atomically replaces only its
  results file. No caller can supply a filesystem path.
- An identical repeat submission is acknowledged without rewriting. A
  different result for an already-completed game raises a visible CONFLICT;
  neither value is silently overwritten.
- A small local .uwh_sync_*.json file remembers which game results the server
  acknowledged. If it is missing after a crash, submissions are reconstructed
  from the completed local results CSV, and duplicate submissions are safe.
- Zero–zero is a completed result: both score cells contain the string "0".
  Any row with a blank score remains unsubmitted.
- A locked CSV, missing server, wrong token or disk error means **pending**,
  never "synced." Retrying the same game does not erase other games.
- An even/odd or consecutive court selection is applied by the existing
  local Tournament List control. The server merges by game number.

## 1. Set up the third results computer

Windows 11 or Raspberry Pi/Linux can run the service. Use Python 3.11+ and a
permanent folder containing the **source ZIP** files:

    tournament_results_server.py
    tournament_files.py
    csv_export.py
    Tournament_Draw.csv

The easiest route is to extract the full updated GitHub source ZIP on the
third computer and copy the same original draw beside these Python files.
Do not use the packaged Windows application EXE as the server.

Generate a long, unpredictable secret once, and record it securely:

    python -c "import secrets; print(secrets.token_urlsafe(32))"

If the Windows Python executable is named differently, use py -3 instead.
Enter the same secret on the two courts. It must be at least 16 characters.

### Windows 11 results computer

In PowerShell in the extracted project folder (for example C:\UWH):

    cd C:\UWH
    $env:UWH_SYNC_TOKEN = Read-Host "Shared results token"
    python tournament_results_server.py --draw "C:\UWH\Tournament_Draw.csv" --bind 0.0.0.0 --port 8765

The 0.0.0.0 option lets other computers connect; the default is localhost
only. On a **private LAN** you may need an administrator PowerShell to allow
TCP port 8765 through Windows Firewall:

    New-NetFirewallRule -DisplayName "UWH Results" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8765 -Profile Private -RemoteAddress LocalSubnet

For example, if the third computer has the IP address 192.168.1.50, courts
would enter http://192.168.1.50:8765 into the UWH widget.

### Raspberry Pi/Linux results computer

In a Terminal in the extracted project folder:

    cd /home/uwh/UWH
    read -r -s -p "Shared results token: " UWH_SYNC_TOKEN
    echo
    export UWH_SYNC_TOKEN
    python3 tournament_results_server.py --draw /home/uwh/UWH/Tournament_Draw.csv --bind 0.0.0.0 --port 8765

Adapt the path to where you extracted the source. On Linux, also restrict
firewall access to the scoring computers on the local network. The service
runs in the Terminal until Ctrl+C; make it a startup service only after
testing. Back up the server's combined results CSV periodically.

**Security:** HTTP on port 8765 is unencrypted. Use a trusted, isolated LAN,
or HTTPS/VPN for untrusted networks. Do not forward the port to the public
internet. The masked access token is stored in each court's settings.json;
protect that file from other users and back it up.

## 2. Configure the two court computers

Copy the same original draw to each updated court installation. Back up each
court's settings.json, original draw and any existing local results file
before installing a new release/source ZIP.

In Game Variables → Tournament List:

1. Check Use Tournament List? and choose Tournament_Draw.csv.
2. Choose the starting game and select **even** on one court, **odd** on the
   other. Existing game/period rules remain unchanged.
3. Verify the read-only **Tournament Results** box shows
   Tournament_Results.csv, the LOCAL results output derived from the draw.
4. Under Results sync, select **Shared server**.
5. Enter the server URL, such as http://192.168.1.50:8765, and the same
   shared access token on both courts.
6. Press **Save & Sync** to save this machine's settings and begin submitting
   completed games. **Sync Now** wakes a pending retry immediately.
7. Watch the status text for pending, synced, server-unavailable or conflict
   messages. The original draw remains read-only from the app.

To disable uploads, choose **Local only** and press Save & Sync. Results
continue to be saved on that court, and the other court is unaffected.

**The server URL is not a Windows UNC path or a mapped drive letter.** It is
the address of the single-writer service. No SMB mount is needed on the RP5.
Windows and Raspberry Pi both use the same URL, even though the server's
CSV file may be stored in a Windows or Linux folder.

## 3. Test before a live tournament

Use a copy of the draw, not a live tournament:

1. Submit even Game 2 from Court 1, then odd Game 1 from Court 2. Both must
   appear in the combined server CSV without modifying either original draw.
2. Stop the server/network; finish another game. The court's local CSV must
   contain it, the timer must still advance, and the status must remain
   pending/offline.
3. Restore the server. The result must appear automatically after a retry
   without erasing either earlier game.
4. Restart a court: previous games must remain saved and acknowledged.
5. In disposable files, submit two **different** results for the same game.
   The second must report CONFLICT and preserve both copies for review.
6. On Windows, temporarily hold the server CSV open in a program that
   exclusively locks it. A failed write must leave local data safe and retry
   after the lock is released.

Only test on production hardware after the headless tests pass. If CONFLICT
appears, back up the local and server result files and reconcile the affected
game manually. The software must not guess which court's score is correct.

## 4. Status messages

| Message | Action |
| --- | --- |
| Local results saved · network sync off | Shared upload is disabled; enable it and Save & Sync if required. |
| Network unavailable · retry in 10 s | Check server, LAN address and firewall. Local results remain safe. |
| Sync blocked (HTTP 401) | Correct the access token on this court. |
| Sync blocked (HTTP 503) | Server results file is locked, disk full or unwritable; fix then retry. |
| CONFLICT game N | Different existing result or draw mismatch. Stop and reconcile manually. |
| All completed games synced | Every completed game this court knows about has a server acknowledgement. |

The court files do **not** need to contain the other court's games. The
results computer's combined CSV is the tournament's combined record.
