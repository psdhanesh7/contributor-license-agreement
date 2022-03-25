# The line is of the format "+| `full name`| [gitLogin](https://github.com/gitLogin) |12-july-2021|"
import os
import sys
import requests
import json
import subprocess
import re
from diff_parser import get_diff_details

print("current working directory is: ", os.getcwd())
STATUS_FAILED = 'FAILED'
EXPECTED_SUCCESS_MESSAGE = "ok"

def get_github_details():
    github_info_file = open('./.tmp/github.json', 'r') 
    return json.load(github_info_file)


def get_commit_details():
    commit_info_file = open('./.tmp/commitDetails.json', 'r') 
    return json.load(commit_info_file)


def process_git_local_details():
    # Check if current dir is git dir
    is_git_dir = subprocess.check_output(
            ['/usr/bin/git', 'rev-parse', '--is-inside-work-tree']).decode('utf-8')
    print("Is git dir: ", is_git_dir)

    # git status
    git_status = subprocess.check_output(
            ['/usr/bin/git', 'status']).decode('utf-8')
    print("Git status: ", git_status)

    # last n commits
    last_10_commit_list = subprocess.check_output(
            ['/usr/bin/git', 'rev-list', '--max-count=10', 'HEAD']).decode('utf-8')
    print("last 10 commit ids are: ", last_10_commit_list)

    return {
        'is_git_dir': is_git_dir,
        'last_10_commit_list': last_10_commit_list
    }


def extract_pull_request_changes(commits):
    # github logins of all committers
    commit_logins = []
    commit_id_list = []
    files_updated = []
    for commit in commits:
        commiter_github_login = commit['committer']['login']
        if commiter_github_login not in commit_logins:
            commit_logins.append(commiter_github_login)
        
        commit_id = commit['sha']
        commit_id_list.append(commit_id)
        try:
            files = subprocess.check_output(
            ['/usr/bin/git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit_id]).decode('utf-8').splitlines()
            for file in files:
                if file not in files_updated:
                    files_updated.append(file)
        except subprocess.CalledProcessError as e:
            print("Exception on process, rc=", e.returncode, "output=", e.output)
            sys.exit(1)

    print("All github users who made changes in the pull request: ", commit_logins)
    print("All commit ids in pull request: ", commit_id_list)
    print("All files updated in pull request: ", files_updated)
    
    return {
        'commit_id_list': commit_id_list,
        'commit_logins': commit_logins,
        'files_updated': files_updated
    }



def collect_pr_details(): 
    github = get_github_details()
    commits = get_commit_details()
    git_local = process_git_local_details()
    pr_changes = extract_pull_request_changes(commits)
    return {
        'github': github,
        'commits': commits,
        'num_commits_in_pr': len(commits),
        'event_name': github["event_name"],
        'pr_submitter_github_login': github['event']['pull_request']['user']['login'],
        'github_repo': github['repository'],
        'pr_number' : github['event']['number'],
        'is_git_dir': git_local['is_git_dir'],
        'last_10_commit_list': git_local['last_10_commit_list'],
        'commit_id_list': pr_changes['commit_id_list'],
        'commit_logins': pr_changes['commit_logins'],
        'files_updated': pr_changes['files_updated']
    }


def write_comment(comment):
    print(comment)
    f = open("./.tmp/comment", "a")
    f.write(comment)
    f.write("\n")
    f.close()


def task_failed(comment):
    f = open("./.tmp/failed", "a")
    f.write(comment)
    f.write("\n")
    f.close()
    write_comment(comment)
    return STATUS_FAILED


def validate_is_pull_request(pr_details):
    github_details = pr_details['github']
    if github_details["event_name"] != "pull_request" :
        print("Error! This operation is valid on github pull requests. Exiting. Event received: ", github_details["event_name"])
        sys.exit(1)

def getChanges(patch_details):
    diff_details = get_diff_details(patch_details)
    line_added = None
    if len(diff_details['linesAdded']) == 1:
        line_added = diff_details['linesAdded'][0]
    return {
        'linesRemoved' : len(diff_details['linesRemoved']),
        'linesAdded': len(diff_details['linesAdded']),
        'textAdded': line_added
    }



# Regular expression for checking whether the change is of the specified line format
# \| `[A-Za-z]+(\s[A-Za-z]+)*` ?\| ?\[[a-zA-Z\d](?:[A-Za-z\d]|-(?=[a-zA-Z\d])){0,38}\]\(https://github\.com/[a-zA-Z\d](?:[A-Za-z\d]|-(?=[a-zA-Z\d])){0,38}\) ?\| ?[\d]{2}-[a-zA-Z]+-[\d]{4} ?\|


def validate_row_formatting(row):
    # validate change line format
    format_re = "\+\|\s*`[A-Za-z]+(\s[A-Za-z]+)*`\s*\|\s*\[[a-zA-Z\d](?:[A-Za-z\d]|-(?=[a-zA-Z\d])){0,38}\]\(https:\/\/github\.com\/[a-zA-Z\d](?:[A-Za-z\d]|-(?=[a-zA-Z\d])){0,38}\)\s*\|\s*[\d]{2}-[a-zA-Z]+-[\d]{4}\s*\|"
    if re.match(format_re, row):
        return EXPECTED_SUCCESS_MESSAGE
    else:
        return "Error: The expected line should be: | `full name` | [git-username](https://github.com/git-username) | dd-month-yyyy | \n"
    
# Change line is of the format "+| `full name`| [pr_raiser_login](https://github.com/pr_raiser_login) |12-july-2021|"
def validate_change(pr_raiser_login, change):

    # validation code here
    if validate_row_formatting(change) != EXPECTED_SUCCESS_MESSAGE:
        EXPECTED_ERROR_MESSAGE = "Error, invalid row format: The expected line should be: | `full name`| [git-username](https://github.com/git-username) |dd-month-yyyy| \n"

        # Extra spaces in the start of the line
        format_re = "\+\s+\|\s*`[A-Za-z]+(\s[A-Za-z]+)*`\s*\|\s*\[[a-zA-Z\d](?:[A-Za-z\d]|-(?=[a-zA-Z\d])){0,38}\]\(https:\/\/github\.com\/[a-zA-Z\d](?:[A-Za-z\d]|-(?=[a-zA-Z\d])){0,38}\)\s*\|\s*[\d]{2}-[a-zA-Z]+-[\d]{4}\s*\|"
        if re.match(format_re, change):
            return EXPECTED_ERROR_MESSAGE + "Please remove extra spaces in the start of the line."

        return EXPECTED_ERROR_MESSAGE

    # Return success message if none of the checks failed
    return EXPECTED_SUCCESS_MESSAGE


# # user names should be valid
# EXPECTED_ERROR_MESSAGE = "Error: The expected line should be: | `full name` | [naren](https://github.com/naren) | 14-july-2021 | \n"
# assert validate_change('naren', "+| `full name`| [some_wrong_user](https://github.com/naren) |14-july-2021|") == EXPECTED_ERROR_MESSAGE + 'Github username should be same as pull request user name'
# assert validate_change('naren', "+| `full name`| [naren](https://github.com/some_wrong_user) |14-july-2021|") == EXPECTED_ERROR_MESSAGE + 'Github username should be same as pull request user name'
# assert validate_change('naren', "+| 'full name'| [naren](https://github.com/some_wrong_user) |14-july-2021|") == EXPECTED_ERROR_MESSAGE + "please use `full name` instead of 'full name'"

# # Date should be within one week of today and should be of the format dd-month-YYYY
# DATE_ERROR_MESSAGE = EXPECTED_ERROR_MESSAGE + "Invalid date: date should be within one week of <today's date in dd-month-YYYY format>"
# assert validate_change('naren', "+| `full name`| [naren](https://github.com/naren) |14-july-2020|") == DATE_ERROR_MESSAGE
# assert validate_change('naren', "+| `full name`| [naren](https://github.com/naren) |14-06-2021|") == DATE_ERROR_MESSAGE
# assert validate_change('naren', "+| `full name`| [naren](https://github.com/naren) ||") == DATE_ERROR_MESSAGE

# # Invalid row fomatting
EXPECTED_ERROR_MESSAGE = "Error, invalid row format: The expected line should be: | `full name`| [git-username](https://github.com/git-username) |dd-month-yyyy| \n"
assert validate_change('naren', "+ `full name`| [naren](https://github.com/naren) |14-july-2021|") == EXPECTED_ERROR_MESSAGE
assert validate_change('naren', "lols") == EXPECTED_ERROR_MESSAGE
assert validate_change('naren', "+| `full name` [naren](https://github.com/naren) |14-july-2021|") == EXPECTED_ERROR_MESSAGE
assert validate_change('naren', "+ `full name`| [nare") == EXPECTED_ERROR_MESSAGE
assert validate_change('naren', "+       | `full name`|   [naren](https://github.com/naren)  |14-july-2021  |   ") == EXPECTED_ERROR_MESSAGE + "Please remove extra spaces in the start of the line."

# # check if already signed
# EXPECTED_ERROR_MESSAGE = "Error,  Njay2000 has already signed the personal contributor license agreement."
# assert validate_change('Njay2000', "+| `full name`| [Njay2000](https://github.com/Njay2000) |14-july-2021|") == EXPECTED_ERROR_MESSAGE
# EXPECTED_ERROR_MESSAGE = "Error,  mathewdennis1 has already signed the employer contributor license agreement."
# assert validate_change('mathewdennis1', "+| `full name`| [mathewdennis1](https://github.com/mathewdennis1) |14-july-2021|") == EXPECTED_ERROR_MESSAGE

# # success case
EXPECTED_SUCCESS_MESSAGE = "ok"
assert validate_change('newuser', "+| `full name user` | [newuser](https://github.com/newuser) | 14-july-2021 |") == EXPECTED_SUCCESS_MESSAGE
assert validate_change('newuser', "+|`full name user`|[newuser](https://github.com/newuser)|14-july-2021|") == EXPECTED_SUCCESS_MESSAGE
assert validate_change('newuser', "+|  `full name user`   |    [newuser](https://github.com/newuser)   |  14-july-2021  |") == EXPECTED_SUCCESS_MESSAGE

# print("success")

