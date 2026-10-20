"""python main.py로 실행하는 Mini Git 대화형 CLI다."""

import shlex

from repository import Repository


PROMPT = "mini-git> "
AUTHOR_OPTION = "--author="
SORT_OPTION = "--sort-by="
HELP_TEXT = """INIT <user_name>
BRANCH <branch_name>
SWITCH <branch_name>
COMMIT <message>
LOG [--sort-by=date|author]
PATH <commit1> <commit2>
ANCESTORS <commit_hash>
SEARCH <keyword> | SEARCH --author=<name>
HELP | EXIT | QUIT
공백이 있는 인자는 따옴표로 감싸세요. 예: COMMIT "Add login"
"""


def require_args(args, count):
    """빈 문자열·공백뿐인 인자도 잘못된 입력으로 처리한다."""
    if len(args) != count or any(not value.strip() for value in args):
        raise ValueError("Invalid args")


def print_commits(commits):
    """조회 결과는 반환값이 아니라 화면에 출력한다."""
    if not commits:
        print("No commits")
        return
    for node in commits:
        timestamp = node.timestamp.isoformat(timespec="microseconds")
        print(f"commit {node.hash} ({node.author}, {timestamp})")
        print(f"  {node.message}")


def execute(repository, line):
    """한 줄을 해석하고 계속 실행하면 True, 종료이면 False를 준다."""
    try:
        tokens = shlex.split(line)
    except ValueError:
        raise ValueError("Invalid args") from None
    if not tokens:
        return True
    command = tokens[0].upper()
    args = tokens[1:]
    if command in ("EXIT", "QUIT", "HELP"):
        require_args(args, 0)
        if command == "HELP":
            print(HELP_TEXT)
            return True
        return False
    if command == "LOG":
        handle_log(repository, args)
    elif command == "SEARCH":
        handle_search(repository, args)
    elif command == "PATH":
        require_args(args, 2)
        path = repository.path(args[0], args[1])
        print("Path: " + " -> ".join(path) if path else "No path")
    elif command in ("INIT", "BRANCH", "SWITCH", "COMMIT", "ANCESTORS"):
        require_args(args, 1)
        handle_single_arg(repository, command, args[0])
    else:
        raise ValueError(f"Unknown command: {tokens[0]}")
    return True


def handle_log(repository, args):
    """옵션을 검증한 뒤 로그를 표시한다."""
    if not args:
        print_commits(repository.log())
        return
    require_args(args, 1)
    if not args[0].startswith(SORT_OPTION):
        raise ValueError("Invalid args")
    sort_by = args[0][len(SORT_OPTION):]
    print_commits(repository.log(sort_by))


def handle_search(repository, args):
    """키워드와 작성자 옵션을 구분하고 인덱스 조회 결과를 출력한다."""
    require_args(args, 1)
    value = args[0]
    by_author = value.startswith(AUTHOR_OPTION)
    if by_author:
        value = value[len(AUTHOR_OPTION):]
    elif value.startswith("--"):
        raise ValueError("Invalid args")
    if not value.strip():
        raise ValueError("Invalid args")
    results = repository.search(value, by_author)
    print(f"Found {len(results)} commit(s)")
    print_commits(results)


def handle_single_arg(repository, command, value):
    """하나의 인자를 받는 명령의 상태 변경과 결과 출력을 연결한다."""
    if command == "INIT":
        repository.initialize(value)
        print("Initialized repository.")
        print(f"Current branch: {repository.current_branch}")
        print(f"Current user: {repository.user}")
    elif command == "BRANCH":
        repository.create_branch(value)
        print(f"Created branch: {value}")
    elif command == "SWITCH":
        repository.switch_branch(value)
        print(f"Switched to branch: {value}")
    elif command == "COMMIT":
        node = repository.commit(value)
        print(f"[{repository.current_branch} {node.hash}] {node.message}")
    else:
        print_commits(repository.ancestors(value))


def main():
    """입력 오류 후에도 REPL을 유지하며 EOF·Ctrl+C로 정상 종료한다."""
    repository = Repository()
    while True:
        try:
            line = input(PROMPT)
            if not execute(repository, line):
                break
        except ValueError as error:
            print(error)
        except (EOFError, KeyboardInterrupt):
            print()
            break


if __name__ == "__main__":
    main()
