import os
import subprocess
import logging

logger = logging.getLogger(__name__)

class GitSyncService:
    def __init__(self, repo_url: str, local_dir: str = "/app/personas", branch: str = "main"):
        self.repo_url = repo_url
        self.local_dir = local_dir
        self.branch = branch

    def startup_pull(self):
        """Pulls from the github repository into /app/personas"""
        if not os.path.exists(self.local_dir):
            os.makedirs(self.local_dir, exist_ok=True)
            logger.info(f"Cloning {self.repo_url} into {self.local_dir}...")
            try:
                subprocess.run(["git", "clone", "--depth", "1", "-b", self.branch, self.repo_url, self.local_dir], check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"Error cloning repository: {e.stderr}")
        else:
            logger.info(f"Pulling updates in {self.local_dir}...")
            try:
                subprocess.run(["git", "-C", self.local_dir, "pull", "origin", self.branch], check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"Error pulling repository: {e.stderr}")

    def background_push(self, commit_message: str = "Update personas"):
        """Pushes any new generated JSON personas to github."""
        try:
            # Need to figure out the right auth path if pushing to github. For now assume configured.
            subprocess.run(["git", "-C", self.local_dir, "add", "."], check=True, capture_output=True, text=True)

            # Check if there are changes to commit
            status = subprocess.run(["git", "-C", self.local_dir, "status", "--porcelain"], capture_output=True, text=True)
            if not status.stdout.strip():
                logger.info("No changes to push.")
                return

            subprocess.run(["git", "-C", self.local_dir, "commit", "-m", commit_message], check=True, capture_output=True, text=True)
            subprocess.run(["git", "-C", self.local_dir, "push", "origin", self.branch], check=True, capture_output=True, text=True)
            logger.info(f"Successfully pushed changes to {self.branch}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error pushing to repository: {e.stderr}")

git_sync = GitSyncService("https://github.com/JsonLord/agent-notes.git", "/app/personas")
