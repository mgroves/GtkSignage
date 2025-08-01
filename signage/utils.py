import subprocess
import os
import logging

def is_update_available():
    try:
        repo_dir = os.getenv("SIGNAGE_REPO_DIR", "/opt/gtk-signage")

        if not os.path.exists(repo_dir):
            logging.warning(f"Repo path does not exist: {repo_dir}")
            return False

        # Fetch the latest from the remote
        subprocess.run(['git', 'fetch'], cwd=repo_dir, check=True)

        # Check if there are new commits
        result = subprocess.run(
            ['git', 'rev-list', 'HEAD..origin/prod', '--count'],
            cwd=repo_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
        count = int(result.stdout.strip())
        return count > 0
    except Exception as e:
        logging.error(f"Error checking for update: {e}")
        return False
