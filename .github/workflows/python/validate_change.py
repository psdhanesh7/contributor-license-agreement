# The line is of the format "+| `full name`| [gitLogin](https://github.com/gitLogin) |12-july-2021|"
import os
import json 
import sys
import re
from requests import request
from os import error

EXPECTED_SUCCESS_MESSAGE = "ok"

# Regular expression for checking whether the change is of the specified line format
# \| `[A-Za-z]+(\s[A-Za-z]+)*` ?\| ?\[[a-zA-Z\d](?:[A-Za-z\d]|-(?=[a-zA-Z\d])){0,38}\]\(https://github\.com/[a-zA-Z\d](?:[A-Za-z\d]|-(?=[a-zA-Z\d])){0,38}\) ?\| ?[\d]{2}-[a-zA-Z]+-[\d]{4} ?\|


# Change line is of the format "+| `full name`| [pr_raiser_login](https://github.com/pr_raiser_login) |12-july-2021|"

def validate_row_formatting(row):
    # validate change line format
    format_re = "\+\|\s*`[A-Za-z]+(\s[A-Za-z]+)*`\s*\|\s*\[[a-zA-Z\d](?:[A-Za-z\d]|-(?=[a-zA-Z\d])){0,38}\]\(https:\/\/github\.com\/[a-zA-Z\d](?:[A-Za-z\d]|-(?=[a-zA-Z\d])){0,38}\)\s*\|\s*[\d]{2}-[a-zA-Z]+-[\d]{4}\s*\|"
    if re.match(format_re, row):
        return EXPECTED_SUCCESS_MESSAGE
    else:
        return "Error: The expected line should be: | `full name` | [git-username](https://github.com/git-username) | dd-month-yyyy | \n"
    

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

def extract_change():
    print("current working directory is: ", os.getcwd())

    github_info_file = open('./.tmp/github.json', 'r') 
    github_details = json.load(github_info_file)

    commit_info_file = open('./.tmp/commitDetails.json', 'r') 
    commit_details = json.load(commit_info_file)

    if github_details["event_name"] != "pull_request":
        print("Error! This operation is valid on github pull requests. Exiting")
        sys.exit(1)

    pr_raiser_login = github_details['event']['pull_request']['user']['login']

    print("Pull request submitted by github login: ", pr_raiser_login)
    print("Number of commits in the pull request: ", len(commit_details))

    commit_details_url = commit_details[0]["url"]
    response = request(url=commit_details_url, data_as_json=True)
    commit_changed_files = json.loads(response.body)["files"]

    change = ""
    for file in commit_changed_files:
        if file["filename"] == "test1.doc": # Note: Filename need to be changed to contributor_....md
            change = file["patch"]

    change_line_regex = re.compile('\+.+$')
    change_line = change_line_regex.findall(change)[0]
    print(change_line)
    
    return (pr_raiser_login, change_line)


pr_raiser_login, change = extract_change()
print("Pull request submitted by github login: " + pr_raiser_login)
print("Modifications to the file: " + change)

EXPECTED_ERROR_MESSAGE = "Error, invalid row format: The expected line should be: | `full name`| [git-username](https://github.com/git-username) |dd-month-yyyy| \n"
if validate_change(pr_raiser_login, change) == EXPECTED_SUCCESS_MESSAGE:
    print(EXPECTED_SUCCESS_MESSAGE)
else:
    print("Validation failed!")
    sys.exit(1)


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
# EXPECTED_SUCCESS_MESSAGE = "ok"
# assert validate_change('newuser', "+| `full name user` | [newuser](https://github.com/newuser) | 14-july-2021 |") == EXPECTED_SUCCESS_MESSAGE
# assert validate_change('newuser', "+|`full name user`|[newuser](https://github.com/newuser)|14-july-2021|") == EXPECTED_SUCCESS_MESSAGE
# assert validate_change('newuser', "+|  `full name user`   |    [newuser](https://github.com/newuser)   |  14-july-2021  |") == EXPECTED_SUCCESS_MESSAGE

# print("success")

