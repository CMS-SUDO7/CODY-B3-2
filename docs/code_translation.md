# Mini Git 코드 흐름과 줄별 해설

이 문서는 **명령 하나가 어떤 함수를 거쳐 어떤 상태를 바꾸는지** 따라가는 코드 해설입니다. 먼저 전체 흐름과 작은 입력 예제를 읽고, 궁금한 함수의 줄별 표로 이동하세요. 개념·비유는 [기초·핵심 지식](basic_knowledge.md), 말로 설명하는 연습은 [학습 질문과 답변](study_qa.md)에서 이어집니다.

바로 가기: [전체 흐름](#flow) · [입력과 상태 추적](#trace) · [오류와 빈 결과](#errors) · [main.py](#main) · [repository.py](#repository) · [index.py](#index) · [algorithms.py](#algorithms) · [해설 검증](#verification)

<a id="flow"></a>

## 1. 전체 흐름과 읽는 길

프로그램은 `main()`에서 저장소 객체 하나를 만든 뒤 명령을 반복해서 받습니다. 입력 한 줄은 `execute()`가 해석하고, `Repository`가 실제 상태 변경이나 조회를 맡습니다. 탐색·정렬은 `algorithms.py`, 검색 인덱스는 `index.py`에서 처리합니다. 조회 결과는 호출한 곳으로 돌아오고 최종 화면 표시는 CLI가 담당합니다.

| 파일 | 맡은 역할 | 실행 후 얻는 결과 |
| --- | --- | --- |
| `main.py` | 입력 해석·인자 검사·출력·종료 처리 | 화면 출력, 계속 실행할지 나타내는 논리값 |
| `repository.py` | 커밋·브랜치·현재 위치 관리와 조회 연결 | 커밋 객체·커밋 목록·hash 경로 |
| `index.py` | 단어·작성자별 후보 등록과 검색 | 조건에 맞는 hash 목록 |
| `algorithms.py` | 병합 정렬·위상 정렬·DFS·BFS | 정렬된 목록·방문 순서·최단 경로 |

### 질문에 맞춰 찾아 읽기

| 알고 싶은 것 | 먼저 읽을 처리 | 이어서 볼 처리 |
| --- | --- | --- |
| 공백이 있는 메시지는 어떻게 읽을까? | `execute()`의 입력 분리 | `require_args()`의 검증 |
| 브랜치는 언제 이동할까? | `Repository.commit()` | `create_branch()`·`switch_branch()` |
| 부모가 먼저 나오게 하려면? | `Repository.log()` | `topological_order()` |
| 최단 경로와 사전순 동률은 어떻게 나눌까? | `Repository.path()` | `shortest_path()`의 거리 계산·복원 |
| 공유 조상을 중복 없이 찾으려면? | `Repository.ancestors()` | `find_ancestors()` |
| 전체 메시지를 읽지 않고 검색하려면? | `InvertedIndex.add()` | `search_keyword()`·`Repository.search()` |

`def`로 적힌 본문은 함수가 호출될 때 실행됩니다. 파일 끝의 `if __name__ == "__main__":`는 `python main.py`로 직접 실행할 때 REPL을 시작하는 진입점입니다. REPL은 입력을 읽고 실행 결과를 보여 주는 일을 반복하는 대화형 루프입니다.

### import는 무엇을 준비할까?

- `shlex`: 따옴표로 묶인 공백 인자를 구분합니다. 이 프로그램에서 셸 명령을 실행하는 용도로 쓰지 않습니다.
- `dataclasses.dataclass`: 커밋 필드에 맞는 생성자 등을 만듭니다.
- `datetime.datetime`, `timezone`: 시간대가 있는 UTC 커밋 시각을 만듭니다.
- `collections.deque`: BFS와 칸 알고리즘에서 앞 항목을 빠르게 꺼내는 큐입니다. 그래프 전용 라이브러리는 아닙니다.
- 프로젝트 내부 import: CLI가 저장소를 호출하고 저장소가 탐색·정렬·검색 도구를 사용하도록 연결합니다.

<a id="trace"></a>

## 2. 작은 입력으로 상태 추적하기

### 2-1. 첫 커밋을 만들고 검색하기

새 실행에서 다음 명령을 한 줄씩 입력합니다.

```text
INIT Alice
COMMIT "Add LOGIN login"
SEARCH login
```

먼저 CLI가 공백을 처리합니다. `COMMIT "Add LOGIN login"`은 `['COMMIT', 'Add LOGIN login']`으로 나뉘므로 메시지 전체가 인자 하나로 남습니다. 명령 토큰만 대문자로 통일하며 메시지 원문은 바꾸지 않습니다.

| 단계 | 처리 | 바뀌는 데이터 또는 반환값 |
| --- | --- | --- |
| 1 | 저장소 초기화 | `user='Alice'`, `current_branch='main'`, `branches={'main': None}` |
| 2 | 첫 부모와 식별자 결정 | `parent=None`, `parents=()`, `hash='00000001'` |
| 3 | 커밋·그래프 등록 | `commits`에 객체, `children`·`neighbors`에 빈 목록 등록 |
| 4 | 역색인 등록 | add·login·작성자 Alice의 목록에 hash 등록 |
| 5 | 현재 브랜치 이동 | `branches['main']='00000001'`, 다음 카운터는 2 |
| 6 | login 검색 | 역색인에서 `['00000001']`을 얻고 해당 커밋만 조회 |

마지막으로 CLI는 `Found 1 commit(s)`와 커밋 정보를 출력합니다. 시각은 실행할 때 생성되므로 매번 달라집니다.

메시지는 원문 그대로 저장하지만 검색용 토큰은 소문자·공백 기준으로 만듭니다. 같은 메시지의 LOGIN과 login은 중복 제거되어 해당 단어 목록에 hash가 한 번만 들어갑니다. 토큰을 set으로 순회하는 순서와, 단어별 목록에 커밋이 추가되는 생성 순서는 구분해야 합니다.

### 2-2. 브랜치를 만들고 이동한 뒤 커밋하기

위 상태에서 다음 명령을 이어서 실행합니다.

```text
BRANCH feature
SWITCH feature
COMMIT "Add payment"
PATH 00000001 00000002
```

| 명령 직후 | 현재 브랜치 | main의 위치 | feature의 위치 | 새로 생긴 관계 |
| --- | --- | --- | --- | --- |
| `BRANCH feature` | main | 00000001 | 00000001 | 없음 |
| `SWITCH feature` | feature | 00000001 | 00000001 | 없음 |
| `COMMIT "Add payment"` | feature | 00000001 | 00000002 | 새 커밋의 부모는 00000001 |

마지막 COMMIT에서는 세 가지 관계 자료를 함께 갱신합니다. 새 커밋의 `parents`에는 기존 HEAD를, 기존 부모의 `children`에는 새 커밋을, `neighbors`에는 양방향 연결을 저장합니다. 그다음 역색인을 갱신하고 feature의 위치를 옮깁니다.

PATH는 `['00000001', '00000002']`를 반환합니다. CLI는 이를 `Path: 00000001 -> 00000002`로 표시합니다. 알고리즘이 돌려주는 목록과 사용자가 보는 출력 문구를 구분해 읽으세요.

<a id="errors"></a>

## 3. 오류·빈 결과·종료를 구분하기

| 상황 | 처리 경로 | 사용자가 보는 결과 |
| --- | --- | --- |
| 공백만 입력 | `execute()`가 `True` 반환 | 다음 입력 대기 |
| 인자 개수·따옴표 오류 | `ValueError` → `main()`의 예외 처리 | `Invalid args`, 이후 계속 입력 가능 |
| 없는 커밋 조회 | `get_commit()`에서 `ValueError` | `Unknown commit: <hash>` |
| 존재하지만 연결되지 않은 두 커밋 | 탐색이 빈 경로 반환 | `No path` |
| 검색 결과 없음 | 빈 커밋 목록 반환 | `Found 0 commit(s)` 다음 `No commits` |
| `EXIT`·`QUIT` | `execute()`가 `False` 반환 | 입력 루프 종료 |
| EOF·Ctrl+C | `main()`에서 종료 예외 처리 | 줄바꿈 후 입력 루프 종료 |

존재하지 않는 커밋과 경로가 없는 커밋은 다르게 처리합니다. 먼저 두 hash가 존재하는지 검사한 뒤에 탐색하므로, 잘못된 hash를 단순한 `No path`로 감추지 않습니다.

초기화 여부 검사는 저장소 기능에서 수행합니다. 따라서 INIT 전에도 HELP·EXIT·QUIT와 빈 입력 처리는 가능하지만, 커밋·브랜치 변경과 저장소 조회는 거부됩니다.

### 아래 줄별 표를 읽는 기준

줄 번호는 현재 Python 원본의 실제 번호입니다. 각 표는 하나의 역할이나 처리 단계만 묶으며 **의미 있는 각 소스 줄의 개별 해설은 모두 유지**합니다.

import는 위에서 역할을 설명하고 표에서는 제외합니다. 빈 줄·순수 주석·독스트링·닫는 구분자만 있는 줄도 제외합니다. `HELP_TEXT`는 화면에 표시할 데이터이므로 내용 줄을 개별로 설명합니다. 표에서는 들여쓰기를 줄여 표시하지만 소스 파일은 바꾸지 않습니다.

<a id="main"></a>

## 4. main.py — 입력과 화면 출력

이 파일의 핵심은 명령을 해석해 적절한 저장소 기능을 호출하는 것입니다. 검색·탐색 알고리즘 자체를 이곳에서 구현하지 않습니다.

### 4-1. 프롬프트·옵션·도움말

자주 쓰는 문자열을 상수로 둡니다. HELP_TEXT의 각 줄은 실행할 명령이 아니라 HELP를 눌렀을 때 표시할 데이터입니다.

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

### 4-2. require_args(): 실행 전에 인자 검사

개수만 맞는지 보지 않고 빈 문자열과 공백뿐인 값도 거부합니다. 검증을 통과한 뒤에 저장소 기능을 호출합니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 24 | `def require_args(args, count):` | 인자 목록과 기대 개수를 받는 공통 검증 함수를 정의합니다. 아직 검증을 실행하지는 않습니다. |
| 26 | `if len(args) != count:` | 전달된 인자 수가 명령에서 요구하는 개수와 다른지 확인합니다. |
| 27 | `raise ValueError("Invalid args")` | 잘못된 입력을 ValueError로 알리고 현재 명령의 실행을 중단합니다. |
| 29 | `for value in args:` | 개수가 맞으면 각 인자의 내용을 하나씩 확인합니다. |
| 30 | `if not value.strip():` | 빈 문자열 또는 공백만 있는 인자인지 검사합니다. |
| 31 | `raise ValueError("Invalid args")` | 잘못된 입력을 ValueError로 알리고 현재 명령의 실행을 중단합니다. |

### 4-3. print_commits(): 커밋 목록을 화면에 표시

조회한 커밋을 공통 형식으로 출력합니다. 빈 결과와 날짜 형식을 한곳에서 처리하므로 LOG·SEARCH·ANCESTORS의 출력이 일관됩니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 34 | `def print_commits(commits):` | 커밋 객체 목록을 받아 화면에 표시하는 함수를 정의합니다. |
| 36 | `if not commits:` | 목록이 비어 있는지 확인합니다. 빈 목록은 조건식에서 거짓으로 취급됩니다. |
| 37 | `print("No commits")` | 빈 조회 결과라는 문구를 출력합니다. |
| 38 | `return` | 현재 함수의 처리를 마칩니다. 명시된 반환값은 없으므로 None입니다. |
| 40 | `for commit in commits:` | 조회 결과에서 커밋 객체를 하나씩 꺼냅니다. |
| 41 | `timestamp = commit.timestamp.isoformat(timespec="microseconds")` | 커밋 시각을 마이크로초와 시간대가 표시되는 ISO 문자열로 바꿉니다. |
| 42 | `print(f"commit {commit.hash} ({commit.author}, {timestamp})")` | 커밋 hash, 작성자, 시각을 한 줄에 출력합니다. |
| 43 | `print(f"  {commit.message}")` | 해당 커밋의 메시지를 다음 줄에 출력합니다. |

### 4-4. execute() ① 입력 분리와 명령 정규화

따옴표를 해석해 명령과 인자를 나눈 뒤 명령 이름만 대문자로 통일합니다. 짝이 맞지 않는 따옴표는 표준 오류 문구로 바꿉니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 46 | `def execute(repository, line):` | 저장소 객체와 입력 한 줄을 받아 명령을 실행하는 함수를 정의합니다. |
| 48 | `try:` | 따옴표 파싱에서 발생할 수 있는 오류를 처리할 범위를 시작합니다. |
| 49 | `tokens = shlex.split(line)` | shlex.split은 따옴표 안의 공백을 유지하면서 입력을 명령·인자 토큰으로 나눕니다. |
| 50 | `except ValueError:` | 짝이 맞지 않는 따옴표 등 shlex의 ValueError를 받습니다. |
| 51 | `raise ValueError("Invalid args") from None` | 파서의 상세 오류 대신 미션의 Invalid args로 바꿉니다. from None은 이전 예외의 연결 표시를 숨깁니다. |
| 53 | `if not tokens:` | 입력이 빈 줄이거나 공백뿐이라 토큰이 없는지 확인합니다. |
| 54 | `return True` | 빈 입력은 아무것도 변경하지 않고 계속 실행하라는 True를 반환합니다. |
| 56 | `command = tokens[0].upper()` | 첫 토큰인 명령어만 대문자로 바꿔 명령의 대소문자 구분을 없앱니다. |
| 57 | `args = tokens[1:]` | 두 번째 토큰부터 마지막까지를 인자 목록으로 분리합니다. |

### 4-5. execute() ② 종료와 도움말

종료는 False, 도움말은 True를 반환합니다. 이 반환값을 바깥 입력 루프가 사용합니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 59 | `if command in ("EXIT", "QUIT"):` | 프로그램을 종료하는 명령인지 확인합니다. |
| 60 | `require_args(args, 0)` | 도움말 또는 종료 명령 뒤에 추가 인자가 없는지 확인합니다. |
| 61 | `return False` | REPL을 종료하라는 뜻으로 False를 반환합니다. |
| 63 | `if command == "HELP":` | HELP 명령인지 확인합니다. |
| 64 | `require_args(args, 0)` | 도움말 또는 종료 명령 뒤에 추가 인자가 없는지 확인합니다. |
| 65 | `print(HELP_TEXT)` | 미리 저장한 여러 줄 도움말을 화면에 출력합니다. |
| 66 | `return True` | 도움말 이후에는 REPL을 계속해야 하므로 True를 반환합니다. |

### 4-6. execute() ③ 명령별 처리로 연결

명령마다 필요한 검증과 출력 담당을 고릅니다. 지원하지 않는 명령은 이름을 포함한 오류로 알립니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 68 | `if command == "LOG":` | 로그 명령인지 확인합니다. |
| 69 | `handle_log(repository, args)` | 옵션 검증과 로그 출력을 handle_log에 위임합니다. |
| 71 | `elif command == "SEARCH":` | 앞 조건이 아니고 SEARCH 명령인지 확인합니다. |
| 72 | `handle_search(repository, args)` | 키워드·작성자 검색 분기와 출력을 handle_search에 위임합니다. |
| 74 | `elif command == "PATH":` | PATH 명령인지 확인합니다. |
| 75 | `handle_path(repository, args)` | 경로 명령의 인자 검증과 출력을 전용 처리 함수에 맡깁니다. |
| 77 | `elif command in ("INIT", "BRANCH", "SWITCH", "COMMIT", "ANCESTORS"):` | 인자 하나를 받는 다섯 가지 명령 중 하나인지 검사합니다. |
| 78 | `require_args(args, 1)` | 공백뿐인 값이 아닌 인자 하나가 전달되었는지 확인합니다. |
| 79 | `handle_single_arg(repository, command, args[0])` | 명령 종류와 실제 인자 하나를 공통 처리 함수에 전달합니다. |
| 81 | `else:` | 지금까지 어느 지원 명령에도 해당하지 않는 경우입니다. |
| 82 | `raise ValueError(f"Unknown command: {tokens[0]}")` | 입력한 명령 이름을 포함한 오류를 발생시킵니다. |
| 84 | `return True` | 정상 명령을 마친 뒤 다음 입력을 받으라는 True를 반환합니다. |

### 4-7. handle_log(): 기본 조회와 옵션 조회 분리

옵션이 없으면 부모 우선 로그를 요청합니다. 옵션이 있으면 접두사를 제거한 date 또는 author 값을 저장소에 넘깁니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 87 | `def handle_log(repository, args):` | LOG의 선택 옵션을 해석하는 함수를 정의합니다. |
| 89 | `if not args:` | 추가 인자가 없는 기본 LOG인지 확인합니다. |
| 90 | `print_commits(repository.log())` | 위상 순서의 커밋 목록을 반환받아 화면에 출력합니다. |
| 91 | `return` | 현재 함수의 처리를 마칩니다. 명시된 반환값은 없으므로 None입니다. |
| 93 | `require_args(args, 1)` | 옵션은 한 토큰만 허용하므로 인자 개수와 빈 값을 검사합니다. |
| 94 | `if not args[0].startswith(SORT_OPTION):` | 유일한 인자가 정해진 --sort-by=로 시작하는지 확인합니다. |
| 95 | `raise ValueError("Invalid args")` | 잘못된 입력을 ValueError로 알리고 현재 명령의 실행을 중단합니다. |
| 97 | `sort_by = args[0][len(SORT_OPTION):]` | 옵션 접두사의 길이만큼 앞을 잘라 date 또는 author 부분을 추출합니다. |
| 98 | `print_commits(repository.log(sort_by))` | 저장소에서 기준 값의 유효성을 검사하고 직접 병합 정렬한 결과를 출력합니다. |

### 4-8. handle_search(): 키워드와 작성자 구분

작성자 옵션을 확인한 뒤 접두사를 잘라냅니다. 실제 후보 검색은 저장소에 맡기고 결과 건수와 커밋을 출력합니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 101 | `def handle_search(repository, args):` | SEARCH 인자 하나를 키워드 또는 작성자 검색으로 해석하는 함수를 정의합니다. |
| 103 | `require_args(args, 1)` | 검색 인자가 정확히 하나이고 빈 문자열이 아닌지 확인합니다. |
| 104 | `value = args[0]` | 검색 토큰 하나를 value에 저장합니다. |
| 105 | `by_author = value.startswith(AUTHOR_OPTION)` | --author=로 시작하는지 검사한 논리값을 by_author에 저장합니다. |
| 107 | `if by_author:` | 작성자 검색이라면 옵션 부분을 제거하는 처리를 합니다. |
| 108 | `value = value[len(AUTHOR_OPTION):]` | --author= 다음의 실제 이름만 잘라 value를 갱신합니다. 이름 안 공백은 파서에서 보존되어 있습니다. |
| 109 | `elif value.startswith("--"):` | 작성자 옵션은 아닌데 --로 시작하면 지원하지 않는 옵션으로 판단합니다. |
| 110 | `raise ValueError("Invalid args")` | 잘못된 입력을 ValueError로 알리고 현재 명령의 실행을 중단합니다. |
| 112 | `if not value.strip():` | 빈 문자열 또는 공백만 있는 인자인지 검사합니다. |
| 113 | `raise ValueError("Invalid args")` | 잘못된 입력을 ValueError로 알리고 현재 명령의 실행을 중단합니다. |
| 115 | `results = repository.search(value, by_author)` | value와 검색 종류를 저장소에 전달해 커밋 결과 목록을 받습니다. 검색은 전체 커밋을 순회하지 않습니다. |
| 116 | `print(f"Found {len(results)} commit(s)")` | 결과 목록의 길이를 이용해 검색 건수를 출력합니다. |
| 117 | `print_commits(results)` | 찾은 커밋의 필드를 화면에 출력합니다. 결과가 없으면 공통 출력 함수가 No commits를 표시합니다. |

### 4-9. handle_path(): 경로 목록을 출력 문구로 변환

두 인자를 검증하고 반환된 경로를 화살표로 연결합니다. 빈 경로는 별도로 표시합니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 120 | `def handle_path(repository, args):` | PATH 명령의 인자를 검증하고 경로를 출력하는 함수를 정의합니다. |
| 122 | `require_args(args, 2)` | 출발점과 목표점 hash 두 개를 받았는지 검증합니다. |
| 123 | `start, target = args` | 첫 번째 인자를 출발점, 두 번째 인자를 목표점으로 나눠 이름을 붙입니다. |
| 124 | `path = repository.path(start, target)` | 저장소에서 두 커밋의 존재를 확인하고 최단 경로 hash 목록을 받습니다. |
| 126 | `if not path:` | 두 커밋을 연결하는 경로가 없는지 확인합니다. |
| 127 | `print("No path")` | 연결된 경로가 없다는 문구를 출력합니다. |
| 128 | `return` | 현재 함수의 처리를 마칩니다. 명시된 반환값은 없으므로 None입니다. |
| 130 | `print("Path: " + " -> ".join(path))` | 경로의 hash들을 화살표로 이어 화면에 출력합니다. |

### 4-10. handle_single_arg(): 인자 하나를 받는 명령

저장소의 상태 변경이 성공한 뒤 해당 결과를 표시합니다. ANCESTORS는 상태를 바꾸지 않는 조회입니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 133 | `def handle_single_arg(repository, command, value):` | 인자 하나로 처리하는 명령들의 실행과 결과 출력을 연결하는 함수를 정의합니다. |
| 135 | `if command == "INIT":` | 초기화 명령인지 확인합니다. |
| 136 | `repository.initialize(value)` | 저장소에 사용자 이름을 전달하여 main·HEAD·현재 사용자를 설정합니다. |
| 137 | `print("Initialized repository.")` | 초기화 성공 메시지를 출력합니다. |
| 138 | `print(f"Current branch: {repository.current_branch}")` | 설정된 현재 브랜치 이름을 출력합니다. |
| 139 | `print(f"Current user: {repository.user}")` | 설정된 사용자 이름을 출력합니다. |
| 141 | `elif command == "BRANCH":` | 브랜치 생성 명령인지 확인합니다. |
| 142 | `repository.create_branch(value)` | 현재 커밋을 가리키는 브랜치를 생성합니다. 저장소 상태가 바뀝니다. |
| 143 | `print(f"Created branch: {value}")` | 성공적으로 생성한 브랜치 이름을 출력합니다. |
| 145 | `elif command == "SWITCH":` | 브랜치 전환 명령인지 확인합니다. |
| 146 | `repository.switch_branch(value)` | 저장소에서 현재 브랜치를 변경합니다. 존재하지 않으면 여기서 예외가 발생합니다. |
| 147 | `print(f"Switched to branch: {value}")` | 전환 성공과 대상 브랜치를 출력합니다. |
| 149 | `elif command == "COMMIT":` | 커밋 생성 명령인지 확인합니다. |
| 150 | `commit = repository.commit(value)` | 커밋을 생성하고 반환된 Commit 객체를 받습니다. |
| 151 | `print(f"[{repository.current_branch} {commit.hash}] {commit.message}")` | 현재 브랜치와 새 커밋의 hash, 메시지를 출력합니다. |
| 153 | `elif command == "ANCESTORS":` | 조상 조회 명령임을 명시적으로 확인합니다. |
| 154 | `print_commits(repository.ancestors(value))` | 해당 hash의 조상 객체 목록을 반환받아 출력합니다. |

### 4-11. main(): 저장소 하나로 입력 루프 유지

입력 오류는 출력 후 다음 반복으로 이어가고, 정상 종료 요청·EOF·Ctrl+C는 루프를 끝냅니다. 파일을 직접 실행할 때만 이 루프를 시작합니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 157 | `def main():` | 입력·실행·출력 루프의 시작 함수를 정의합니다. |
| 159 | `repository = Repository()` | 프로그램이 살아 있는 동안 사용할 저장소 객체 하나를 만듭니다. |
| 161 | `while True:` | 종료 요청이 있을 때까지 입력을 반복합니다. |
| 162 | `try:` | 각 입력·실행 과정의 사용자 입력 오류와 종료 신호를 처리할 범위를 시작합니다. |
| 163 | `line = input(PROMPT)` | 프롬프트를 표시하고 사용자가 입력한 한 줄을 문자열로 받습니다. |
| 164 | `if not execute(repository, line):` | execute가 False를 반환했는지 확인합니다. True이면 다음 반복으로 이어집니다. |
| 165 | `break` | EXIT·QUIT 요청이므로 while 반복문을 끝냅니다. |
| 167 | `except ValueError as error:` | 파싱·명령 실행 중 발생한 ValueError를 error라는 이름으로 받습니다. |
| 168 | `print(error)` | 오류 문구를 출력합니다. 반복문 밖으로 나가지 않으므로 다음 입력을 받습니다. |
| 170 | `except (EOFError, KeyboardInterrupt):` | 입력 종료인 EOF 또는 Ctrl+C의 KeyboardInterrupt를 처리합니다. |
| 171 | `print()` | 프롬프트 뒤에 줄바꿈을 출력해 종료 화면을 정리합니다. |
| 172 | `break` | EOF·Ctrl+C라면 입력 루프를 끝냅니다. |
| 175 | `if __name__ == "__main__":` | 이 파일을 직접 실행했는지 검사합니다. 다른 코드에서 import할 때는 REPL을 자동 실행하지 않습니다. |
| 176 | `main()` | 직접 실행한 경우 main 함수를 호출해 프로그램을 시작합니다. |

<a id="repository"></a>

## 5. repository.py — 저장소 상태와 기능 연결

이 파일에서 INIT·BRANCH·SWITCH·COMMIT은 저장소 상태를 바꿉니다. LOG·PATH·ANCESTORS·SEARCH는 기존 상태를 읽어 새 조회 결과를 반환합니다.

### 5-1. 커밋 필드와 식별자 규칙

frozen=True는 일반적인 필드 재대입을 막고 parents는 튜플로 보관합니다. 저장소의 딕셔너리 전체까지 불변으로 만드는 설정은 아닙니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 10 | `DEFAULT_BRANCH = "main"` | 초기 브랜치 이름 main을 의미 있는 상수로 지정합니다. |
| 11 | `HASH_WIDTH = 8` | hash의 최소 표시 폭을 8자리로 지정합니다. 상한 자릿수가 아닙니다. |
| 14 | `@dataclass(frozen=True)` | dataclass가 필드 기반 생성자 등을 만들도록 하고 frozen=True로 필드 재대입을 막습니다. |
| 15 | `class Commit:` | 커밋 메타데이터를 보관할 Commit 클래스를 선언합니다. |
| 18 | `hash: str` | hash 필드가 문자열이라는 타입 힌트를 선언합니다. |
| 19 | `message: str` | message 필드가 커밋 메시지 문자열이라는 것을 선언합니다. |
| 20 | `author: str` | author 필드가 작성자 문자열이라는 것을 선언합니다. |
| 21 | `timestamp: datetime` | timestamp 필드가 datetime 객체라는 것을 선언합니다. |
| 22 | `parents: tuple[str, ...]` | parents가 문자열 hash를 0개 이상 담는 튜플임을 나타냅니다. ...는 같은 타입의 가변 개수를 뜻합니다. |

### 5-2. Repository 생성: 서로 다른 조회표 준비

commits는 hash 조회, branches는 이름별 현재 위치, children은 부모→자식, neighbors는 양방향 탐색을 맡습니다. 같은 커밋 관계를 기능에 맞는 관점으로 저장합니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 25 | `class Repository:` | 저장소의 상태와 그 상태를 바꾸는 동작을 묶는 클래스를 선언합니다. |
| 28 | `def __init__(self):` | Repository 객체를 만들 때 초기 상태를 구성하는 생성자를 정의합니다. |
| 29 | `self.user = None` | 초기화 전에는 작성자가 없음을 None으로 표시합니다. |
| 30 | `self.current_branch = None` | 초기화 전에는 현재 브랜치가 없음을 None으로 표시합니다. |
| 32 | `self.commits = {}` | hash로 Commit 객체를 직접 찾는 딕셔너리를 만듭니다. |
| 33 | `self.branches = {}` | 브랜치 이름에서 커밋 hash 또는 None으로 연결하는 딕셔너리를 만듭니다. |
| 34 | `self.children = {}` | 각 커밋의 자식 hash 목록을 보관할 표를 만듭니다. 위상 정렬에 사용합니다. |
| 35 | `self.neighbors = {}` | 각 커밋의 부모와 자식을 함께 보관할 무방향 이웃 표를 만듭니다. PATH에 사용합니다. |
| 37 | `self.index = InvertedIndex()` | 키워드·작성자 검색을 전담하는 역색인 객체를 만듭니다. |
| 38 | `self.next_commit_id = 1` | 새 커밋의 식별자를 만들 증가 카운터를 1부터 시작합니다. |

### 5-3. 초기화 검사와 INIT

초기화 전 변경·조회를 막고, 반복 INIT는 기존 이력을 지우는 대신 거부합니다. 처음 main은 존재하지만 가리키는 커밋은 없습니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 40 | `def require_initialized(self):` | 저장소가 INIT되었는지 확인하는 공통 메서드를 정의합니다. |
| 42 | `if self.user is None:` | 현재 사용자 값이 None이면 초기화 전으로 판단합니다. |
| 43 | `raise ValueError("Repository not initialized")` | 초기화가 필요한 명령의 실행을 오류로 중단합니다. |
| 45 | `def initialize(self, user):` | 현재 사용자와 초기 브랜치를 설정할 메서드를 정의합니다. |
| 47 | `if self.user is not None:` | 이미 사용자가 설정되어 초기화된 저장소인지 검사합니다. |
| 48 | `raise ValueError("Repository already initialized")` | 다시 INIT해서 기존 데이터를 지우지 않도록 오류를 발생시킵니다. |
| 50 | `self.user = user` | 전달받은 사용자 이름을 저장소 상태에 기록합니다. |
| 51 | `self.current_branch = DEFAULT_BRANCH` | 현재 브랜치를 main으로 지정합니다. |
| 52 | `self.branches[DEFAULT_BRANCH] = None` | main 브랜치를 등록하되 아직 커밋이 없으므로 참조를 None으로 둡니다. |

### 5-4. BRANCH와 SWITCH: 이름 추가와 현재 위치 변경

BRANCH는 현재 hash를 공유하는 이름을 추가하고, SWITCH는 현재 브랜치 이름만 바꿉니다. 두 동작 모두 새 커밋을 만들지 않습니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 54 | `def create_branch(self, name):` | 현재 위치를 공유하는 브랜치를 만드는 메서드를 정의합니다. |
| 56 | `self.require_initialized()` | 브랜치를 만들기 전에 초기화 여부를 확인합니다. |
| 57 | `if name in self.branches:` | 동일한 이름의 브랜치가 이미 있는지 딕셔너리 키로 검사합니다. |
| 58 | `raise ValueError(f"Branch already exists: {name}")` | 중복 이름을 덮어쓰지 않고 오류를 알립니다. |
| 60 | `self.branches[name] = self.branches[self.current_branch]` | 현재 브랜치가 가리키는 hash를 새 브랜치에 저장합니다. 커밋 객체를 복사하지 않습니다. |
| 62 | `def switch_branch(self, name):` | 현재 브랜치를 옮기는 메서드를 정의합니다. |
| 64 | `self.require_initialized()` | 전환에 앞서 저장소 초기화를 확인합니다. |
| 65 | `if name not in self.branches:` | 이동할 브랜치 이름이 등록되어 있지 않은지 검사합니다. |
| 66 | `raise ValueError(f"Unknown branch: {name}")` | 존재하지 않는 브랜치 이름을 포함한 오류를 발생시킵니다. |
| 68 | `self.current_branch = name` | 현재 브랜치 이름을 바꿉니다. 기존 커밋의 부모나 메시지는 변경하지 않습니다. |

### 5-5. get_commit(): 전체 hash의 존재 검사

커밋의 실제 존재 여부를 확인하는 공통 경로입니다. PATH는 출발점과 목적지 모두 이 검사를 거칩니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 70 | `def get_commit(self, commit_hash):` | 전체 hash 하나로 커밋을 조회하는 메서드를 정의합니다. |
| 72 | `if commit_hash not in self.commits:` | 정확한 hash 키가 커밋 표에 없는지 확인합니다. |
| 73 | `raise ValueError(f"Unknown commit: {commit_hash}")` | 해당 hash가 없다는 오류를 발생시킵니다. |
| 75 | `return self.commits[commit_hash]` | 딕셔너리에서 찾은 Commit 객체를 호출자에게 반환합니다. 화면 출력은 하지 않습니다. |

### 5-6. COMMIT ① 부모·식별자·메타데이터 생성

현재 브랜치의 기존 커밋을 부모로 고릅니다. 식별자는 증가 카운터이며 메시지 내용을 암호학적으로 요약한 값이 아닙니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 77 | `def commit(self, message):` | 메시지를 받아 새 커밋을 생성하는 메서드를 정의합니다. |
| 79 | `self.require_initialized()` | 커밋을 만들기 전에 저장소 초기화를 확인합니다. |
| 81 | `parent = self.branches[self.current_branch]` | 현재 브랜치가 가리키는 커밋 hash를 부모 후보로 가져옵니다. |
| 82 | `parents = () if parent is None else (parent,)` | 첫 커밋이면 부모 없는 빈 튜플, 아니면 부모 hash 하나의 튜플을 만듭니다. |
| 85 | `commit_hash = f"{self.next_commit_id:0{HASH_WIDTH}x}"` | 증가 정수를 16진수로 표시하고 최소 폭까지 0으로 채웁니다. 카운터를 재사용하지 않고 자릿수를 잘라내지 않는 정상 생성 흐름에서 식별자가 겹치지 않습니다. |
| 86 | `commit = Commit(` | 필드 이름을 명시하는 방식으로 새 Commit 객체 생성을 시작합니다. |
| 87 | `hash=commit_hash,` | 생성한 식별자를 hash 필드에 전달합니다. |
| 88 | `message=message,` | 사용자가 입력한 메시지를 message 필드에 전달합니다. |
| 89 | `author=self.user,` | 현재 사용자를 작성자로 전달합니다. |
| 90 | `timestamp=datetime.now(timezone.utc),` | 시간대가 명시된 현재 UTC 시각을 커밋 시각으로 전달합니다. |
| 91 | `parents=parents,` | 앞에서 정한 부모 hash 튜플을 전달합니다. |
| 93 | `self.next_commit_id += 1` | 다음 커밋에서 같은 숫자를 쓰지 않도록 카운터를 1 올립니다. |

### 5-7. COMMIT ② 그래프·역색인·브랜치 갱신

새 커밋과 양방향 이웃을 등록한 뒤 색인을 갱신하고 현재 브랜치를 이동합니다. 여러 자료구조가 같은 커밋을 가리키도록 함께 유지해야 합니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 95 | `self.commits[commit_hash] = commit` | 새 hash를 키로 커밋 객체를 등록합니다. |
| 96 | `self.children[commit_hash] = []` | 새 커밋은 아직 자식이 없으므로 자식 목록을 빈 리스트로 등록합니다. |
| 97 | `self.neighbors[commit_hash] = list(parents)` | 새 커밋의 무방향 이웃 목록을 부모 목록으로 초기화합니다. |
| 99 | `for parent_hash in parents:` | 부모 hash들을 하나씩 처리합니다. 필수 COMMIT은 0개 또는 1개입니다. |
| 100 | `self.children[parent_hash].append(commit_hash)` | 부모의 자식 목록에 새 커밋 hash를 추가하여 부모→자식 표를 갱신합니다. |
| 101 | `self.neighbors[parent_hash].append(commit_hash)` | 부모의 무방향 이웃에도 새 커밋을 넣어 양방향 이동이 되게 합니다. |
| 103 | `self.index.add(commit)` | 새 커밋의 메시지 단어와 작성자를 역색인에 등록합니다. |
| 104 | `self.branches[self.current_branch] = commit_hash` | 현재 브랜치의 참조를 새 커밋으로 옮깁니다. 다른 브랜치는 그대로입니다. |
| 105 | `return commit` | 생성한 Commit 객체를 호출자에게 반환합니다. |

### 5-8. LOG: 위상 순서 또는 비교 기준 정렬

기본 LOG와 옵션 LOG는 서로 다른 조회 방식입니다. 기본은 전체 저장소의 부모 우선 순서이고 옵션은 시각·작성자 기준의 안정 병합 정렬입니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 107 | `def log(self, sort_by=None):` | 정렬 기준을 선택적으로 받는 로그 조회 메서드를 정의합니다. 기본값 None은 기본 LOG입니다. |
| 109 | `self.require_initialized()` | 조회 전에 INIT 여부를 확인합니다. |
| 111 | `if sort_by is None:` | 정렬 옵션이 없는 기본 LOG인지 검사합니다. |
| 112 | `hashes = topological_order(self.commits, self.children)` | 모든 커밋과 자식 표를 넘겨 부모 우선의 hash 목록을 받습니다. |
| 113 | `return [self.commits[commit_hash] for commit_hash in hashes]` | 순서대로 받은 hash를 각각 Commit 객체로 조회해 목록으로 반환합니다. |
| 115 | `if sort_by not in ("date", "author"):` | 옵션이 있는데 date도 author도 아니면 잘못된 인자로 판단합니다. |
| 116 | `raise ValueError("Invalid args")` | 지원하지 않는 정렬 기준을 Invalid args로 거부합니다. |
| 118 | `field = "timestamp" if sort_by == "date" else "author"` | date 옵션은 객체의 timestamp 속성으로, author 옵션은 author 속성으로 연결합니다. |
| 119 | `return merge_sort(` | 정렬한 새 목록을 반환하도록 직접 구현한 병합 정렬을 호출합니다. |
| 120 | `list(self.commits.values()),` | 전체 커밋 객체를 생성 순서의 목록으로 복사해 정렬 대상으로 전달합니다. |
| 121 | `key=lambda commit: getattr(commit, field),` | 선택된 timestamp 또는 author 속성을 정렬 비교 값으로 사용합니다. |

### 5-9. PATH와 ANCESTORS: 존재 검사 후 탐색

PATH는 양방향 이웃을, ANCESTORS는 커밋의 부모 정보를 사용합니다. 알고리즘이 돌려준 hash를 필요에 따라 커밋 객체로 바꿉니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 124 | `def path(self, start, target):` | 두 커밋 사이의 경로를 조회하는 메서드를 정의합니다. |
| 126 | `self.require_initialized()` | PATH를 실행하기 전에 초기화 여부를 검사합니다. |
| 127 | `self.get_commit(start)` | 출발 hash가 실제 커밋인지 검사합니다. 없으면 예외가 납니다. |
| 128 | `self.get_commit(target)` | 목적지 hash도 존재하는지 검사합니다. 없는 노드와 연결되지 않은 노드를 구분합니다. |
| 130 | `return shortest_path(self.neighbors, start, target)` | 무방향 이웃 표를 탐색 함수에 넘기고 경로 hash 목록을 그대로 반환합니다. |
| 132 | `def ancestors(self, commit_hash):` | 특정 커밋의 조상 객체 목록을 구하는 메서드를 정의합니다. |
| 134 | `self.require_initialized()` | 조상 조회 전 초기화 여부를 검사합니다. |
| 135 | `self.get_commit(commit_hash)` | 시작 커밋이 있는지 확인합니다. |
| 137 | `hashes = find_ancestors(self.commits, commit_hash)` | 부모 방향 DFS로 찾은 조상 hash 목록을 받습니다. |
| 138 | `return [self.commits[ancestor_hash] for ancestor_hash in hashes]` | DFS로 찾은 조상 hash를 커밋 객체 목록으로 바꾸어 반환합니다. |

### 5-10. SEARCH: 인덱스 후보만 커밋 객체로 조회

전체 커밋을 다시 순회하지 않습니다. 단어 또는 작성자 색인에서 받은 hash만 조회하고, 결과를 화면에 표시하는 일은 CLI에 맡깁니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 140 | `def search(self, value, by_author=False):` | 검색어와 검색 종류를 받는 메서드를 정의합니다. 기본값 False는 메시지 검색입니다. |
| 142 | `self.require_initialized()` | 검색을 시작하기 전에 INIT 여부를 확인합니다. |
| 144 | `if by_author:` | 작성자 검색이 요청되었는지 확인합니다. |
| 145 | `hashes = self.index.search_author(value)` | 작성자 역색인에서 해당 이름의 커밋 hash 목록을 받습니다. |
| 146 | `else:` | 작성자 검색이 아니면 메시지 키워드 검색을 수행합니다. |
| 147 | `hashes = self.index.search_keyword(value)` | 단어 역색인에서 조건에 맞는 커밋 hash 목록을 받습니다. |
| 149 | `return [self.commits[commit_hash] for commit_hash in hashes]` | 순서대로 받은 hash를 각각 Commit 객체로 조회해 목록으로 반환합니다. |

<a id="index"></a>

## 6. index.py — 역색인 등록과 조회

등록 때 검색용 정보를 추가로 정리해 두고 조회 때 후보를 좁힙니다. 단어는 소문자로 정규화하지만 작성자는 원래 전체 이름을 키로 씁니다.

### 6-1. 검색 표 준비

단어와 작성자를 별도 표로 관리합니다. 각 값은 그 조건에 해당하는 커밋 hash 목록입니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 4 | `class InvertedIndex:` | 키워드·작성자 역색인을 담당하는 클래스를 선언합니다. |
| 7 | `def __init__(self):` | 인덱스 객체를 만들 때 빈 검색 표를 준비하는 생성자를 정의합니다. |
| 8 | `self.keywords = {}` | 메시지 토큰에서 커밋 hash 목록으로 연결하는 딕셔너리를 만듭니다. |
| 9 | `self.authors = {}` | 작성자 이름에서 커밋 hash 목록으로 연결하는 딕셔너리를 만듭니다. |

### 6-2. add(): 같은 단어는 한 커밋당 한 번만 등록

메시지를 공백으로 나누고 중복 단어를 제거합니다. 한 단어의 목록에는 새 커밋 hash를 뒤에 붙이므로 생성 순서가 유지됩니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 11 | `def add(self, commit):` | 새 커밋 하나를 역색인 두 곳에 등록하는 메서드를 정의합니다. |
| 13 | `for word in set(commit.message.lower().split()):` | 메시지를 소문자·공백 토큰으로 바꾸고 set으로 중복 단어를 제거한 뒤 각 단어를 처리합니다. |
| 14 | `self.keywords.setdefault(word, []).append(commit.hash)` | 처음 본 단어이면 빈 목록을 만든 후 해당 커밋 hash를 뒤에 추가합니다. 기존 단어이면 기존 목록을 씁니다. |
| 16 | `self.authors.setdefault(commit.author, []).append(commit.hash)` | 작성자 이름에도 같은 방식으로 커밋 hash를 추가합니다. 이름의 대소문자는 변환하지 않습니다. |

### 6-3. search_keyword() ① 정규화와 후보 선택

등록과 같은 규칙으로 검색어를 나누고 가장 짧은 목록을 고릅니다. min은 최솟값 하나를 선택하며 목록 전체를 정렬하지 않습니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 18 | `def search_keyword(self, keyword):` | 공백으로 구분된 하나 이상의 검색 단어를 처리하는 메서드를 정의합니다. |
| 20 | `words = list(set(keyword.lower().split()))` | 검색어를 등록 때와 같은 규칙으로 정규화하고 중복을 제거한 뒤 목록으로 바꿉니다. |
| 21 | `if not words:` | 검색 토큰이 하나도 없는지 검사합니다. |
| 22 | `return []` | 아무 토큰도 없으면 결과 없는 빈 목록을 반환합니다. |
| 24 | `postings = [self.keywords.get(word, []) for word in words]` | 각 단어의 후보 hash 목록을 가져옵니다. 없는 단어는 빈 목록으로 처리해 KeyError를 막습니다. |
| 26 | `smallest = min(postings, key=len)` | len을 비교 기준으로 사용해 가장 짧은 후보 목록을 고릅니다. min은 전체를 정렬하지 않고 최솟값만 고릅니다. |
| 27 | `posting_sets = [set(values) for values in postings]` | 각 후보 목록을 포함 여부 검사가 빠른 집합으로 복사합니다. |

### 6-4. search_keyword() ② 모든 단어의 교집합

가장 짧은 목록만 순회하면서 모든 단어의 후보 집합에 들어 있는 hash를 고릅니다. 후보가 적어도 목록을 집합으로 복사하는 비용은 발생합니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 29 | `return [` | 검색 조건을 만족하는 hash로 새 결과 목록을 구성해 반환합니다. |
| 30 | `commit_hash` | 조건을 통과한 hash를 결과 목록의 원소로 사용합니다. |
| 31 | `for commit_hash in smallest` | 가장 짧은 후보 목록을 원래 순서대로 확인합니다. |
| 32 | `if all(commit_hash in posting_set for posting_set in posting_sets)` | 모든 검색 단어의 후보 집합에 속한 hash만 선택하여 AND 검색을 수행합니다. |

### 6-5. search_author(): 이름 조회 후 목록 복사

작성자 전체 이름을 그대로 조회합니다. 결과를 수정해도 원래 인덱스 목록이 바뀌지 않도록 복사본을 반환합니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 35 | `def search_author(self, author):` | 작성자 전체 이름으로 조회하는 메서드를 정의합니다. |
| 37 | `return list(self.authors.get(author, []))` | 해당 작성자의 목록을 찾아 복사본을 반환합니다. 외부에서 결과를 바꾸어도 원본 인덱스가 수정되지 않습니다. |

<a id="algorithms"></a>

## 7. algorithms.py — 정렬과 그래프 탐색

각 함수는 입력 그래프·목록을 직접 바꾸지 않고 지역 변수로 결과를 계산합니다. 큐를 쓴다는 공통점만으로 BFS와 칸 알고리즘을 같은 처리로 이해하지 않도록 목적을 먼저 확인하세요.

### 7-1. merge_sort() ① 나누기와 종료 조건

0개·1개이면 복사본을 반환하고, 그보다 길면 왼쪽과 오른쪽을 각각 재귀 정렬합니다. 각 호출이 받는 목록은 점점 짧아집니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 6 | `def merge_sort(items, key):` | 정렬 대상과 비교 값을 뽑는 함수 key를 받는 병합 정렬 함수를 정의합니다. |
| 8 | `if len(items) < 2:` | 원소 수가 0개 또는 1개인지 검사합니다. 더 나눌 필요가 없는 종료 조건입니다. |
| 9 | `return list(items)` | 입력의 복사본을 반환합니다. 짧은 목록에서도 새 결과 목록이라는 계약을 유지합니다. |
| 11 | `middle = len(items) // 2` | 정수 나눗셈으로 가운데 위치를 계산합니다. |
| 12 | `left = merge_sort(items[:middle], key)` | 왼쪽 절반을 슬라이스로 나누어 같은 기준으로 재귀 정렬합니다. |
| 13 | `right = merge_sort(items[middle:], key)` | 오른쪽 절반도 같은 기준으로 재귀 정렬합니다. |
| 15 | `merged = []` | 정렬된 두 절반을 합칠 빈 결과 목록을 만듭니다. |
| 16 | `left_index = right_index = 0` | 왼쪽·오른쪽에서 아직 선택하지 않은 첫 위치를 각각 0으로 시작합니다. |

### 7-2. merge_sort() ② 병합과 동률 처리

아직 남은 양쪽 앞 항목을 비교해 하나씩 선택합니다. 같은 key 값에서 왼쪽을 먼저 고르는 <=가 원래 상대 순서를 보존합니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 18 | `while left_index < len(left) and right_index < len(right):` | 양쪽 모두 남은 원소가 있을 동안 앞부분을 비교합니다. 둘 중 하나가 끝나면 반복도 끝납니다. |
| 19 | `if key(left[left_index]) <= key(right[right_index]):` | key를 호출한 두 값을 비교합니다. 같은 값이면 왼쪽을 고르는 <=가 안정 정렬의 핵심입니다. |
| 20 | `merged.append(left[left_index])` | 왼쪽의 현재 원소를 결과 뒤에 추가합니다. |
| 21 | `left_index += 1` | 선택한 왼쪽 원소를 다시 쓰지 않도록 왼쪽 위치를 1 올립니다. |
| 22 | `else:` | 왼쪽 키가 더 큰 경우 오른쪽 원소를 선택합니다. |
| 23 | `merged.append(right[right_index])` | 오른쪽의 현재 원소를 결과에 추가합니다. |
| 24 | `right_index += 1` | 오른쪽 위치를 다음 원소로 옮깁니다. |
| 26 | `merged.extend(left[left_index:])` | 오른쪽이 먼저 끝났을 수도 있으므로 남은 왼쪽 항목을 한 번에 덧붙입니다. |
| 27 | `merged.extend(right[right_index:])` | 왼쪽이 먼저 끝났을 수도 있으므로 남은 오른쪽 항목도 덧붙입니다. 빈 조각이면 변화가 없습니다. |
| 28 | `return merged` | 정렬을 마친 새 목록을 반환합니다. 원래 입력을 제자리 변경하지 않습니다. |

### 7-3. topological_order() ① 남은 부모 수와 큐

부모→자식 방향에서 진입 차수에 해당하는 값을 셉니다. 부모가 없는 노드부터 처리할 수 있습니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 31 | `def topological_order(commits, children):` | 커밋 표와 부모→자식 표를 받는 위상 정렬 함수를 정의합니다. |
| 33 | `remaining = {` | 각 커밋의 아직 처리하지 않은 부모 수를 저장할 표를 만듭니다. |
| 34 | `commit_hash: len(commit.parents)` | 커밋 hash를 키로 삼고 부모 수를 초기 값으로 저장합니다. |
| 35 | `for commit_hash, commit in commits.items()` | 전체 커밋 표에서 hash와 커밋 객체를 하나씩 가져옵니다. |
| 37 | `ready = deque(` | 처리 가능한 커밋들을 담을 큐를 만듭니다. |
| 38 | `commit_hash for commit_hash in commits if remaining[commit_hash] == 0` | 남은 부모 수가 0인 커밋만 생성 순서대로 큐에 넣습니다. |
| 40 | `ordered = []` | 최종 hash 순서를 모을 빈 목록을 만듭니다. |

### 7-4. topological_order() ② 부모를 처리한 뒤 자식 허용

부모 하나를 처리할 때마다 자식의 남은 수를 줄입니다. 모든 부모가 끝난 자식만 큐에 넣습니다. 순환 검출은 부모·자식 표가 일관된 그래프라는 전제를 따릅니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 42 | `while ready:` | 처리할 커밋이 큐에 남아 있는 동안 반복합니다. |
| 43 | `current = ready.popleft()` | 큐 앞에서 hash 하나를 꺼냅니다. deque.popleft는 앞을 제거할 때 전체를 이동하지 않습니다. |
| 44 | `ordered.append(current)` | 그 hash는 부모가 모두 처리되었으므로 출력 순서 결과에 추가합니다. |
| 46 | `for child in children[current]:` | 현재 커밋을 부모로 가진 각 자식을 확인합니다. |
| 47 | `remaining[child] -= 1` | 현재 부모가 처리되었으므로 해당 자식의 남은 부모 수를 하나 줄입니다. |
| 48 | `if remaining[child] == 0:` | 모든 부모가 처리되어 남은 수가 0이 되었는지 검사합니다. |
| 49 | `ready.append(child)` | 이제 출력 가능한 자식 hash를 큐 뒤에 넣습니다. |
| 51 | `if len(ordered) != len(commits):` | 처리한 수가 전체 수와 다르면 끝까지 출력할 수 없는 노드가 남았는지 확인합니다. |
| 52 | `raise ValueError("Cycle detected")` | 일관된 부모·자식 표를 전제로 순환이 있다는 오류를 알립니다. 정상 저장소 생성 경로에서는 발생하지 않습니다. |
| 54 | `return ordered` | 부모가 자식보다 앞선 hash 목록을 반환합니다. |

### 7-5. find_ancestors(): 부모 방향 DFS

시작점의 부모들로 스택을 만들고 이미 방문한 조상은 건너뜁니다. 공유 조상이 있어도 결과에는 한 번만 나오고, 시작 커밋 자신은 제외됩니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 57 | `def find_ancestors(commits, start):` | 시작 커밋의 모든 조상을 구하는 함수를 정의합니다. |
| 59 | `visited = set()` | 이미 방문한 조상을 기억할 집합을 만듭니다. |
| 60 | `stack = list(commits[start].parents)` | 시작점 자신을 제외하기 위해 그 부모 hash들로 스택을 초기화합니다. |
| 61 | `result = []` | 중복 없는 조상 방문 순서를 기록할 목록을 만듭니다. |
| 63 | `while stack:` | 탐색할 부모가 스택에 남아 있는 동안 반복합니다. |
| 64 | `current = stack.pop()` | 리스트 끝에서 하나를 꺼내 깊이 우선 탐색을 진행합니다. |
| 65 | `if current in visited:` | 공유 조상 등으로 이미 처리한 hash인지 검사합니다. |
| 66 | `continue` | 중복 노드는 결과에 다시 넣지 않고 다음 반복으로 넘어갑니다. |
| 68 | `visited.add(current)` | 처음 방문한 hash를 방문 집합에 기록합니다. |
| 69 | `result.append(current)` | 해당 조상 hash를 결과 순서 목록에 추가합니다. |
| 70 | `stack.extend(commits[current].parents)` | 현재 조상의 부모들도 스택에 넣어 더 오래된 조상을 탐색합니다. |
| 72 | `return result` | 방문한 모든 조상 hash 목록을 반환합니다. |

### 7-6. shortest_path() ① 목적지에서 거리 계산

무방향 이웃을 대상으로 목적지부터 BFS를 수행합니다. 처음 발견할 때 거리를 남겨 중복 큐 등록을 막습니다. 현재 코드는 출발점을 찾아도 연결 요소의 BFS를 끝까지 진행합니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 75 | `def shortest_path(neighbors, start, target):` | 무방향 이웃 표와 출발·목적지 hash를 받는 최단 경로 함수를 정의합니다. |
| 77 | `distance = {target: 0}` | 목적지에서 목적지까지 거리를 0으로 설정합니다. 역방향 BFS의 시작 상태입니다. |
| 78 | `queue = deque([target])` | 목적지를 첫 BFS 대기 노드로 넣습니다. |
| 80 | `while queue:` | BFS로 방문할 노드가 남아 있는 동안 반복합니다. |
| 81 | `current = queue.popleft()` | 큐 앞에서 다음 방문 노드를 꺼내 가까운 거리부터 처리합니다. |
| 82 | `for neighbor in neighbors[current]:` | 현재 노드에 직접 연결된 부모·자식 이웃을 차례로 확인합니다. |
| 83 | `if neighbor not in distance:` | 거리 표에 없는 이웃만 처음 방문합니다. 같은 노드를 반복해서 넣지 않습니다. |
| 84 | `distance[neighbor] = distance[current] + 1` | 그 이웃의 목적지까지 거리를 현재 거리에 간선 하나를 더한 값으로 기록합니다. |
| 85 | `queue.append(neighbor)` | 처음 발견한 이웃을 큐 뒤에 넣어 이후 그 이웃의 연결도 확인합니다. |
| 87 | `if start not in distance:` | BFS를 끝냈는데 출발지가 거리 표에 없으면 서로 연결되지 않은 경우입니다. |
| 88 | `return []` | 경로 없음이라는 의미로 빈 목록을 반환합니다. |

### 7-7. shortest_path() ② 거리 감소와 사전순으로 복원

출발지에서 목적지 거리가 1씩 줄어드는 이웃만 고릅니다. 이 안에서 구분자까지 붙인 문자열이 가장 작은 후보를 선택하므로 최단 조건과 사전순 동률 조건을 함께 지킵니다.

| 원본 줄 번호 | 해당 코드 | 쉬운 설명 |
| --- | --- | --- |
| 90 | `path = [start]` | 출발지만 담은 경로 목록으로 복원을 시작합니다. |
| 92 | `while path[-1] != target:` | 현재 경로의 마지막 노드가 목적지가 될 때까지 다음 노드를 선택합니다. |
| 93 | `current = path[-1]` | 현재 위치를 경로 목록의 마지막 hash로 가져옵니다. |
| 94 | `best = None` | 이번 단계에서 고를 가장 작은 후보가 아직 없음을 None으로 표시합니다. |
| 96 | `for neighbor in neighbors[current]:` | 현재 위치의 모든 이웃을 검토합니다. |
| 97 | `if distance.get(neighbor) != distance[current] - 1:` | 목적지까지 거리가 정확히 1 줄어드는 이웃인지 검사합니다. BFS가 연결 요소를 모두 탐색했으므로 일관된 이웃 표에서는 현재 노드의 이웃도 거리 표에 있습니다. |
| 98 | `continue` | 거리를 줄이지 않는 이웃은 최단 경로에 쓸 수 없으므로 건너뜁니다. |
| 101 | `if best is None or neighbor + "->" < best + "->":` | 첫 유효 후보이거나 구분자를 붙인 hash 문자열이 기존 후보보다 사전순으로 작으면 선택합니다. or의 단축 평가가 None과의 덧셈을 막습니다. |
| 102 | `best = neighbor` | 현재까지 가장 작은 유효 이웃을 best로 갱신합니다. |
| 104 | `path.append(best)` | 고른 이웃을 경로 뒤에 붙입니다. 출발지의 거리가 존재하므로 거리를 1 줄이는 이웃도 반드시 있습니다. |
| 106 | `return path` | 최소 간선 수와 사전순 동률 조건을 만족하는 경로 hash 목록을 반환합니다. |

<a id="verification"></a>

## 8. 해설 대조와 미션 범위

각 표의 원본 줄 번호와 코드 조각을 현재 소스에 대조했습니다. AST로 import·독스트링 범위를 구분하고 제외 규칙을 적용한 뒤 누락·중복·없는 번호를 확인했습니다.

| 파일 | 개별 해설 줄 수 |
| --- | --- |
| `main.py` | 116 |
| `repository.py` | 91 |
| `index.py` | 21 |
| `algorithms.py` | 69 |
| 합계 | 297 |

첨부 미션의 필수 기능·제약은 PDF 3–6쪽, 선택 과제는 5쪽에 있습니다. 현재 코드의 줄별 해설에 MERGE·DIFF·다른 정렬 알고리즘의 실행 흐름을 넣지 않은 이유는 이 기능들이 현재 구현되어 있지 않기 때문입니다. 선택 과제의 학습 방향과 필수 요구사항의 연결은 [학습 질문과 답변](study_qa.md)에서 확인하세요.

줄 번호는 소스가 바뀌면 함께 갱신해야 합니다. 이 대조는 문서와 소스의 일치를 확인한 것이며 미션의 공식 평가 통과를 뜻하지는 않습니다.
