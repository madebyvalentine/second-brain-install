"""install.sh from the request to a configured Mac, against a local front door (brain_admin.py from
second-brain-server) and a fake brain, in a throwaway home folder. The Keychain item has a test name and is removed.
  python3 tests/test_install.py [path/to/second-brain-server]
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

here = Path(__file__).resolve().parent.parent
server_repo = Path(sys.argv[1] if len(sys.argv) > 1 else here.parent / "vps-work")
KEYCHAIN = "second-brain-install-test"
results = []


def check(label, cond, detail=""):
    results.append(bool(cond))
    print(("PASS" if cond else "FAIL"), label, "" if cond else f" [{str(detail)[:400]}]")


# a person's home: logged in to Claude Code on Pro, 2 conversations, one hook and instructions of their own
home = Path(tempfile.mkdtemp())
(home / ".claude" / "projects" / "-Users-x-site").mkdir(parents=True)
for n in ("a", "b"):
    (home / ".claude" / "projects" / "-Users-x-site" / f"{n}.jsonl").write_text("{}\n")
(home / ".claude.json").write_text(json.dumps({"oauthAccount": {"fullName": "Thomas de Vries", "emailAddress": "thomas@example.com",
                                                                 "organizationType": "claude_pro"}}))
(home / ".claude" / "settings.json").write_text(json.dumps({"model": "sonnet", "hooks": {"Stop": [
    {"hooks": [{"type": "command", "command": "say done"}]}]}}))
(home / ".claude" / "CLAUDE.md").write_text("# My own rules\n\nBe brief.\n")

# the fake brain: serves the client script
brain_dir = Path(tempfile.mkdtemp())
(brain_dir / "client").mkdir()
shutil.copy(server_repo / "plugin/second-brain/scripts/brain_hook.py", brain_dir / "client" / "brain_hook.py")
brain = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(brain_dir)))
threading.Thread(target=brain.serve_forever, daemon=True).start()
brain_url = f"http://127.0.0.1:{brain.server_address[1]}"

# the front door, with making a brain stubbed to "ready at the fake brain"
root = Path(tempfile.mkdtemp())
(root / "secrets").mkdir()
(root / "secrets" / "admin.env").write_text("ADMIN_SHARED_SECRET=s3cret\n")
os.environ["BRAIN_ROOT"] = str(root)
spec = importlib.util.spec_from_file_location("brain_admin", server_repo / "deploy/vps/admin/brain_admin.py")
admin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admin)
admin.notify = lambda event, req: None


def fake_provision(rid):
    req = admin.load(rid)
    req.update(state="ready", user="thomas", url=brain_url, mcp=brain_url + "/mcp", client_token="sb_client_test")
    admin.save(req)


admin.provision = fake_provision
door = ThreadingHTTPServer(("127.0.0.1", 0), admin.Handler)
threading.Thread(target=door.serve_forever, daemon=True).start()

kc = str(home / "test.keychain-db")
subprocess.run(["security", "create-keychain", "-p", "t", kc], capture_output=True)
subprocess.run(["security", "unlock-keychain", "-p", "t", kc], capture_output=True)
env = dict(os.environ, HOME=str(home), BRAIN_KEYCHAIN_FILE=kc, BRAIN_ADMIN_URL=f"http://127.0.0.1:{door.server_address[1]}",
           BRAIN_KEYCHAIN_SERVICE=KEYCHAIN, CLAUDE_CONFIG_DIR=str(home / ".claude"))


def install(*args):
    p = subprocess.run(["bash", str(here / "install.sh"), *args], env=env, capture_output=True, text=True, timeout=120)
    return p.returncode, (p.stdout + p.stderr).strip()


code, out = install("start")
check("start sends the request with what the login says", code == 0 and "pro, 2 gesprekken" in out, out)
reqs = admin.all_requests()
check("the front door has name, email and plan", reqs and reqs[0]["name"] == "Thomas de Vries" and reqs[0]["plan"] == "pro", reqs)
check("a second start does not send a second request", "loopt al" in install("start")[1])

admin.decide(reqs[0]["id"], "valentine")
code, out = install("wait")
check("wait installs the client once the brain is ready", code == 0 and "staat klaar" in out, out)

settings = json.loads((home / ".claude" / "settings.json").read_text())
hooks = settings["hooks"]
check("the five brain hooks are in the user's settings",
      all(any("hook.sh" in json.dumps(e) for e in hooks.get(ev, [])) for ev in ("SessionStart", "UserPromptSubmit", "Stop", "PreCompact", "SessionEnd")), hooks)
check("the person's own hook and settings stay", settings.get("model") == "sonnet" and "say done" in json.dumps(hooks["Stop"]), settings)
check("a backup of their settings is kept", (home / ".claude" / "settings.json.before-brain").exists())
claude_json = json.loads((home / ".claude.json").read_text()) if (home / ".claude.json").exists() else {}
cfg_json = home / ".claude" / ".claude.json"
if cfg_json.exists():
    claude_json = json.loads(cfg_json.read_text())
mcp = (claude_json.get("mcpServers") or {}).get("second-brain", {})
check("the brain's tools are added for every session", mcp.get("url") == brain_url + "/mcp" and "security find-generic-password" in mcp.get("headersHelper", ""), claude_json.get("mcpServers"))
md = (home / ".claude" / "CLAUDE.md").read_text()
check("the brain's instructions are added and theirs stay", "second-brain:start" in md and "Be brief." in md, md)
check("the client and its address are in place", (home / ".second-brain" / "brain_hook.py").exists()
      and json.loads((home / ".second-brain" / "config.json").read_text())["api_url"] == brain_url)
tok = subprocess.run(["security", "find-generic-password", "-s", KEYCHAIN, "-w", kc], capture_output=True, text=True)
check("the client token is in the Keychain, not in a file", tok.stdout.strip() == "sb_client_test"
      and "sb_client_test" not in (home / ".second-brain" / "join.json").read_text())
check("nothing printed a token", "sb_client_test" not in out)

# a second install over the first changes nothing twice
os.environ["HOME"] = str(home)
before = (home / ".claude" / "settings.json").read_text()
subprocess.run(["bash", "-c", f'. "{here}/install.sh" >/dev/null 2>&1; install_client "{brain_url}" sb_client_test'],
               env=dict(env, BASH_ENV=""), capture_output=True, text=True)
after = json.loads((home / ".claude" / "settings.json").read_text())
check("installing twice adds no hook twice", sum("hook.sh" in json.dumps(e) for e in after["hooks"]["Stop"]) <= 1, after["hooks"]["Stop"])
check("and no instructions twice", (home / ".claude" / "CLAUDE.md").read_text().count("second-brain:start") == 1)

# the hook itself runs and stays quiet without a brain behind it
p = subprocess.run(["sh", str(home / ".second-brain" / "hook.sh"), "context"], input="{}", env=env, capture_output=True, text=True, timeout=60)
check("the installed hook runs and exits 0", p.returncode == 0, p.stderr)

# a test install, then a reset that leaves nothing behind
(home / ".second-brain" / "join.json").unlink()
resets = []
admin.reset = lambda rid: resets.append(rid) or admin._path(rid).unlink() or {"reset": True}
code, out = install("start", "--test")
check("a test install says it reads in nothing", code == 0 and "Testinstallatie" in out, out)
treq = [r for r in admin.all_requests() if r.get("test")]
check("the server sees it as a test", len(treq) == 1, admin.all_requests())
admin.decide(treq[0]["id"], "valentine")
check("the test install is set up", install("wait")[0] == 0)
code, out = install("reset")
check("reset reports everything gone", code == 0 and "Alles van de testinstallatie is weg" in out, out)
check("the server was asked to remove the test", resets == [treq[0]["id"]], resets)
settings = json.loads((home / ".claude" / "settings.json").read_text())
check("no brain hook is left, the person's own hook stays", "hook.sh" not in json.dumps(settings) and "say done" in json.dumps(settings), settings)
check("the backup of their settings is gone", not (home / ".claude" / "settings.json.before-brain").exists())
cfg = home / ".claude" / ".claude.json"
left = json.loads(cfg.read_text()) if cfg.exists() else {}
check("the brain's tools are gone", "second-brain" not in (left.get("mcpServers") or {}), left.get("mcpServers"))
md = (home / ".claude" / "CLAUDE.md").read_text()
check("the brain's instructions are gone, theirs stay", "second-brain" not in md and "Be brief." in md, md)
check("~/.second-brain is gone", not (home / ".second-brain").exists())
gone = subprocess.run(["security", "find-generic-password", "-s", KEYCHAIN, kc], capture_output=True)
check("the Keychain item is gone", gone.returncode != 0)
code, out = install("reset")
check("a second reset finds nothing", "niets om te wissen" in out, out)

subprocess.run(["security", "delete-keychain", kc], capture_output=True)
door.shutdown(); brain.shutdown()
print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
