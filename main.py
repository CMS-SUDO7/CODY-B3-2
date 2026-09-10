import shlex
from repository import Repository

# 같은 형식으로 로그·검색·조상 결과를 보여 준다.
# 저장소와 출력할 커밋 식별자 목록을 받는다.
def print_commits(repo, commit_ids):
    if not commit_ids:
        print('No commits')
    for commit_id in commit_ids:
        commit = repo.commits[commit_id]
        print(f"commit {commit['hash']} | {commit['author']} | {commit['timestamp']}")
        print('  ' + commit['message'])

# 잘못된 문법을 저장소 변경 전에 공통으로 검사한다.
# 대문자 명령과 파싱된 인자 목록을 검사한다.
def validate(command, args):
    counts = {'INIT': 1, 'BRANCH': 1, 'SWITCH': 1, 'COMMIT': 1, 'PATH': 2, 'ANCESTORS': 1, 'SEARCH': 1, 'EXIT': 0, 'QUIT': 0}
    if command == 'LOG':
        if args not in ([], ['--sort-by=date'], ['--sort-by=author']):
            raise ValueError('Invalid args')
    elif command not in counts:
        raise ValueError('Unknown command: ' + command)
    elif len(args) != counts[command]:
        raise ValueError('Invalid args')
    if any(not arg.strip() for arg in args):
        raise ValueError('Invalid args')
    if command == 'SEARCH' and args[0].startswith('--'):
        if not args[0].startswith('--author=') or not args[0][9:].strip():
            raise ValueError('Invalid args')

# 한 줄 명령을 실행하고 다음 반복에서 사용할 저장소를 반환한다.
# 검증된 명령만 받으며 종료 처리는 main에서 담당한다.
def execute(repo, command, args):
    if command == 'INIT':
        if repo is not None:
            raise ValueError('Repository already initialized')
        repo = Repository(args[0])
        print('Initialized repository.')
        print('Current branch: main')
        print('Current user: ' + repo.user)
        return repo
    if repo is None:
        raise ValueError('Repository not initialized: use INIT <user_name>')
    if command == 'BRANCH':
        repo.branch(args[0])
        print('Created branch: ' + args[0])
    elif command == 'SWITCH':
        repo.switch(args[0])
        print('Switched to branch: ' + args[0])
    elif command == 'COMMIT':
        commit_id = repo.commit(args[0])
        print(f'[{repo.current_branch} {commit_id}] {args[0]}')
    elif command == 'LOG':
        sort_by = None
        if args:
            sort_by = args[0].split('=', 1)[1]
        print_commits(repo, repo.log(sort_by))
    elif command == 'PATH':
        path = repo.path(args[0], args[1])
        if path is None:
            print('No path')
        else:
            print('Path: ' + '->'.join(path))
    elif command == 'ANCESTORS':
        print_commits(repo, repo.ancestors(args[0]))
    elif command == 'SEARCH':
        query = args[0]
        by_author = query.startswith('--author=')
        if by_author:
            query = query[9:]
        found = repo.search(query, by_author)
        print(f'Found {len(found)} commit(s):')
        print_commits(repo, found)
    return repo

# REPL은 읽기(Read), 실행(Evaluate), 출력(Print)을 반복(Loop)한다.
# 프로그램의 대화형 실행을 시작하는 함수이다.
def main():
    repo = None
    print('Mini Git | INIT <user_name> | exit / quit')
    while True:
        try:
            line = input('mini-git> ')
            try:
                tokens = shlex.split(line)
            except ValueError:
                raise ValueError('Invalid args') from None
            if not tokens:
                continue
            command = tokens[0].upper()
            args = tokens[1:]
            validate(command, args)
            if command in ('EXIT', 'QUIT'):
                print('Bye')
                break
            repo = execute(repo, command, args)
        except ValueError as error:
            print(str(error))
        except (EOFError, KeyboardInterrupt):
            print('\nBye')
            break

if __name__ == '__main__':
    main()
