# 코드 흐름과 줄별 해설

## 1. 읽는 순서

`main.py`의 `main()` → `execute()` → `repository.py`의 명령별 메서드 → `algorithms.py` / `index.py` 순서로 읽습니다. 각 `def`는 호출할 동작의 정의이며 함수 본문은 호출될 때 실행됩니다. `main.py`의 마지막 실행 조건만 직접 실행 시 REPL을 시작합니다.

| 파일 | 입력 | 반환·화면 출력 | 바뀌는 상태 |
| --- | --- | --- | --- |
| main.py | 사용자 입력 한 줄 | execute는 계속 여부, 나머지는 화면 출력 중심 | 메서드 호출로 저장소 변경 |
| repository.py | 이름·메시지·hash·옵션 | Commit·커밋 목록·경로 또는 None | INIT·BRANCH·SWITCH·COMMIT만 상태 변경 |
| index.py | 커밋 또는 검색어 | 검색은 hash 목록 | add만 두 인덱스 변경 |
| algorithms.py | 목록·키 함수·그래프 | 정렬 목록·hash 순서·경로 | 입력을 바꾸지 않고 지역 자료구조 사용 |

오류는 `ValueError`로 호출자에게 전달되어 최종적으로 REPL에서 출력합니다. `No path`는 두 노드가 존재하지만 연결되지 않은 결과이고 `Unknown commit`은 노드가 없다는 오류입니다.

### import 역할

- `shlex`: CLI 따옴표 인식. 터미널 자체를 실행하거나 셸 명령을 실행하는 모듈로 사용하지 않습니다.
- `dataclasses.dataclass`: 커밋 필드에 맞는 생성자 등의 자동 생성.
- `datetime.datetime`, `timezone`: 시간대가 있는 UTC 시각 생성.
- `collections.deque`: BFS와 위상 정렬에서 사용하는 앞뒤 처리가 빠른 큐. 그래프 전용 라이브러리가 아닙니다.
- 프로젝트 내부 import: CLI가 저장소를 부르고, 저장소가 탐색·정렬·검색을 호출합니다.

## 2. 실제 입력을 따라가기

새 실행에서 다음 순서로 입력합니다.

```text
INIT Alice
COMMIT "Add LOGIN login"
SEARCH login
```

| 단계 | 입력·변수 | 실행·데이터 변화 | 결과 |
| --- | --- | --- | --- |
| 1 | `INIT Alice` | `tokens=['INIT','Alice']`, `initialize` 호출 | user=Alice, current_branch=main, branches={'main': None} |
| 2 | `COMMIT "Add LOGIN login"` | shlex가 메시지를 한 인자로 묶음 | args=['Add LOGIN login'] |
| 3 | commit 내부 | parent=None, parents=(), hash=00000001 | Commit 객체 생성 |
| 4 | 그래프 등록 | commits에 객체 등록, children·neighbors에 빈 목록 | 루트 노드 하나 |
| 5 | 인덱스 등록 | 소문자 토큰 add, login. 중복 login 제거 | keywords의 각 목록에 00000001, authors의 Alice 목록에도 등록 |
| 6 | HEAD 이동 | branches['main']='00000001' | CLI가 새 hash와 메시지 출력 |
| 7 | `SEARCH login` | keywords의 login 후보만 가져옴 | hash 목록 ['00000001'] |
| 8 | 조회와 출력 | commits에서 그 hash만 직접 조회 | Found 1 commit(s)와 커밋 필드 출력 |

토큰을 set으로 처리하는 순간 단어들의 순서는 정해지지 않지만 각 단어의 목록에는 커밋을 생성한 순서대로 추가합니다. 이 때문에 검색 결과의 생성 순서는 유지됩니다.

## 3. 줄별 해설 기준

아래 줄 번호와 코드는 최종 소스에서 읽어 생성했습니다. import의 역할은 위에서 설명하며 줄별 표에서는 제외합니다. 빈 줄·순수 주석·독스트링·닫는 구분자만 있는 줄도 제외합니다. 출력 데이터인 HELP_TEXT의 문자열 내용은 독스트링이 아니므로 줄마다 설명합니다. 표의 소스 들여쓰기는 원본에 그대로 있으며 표에서는 코드를 읽기 쉽게 표시합니다.

### main.py

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 8 | `PROMPT = "mini-git> "` | 입력창에 반복해서 표시할 프롬프트 문자열을 상수로 지정합니다. |
| 9 | `AUTHOR_OPTION = "--author="` | 작성자 검색 옵션의 접두사를 상수로 두어 검사와 잘라내기에 함께 씁니다. |
| 10 | `SORT_OPTION = "--sort-by="` | 로그 정렬 옵션의 접두사를 한곳에서 정의합니다. |
| 11 | `HELP_TEXT = """INIT <user_name>` | 여러 줄 도움말 문자열을 시작하며 INIT의 문법을 첫 줄로 저장합니다. 함수 설명용 독스트링이 아니라 출력할 데이터입니다. |
| 12 | `BRANCH <branch_name>` | 도움말 데이터에 브랜치 생성 명령의 문법을 넣습니다. 여기서 명령이 실행되는 것은 아닙니다. |
| 13 | `SWITCH <branch_name>` | 도움말 데이터에 브랜치 이동 명령을 넣습니다. |
| 14 | `COMMIT <message>` | 도움말 데이터에 메시지를 받는 커밋 명령을 넣습니다. |
| 15 | `LOG [--sort-by=date\|author]` | 도움말에 정렬 옵션은 선택 사항이고 date 또는 author를 받는다고 표시합니다. |
| 16 | `PATH <commit1> <commit2>` | 도움말에 두 커밋 hash를 받는 경로 명령을 넣습니다. |
| 17 | `ANCESTORS <commit_hash>` | 도움말에 조상을 조회할 커밋 hash를 받는 문법을 넣습니다. |
| 18 | `SEARCH <keyword> \| SEARCH --author=<name>` | 도움말에 키워드 검색과 작성자 검색의 두 형식을 표시합니다. 세로 막대는 대안이라는 안내용 문자입니다. |
| 19 | `HELP \| EXIT \| QUIT` | 도움말에 추가 도움말과 두 종료 명령을 나열합니다. |
| 20 | `공백이 있는 인자는 따옴표로 감싸세요. 예: COMMIT "Add login"` | 도움말 문자열 안에서 공백 인자를 따옴표로 감싸는 예시를 안내합니다. |
| 24 | `def require_args(args, count):` | 인자 목록과 기대 개수를 받는 공통 검증 함수를 정의합니다. 아직 검증을 실행하지는 않습니다. |
| 26 | `if len(args) != count or any(not value.strip() for value in args):` | 개수가 다르거나 strip으로 공백을 제거한 값이 빈 인자가 하나라도 있는지 검사합니다. any는 하나라도 참이면 참입니다. |
| 27 | `raise ValueError("Invalid args")` | 잘못된 인자라면 ValueError를 발생시켜 이후 상태 변경을 중단합니다. |
| 30 | `def print_commits(commits):` | 커밋 객체 목록을 받아 화면에 표시하는 함수를 정의합니다. |
| 32 | `if not commits:` | 목록이 비어 있는지 확인합니다. 빈 목록은 조건식에서 거짓으로 취급됩니다. |
| 33 | `print("No commits")` | 빈 조회 결과라는 문구를 출력합니다. |
| 34 | `return` | 출력할 커밋이 없으므로 함수를 바로 끝냅니다. 명시된 반환값은 없어 None입니다. |
| 35 | `for node in commits:` | 결과 목록에서 커밋 객체를 하나씩 꺼냅니다. |
| 36 | `timestamp = node.timestamp.isoformat(timespec="microseconds")` | UTC 시각을 마이크로초와 시간대가 표시되는 ISO 형식 문자열로 만듭니다. |
| 37 | `print(f"commit {node.hash} ({node.author}, {timestamp})")` | f-string으로 hash·작성자·시각을 한 줄에 출력합니다. |
| 38 | `print(f"  {node.message}")` | 해당 커밋의 메시지를 다음 줄에 출력합니다. |
| 41 | `def execute(repository, line):` | 저장소 객체와 입력 한 줄을 받아 명령을 실행하는 함수를 정의합니다. |
| 43 | `try:` | 따옴표 파싱에서 발생할 수 있는 오류를 처리할 범위를 시작합니다. |
| 44 | `tokens = shlex.split(line)` | shlex.split은 따옴표 안의 공백을 유지하면서 입력을 명령·인자 토큰으로 나눕니다. |
| 45 | `except ValueError:` | 짝이 맞지 않는 따옴표 등 shlex의 ValueError를 받습니다. |
| 46 | `raise ValueError("Invalid args") from None` | 파서의 상세 오류 대신 미션의 Invalid args로 바꿉니다. from None은 이전 예외의 연결 표시를 숨깁니다. |
| 47 | `if not tokens:` | 입력이 빈 줄이거나 공백뿐이라 토큰이 없는지 확인합니다. |
| 48 | `return True` | 빈 입력은 아무것도 변경하지 않고 계속 실행하라는 True를 반환합니다. |
| 49 | `command = tokens[0].upper()` | 첫 토큰인 명령어만 대문자로 바꿔 명령의 대소문자 구분을 없앱니다. |
| 50 | `args = tokens[1:]` | 두 번째 토큰부터 마지막까지를 인자 목록으로 분리합니다. |
| 51 | `if command in ("EXIT", "QUIT", "HELP"):` | 도움말·종료처럼 저장소 초기화 없이도 쓸 수 있는 명령인지 판단합니다. |
| 52 | `require_args(args, 0)` | HELP·EXIT·QUIT 뒤에 불필요한 인자가 없는지 검사합니다. |
| 53 | `if command == "HELP":` | 세 명령 중 HELP인지 확인합니다. |
| 54 | `print(HELP_TEXT)` | 미리 저장한 여러 줄 도움말을 화면에 출력합니다. |
| 55 | `return True` | 도움말 이후에는 REPL을 계속해야 하므로 True를 반환합니다. |
| 56 | `return False` | EXIT 또는 QUIT이면 종료 요청이라는 False를 반환합니다. |
| 57 | `if command == "LOG":` | 로그 명령인지 확인합니다. |
| 58 | `handle_log(repository, args)` | 옵션 검증과 로그 출력을 handle_log에 위임합니다. |
| 59 | `elif command == "SEARCH":` | 앞 조건이 아니고 SEARCH 명령인지 확인합니다. |
| 60 | `handle_search(repository, args)` | 키워드·작성자 검색 분기와 출력을 handle_search에 위임합니다. |
| 61 | `elif command == "PATH":` | PATH 명령인지 확인합니다. |
| 62 | `require_args(args, 2)` | 출발·목적지 hash 두 개가 모두 전달되었는지 검사합니다. |
| 63 | `path = repository.path(args[0], args[1])` | 저장소가 두 hash의 존재를 확인하고 경로 hash 목록을 돌려주면 path에 받습니다. |
| 64 | `print("Path: " + " -> ".join(path) if path else "No path")` | 경로가 있으면 화살표로 이어 출력하고 빈 목록이면 No path를 출력합니다. 조건 표현식 전체가 print의 인자입니다. |
| 65 | `elif command in ("INIT", "BRANCH", "SWITCH", "COMMIT", "ANCESTORS"):` | 인자 하나를 받는 다섯 가지 명령 중 하나인지 검사합니다. |
| 66 | `require_args(args, 1)` | 공백뿐인 값이 아닌 인자 하나가 전달되었는지 확인합니다. |
| 67 | `handle_single_arg(repository, command, args[0])` | 명령 종류와 실제 인자 하나를 공통 처리 함수에 전달합니다. |
| 68 | `else:` | 지금까지 어느 지원 명령에도 해당하지 않는 경우입니다. |
| 69 | `raise ValueError(f"Unknown command: {tokens[0]}")` | 입력한 명령 이름을 포함한 오류를 발생시킵니다. |
| 70 | `return True` | 정상 명령을 마친 뒤 다음 입력을 받으라는 True를 반환합니다. |
| 73 | `def handle_log(repository, args):` | LOG의 선택 옵션을 해석하는 함수를 정의합니다. |
| 75 | `if not args:` | 추가 인자가 없는 기본 LOG인지 확인합니다. |
| 76 | `print_commits(repository.log())` | 위상 순서의 커밋 목록을 반환받아 화면에 출력합니다. |
| 77 | `return` | 기본 LOG 처리가 끝났으므로 옵션 검사로 내려가지 않고 끝냅니다. |
| 78 | `require_args(args, 1)` | 옵션은 한 토큰만 허용하므로 인자 개수와 빈 값을 검사합니다. |
| 79 | `if not args[0].startswith(SORT_OPTION):` | 유일한 인자가 정해진 --sort-by=로 시작하는지 확인합니다. |
| 80 | `raise ValueError("Invalid args")` | 정해진 옵션 접두사가 아니면 Invalid args 오류를 발생시킵니다. |
| 81 | `sort_by = args[0][len(SORT_OPTION):]` | 옵션 접두사의 길이만큼 앞을 잘라 date 또는 author 부분을 추출합니다. |
| 82 | `print_commits(repository.log(sort_by))` | 저장소에서 기준 값의 유효성을 검사하고 직접 병합 정렬한 결과를 출력합니다. |
| 85 | `def handle_search(repository, args):` | SEARCH 인자 하나를 키워드 또는 작성자 검색으로 해석하는 함수를 정의합니다. |
| 87 | `require_args(args, 1)` | 검색 인자가 정확히 하나이고 빈 문자열이 아닌지 확인합니다. |
| 88 | `value = args[0]` | 검색 토큰 하나를 value에 저장합니다. |
| 89 | `by_author = value.startswith(AUTHOR_OPTION)` | --author=로 시작하는지 검사한 논리값을 by_author에 저장합니다. |
| 90 | `if by_author:` | 작성자 검색이라면 옵션 부분을 제거하는 처리를 합니다. |
| 91 | `value = value[len(AUTHOR_OPTION):]` | --author= 다음의 실제 이름만 잘라 value를 갱신합니다. 이름 안 공백은 파서에서 보존되어 있습니다. |
| 92 | `elif value.startswith("--"):` | 작성자 옵션은 아닌데 --로 시작하면 지원하지 않는 옵션으로 판단합니다. |
| 93 | `raise ValueError("Invalid args")` | 지원하지 않는 검색 옵션을 Invalid args로 거부합니다. |
| 94 | `if not value.strip():` | 옵션을 잘라낸 뒤 작성자 이름이 비거나 공백뿐인지 다시 검사합니다. |
| 95 | `raise ValueError("Invalid args")` | 빈 작성자 값도 잘못된 인자라고 알립니다. |
| 96 | `results = repository.search(value, by_author)` | value와 검색 종류를 저장소에 전달해 커밋 결과 목록을 받습니다. 검색은 전체 커밋을 순회하지 않습니다. |
| 97 | `print(f"Found {len(results)} commit(s)")` | 결과 목록의 길이를 이용해 검색 건수를 출력합니다. |
| 98 | `print_commits(results)` | 찾은 커밋의 필드를 화면에 출력합니다. 결과가 없으면 공통 출력 함수가 No commits를 표시합니다. |
| 101 | `def handle_single_arg(repository, command, value):` | 인자 하나로 처리하는 명령들의 실행과 결과 출력을 연결하는 함수를 정의합니다. |
| 103 | `if command == "INIT":` | 초기화 명령인지 확인합니다. |
| 104 | `repository.initialize(value)` | 저장소에 사용자 이름을 전달하여 main·HEAD·현재 사용자를 설정합니다. |
| 105 | `print("Initialized repository.")` | 초기화 성공 메시지를 출력합니다. |
| 106 | `print(f"Current branch: {repository.current_branch}")` | 설정된 현재 브랜치 이름을 출력합니다. |
| 107 | `print(f"Current user: {repository.user}")` | 설정된 사용자 이름을 출력합니다. |
| 108 | `elif command == "BRANCH":` | 브랜치 생성 명령인지 확인합니다. |
| 109 | `repository.create_branch(value)` | 현재 커밋을 가리키는 브랜치를 생성합니다. 저장소 상태가 바뀝니다. |
| 110 | `print(f"Created branch: {value}")` | 성공적으로 생성한 브랜치 이름을 출력합니다. |
| 111 | `elif command == "SWITCH":` | 브랜치 전환 명령인지 확인합니다. |
| 112 | `repository.switch_branch(value)` | 저장소에서 현재 브랜치를 변경합니다. 존재하지 않으면 여기서 예외가 발생합니다. |
| 113 | `print(f"Switched to branch: {value}")` | 전환 성공과 대상 브랜치를 출력합니다. |
| 114 | `elif command == "COMMIT":` | 커밋 생성 명령인지 확인합니다. |
| 115 | `node = repository.commit(value)` | 메시지로 커밋을 만들고 생성된 객체를 node에 받습니다. |
| 116 | `print(f"[{repository.current_branch} {node.hash}] {node.message}")` | 현재 브랜치·새 hash·메시지를 출력하여 다음 명령에서 hash를 사용할 수 있게 합니다. |
| 117 | `else:` | execute에서 허용한 나머지 단일 인자 명령인 ANCESTORS를 처리합니다. |
| 118 | `print_commits(repository.ancestors(value))` | 해당 hash의 조상 객체 목록을 반환받아 출력합니다. |
| 121 | `def main():` | 입력·실행·출력 루프의 시작 함수를 정의합니다. |
| 123 | `repository = Repository()` | 프로그램이 살아 있는 동안 사용할 저장소 객체 하나를 만듭니다. |
| 124 | `while True:` | 종료 요청이 있을 때까지 입력을 반복합니다. |
| 125 | `try:` | 각 입력·실행 과정의 사용자 입력 오류와 종료 신호를 처리할 범위를 시작합니다. |
| 126 | `line = input(PROMPT)` | 프롬프트를 표시하고 사용자가 입력한 한 줄을 문자열로 받습니다. |
| 127 | `if not execute(repository, line):` | execute가 False를 반환했는지 확인합니다. True이면 다음 반복으로 이어집니다. |
| 128 | `break` | EXIT·QUIT 요청이므로 while 반복문을 끝냅니다. |
| 129 | `except ValueError as error:` | 파싱·명령 실행 중 발생한 ValueError를 error라는 이름으로 받습니다. |
| 130 | `print(error)` | 오류 문구를 출력합니다. 반복문 밖으로 나가지 않으므로 다음 입력을 받습니다. |
| 131 | `except (EOFError, KeyboardInterrupt):` | 입력 종료인 EOF 또는 Ctrl+C의 KeyboardInterrupt를 처리합니다. |
| 132 | `print()` | 프롬프트 뒤에 줄바꿈을 출력해 종료 화면을 정리합니다. |
| 133 | `break` | EOF·Ctrl+C라면 입력 루프를 끝냅니다. |
| 136 | `if __name__ == "__main__":` | 이 파일을 직접 실행했는지 검사합니다. 다른 코드에서 import할 때는 REPL을 자동 실행하지 않습니다. |
| 137 | `main()` | 직접 실행한 경우 main 함수를 호출해 프로그램을 시작합니다. |

### repository.py

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 11 | `DEFAULT_BRANCH = "main"` | 초기 브랜치 이름 main을 의미 있는 상수로 지정합니다. |
| 12 | `HASH_WIDTH = 8` | hash의 최소 표시 폭을 8자리로 지정합니다. 상한 자릿수가 아닙니다. |
| 15 | `@dataclass(frozen=True)` | dataclass가 필드 기반 생성자 등을 만들도록 하고 frozen=True로 필드 재대입을 막습니다. |
| 16 | `class Commit:` | 커밋 메타데이터를 보관할 Commit 클래스를 선언합니다. |
| 19 | `hash: str` | hash 필드가 문자열이라는 타입 힌트를 선언합니다. |
| 20 | `message: str` | message 필드가 커밋 메시지 문자열이라는 것을 선언합니다. |
| 21 | `author: str` | author 필드가 작성자 문자열이라는 것을 선언합니다. |
| 22 | `timestamp: datetime` | timestamp 필드가 datetime 객체라는 것을 선언합니다. |
| 23 | `parents: tuple[str, ...]` | parents가 문자열 hash를 0개 이상 담는 튜플임을 나타냅니다. ...는 같은 타입의 가변 개수를 뜻합니다. |
| 26 | `class Repository:` | 저장소의 상태와 그 상태를 바꾸는 동작을 묶는 클래스를 선언합니다. |
| 29 | `def __init__(self):` | Repository 객체를 만들 때 초기 상태를 구성하는 생성자를 정의합니다. |
| 30 | `self.user = None` | 초기화 전에는 작성자가 없음을 None으로 표시합니다. |
| 31 | `self.current_branch = None` | 초기화 전에는 현재 브랜치가 없음을 None으로 표시합니다. |
| 32 | `self.commits = {}` | hash로 Commit 객체를 직접 찾는 딕셔너리를 만듭니다. |
| 33 | `self.branches = {}` | 브랜치 이름에서 커밋 hash 또는 None으로 연결하는 딕셔너리를 만듭니다. |
| 34 | `self.children = {}` | 각 커밋의 자식 hash 목록을 보관할 표를 만듭니다. 위상 정렬에 사용합니다. |
| 35 | `self.neighbors = {}` | 각 커밋의 부모와 자식을 함께 보관할 무방향 이웃 표를 만듭니다. PATH에 사용합니다. |
| 36 | `self.index = InvertedIndex()` | 키워드·작성자 검색을 전담하는 역색인 객체를 만듭니다. |
| 37 | `self.next_commit_id = 1` | 새 커밋의 식별자를 만들 증가 카운터를 1부터 시작합니다. |
| 39 | `def require_initialized(self):` | 저장소가 INIT되었는지 확인하는 공통 메서드를 정의합니다. |
| 41 | `if self.user is None:` | 현재 사용자 값이 None이면 초기화 전으로 판단합니다. |
| 42 | `raise ValueError("Repository not initialized")` | 초기화가 필요한 명령의 실행을 오류로 중단합니다. |
| 44 | `def initialize(self, user):` | 현재 사용자와 초기 브랜치를 설정할 메서드를 정의합니다. |
| 46 | `if self.user is not None:` | 이미 사용자가 설정되어 초기화된 저장소인지 검사합니다. |
| 47 | `raise ValueError("Repository already initialized")` | 다시 INIT해서 기존 데이터를 지우지 않도록 오류를 발생시킵니다. |
| 48 | `self.user = user` | 전달받은 사용자 이름을 저장소 상태에 기록합니다. |
| 49 | `self.current_branch = DEFAULT_BRANCH` | 현재 브랜치를 main으로 지정합니다. |
| 50 | `self.branches[DEFAULT_BRANCH] = None` | main 브랜치를 등록하되 아직 커밋이 없으므로 참조를 None으로 둡니다. |
| 52 | `def create_branch(self, name):` | 현재 위치를 공유하는 브랜치를 만드는 메서드를 정의합니다. |
| 54 | `self.require_initialized()` | 브랜치를 만들기 전에 초기화 여부를 확인합니다. |
| 55 | `if name in self.branches:` | 동일한 이름의 브랜치가 이미 있는지 딕셔너리 키로 검사합니다. |
| 56 | `raise ValueError(f"Branch already exists: {name}")` | 중복 이름을 덮어쓰지 않고 오류를 알립니다. |
| 57 | `self.branches[name] = self.branches[self.current_branch]` | 현재 브랜치가 가리키는 hash를 새 브랜치에 저장합니다. 커밋 객체를 복사하지 않습니다. |
| 59 | `def switch_branch(self, name):` | 현재 브랜치를 옮기는 메서드를 정의합니다. |
| 61 | `self.require_initialized()` | 전환에 앞서 저장소 초기화를 확인합니다. |
| 62 | `if name not in self.branches:` | 이동할 브랜치 이름이 등록되어 있지 않은지 검사합니다. |
| 63 | `raise ValueError(f"Unknown branch: {name}")` | 존재하지 않는 브랜치 이름을 포함한 오류를 발생시킵니다. |
| 64 | `self.current_branch = name` | 현재 브랜치 이름을 바꿉니다. 기존 커밋의 부모나 메시지는 변경하지 않습니다. |
| 66 | `def get_commit(self, commit_hash):` | 전체 hash 하나로 커밋을 조회하는 메서드를 정의합니다. |
| 68 | `if commit_hash not in self.commits:` | 정확한 hash 키가 커밋 표에 없는지 확인합니다. |
| 69 | `raise ValueError(f"Unknown commit: {commit_hash}")` | 해당 hash가 없다는 오류를 발생시킵니다. |
| 70 | `return self.commits[commit_hash]` | 딕셔너리에서 찾은 Commit 객체를 호출자에게 반환합니다. 화면 출력은 하지 않습니다. |
| 72 | `def commit(self, message):` | 메시지를 받아 새 커밋을 생성하는 메서드를 정의합니다. |
| 74 | `self.require_initialized()` | 커밋을 만들기 전에 저장소 초기화를 확인합니다. |
| 75 | `parent = self.branches[self.current_branch]` | 현재 브랜치가 가리키는 커밋 hash를 부모 후보로 가져옵니다. |
| 76 | `parents = () if parent is None else (parent,)` | 첫 커밋이면 부모 없는 빈 튜플, 아니면 부모 hash 하나의 튜플을 만듭니다. |
| 78 | `commit_hash = f"{self.next_commit_id:0{HASH_WIDTH}x}"` | 증가 정수를 16진수로 표시하고 최소 폭까지 0으로 채웁니다. 폭을 넘는 숫자를 잘라내지 않아 중복되지 않습니다. |
| 79 | `node = Commit(commit_hash, message, self.user,` | 새 hash·메시지·현재 작성자를 Commit 생성자에 전달하는 다중행 호출을 시작합니다. |
| 80 | `datetime.now(timezone.utc), parents)` | 시간대가 명시된 현재 UTC 시각과 부모 튜플을 더해 Commit 객체 생성을 마칩니다. |
| 81 | `self.next_commit_id += 1` | 다음 커밋에서 같은 숫자를 쓰지 않도록 카운터를 1 올립니다. |
| 82 | `self.commits[commit_hash] = node` | 새 hash를 키로 커밋 객체를 등록합니다. |
| 83 | `self.children[commit_hash] = []` | 새 커밋은 아직 자식이 없으므로 자식 목록을 빈 리스트로 등록합니다. |
| 84 | `self.neighbors[commit_hash] = list(parents)` | 새 커밋의 무방향 이웃 목록을 부모 목록으로 초기화합니다. |
| 85 | `for parent_hash in parents:` | 부모 hash들을 하나씩 처리합니다. 필수 COMMIT은 0개 또는 1개입니다. |
| 86 | `self.children[parent_hash].append(commit_hash)` | 부모의 자식 목록에 새 커밋 hash를 추가하여 부모→자식 표를 갱신합니다. |
| 87 | `self.neighbors[parent_hash].append(commit_hash)` | 부모의 무방향 이웃에도 새 커밋을 넣어 양방향 이동이 되게 합니다. |
| 88 | `self.index.add(node)` | 새 커밋의 메시지 토큰과 작성자를 역색인에 등록합니다. |
| 89 | `self.branches[self.current_branch] = commit_hash` | 현재 브랜치의 참조를 새 커밋으로 옮깁니다. 다른 브랜치는 그대로입니다. |
| 90 | `return node` | 생성된 Commit 객체를 반환하여 CLI가 hash와 메시지를 출력할 수 있게 합니다. |
| 92 | `def log(self, sort_by=None):` | 정렬 기준을 선택적으로 받는 로그 조회 메서드를 정의합니다. 기본값 None은 기본 LOG입니다. |
| 94 | `self.require_initialized()` | 조회 전에 INIT 여부를 확인합니다. |
| 95 | `if sort_by is None:` | 정렬 옵션이 없는 기본 LOG인지 검사합니다. |
| 96 | `hashes = topological_order(self.commits, self.children)` | 모든 커밋과 자식 표를 넘겨 부모 우선의 hash 목록을 받습니다. |
| 97 | `return [self.commits[value] for value in hashes]` | 위상 순서의 hash 각각을 Commit 객체로 바꾸어 반환합니다. |
| 98 | `if sort_by not in ("date", "author"):` | 옵션이 있는데 date도 author도 아니면 잘못된 인자로 판단합니다. |
| 99 | `raise ValueError("Invalid args")` | 지원하지 않는 정렬 기준을 Invalid args로 거부합니다. |
| 100 | `field = "timestamp" if sort_by == "date" else "author"` | date 옵션은 객체의 timestamp 속성으로, author 옵션은 author 속성으로 연결합니다. |
| 101 | `return merge_sort(list(self.commits.values()),` | 전체 커밋 객체를 생성 순서의 목록으로 복사하여 직접 만든 병합 정렬에 전달합니다. |
| 102 | `key=lambda node: getattr(node, field))` | lambda가 각 객체의 선택된 속성을 반환하게 하여 정렬 키로 사용합니다. 정렬된 새 목록을 반환합니다. |
| 104 | `def path(self, start, target):` | 두 커밋 사이의 경로를 조회하는 메서드를 정의합니다. |
| 106 | `self.require_initialized()` | PATH를 실행하기 전에 초기화 여부를 검사합니다. |
| 107 | `self.get_commit(start)` | 출발 hash가 실제 커밋인지 검사합니다. 없으면 예외가 납니다. |
| 108 | `self.get_commit(target)` | 목적지 hash도 존재하는지 검사합니다. 없는 노드와 연결되지 않은 노드를 구분합니다. |
| 109 | `return shortest_path(self.neighbors, start, target)` | 무방향 이웃 표를 탐색 함수에 넘기고 경로 hash 목록을 그대로 반환합니다. |
| 111 | `def ancestors(self, commit_hash):` | 특정 커밋의 조상 객체 목록을 구하는 메서드를 정의합니다. |
| 113 | `self.require_initialized()` | 조상 조회 전 초기화 여부를 검사합니다. |
| 114 | `self.get_commit(commit_hash)` | 시작 커밋이 있는지 확인합니다. |
| 115 | `hashes = find_ancestors(self.commits, commit_hash)` | 부모 방향 DFS로 찾은 조상 hash 목록을 받습니다. |
| 116 | `return [self.commits[value] for value in hashes]` | 각 조상 hash를 커밋 객체로 직접 조회해 결과 목록으로 반환합니다. |
| 118 | `def search(self, value, by_author=False):` | 검색어와 검색 종류를 받는 메서드를 정의합니다. 기본값 False는 메시지 검색입니다. |
| 120 | `self.require_initialized()` | 검색을 시작하기 전에 INIT 여부를 확인합니다. |
| 121 | `if by_author:` | 작성자 검색이 요청되었는지 확인합니다. |
| 122 | `hashes = self.index.search_author(value)` | 작성자 역색인에서 해당 이름의 커밋 hash 목록을 받습니다. |
| 123 | `else:` | 작성자 검색이 아니면 메시지 키워드 검색을 수행합니다. |
| 124 | `hashes = self.index.search_keyword(value)` | 단어 역색인에서 조건에 맞는 커밋 hash 목록을 받습니다. |
| 125 | `return [self.commits[commit_hash] for commit_hash in hashes]` | 후보 hash만 커밋 표에서 직접 조회해 반환합니다. 전체 commits.values 순회가 없습니다. |

### index.py

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 4 | `class InvertedIndex:` | 키워드·작성자 역색인을 담당하는 클래스를 선언합니다. |
| 7 | `def __init__(self):` | 인덱스 객체를 만들 때 빈 검색 표를 준비하는 생성자를 정의합니다. |
| 8 | `self.keywords = {}` | 메시지 토큰에서 커밋 hash 목록으로 연결하는 딕셔너리를 만듭니다. |
| 9 | `self.authors = {}` | 작성자 이름에서 커밋 hash 목록으로 연결하는 딕셔너리를 만듭니다. |
| 11 | `def add(self, commit):` | 새 커밋 하나를 역색인 두 곳에 등록하는 메서드를 정의합니다. |
| 13 | `for word in set(commit.message.lower().split()):` | 메시지를 소문자·공백 토큰으로 바꾸고 set으로 중복 단어를 제거한 뒤 각 단어를 처리합니다. |
| 14 | `self.keywords.setdefault(word, []).append(commit.hash)` | 처음 본 단어이면 빈 목록을 만든 후 해당 커밋 hash를 뒤에 추가합니다. 기존 단어이면 기존 목록을 씁니다. |
| 15 | `self.authors.setdefault(commit.author, []).append(commit.hash)` | 작성자 이름에도 같은 방식으로 커밋 hash를 추가합니다. 이름의 대소문자는 변환하지 않습니다. |
| 17 | `def search_keyword(self, keyword):` | 공백으로 구분된 하나 이상의 검색 단어를 처리하는 메서드를 정의합니다. |
| 19 | `words = list(set(keyword.lower().split()))` | 검색어를 등록 때와 같은 규칙으로 정규화하고 중복을 제거한 뒤 목록으로 바꿉니다. |
| 20 | `if not words:` | 검색 토큰이 하나도 없는지 검사합니다. |
| 21 | `return []` | 아무 토큰도 없으면 결과 없는 빈 목록을 반환합니다. |
| 22 | `postings = [self.keywords.get(word, []) for word in words]` | 각 단어의 후보 hash 목록을 가져옵니다. 없는 단어는 빈 목록으로 처리해 KeyError를 막습니다. |
| 24 | `smallest = min(postings, key=len)` | len을 비교 기준으로 사용해 가장 짧은 후보 목록을 고릅니다. min은 전체를 정렬하지 않고 최솟값만 고릅니다. |
| 25 | `posting_sets = [set(values) for values in postings]` | 각 후보 목록을 포함 여부 검사가 빠른 집합으로 복사합니다. |
| 26 | `return [value for value in smallest` | 가장 짧은 목록의 hash를 순서대로 검사해 남길 결과 목록을 구성하기 시작합니다. |
| 27 | `if all(value in values for values in posting_sets)]` | all로 모든 단어의 후보 집합에 들어 있는지 검사하여 AND 조건을 만족하는 hash만 반환합니다. |
| 29 | `def search_author(self, author):` | 작성자 전체 이름으로 조회하는 메서드를 정의합니다. |
| 31 | `return list(self.authors.get(author, []))` | 해당 작성자의 목록을 찾아 복사본을 반환합니다. 외부에서 결과를 바꾸어도 원본 인덱스가 수정되지 않습니다. |

### algorithms.py

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 6 | `def merge_sort(items, key):` | 정렬 대상과 비교 값을 뽑는 함수 key를 받는 병합 정렬 함수를 정의합니다. |
| 8 | `if len(items) < 2:` | 원소 수가 0개 또는 1개인지 검사합니다. 더 나눌 필요가 없는 종료 조건입니다. |
| 9 | `return list(items)` | 입력의 복사본을 반환합니다. 짧은 목록에서도 새 결과 목록이라는 계약을 유지합니다. |
| 10 | `middle = len(items) // 2` | 정수 나눗셈으로 가운데 위치를 계산합니다. |
| 11 | `left = merge_sort(items[:middle], key)` | 왼쪽 절반을 슬라이스로 나누어 같은 기준으로 재귀 정렬합니다. |
| 12 | `right = merge_sort(items[middle:], key)` | 오른쪽 절반도 같은 기준으로 재귀 정렬합니다. |
| 13 | `merged = []` | 정렬된 두 절반을 합칠 빈 결과 목록을 만듭니다. |
| 14 | `left_index = right_index = 0` | 왼쪽·오른쪽에서 아직 선택하지 않은 첫 위치를 각각 0으로 시작합니다. |
| 15 | `while left_index < len(left) and right_index < len(right):` | 양쪽 모두 남은 원소가 있을 동안 앞부분을 비교합니다. 둘 중 하나가 끝나면 반복도 끝납니다. |
| 16 | `if key(left[left_index]) <= key(right[right_index]):` | key를 호출한 두 값을 비교합니다. 같은 값이면 왼쪽을 고르는 <=가 안정 정렬의 핵심입니다. |
| 17 | `merged.append(left[left_index])` | 왼쪽의 현재 원소를 결과 뒤에 추가합니다. |
| 18 | `left_index += 1` | 선택한 왼쪽 원소를 다시 쓰지 않도록 왼쪽 위치를 1 올립니다. |
| 19 | `else:` | 왼쪽 키가 더 큰 경우 오른쪽 원소를 선택합니다. |
| 20 | `merged.append(right[right_index])` | 오른쪽의 현재 원소를 결과에 추가합니다. |
| 21 | `right_index += 1` | 오른쪽 위치를 다음 원소로 옮깁니다. |
| 22 | `merged.extend(left[left_index:])` | 오른쪽이 먼저 끝났을 수도 있으므로 남은 왼쪽 항목을 한 번에 덧붙입니다. |
| 23 | `merged.extend(right[right_index:])` | 왼쪽이 먼저 끝났을 수도 있으므로 남은 오른쪽 항목도 덧붙입니다. 빈 조각이면 변화가 없습니다. |
| 24 | `return merged` | 정렬을 마친 새 목록을 반환합니다. 원래 입력을 제자리 변경하지 않습니다. |
| 27 | `def topological_order(commits, children):` | 커밋 표와 부모→자식 표를 받는 위상 정렬 함수를 정의합니다. |
| 29 | `remaining = {value: len(node.parents) for value, node in commits.items()}` | 각 hash별로 아직 출력하지 않은 부모 수를 저장합니다. 처음에는 전체 부모 수입니다. |
| 30 | `ready = deque(value for value in commits if remaining[value] == 0)` | 남은 부모가 0인 모든 루트를 큐에 넣습니다. 생성 순서의 딕셔너리 순회를 따릅니다. |
| 31 | `ordered = []` | 최종 hash 순서를 모을 빈 목록을 만듭니다. |
| 32 | `while ready:` | 처리할 커밋이 큐에 남아 있는 동안 반복합니다. |
| 33 | `current = ready.popleft()` | 큐 앞에서 hash 하나를 꺼냅니다. deque.popleft는 앞을 제거할 때 전체를 이동하지 않습니다. |
| 34 | `ordered.append(current)` | 그 hash는 부모가 모두 처리되었으므로 출력 순서 결과에 추가합니다. |
| 35 | `for child in children[current]:` | 현재 커밋을 부모로 가진 각 자식을 확인합니다. |
| 36 | `remaining[child] -= 1` | 현재 부모가 처리되었으므로 해당 자식의 남은 부모 수를 하나 줄입니다. |
| 37 | `if remaining[child] == 0:` | 모든 부모가 처리되어 남은 수가 0이 되었는지 검사합니다. |
| 38 | `ready.append(child)` | 이제 출력 가능한 자식 hash를 큐 뒤에 넣습니다. |
| 39 | `if len(ordered) != len(commits):` | 처리한 수가 전체 수와 다르면 끝까지 출력할 수 없는 노드가 남았는지 확인합니다. |
| 40 | `raise ValueError("Cycle detected")` | 일관된 부모·자식 표를 전제로 순환이 있다는 오류를 알립니다. 정상 저장소 생성 경로에서는 발생하지 않습니다. |
| 41 | `return ordered` | 부모가 자식보다 앞선 hash 목록을 반환합니다. |
| 44 | `def find_ancestors(commits, start):` | 시작 커밋의 모든 조상을 구하는 함수를 정의합니다. |
| 46 | `visited = set()` | 이미 방문한 조상을 기억할 집합을 만듭니다. |
| 47 | `stack = list(commits[start].parents)` | 시작점 자신을 제외하기 위해 그 부모 hash들로 스택을 초기화합니다. |
| 48 | `result = []` | 중복 없는 조상 방문 순서를 기록할 목록을 만듭니다. |
| 49 | `while stack:` | 탐색할 부모가 스택에 남아 있는 동안 반복합니다. |
| 50 | `current = stack.pop()` | 리스트 끝에서 하나를 꺼내 깊이 우선 탐색을 진행합니다. |
| 51 | `if current in visited:` | 공유 조상 등으로 이미 처리한 hash인지 검사합니다. |
| 52 | `continue` | 중복 노드는 결과에 다시 넣지 않고 다음 반복으로 넘어갑니다. |
| 53 | `visited.add(current)` | 처음 방문한 hash를 방문 집합에 기록합니다. |
| 54 | `result.append(current)` | 해당 조상 hash를 결과 순서 목록에 추가합니다. |
| 55 | `stack.extend(commits[current].parents)` | 현재 조상의 부모들도 스택에 넣어 더 오래된 조상을 탐색합니다. |
| 56 | `return result` | 방문한 모든 조상 hash 목록을 반환합니다. |
| 59 | `def shortest_path(neighbors, start, target):` | 무방향 이웃 표와 출발·목적지 hash를 받는 최단 경로 함수를 정의합니다. |
| 61 | `distance = {target: 0}` | 목적지에서 목적지까지 거리를 0으로 설정합니다. 역방향 BFS의 시작 상태입니다. |
| 62 | `queue = deque([target])` | 목적지를 첫 BFS 대기 노드로 넣습니다. |
| 63 | `while queue:` | BFS로 방문할 노드가 남아 있는 동안 반복합니다. |
| 64 | `current = queue.popleft()` | 큐 앞에서 다음 방문 노드를 꺼내 가까운 거리부터 처리합니다. |
| 65 | `for neighbor in neighbors[current]:` | 현재 노드에 직접 연결된 부모·자식 이웃을 차례로 확인합니다. |
| 66 | `if neighbor not in distance:` | 거리 표에 없는 이웃만 처음 방문합니다. 같은 노드를 반복해서 넣지 않습니다. |
| 67 | `distance[neighbor] = distance[current] + 1` | 그 이웃의 목적지까지 거리를 현재 거리에 간선 하나를 더한 값으로 기록합니다. |
| 68 | `queue.append(neighbor)` | 처음 발견한 이웃을 큐 뒤에 넣어 이후 그 이웃의 연결도 확인합니다. |
| 69 | `if start not in distance:` | BFS를 끝냈는데 출발지가 거리 표에 없으면 서로 연결되지 않은 경우입니다. |
| 70 | `return []` | 경로 없음이라는 의미로 빈 목록을 반환합니다. |
| 71 | `path = [start]` | 출발지만 담은 경로 목록으로 복원을 시작합니다. |
| 72 | `while path[-1] != target:` | 현재 경로의 마지막 노드가 목적지가 될 때까지 다음 노드를 선택합니다. |
| 73 | `current = path[-1]` | 현재 위치를 경로 목록의 마지막 hash로 가져옵니다. |
| 74 | `best = None` | 이번 단계에서 고를 가장 작은 후보가 아직 없음을 None으로 표시합니다. |
| 75 | `for neighbor in neighbors[current]:` | 현재 위치의 모든 이웃을 검토합니다. |
| 76 | `if distance.get(neighbor) != distance[current] - 1:` | 목적지까지 거리가 정확히 1 줄어드는 이웃인지 검사합니다. 다른 연결 요소의 값은 get이 None을 반환합니다. |
| 77 | `continue` | 거리를 줄이지 않는 이웃은 최단 경로에 쓸 수 없으므로 건너뜁니다. |
| 79 | `if best is None or neighbor + "->" < best + "->":` | 첫 유효 후보이거나 구분자를 붙인 hash 문자열이 기존 후보보다 사전순으로 작으면 선택합니다. or의 단축 평가가 None과의 덧셈을 막습니다. |
| 80 | `best = neighbor` | 현재까지 가장 작은 유효 이웃을 best로 갱신합니다. |
| 81 | `path.append(best)` | 고른 이웃을 경로 뒤에 붙입니다. 출발지의 거리가 존재하므로 거리를 1 줄이는 이웃도 반드시 있습니다. |
| 82 | `return path` | 최소 간선 수와 사전순 동률 조건을 만족하는 경로 hash 목록을 반환합니다. |

## 4. 해설 대조 결과

최종 소스에서 의미 있는 줄 번호를 AST 기반 제외 규칙과 대조했습니다. 누락·중복·없는 줄 번호가 없고 표의 코드는 해당 원본 줄과 일치합니다.

| 파일 | 개별 해설 줄 수 |
| --- | --- |
| main.py | 106 |
| repository.py | 86 |
| index.py | 19 |
| algorithms.py | 66 |
