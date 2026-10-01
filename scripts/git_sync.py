"""
Git Synchronization & Client-Agnostic Persistence Engine
Persists all system changes (trades, factor calibrations, retrospective logs)
to remote GitHub repository: git@github.com:kevinhayesanderson/autonomous-trading-agent.git

Ensures client-agnostic operation:
The bot can be run from Antigravity, Claude Desktop, Cursor, headless terminal,
or CI/CD without state divergence across environments.
"""

import os
import sys
import subprocess
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def get_repo_root():
    """Finds root of the git repository."""
    # First check relative to this file
    candidate = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=candidate,
            capture_output=True,
            text=True,
            check=False
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    return candidate

def is_git_repo(repo_dir):
    """Verifies that repo_dir is an initialized git repository."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=False
        )
        return res.returncode == 0 and res.stdout.strip() == "true"
    except Exception:
        return False

def sync_system_to_git(commit_msg=None, repo_dir=None, push=True):
    """
    Persists system state to git:
    1. Stages changes (respecting .gitignore to protect secrets/tokens).
    2. Verifies safety invariant (no token files staged).
    3. Commits with structured message.
    4. Pushes to remote origin (with auto-rebase if diverged).
    """
    if repo_dir is None:
        repo_dir = get_repo_root()

    print("\n" + "-" * 70)
    print(" [GIT SYNC] Persisting System State & Memory to Remote...")
    print(f"  Working Directory: {repo_dir}")

    if not is_git_repo(repo_dir):
        print("  [!] Warning: Directory is not a git repository. Skipping git sync.")
        print("-" * 70 + "\n")
        return False

    try:
        # 1. Check status
        status_res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=False
        )
        has_local_changes = bool(status_res.stdout.strip())

        # 2. Stage changes if present
        if has_local_changes:
            subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)

            # Safety verification: ensure no token or secret files are staged
            staged_res = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                check=True
            )
            staged_files = staged_res.stdout.splitlines()

            for sf in staged_files:
                sf_lower = sf.lower()
                is_token = "token" in sf_lower
                is_env = (".env" in sf_lower and not sf_lower.endswith(".example"))
                is_key = "id_rsa" in sf_lower or "trade_journal.jsonl" in sf_lower
                if is_token or is_env or is_key:
                    print(f"  [CRITICAL SAFETY ALERT] Refusing to commit sensitive file: {sf}")
                    subprocess.run(["git", "reset", "HEAD", sf], cwd=repo_dir, check=False)

            # Re-check if any valid files remain staged
            staged_after_check = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()

            if not staged_after_check:
                print("  [Git Sync] No changes to commit after safety filters.")
            else:
                # 3. Create Commit
                if not commit_msg:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    commit_msg = f"[Auto-Sync] State update at {timestamp} (agent memory & calibrations)"

                commit_res = subprocess.run(
                    ["git", "commit", "-m", commit_msg],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True,
                    check=False
                )
                if commit_res.returncode == 0:
                    print(f"  [SUCCESS] Local commit created: \"{commit_msg}\"")
                else:
                    print(f"  [!] Commit notice: {commit_res.stdout.strip() or commit_res.stderr.strip()}")

        # 4. Push to remote
        if push:
            # Detect current branch
            branch_res = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                check=False
            )
            branch = branch_res.stdout.strip() or "main"

            # Check if remote origin is configured
            remotes_res = subprocess.run(
                ["git", "remote"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                check=False
            )
            if "origin" not in remotes_res.stdout.splitlines():
                print("  [!] Notice: 'origin' remote not configured. Local changes committed successfully.")
                print("-" * 70 + "\n")
                return True

            print(f"  -> Pushing changes to origin/{branch}...")
            push_res = subprocess.run(
                ["git", "push", "origin", branch],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                check=False,
                timeout=45
            )

            if push_res.returncode == 0:
                print(f"  [SUCCESS] Remote synchronized: origin/{branch} is up to date.")
                print("-" * 70 + "\n")
                return True
            else:
                # Attempt auto-rebase in case another client pushed
                print("  [Notice] Push rejected, attempting git pull --rebase origin...")
                subprocess.run(
                    ["git", "pull", "--rebase", "origin", branch],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True,
                    check=False
                )
                retry_push = subprocess.run(
                    ["git", "push", "origin", branch],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=45
                )
                if retry_push.returncode == 0:
                    print(f"  [SUCCESS] Remote synchronized after rebase: origin/{branch} is up to date.")
                    print("-" * 70 + "\n")
                    return True
                else:
                    err = retry_push.stderr.strip() or retry_push.stdout.strip()
                    print(f"  [!] Warning: Push failed ({err}). Local commit preserved.")
                    print("-" * 70 + "\n")
                    return False

        print("  [Git Sync] Local state clean.")
        print("-" * 70 + "\n")
        return True

    except subprocess.TimeoutExpired:
        print("  [!] Warning: Git push timed out. Local commit preserved; will sync on next cycle.")
        print("-" * 70 + "\n")
        return False
    except Exception as e:
        print(f"  [!] Warning during git sync: {e}")
        print("-" * 70 + "\n")
        return False

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else None
    sync_system_to_git(commit_msg=msg)
