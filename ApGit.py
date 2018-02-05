import json
from github3 import login
import requests


class ApGit:
    def __init__(self, username=None, password=None, api_token=None):
        if username and password:
            self.git = login(username=username, password=password)
        else:
            self.git = login(token=api_token)
        self.username = username
        self.user = self.git.user(self.username)

    def _get_repo_owner(self, repo_owner):
        """Private helper
        """
        if not repo_owner and not self.username:
            if not self.username:
                raise Exception("Must either login using username or provide repository owner")
            else:
                repo_owner = self.username
        return repo_owner

    def get_user_info(self):
        name = self.user.name
        location = self.user.location
        company = self.user.company
        email = self.user.email
        bio = self.user.bio
        followers = self.user.followers
        following = self.user.following
        return {
            "name": name,
            "location": location,
            "company": company,
            "email": email,
            "bio": bio,
            "followers": followers,
            "following": following
        }

    def get_repositories(self, repo_owner=None):
        """Get repositories for the specified repo_owner or current logged in user

        :param repo_owner: Repo owner
        """
        repo_owner = self._get_repo_owner(repo_owner)
        resp = requests.get("https://api.github.com/users/%s/repos" % repo_owner).text
        repositories = json.loads(resp)
        user_repositories = list()
        for repo in repositories:
            id = repo.get("id")
            name = repo.get("name")
            default_branch = repo.get("default_branch")
            description = repo.get("description")
            clone_url = repo.get("clone_url")
            entry = {"id": id, "name": name, "description": description, "default_branch": default_branch,
                     "clone_url": clone_url}
            user_repositories.append(entry)

        return user_repositories

    def get_repository_contents(self, repo_name, repo_owner=None, path="/"):
        """Get contents of the repository

        :param repo_name: Name of the repository
        :param repo_owner: Owner of the repository
        :param path: Path to list the contents of (default is root)
        """
        resp = list()
        repo_owner = self._get_repo_owner(repo_owner)
        repo = self.git.repository(repo_owner, repo_name)
        contents = repo.contents(path=path)
        for item in contents.items():
            entry = {"name": item[0], "type": item[1].type, "git_url": item[1].git_url, "path": item[1].path}
            resp.append(entry)

        return resp

    def get_default_branch(self, repo_name, repo_owner=None):
        """Get the default branch name of the repository

        :param repo_name: Name of the repository
        :param repo_owner: Owner of the repository
        """
        repo_owner = self._get_repo_owner(repo_owner)
        repo = self.git.repository(repo_owner, repo_name)
        return repo.default_branch

    def get_commit_messages(self, repo_name, repo_owner=None, branch_name=None):
        """Get commit messages for the given repository

        :param repo_name: Name of the repository
        :param repo_owner: Owner of the repository
        :param branch_name: Name of the branch (default branch if not provided)
        """
        repo_owner = self._get_repo_owner(repo_owner)
        commit_messages = list()
        commit_sha_list = list()
        repo = self.git.repository(repo_owner, repo_name)
        if not branch_name:
            branch_name = repo.default_branch
        branch = repo.branch(branch_name)
        # Append latest commit SHA to commit list
        commit_sha_list.append(branch.commit.sha)

        # BFS like algorithm to traverse CommitTree.
        # Each commit has a parent commit, except the last commit. Keep looping until we find that commit.
        while commit_sha_list:
            commit_sha = commit_sha_list.pop(0)
            # Get the commit object using the commit SHA
            user_commit = repo.commit(commit_sha)
            commit_message = user_commit.commit.message
            commit_messages.append({"sha": commit_sha, "message": commit_message})
            # Check if current commit has a parent.
            if user_commit.parents:
                parent_sha = user_commit.parents[0].get('sha')
                commit_sha_list.append(parent_sha)

        return commit_messages

    def get_commit(self, repo_name, commit_sha, repo_owner=None):
        """Get a commit from the repo with given SHA

        :param repo_name: Name of the repository
        :param commit_sha: Commit SHA
        :param repo_owner: Owner of the repository
        """
        repo_owner = self._get_repo_owner(repo_owner)
        repo = self.git.repository(repo_owner, repo_name)
        commit = repo.commit(commit_sha)
        return commit

    def view_commit_changes(self, repo_name, commit_sha, repo_owner=None, status_filter=['added', 'modified', 'deleted']):
        """Get the changes made in the commit with given SHA

        :param repo_name: Name of the repository
        :param commit_sha: Commit SHA
        :param repo_owner: Owner of the repository
        :param status_filter: List of file status . Can be any combination of ['added' , 'modified', 'deleted']
        """
        commit_changes = list()
        commit = self.get_commit(repo_name, commit_sha, repo_owner)
        files = commit.files
        for file in files:
            status = file.get("status")
            if status in status_filter:
                file_name = file.get("filename")
                additions = file.get("additions")
                changes = file.get("changes")
                deletions = file.get("deletions")
                status = file.get("status")
                patch = file.get("patch")
                entry = {"file_name": file_name, "additions": additions, "changes": changes, "deletions": deletions,
                         "status": status, "patch": patch}
                commit_changes.append(entry)

        return commit_changes
