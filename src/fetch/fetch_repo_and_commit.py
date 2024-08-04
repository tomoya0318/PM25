import requests
import pandas as pd
from tqdm import tqdm
from constants import path
from dotenv import load_dotenv
import os

load_dotenv()


class GitHubPythonRepoAnalyzer:
    def __init__(self, owner):
        self.owner = owner
        self.token = os.getenv("GITHUB_TOKEN")

    def get_github_repos(self):
        url = f"https://api.github.com/users/{self.owner}/repos"
        print(f"start fetch from {url}")
        headers = {"Authorization": f"token {self.token}"}
        repos = []
        page = 1
        while True:
            response = requests.get(url, headers=headers, params={"page": page, "per_page": 100})
            if response.status_code != 200:
                raise Exception(f"Error: {response.status_code}")

            data = response.json()
            if not isinstance(data, list):
                raise Exception("Expected JSON response to be a list")

            if not data:
                break

            repos.extend(data)
            page += 1

        return repos

    def get_repo_languages(self, repo_name):
        url = f"https://api.github.com/repos/{self.owner}/{repo_name}/languages"
        headers = {"Authorization": f"token {self.token}"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Error: {response.status_code}")

        return response.json()

    def get_commit_count(self, repo_name):
        url = f"https://api.github.com/repos/{self.owner}/{repo_name}/commits"
        headers = {"Authorization": f"token {self.token}"}
        response = requests.get(url, headers=headers, params={"per_page": 1})
        if response.status_code != 200:
            raise Exception(f"Error: {response.status_code}")

        if "Link" in response.headers:
            link = response.headers["Link"]
            last_page = link.split(",")[1].split("page=")[2].split(">")[0]
            return int(last_page)
        else:
            commits = response.json()
            return len(commits)

    def get_python_repos_with_commit_count(self):
        repos = self.get_github_repos()
        python_repos_with_commits = []
        for repo in tqdm(repos, desc="Processing repositories"):
            languages = self.get_repo_languages(repo["name"])
            if "Python" in languages:
                commit_count = self.get_commit_count(repo["name"])
                python_repos_with_commits.append({"project": repo["name"], "commit": commit_count})
        return python_repos_with_commits

    def save_to_csv(self, data, filename):
        print("saving to csv...")
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)


# GitHubのオーナー名とパーソナルアクセストークンを指定
if __name__ == "__main__":
    owner = "anaconda"
    analyzer = GitHubPythonRepoAnalyzer(owner)
    python_repos_with_commits = analyzer.get_python_repos_with_commit_count()
    analyzer.save_to_csv(python_repos_with_commits, f"{path.RESULTS}/{owner}.csv")
