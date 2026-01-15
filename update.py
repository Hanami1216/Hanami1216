import requests
import os
import datetime
import re
from dateutil import tz

token = os.getenv('GITHUB_TOKEN', '')
current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
top_repo_num = 10
recent_repo_num = 10

from_zone = tz.tzutc()
to_zone = tz.tzlocal()


def fetcher(username: str):
    result = {
        'name': '',
        'public_repos': 0,
        'top_repos': [],
        'recent_repos': []
    }
    user_info_url = "https://api.github.com/users/{}".format(username)
    header = {} if token == "" else {"Authorization": "bearer {}".format(token)}
    try:
        res = requests.get(user_info_url, headers=header)
        res.raise_for_status()
        user = res.json()
    except Exception as e:
        print(f"Error fetching user info: {e}")
        return result

    result['name'] = user.get('name', username)
    result['public_repos'] = user.get('public_repos', 0)
    repos = []
    
    # Handling pagination
    total_pages = 1 + result['public_repos'] // 100
    for i in range(1, total_pages + 1):
        all_repos_url = "https://api.github.com/users/{}/repos?per_page=100&page={}".format(username, i)
        try:
            res = requests.get(all_repos_url, headers=header)
            res.raise_for_status()
            repos.extend(res.json())
        except Exception as e:
            print(f"Error fetching repos page {i}: {e}")

    processed_repos = []
    for repo in repos:
        if repo.get('fork'):
            continue
        processed_repo = {
            'score': repo.get('stargazers_count', 0) + repo.get('watchers_count', 0) + repo.get('forks_count', 0),
            'star': repo.get('stargazers_count', 0),
            'link': repo.get('html_url', ''),
            'created_at': repo.get('created_at', ''),
            'updated_at': repo.get('updated_at', ''),
            'pushed_at': repo.get('pushed_at', ''),
            'name': repo.get('name', ''),
            'description': repo.get('description', '')
        }
        if not processed_repo['description']:
            processed_repo['description'] = ''
            
        # Timezone conversion
        if processed_repo['pushed_at']:
            try:
                date = datetime.datetime.strptime(processed_repo['pushed_at'], "%Y-%m-%dT%H:%M:%SZ")
                date = date.replace(tzinfo=from_zone)
                date = date.astimezone(to_zone)
                processed_repo['pushed_at'] = date.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
                
        processed_repos.append(processed_repo)

    top_repos = sorted(processed_repos, key=lambda x: x['star'], reverse=True)
    top_repos = top_repos[:top_repo_num]
    result['top_repos'] = top_repos

    recent_repos = sorted(processed_repos, key=lambda x: x['pushed_at'], reverse=True)
    recent_repos = recent_repos[:recent_repo_num]
    result['recent_repos'] = recent_repos

    return result


def replace_chunk(content, marker, chunk, inline=False):
    r = re.compile(
        r'<!\-\- START_SECTION:{} \-\->.*<!\-\- END_SECTION:{} \-\->'.format(marker, marker),
        re.DOTALL | re.MULTILINE,
    )
    if not inline:
        chunk = '\n{}\n'.format(chunk)
    chunk = '<!-- START_SECTION:{} -->{}<!-- END_SECTION:{} -->'.format(marker, chunk, marker)
    return r.sub(chunk, content)


def render(github_data):
    template_path = './TEMPLATE.md'
    if not os.path.exists(template_path):
        print("TEMPLATE.md not found!")
        return ""
        
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Generate Top Repos Table
    top_repos_content = "\n## Top Projects\n|Project|Description|Stars|\n|:--|:--|:--|\n"
    for repo in github_data['top_repos']:
        description = repo['description'].replace('|', '\|') # Escape pipes in description
        top_repos_content += "|[{name}]({link})|{description}|`{star}⭐`|\n".format(
            name=repo['name'], link=repo['link'], description=description, star=repo['star']
        )
    
    # Generate Recent Repos Table
    recent_repos_content = "\n## Recent Updates\n|Project|Description|Last Update|\n|:--|:--|:--|\n"
    for repo in github_data['recent_repos']:
        date_badge = repo['pushed_at'].replace('-', '--').replace(' ', '-').replace(':', '%3A')
        description = repo['description'].replace('|', '\|')
        recent_repos_content += "|[{name}]({link})|{description}|![{pushed_at}](https://img.shields.io/badge/{date}-brightgreen?style=flat-square)|\n".format(
            name=repo['name'], link=repo['link'], description=description, pushed_at=repo['pushed_at'], date=date_badge
        )
    
    footer_content = f"\n*Last updated on: {current_time}*"

    content = replace_chunk(content, 'top_repos', top_repos_content)
    content = replace_chunk(content, 'recent_repos', recent_repos_content)
    content = replace_chunk(content, 'footer', footer_content)
    
    return content


def writer(markdown) -> bool:
    if not markdown:
        return False
    try:
        with open('./README.md', 'w', encoding='utf-8') as f:
            f.write(markdown)
        return True
    except IOError as e:
        print(f'unable to write to file: {e}')
        return False


def main():
    github_username = os.getenv('GITHUB_USERNAME')
    if not github_username:
        # Fallback to current directory name or default to Hanami1216 if detection fails
        cwd = os.getcwd()
        github_username = os.path.split(cwd)[-1]
        # Or explicit fallback
        if github_username == 'Hanami1216': 
             pass
        else:
             # Just a safe fallback
             github_username = 'Hanami1216'

    print(f"Fetching data for {github_username}...")
    github_data = fetcher(github_username)
    
    print("Rendering README...")
    markdown = render(github_data)
    
    if writer(markdown):
        print("README.md updated successfully.")
    else:
        print("Failed to update README.md.")


if __name__ == '__main__':
    main()
