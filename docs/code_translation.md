# Mini Git 코드 한 줄씩 읽기

## 1. 전체 구조와 실행 시작점

`python main.py`로 실행하면 main.py 맨 아래의 조건문이 `main()`을 호출합니다. `main()`은 입력을 받고 shlex로 분리한 뒤 `validate()`로 문법을 검사합니다. 종료 명령이 아니면 `execute()`가 Repository의 기능을 호출하고 결과를 출력합니다.

| 파일 | 주요 호출 관계 |
| --- | --- |
| main.py | main → validate → execute → Repository 메서드, print_commits |
| repository.py | commit → head → add_commit → require_commit / 색인 갱신 |
| repository.py | log → topological_order 또는 merge_sort |
| repository.py | path → require_commit → shortest_path |
| repository.py | ancestors → require_commit → ancestor_ids |
| algorithms.py | merge_sort만 자기 자신을 재귀 호출. 그래프 탐색은 반복문 사용 |

명령 입력 문자열과 실제 데이터 작업을 분리했습니다. repository.py는 결과를 반환하고 main.py가 화면을 담당합니다. algorithms.py는 커밋 메시지가 어떤 뜻인지 몰라도 그래프 연결과 비교 기준만으로 작업합니다.

## 2. 주요 함수의 입력·반환·상태 변화

| 함수 | 입력 | 반환 | 상태 변화와 오류 |
| --- | --- | --- | --- |
| main | 없음 | 종료 시 None | 저장소 참조 유지, 입력 오류 처리 |
| validate | 명령과 인자 목록 | 정상 시 None | 상태 변경 없음. 문법 오류는 ValueError |
| execute | 저장소 또는 None, 검증된 명령, 인자 | 저장소 객체 | 명령별 생성·변경·조회·출력. 미초기화·재초기화 오류 |
| print_commits | 저장소, 식별자 목록 | None | 화면 출력만 수행 |
| Repository.__init__ | 사용자 이름 | 자동 초기화 메서드 | main과 빈 커밋/색인 생성 |
| head | 객체 자신의 상태 | 식별자 또는 None | 조회만 수행 |
| branch / switch | 브랜치 이름 | None | 브랜치 추가 / 현재 브랜치 변경. 중복·없는 이름 오류 |
| require_commit | 식별자 | None | 없는 식별자면 ValueError |
| commit | 메시지 | 새 식별자 | 현재 HEAD를 부모로 하여 add_commit 호출 |
| add_commit | 메시지, 부모 목록 | 새 식별자 | 커밋·연결·색인·브랜치 끝점 변경. 부모 검사는 변경 전에 수행 |
| log | None/date/author | 식별자 목록 | 저장소 변경 없음. sort_by는 CLI에서 검증한 값 사용 |
| path | 출발·도착 식별자 | 경로 목록 또는 None | 없는 커밋 오류. None은 존재하지만 연결되지 않은 경우 |
| ancestors | 기준 식별자 | 조상 목록 | 자신 제외, 중복 제거. 없는 커밋 오류 |
| search | 검색 문자열, 작성자 여부 | 일치 식별자 목록 | 해당 색인 조회, 저장소 변경 없음 |
| merge_sort | 목록, 비교값 추출 함수 | 정렬된 새 목록 | 원본 순서 보존, 동률 안정 정렬 |
| topological_order | 커밋 사전, 자식 연결 | 부모 우선 식별자 목록 | 처리 수가 부족하면 순환 오류 |
| shortest_path | 양방향 이웃, 출발·도착 | 경로 목록 또는 None | 지역 대기열·직전 노드 사전만 변경 |
| ancestor_ids | 커밋 사전, 기준 식별자 | 조상 식별자 목록 | 지역 스택·방문 집합만 변경 |

Repository 내부 함수는 CLI가 검증한 문자열을 받는 구조입니다. 내부 사전을 직접 수정하는 사용법은 일반 CLI 사용 범위가 아닙니다.

## 3. 작은 입력으로 데이터 변화 따라가기

### 첫 번째 명령: INIT "Alice Smith"

1. shlex가 `['INIT', 'Alice Smith']`로 분리합니다.
2. validate가 인자 한 개와 비어 있지 않은 이름을 확인합니다.
3. execute가 Repository를 만들고 반환합니다.
4. main의 repo가 객체를 가리킵니다. `branches = {'main': None}`, `current_branch = 'main'`, `counter = 0`입니다.

### 두 번째 명령: COMMIT "Add LOGIN login"

1. 인자는 `['Add LOGIN login']`입니다. 메시지 대소문자는 그대로 저장합니다.
2. head()는 None을 반환하므로 parents는 `[]`입니다.
3. add_commit이 counter를 1로 올리고 `0000000000000001`을 만듭니다.
4. commits에 다섯 필드가 저장됩니다. 시간은 실행 순간의 UTC입니다.
5. keyword_index에는 `add: [식별자]`, `login: [식별자]`가 생깁니다. login이 두 번 있어도 한 번만 들어갑니다.
6. author_index에는 `Alice Smith: [식별자]`가 생깁니다.
7. main 브랜치 끝점이 이 식별자로 바뀝니다.
8. 반환된 식별자를 execute가 `[main 0000000000000001] Add LOGIN login`으로 출력합니다.

### 세 번째 명령: SEARCH login

query는 login, words는 `['login']`, first는 `[0000000000000001]`에 해당하는 문자열 목록입니다. candidates는 같은 식별자 하나를 가진 집합입니다. 검색 결과 목록을 반환하면 execute가 `Found 1 commit(s):`와 커밋 정보를 출력합니다. 검색에서는 counter나 branches가 바뀌지 않습니다.

### 분기 후 PATH의 변수 변화

a가 최초 커밋이고 b와 c의 부모가 모두 a일 때 `PATH b c`를 실행한다고 생각해 보세요. a,b,c는 설명용 축약명입니다.

| 단계 | queue | previous | 의미 |
| --- | --- | --- | --- |
| 시작 | [b] | {b: None} | 출발점 방문 등록 |
| b 처리 | [b, a] | {b: None, a: b} | b에서 부모 a로 이동 가능 |
| a 처리 | [b, a, c] | {b: None, a: b, c: a} | b는 재방문하지 않고 c 추가 |
| c 도착 | 그대로 | 그대로 | 역추적은 c, a, b이고 반환은 b, a, c |

queue에서 이미 처리한 항목을 지우지 않고 front 위치만 늘립니다. 목록 앞을 지울 때마다 나머지를 옮기는 비용을 피하기 위해서입니다.

## 4. 실제 소스의 줄별 해설

최종 Python 파일을 읽어 얻은 원본 줄 번호입니다. **빈 줄과 주석만 있는 줄은 제외**했습니다. 따라서 번호가 연속되지 않아도 누락이 아닙니다. 들여쓰기를 보존하기 위해 각 줄을 코드 블록으로 표시합니다. import와 닫는 괄호도 각각 설명합니다.

### main.py

**1행**

```python
import shlex
```

따옴표로 묶인 공백 포함 인자를 분리하는 표준 라이브러리를 가져온다.

**2행**

```python
from repository import Repository
```

저장소와 브랜치 기능을 가진 클래스를 가져온다.

**6행**

```python
def print_commits(repo, commit_ids):
```

저장소와 출력할 커밋 식별자 목록을 받는다.

**7행**

```python
    if not commit_ids:
```

출력할 커밋이 없는지 확인한다.

**8행**

```python
        print('No commits')
```

빈 로그나 검색 결과를 명시한다.

**9행**

```python
    for commit_id in commit_ids:
```

요청된 순서 그대로 커밋을 하나씩 출력한다.

**10행**

```python
        commit = repo.commits[commit_id]
```

식별자를 통해 커밋의 상세 정보를 가져온다.

**11행**

```python
        print(f"commit {commit['hash']} | {commit['author']} | {commit['timestamp']}")
```

식별자, 작성자, 시각을 한 줄에 표시한다.

**12행**

```python
        print('  ' + commit['message'])
```

다음 줄에 원래 커밋 메시지를 표시한다.

**16행**

```python
def validate(command, args):
```

대문자 명령과 파싱된 인자 목록을 검사한다.

**17행**

```python
    counts = {'INIT': 1, 'BRANCH': 1, 'SWITCH': 1, 'COMMIT': 1, 'PATH': 2, 'ANCESTORS': 1, 'SEARCH': 1, 'EXIT': 0, 'QUIT': 0}
```

LOG를 제외한 각 명령의 정확한 인자 수를 정의한다.

**18행**

```python
    if command == 'LOG':
```

LOG만 인자를 생략하거나 정렬 옵션 하나를 받는다.

**19행**

```python
        if args not in ([], ['--sort-by=date'], ['--sort-by=author']):
```

허용된 세 가지 형태 외에는 거부한다.

**20행**

```python
            raise ValueError('Invalid args')
```

잘못된 정렬 옵션이나 인자 수를 표준 오류로 알린다.

**21행**

```python
    elif command not in counts:
```

등록되지 않은 명령인지 확인한다.

**22행**

```python
        raise ValueError('Unknown command: ' + command)
```

알 수 없는 명령어임을 알린다.

**23행**

```python
    elif len(args) != counts[command]:
```

명령에 필요한 인자 개수와 실제 개수를 비교한다.

**24행**

```python
        raise ValueError('Invalid args')
```

부족하거나 많은 인자는 실행하지 않는다.

**25행**

```python
    if any(not arg.strip() for arg in args):
```

빈 문자열이나 공백뿐인 인자를 검사한다.

**26행**

```python
        raise ValueError('Invalid args')
```

의미 없는 이름이나 메시지는 거부한다.

**27행**

```python
    if command == 'SEARCH' and args[0].startswith('--'):
```

검색 인자가 옵션 형태이면 추가로 검사한다.

**28행**

```python
        if not args[0].startswith('--author=') or not args[0][9:].strip():
```

정확한 작성자 옵션과 비어 있지 않은 이름을 요구한다.

**29행**

```python
            raise ValueError('Invalid args')
```

오타 옵션이나 빈 작성자는 검색하지 않는다.

**33행**

```python
def execute(repo, command, args):
```

검증된 명령만 받으며 종료 처리는 main에서 담당한다.

**34행**

```python
    if command == 'INIT':
```

저장소를 처음 만드는 명령인지 확인한다.

**35행**

```python
        if repo is not None:
```

이미 초기화된 저장소를 실수로 지우지 않도록 막는다.

**36행**

```python
            raise ValueError('Repository already initialized')
```

재초기화 대신 기존 저장소를 유지한다.

**37행**

```python
        repo = Repository(args[0])
```

사용자 이름으로 새 메모리 저장소를 만든다.

**38행**

```python
        print('Initialized repository.')
```

초기화 성공을 출력한다.

**39행**

```python
        print('Current branch: main')
```

기본 브랜치를 알린다.

**40행**

```python
        print('Current user: ' + repo.user)
```

커밋에 기록할 작성자 이름을 알린다.

**41행**

```python
        return repo
```

생성한 저장소 객체를 REPL에 전달한다.

**42행**

```python
    if repo is None:
```

INIT 이전에 저장소 기능을 요청했는지 확인한다.

**43행**

```python
        raise ValueError('Repository not initialized: use INIT <user_name>')
```

초기화 명령을 먼저 입력하도록 안내한다.

**44행**

```python
    if command == 'BRANCH':
```

브랜치 생성 요청이다.

**45행**

```python
        repo.branch(args[0])
```

현재 커밋에 새 브랜치 이름을 연결한다.

**46행**

```python
        print('Created branch: ' + args[0])
```

성공한 브랜치 이름을 출력한다.

**47행**

```python
    elif command == 'SWITCH':
```

브랜치 전환 요청이다.

**48행**

```python
        repo.switch(args[0])
```

현재 브랜치를 지정한 이름으로 바꾼다.

**49행**

```python
        print('Switched to branch: ' + args[0])
```

이동 결과를 출력한다.

**50행**

```python
    elif command == 'COMMIT':
```

새 커밋 생성 요청이다.

**51행**

```python
        commit_id = repo.commit(args[0])
```

현재 HEAD를 부모로 만들고 새 식별자를 받는다.

**52행**

```python
        print(f'[{repo.current_branch} {commit_id}] {args[0]}')
```

브랜치, 식별자, 메시지를 표시한다.

**53행**

```python
    elif command == 'LOG':
```

전체 커밋 로그 요청이다.

**54행**

```python
        sort_by = None
```

옵션이 없으면 위상 정렬을 사용하도록 기본값을 둔다.

**55행**

```python
        if args:
```

정렬 옵션이 있는지 확인한다.

**56행**

```python
            sort_by = args[0].split('=', 1)[1]
```

옵션의 등호 뒤 date 또는 author를 꺼낸다.

**57행**

```python
        print_commits(repo, repo.log(sort_by))
```

선택된 순서의 커밋 정보를 출력한다.

**58행**

```python
    elif command == 'PATH':
```

두 커밋 사이 최단 경로 요청이다.

**59행**

```python
        path = repo.path(args[0], args[1])
```

출발점과 도착점으로 탐색을 수행한다.

**60행**

```python
        if path is None:
```

연결되지 않은 커밋들이면 경로가 없다.

**61행**

```python
            print('No path')
```

요구된 경로 없음 문구를 출력한다.

**62행**

```python
        else:
```

자신에게 가는 경우를 포함해 경로를 찾은 경우이다.

**63행**

```python
            print('Path: ' + '->'.join(path))
```

커밋 식별자를 화살표로 연결하여 출력한다.

**64행**

```python
    elif command == 'ANCESTORS':
```

모든 조상 조회 요청이다.

**65행**

```python
        print_commits(repo, repo.ancestors(args[0]))
```

DFS 결과의 상세 커밋 정보를 출력한다.

**66행**

```python
    elif command == 'SEARCH':
```

역색인을 이용한 검색 요청이다.

**67행**

```python
        query = args[0]
```

따옴표를 처리한 검색 인자를 저장한다.

**68행**

```python
        by_author = query.startswith('--author=')
```

작성자 옵션인지 판별해 검색 대상을 결정한다.

**69행**

```python
        if by_author:
```

작성자 검색이면 옵션 부분을 제거한다.

**70행**

```python
            query = query[9:]
```

--author= 다음의 실제 이름만 남긴다.

**71행**

```python
        found = repo.search(query, by_author)
```

선택한 색인에서 후보 커밋을 가져온다.

**72행**

```python
        print(f'Found {len(found)} commit(s):')
```

일치하는 커밋 수를 표시한다.

**73행**

```python
        print_commits(repo, found)
```

검색 결과를 같은 커밋 출력 형식으로 표시한다.

**74행**

```python
    return repo
```

명령 실행 후 같은 저장소를 다음 반복에서 사용할 수 있게 반환한다.

**78행**

```python
def main():
```

프로그램의 대화형 실행을 시작하는 함수이다.

**79행**

```python
    repo = None
```

INIT을 입력하기 전에는 저장소가 없다.

**80행**

```python
    print('Mini Git | INIT <user_name> | exit / quit')
```

시작 방법과 종료 방법을 간단히 안내한다.

**81행**

```python
    while True:
```

종료 요청이 올 때까지 계속 명령을 받는다.

**82행**

```python
        try:
```

입력·파싱·실행 중 예상되는 오류를 잡기 위한 구간이다.

**83행**

```python
            line = input('mini-git> ')
```

프롬프트를 표시하고 사용자가 입력한 한 줄을 받는다.

**84행**

```python
            try:
```

따옴표 오류를 공통 문구로 바꾸기 위한 안쪽 예외 처리이다.

**85행**

```python
                tokens = shlex.split(line)
```

따옴표 안 공백은 보존하며 명령과 인자를 나눈다.

**86행**

```python
            except ValueError:
```

닫히지 않은 따옴표 등 파싱 실패를 처리한다.

**87행**

```python
                raise ValueError('Invalid args') from None
```

원래 오류 연결 표시 없이 표준 오류로 바꾼다.

**88행**

```python
            if not tokens:
```

아무것도 입력하지 않은 줄은 작업하지 않는다.

**89행**

```python
                continue
```

다음 프롬프트로 돌아간다.

**90행**

```python
            command = tokens[0].upper()
```

명령어만 대문자로 바꾸어 대소문자를 구분하지 않는다.

**91행**

```python
            args = tokens[1:]
```

명령어 다음 토큰들을 인자 목록으로 분리한다.

**92행**

```python
            validate(command, args)
```

문법을 검증한 뒤에만 실제 작업을 실행한다.

**93행**

```python
            if command in ('EXIT', 'QUIT'):
```

종료 명령인지 확인한다.

**94행**

```python
                print('Bye')
```

정상 종료 안내를 출력한다.

**95행**

```python
                break
```

입력 반복문을 끝낸다.

**96행**

```python
            repo = execute(repo, command, args)
```

한 명령을 실행하고 최신 저장소 참조를 유지한다.

**97행**

```python
        except ValueError as error:
```

잘못된 인자나 없는 브랜치·커밋 오류를 처리한다.

**98행**

```python
            print(str(error))
```

오류를 보여 준 뒤 다음 입력을 계속 받는다.

**99행**

```python
        except (EOFError, KeyboardInterrupt):
```

입력 종료 신호나 Ctrl+C도 정상 종료로 처리한다.

**100행**

```python
            print('\nBye')
```

새 줄에서 종료 안내를 출력한다.

**101행**

```python
            break
```

반복문을 끝내 프로그램을 종료한다.

**103행**

```python
if __name__ == '__main__':
```

이 파일을 직접 실행했을 때만 대화형 프로그램을 시작한다.

**104행**

```python
    main()
```

위에서 정의한 REPL 함수를 호출한다.


### repository.py

**1행**

```python
from datetime import datetime, timezone
```

UTC 시간을 기록하기 위한 표준 라이브러리를 가져온다.

**2행**

```python
from algorithms import ancestor_ids, merge_sort, shortest_path, topological_order
```

직접 구현한 알고리즘을 저장소 기능에 연결한다.

**5행**

```python
class Repository:
```

커밋, 브랜치, 검색 색인을 함께 관리하는 설계도이다.

**7행**

```python
    def __init__(self, user):
```

Repository(user)를 만들 때 자동 실행되는 초기화 함수이다.

**8행**

```python
        self.user = user
```

앞으로 생성할 커밋의 작성자를 저장한다.

**9행**

```python
        self.commits = {}
```

식별자를 키로 사용해 커밋 전체 정보를 빠르게 찾는다.

**10행**

```python
        self.branches = {'main': None}
```

main을 만들며 아직 커밋이 없으므로 끝점은 None이다.

**11행**

```python
        self.current_branch = 'main'
```

HEAD가 가리키는 현재 브랜치 이름을 기록한다.

**12행**

```python
        self.counter = 0
```

중복 없는 커밋 식별자를 만들 증가 카운터이다.

**13행**

```python
        self.children = {}
```

위상 정렬을 위해 부모별 자식 목록을 기록한다.

**14행**

```python
        self.neighbors = {}
```

무방향 최단 경로 탐색에 사용할 양방향 연결 목록이다.

**15행**

```python
        self.keyword_index = {}
```

소문자 단어를 키로, 커밋 식별자 목록을 값으로 저장한다.

**16행**

```python
        self.author_index = {}
```

작성자 이름을 키로, 그 사람이 만든 커밋 목록을 저장한다.

**19행**

```python
    def head(self):
```

현재 브랜치의 마지막 커밋을 조회하는 함수이다.

**20행**

```python
        return self.branches[self.current_branch]
```

브랜치 사전에서 HEAD에 해당하는 식별자 또는 None을 반환한다.

**23행**

```python
    def branch(self, name):
```

현재 위치에서 새 브랜치를 만드는 함수이다.

**24행**

```python
        if name in self.branches:
```

같은 이름으로 기존 브랜치를 덮어쓰지 않도록 확인한다.

**25행**

```python
            raise ValueError('Branch already exists: ' + name)
```

중복 이름이면 오류를 전달한다.

**26행**

```python
        self.branches[name] = self.head()
```

현재 커밋을 가리키는 새 이름만 추가하며 커밋은 복사하지 않는다.

**29행**

```python
    def switch(self, name):
```

현재 브랜치를 변경하는 함수이다.

**30행**

```python
        if name not in self.branches:
```

이동할 브랜치가 존재하는지 검사한다.

**31행**

```python
            raise ValueError('Unknown branch: ' + name)
```

없는 브랜치에는 표준 오류를 전달한다.

**32행**

```python
        self.current_branch = name
```

현재 브랜치를 바꾸어 HEAD도 해당 브랜치 끝점으로 이동한다.

**35행**

```python
    def require_commit(self, commit_id):
```

커밋 식별자가 유효한지 공통으로 검사한다.

**36행**

```python
        if commit_id not in self.commits:
```

해시맵에서 식별자의 존재 여부를 확인한다.

**37행**

```python
            raise ValueError('Unknown commit: ' + commit_id)
```

모르는 식별자이면 탐색을 시작하지 않는다.

**40행**

```python
    def commit(self, message):
```

CLI의 일반 커밋을 만드는 함수이다.

**41행**

```python
        parent = self.head()
```

새 커밋을 만들기 직전 브랜치 끝점을 기억한다.

**42행**

```python
        parents = []
```

첫 커밋이면 부모가 없는 목록을 사용한다.

**43행**

```python
        if parent is not None:
```

현재 브랜치에 기존 커밋이 있으면 부모로 연결한다.

**44행**

```python
            parents.append(parent)
```

현재 HEAD를 유일한 부모로 넣는다.

**45행**

```python
        return self.add_commit(message, parents)
```

실제 생성·색인 갱신 작업에 부모 목록을 전달한다.

**49행**

```python
    def add_commit(self, message, parents):
```

0개 이상의 부모를 지원하는 내부 생성 함수이다. CLI는 commit을 사용한다.

**50행**

```python
        parents = list(dict.fromkeys(parents))
```

부모 중복을 제거하고 최초 순서를 보존한 새 목록을 만든다.

**51행**

```python
        for parent in parents:
```

저장하기 전에 모든 부모를 검사한다.

**52행**

```python
            self.require_commit(parent)
```

미래 또는 존재하지 않는 커밋을 부모로 지정하지 못하게 한다.

**53행**

```python
        if self.counter >= 16 ** 16 - 1:
```

고정 길이 식별자 범위를 넘기 전에 생성을 거부한다.

**54행**

```python
            raise ValueError('Commit ID space exhausted')
```

카운터를 재사용하거나 길이를 늘리는 대신 오류를 낸다.

**55행**

```python
        self.counter += 1
```

새 커밋마다 번호를 하나 올린다.

**56행**

```python
        commit_id = f'{self.counter:016x}'
```

카운터를 16자리 16진수로 표현하며 실제 암호학적 해시는 아니다.

**57행**

```python
        record = {
```

요구된 다섯 필드를 담을 커밋 사전을 시작한다.

**58행**

```python
            'hash': commit_id,
```

세션에서 유일한 커밋 식별자를 기록한다.

**59행**

```python
            'message': message,
```

사용자가 입력한 커밋 메시지를 보존한다.

**60행**

```python
            'author': self.user,
```

현재 저장소 사용자를 작성자로 기록한다.

**61행**

```python
            'timestamp': datetime.now(timezone.utc).isoformat(timespec='microseconds'),
```

시간대와 마이크로초를 포함한 UTC 시각 문자열을 저장한다.

**62행**

```python
            'parents': parents,
```

커밋이 이어지는 부모 식별자 목록을 기록한다.

**63행**

```python
        }
```

커밋 사전 정의를 마친다.

**64행**

```python
        self.commits[commit_id] = record
```

식별자로 커밋을 조회할 수 있도록 저장한다.

**65행**

```python
        self.children[commit_id] = []
```

새 커밋은 아직 자식이 없으므로 빈 목록을 만든다.

**66행**

```python
        self.neighbors[commit_id] = list(parents)
```

새 커밋에서 부모로 이동하는 연결을 기록한다.

**67행**

```python
        for parent in parents:
```

각 부모 쪽의 연결 정보도 갱신한다.

**68행**

```python
            self.children[parent].append(commit_id)
```

부모에서 자식으로 향하는 위상 정렬용 연결을 추가한다.

**69행**

```python
            self.neighbors[parent].append(commit_id)
```

PATH가 부모에서도 자식으로 이동할 수 있게 역방향을 추가한다.

**70행**

```python
        self.author_index.setdefault(self.user, []).append(commit_id)
```

작성자의 색인 목록이 없으면 만들고 새 식별자를 추가한다.

**71행**

```python
        for word in set(message.lower().split()):
```

메시지를 소문자 공백 단위로 나누고 같은 단어의 중복을 제거한다.

**72행**

```python
            self.keyword_index.setdefault(word, []).append(commit_id)
```

각 단어로 이 커밋을 바로 찾을 수 있게 색인을 갱신한다.

**73행**

```python
        self.branches[self.current_branch] = commit_id
```

현재 브랜치 끝점을 새 커밋으로 이동한다.

**74행**

```python
        return commit_id
```

CLI가 생성 결과를 출력할 수 있도록 식별자를 반환한다.

**77행**

```python
    def log(self, sort_by=None):
```

전체 저장소 로그를 기본 위상 순서 또는 지정 기준으로 반환한다.

**78행**

```python
        if sort_by is None:
```

옵션 없는 LOG는 반드시 부모를 먼저 출력한다.

**79행**

```python
            return topological_order(self.commits, self.children)
```

직접 구현한 위상 정렬 결과를 반환한다.

**80행**

```python
        field = {'date': 'timestamp', 'author': 'author'}[sort_by]
```

CLI 옵션을 실제 커밋 필드 이름으로 바꾼다.

**81행**

```python
        return merge_sort(list(self.commits), lambda cid: self.commits[cid][field])
```

해당 필드로 안정 병합 정렬하며 동률이면 생성 순서를 유지한다.

**84행**

```python
    def path(self, start, target):
```

두 커밋 사이 무방향 최단 경로를 구한다.

**85행**

```python
        self.require_commit(start)
```

출발점이 존재하는지 먼저 확인한다.

**86행**

```python
        self.require_commit(target)
```

도착점도 존재해야 탐색할 수 있다.

**87행**

```python
        return shortest_path(self.neighbors, start, target)
```

양방향 연결 목록으로 BFS를 실행한 결과를 반환한다.

**90행**

```python
    def ancestors(self, commit_id):
```

기준 커밋의 모든 조상을 조회한다.

**91행**

```python
        self.require_commit(commit_id)
```

존재하지 않는 기준점은 오류로 처리한다.

**92행**

```python
        return ancestor_ids(self.commits, commit_id)
```

중복 없는 조상 목록을 DFS로 구해 반환한다.

**95행**

```python
    def search(self, query, by_author=False):
```

기본은 단어 검색이고 by_author가 참이면 작성자 검색이다.

**96행**

```python
        if by_author:
```

작성자 옵션이 선택된 경우이다.

**97행**

```python
            return list(self.author_index.get(query, []))
```

전체 커밋 순회 없이 정확히 일치하는 작성자의 목록을 복사한다.

**98행**

```python
        words = list(dict.fromkeys(query.lower().split()))
```

검색어도 소문자 공백 토큰으로 바꾸며 중복 단어를 제거한다.

**99행**

```python
        if not words:
```

검색할 단어가 하나도 없으면 빈 결과이다.

**100행**

```python
            return []
```

빈 검색 결과를 호출자에게 반환한다.

**101행**

```python
        first = self.keyword_index.get(words[0], [])
```

첫 단어가 있는 커밋 후보만 역색인에서 가져온다.

**102행**

```python
        candidates = set(first)
```

여러 단어 검색의 교집합 계산에 사용할 집합이다.

**103행**

```python
        for word in words[1:]:
```

두 번째 검색 단어부터 후보를 좁힌다.

**104행**

```python
            candidates.intersection_update(self.keyword_index.get(word, []))
```

현재 단어도 포함하는 커밋만 남긴다. AND 검색이다.

**105행**

```python
        return [cid for cid in first if cid in candidates]
```

전체 커밋이 아닌 첫 색인만 순회하여 생성 순서로 반환한다.


### algorithms.py

**3행**

```python
def merge_sort(items, key):
```

items는 정렬할 목록, key는 비교할 값을 꺼내는 함수이다.

**4행**

```python
    if len(items) <= 1:
```

원소가 0개 또는 1개이면 이미 정렬되어 있다.

**5행**

```python
        return list(items)
```

원본을 바꾸지 않도록 새 목록으로 반환한다.

**6행**

```python
    middle = len(items) // 2
```

정수 나눗셈으로 목록을 반으로 나눌 위치를 구한다.

**7행**

```python
    left = merge_sort(items[:middle], key)
```

가운데 앞쪽을 같은 함수로 정렬한다. 이것이 재귀 호출이다.

**8행**

```python
    right = merge_sort(items[middle:], key)
```

가운데부터 끝까지도 재귀적으로 정렬한다.

**9행**

```python
    result = []
```

두 정렬된 목록을 합칠 빈 목록이다.

**10행**

```python
    i = j = 0
```

왼쪽과 오른쪽 목록에서 다음에 비교할 위치를 각각 0으로 시작한다.

**11행**

```python
    while i < len(left) and j < len(right):
```

양쪽 모두 비교할 원소가 남아 있는 동안 반복한다.

**12행**

```python
        if key(left[i]) <= key(right[j]):
```

비교값이 같으면 왼쪽을 먼저 골라 기존 순서를 보존한다.

**13행**

```python
            result.append(left[i])
```

왼쪽 원소를 결과 끝에 넣는다.

**14행**

```python
            i += 1
```

왼쪽에서 다음 원소로 이동한다.

**15행**

```python
        else:
```

오른쪽 비교값이 더 작은 경우이다.

**16행**

```python
            result.append(right[j])
```

오른쪽 원소를 결과 끝에 넣는다.

**17행**

```python
            j += 1
```

오른쪽에서 다음 원소로 이동한다.

**18행**

```python
    result.extend(left[i:])
```

왼쪽에 남은 원소를 순서대로 붙인다.

**19행**

```python
    result.extend(right[j:])
```

오른쪽에 남은 원소를 순서대로 붙인다.

**20행**

```python
    return result
```

완성한 정렬 목록을 호출한 곳에 돌려준다.

**24행**

```python
def topological_order(commits, children):
```

커밋 사전과 부모에서 자식으로 가는 연결 사전을 입력받는다.

**25행**

```python
    remaining = {}
```

아직 출력하지 않은 부모 수를 커밋별로 기록한다.

**26행**

```python
    queue = []
```

출력 가능한 커밋을 넣는 선입선출 대기열이다.

**27행**

```python
    for commit_id, commit in commits.items():
```

저장소의 커밋을 생성 순서대로 하나씩 확인한다.

**28행**

```python
        remaining[commit_id] = len(commit['parents'])
```

각 커밋의 부모 수를 기록한다.

**29행**

```python
        if remaining[commit_id] == 0:
```

부모가 없으면 즉시 출력 가능하다.

**30행**

```python
            queue.append(commit_id)
```

시작 커밋을 대기열에 넣는다.

**31행**

```python
    result = []
```

부모가 자식보다 앞서는 최종 순서를 저장한다.

**32행**

```python
    front = 0
```

pop(0) 대신 읽을 위치를 사용해 앞 원소 삭제 비용을 피한다.

**33행**

```python
    while front < len(queue):
```

대기열에서 아직 읽지 않은 커밋이 있는 동안 반복한다.

**34행**

```python
        current = queue[front]
```

가장 먼저 대기한 커밋을 선택한다.

**35행**

```python
        front += 1
```

다음에 읽을 대기열 위치를 증가시킨다.

**36행**

```python
        result.append(current)
```

선택한 커밋을 출력 순서에 기록한다.

**37행**

```python
        for child in children[current]:
```

이 커밋을 부모로 삼는 자식들을 확인한다.

**38행**

```python
            remaining[child] -= 1
```

자식 입장에서 아직 출력되지 않은 부모가 하나 줄었다.

**39행**

```python
            if remaining[child] == 0:
```

모든 부모가 출력된 자식만 준비 완료이다.

**40행**

```python
                queue.append(child)
```

준비가 끝난 자식을 대기열에 넣는다.

**41행**

```python
    if len(result) != len(commits):
```

모든 커밋을 처리하지 못했다면 순환 등 그래프 이상이 있다.

**42행**

```python
        raise ValueError('Invalid graph: cycle detected')
```

잘못된 그래프를 정상 로그처럼 반환하지 않는다.

**43행**

```python
    return result
```

커밋 식별자의 위상 순서를 반환한다.

**47행**

```python
def shortest_path(neighbors, start, target):
```

양방향 인접 목록과 출발·도착 식별자를 받는다.

**48행**

```python
    queue = [start]
```

너비 우선 탐색의 대기열을 출발점으로 시작한다.

**49행**

```python
    previous = {start: None}
```

최초 방문 때의 직전 노드를 기록하고 방문 여부 확인에도 사용한다.

**50행**

```python
    front = 0
```

대기열에서 읽을 위치이다.

**51행**

```python
    while front < len(queue):
```

방문할 후보가 남아 있는 동안 반복한다.

**52행**

```python
        current = queue[front]
```

먼저 들어온 후보부터 처리한다.

**53행**

```python
        front += 1
```

대기열 읽기 위치를 한 칸 이동한다.

**54행**

```python
        if current == target:
```

도착점이면 최단 경로를 복원할 수 있다.

**55행**

```python
            path = []
```

도착점에서 출발점 방향으로 경로를 모은다.

**56행**

```python
            while current is not None:
```

출발점의 직전 값인 None을 만날 때까지 거슬러 간다.

**57행**

```python
                path.append(current)
```

현재 식별자를 경로에 추가한다.

**58행**

```python
                current = previous[current]
```

최초로 이곳에 도달한 직전 커밋으로 이동한다.

**59행**

```python
            return path[::-1]
```

역순으로 모은 목록을 뒤집어 출발점부터 반환한다.

**60행**

```python
        for neighbor in merge_sort(neighbors[current], lambda value: value):
```

이웃을 직접 구현한 정렬로 사전순 방문하여 동률 경로를 결정한다.

**61행**

```python
            if neighbor not in previous:
```

최초 방문인 경우만 처리해 순환 방문을 막는다.

**62행**

```python
                previous[neighbor] = current
```

나중에 경로를 복원할 수 있도록 직전 커밋을 기록한다.

**63행**

```python
                queue.append(neighbor)
```

다음 거리의 탐색 후보를 대기열 끝에 넣는다.

**64행**

```python
    return None
```

도착점을 찾지 못하면 경로가 없음을 반환한다.

**68행**

```python
def ancestor_ids(commits, start):
```

전체 커밋 사전과 조상을 찾을 기준 커밋을 받는다.

**69행**

```python
    stack = list(commits[start]['parents'])
```

기준 커밋 자신은 제외하고 부모부터 탐색한다.

**70행**

```python
    visited = set()
```

중복으로 만난 조상을 다시 처리하지 않도록 기록한다.

**71행**

```python
    result = []
```

발견한 조상의 식별자를 저장한다.

**72행**

```python
    while stack:
```

확인할 조상이 남아 있는 동안 반복한다.

**73행**

```python
        current = stack.pop()
```

마지막에 넣은 커밋부터 꺼내 깊이 우선으로 진행한다.

**74행**

```python
        if current in visited:
```

이미 처리한 공통 조상인지 확인한다.

**75행**

```python
            continue
```

중복 조상은 건너뛰고 다음 후보를 처리한다.

**76행**

```python
        visited.add(current)
```

처음 방문한 커밋을 방문 집합에 기록한다.

**77행**

```python
        result.append(current)
```

해당 조상을 결과에 한 번만 넣는다.

**78행**

```python
        stack.extend(commits[current]['parents'])
```

이 조상의 부모도 탐색 후보로 추가한다.

**79행**

```python
    return result
```

시작 커밋을 제외한 모든 조상을 반환한다.

