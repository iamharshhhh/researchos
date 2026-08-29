import time
import subprocess
import os
from datetime import datetime

def run_cmd(cmd):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
        return res.returncode == 0, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def auto_git_sync(interval_seconds=10):
    print(f"🚀 [Auto-Sync] Git continuous synchronization started! Checking every {interval_seconds}s...")
    
    while True:
        try:
            # Check for modified / untracked files
            success, status_out, _ = run_cmd("git status --porcelain")
            
            if success and status_out:
                print(f"\n🔄 [Auto-Sync] Detected changes:\n{status_out}")
                print("📦 Staging changes...")
                run_cmd("git add .")
                
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                commit_msg = f"Auto-sync update ({now_str})"
                
                print(f"📝 Committing: '{commit_msg}'...")
                commit_ok, commit_out, _ = run_cmd(f'git commit -m "{commit_msg}"')
                
                if commit_ok:
                    print("⬆️ Pushing to GitHub (origin main)...")
                    push_ok, push_out, push_err = run_cmd("git push origin main")
                    if push_ok:
                        print("✅ [Auto-Sync] Successfully pushed changes to GitHub! Streamlit Cloud will re-deploy automatically.")
                    else:
                        print(f"⚠️ [Auto-Sync] Push warning/error: {push_err or push_out}")
            
            time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n🛑 Auto-sync stopped.")
            break
        except Exception as e:
            print(f"⚠️ Sync error: {e}")
            time.sleep(interval_seconds)

if __name__ == "__main__":
    auto_git_sync(interval_seconds=10)
