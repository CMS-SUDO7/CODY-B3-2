# B3-2 Mini Git

커밋·브랜치·HEAD를 메모리에 관리하며 그래프 탐색과 역색인을 배우는 CLI 프로그램입니다. 첨부된 B3-2 미션 PDF의 필수 기능을 구현했습니다. 실제 파일 내용은 추적하지 않으며 종료하면 데이터가 사라집니다.

## 1. 파일 구조와 처리 흐름

| 파일 | 역할 |
| --- | --- |
| `main.py` | 실행 시작점, 따옴표를 고려한 입력 파싱, REPL, 결과 출력 |
| `repository.py` | 커밋 모델, 브랜치·HEAD·커밋 상태, 알고리즘 연결 |
| `algorithms.py` | 안정 병합 정렬, Kahn 위상 정렬, DFS 조상 탐색, BFS 최단 경로 |
| `index.py` | 키워드·작성자 역색인 등록 및 조회 |
| `docs/basic_knowledge.md` | 기초 문법, 자료구조, 복잡도, 학습 과제, 책 한 권 |
| `docs/code_translation.md` | 처리 흐름과 최종 소스의 줄별 해설 |
| `docs/verification.md` | 실제로 실행한 검증 범위와 결과 |

`main()` → `execute()` → `Repository` → 알고리즘/역색인 → `main.py` 화면 출력 순서입니다. 조회 함수는 결과를 반환하고 화면 출력은 CLI에서 담당합니다.

## 2. 실행 환경

- Python 3.10 이상, 외부 패키지 설치 불필요
- Python 표준 라이브러리: `shlex`, `dataclasses`, `datetime`, `collections.deque`
- 그래프 전용 라이브러리와 `sorted()`, `list.sort()` 등 표준 정렬 API를 사용하지 않습니다.
- 이 프로젝트에서는 `dict`, `set`, `list`가 허용됩니다. B3-1의 자료형 금지 조건을 적용하지 않습니다.
- 실제 실행 검증 환경은 Linux / Python 3.12.14입니다. Python 3.10 구문으로도 분석했습니다.

## 3. 빠른 시작

ZIP 압축을 푼 뒤 **`main.py`가 있는 `B3-2-mini-git` 폴더**에서 실행합니다.

Windows PowerShell:

```powershell
cd .\B3-2-mini-git
python main.py
```

Linux/macOS 터미널:

```bash
cd B3-2-mini-git
python3 main.py
```

이후 `mini-git>` 프롬프트에 아래 명령을 **한 줄씩** 입력합니다. `mini-git>` 자체는 입력하지 않습니다.

```text
INIT "Alice Kim"
COMMIT "Initial commit"
BRANCH feature
SWITCH feature
COMMIT "Add login feature"
SWITCH main
COMMIT "Add payment feature"
LOG
PATH 00000002 00000003
ANCESTORS 00000003
SEARCH "login"
SEARCH "add feature"
SEARCH --author="Alice Kim"
LOG --sort-by=date
LOG --sort-by=author
QUIT
```

## 4. 명령어

| 명령 | 동작 |
| --- | --- |
| `INIT <user_name>` | main과 현재 사용자 설정. 첫 커밋 전 HEAD의 커밋은 없음 |
| `BRANCH <branch_name>` | 현재 커밋을 가리키는 브랜치 생성. 자동 전환하지 않음 |
| `SWITCH <branch_name>` | 현재 브랜치 전환 |
| `COMMIT <message>` | 현재 브랜치의 커밋을 부모로 새 커밋 생성, 역색인 갱신 |
| `LOG` | 전체 저장소의 커밋을 부모가 자식보다 먼저 나오도록 출력 |
| `LOG --sort-by=date` | timestamp 오름차순 |
| `LOG --sort-by=author` | 작성자 이름의 Python 문자열 비교 순서로 오름차순 |
| `PATH <commit1> <commit2>` | 부모 연결을 무방향으로 본 최단 경로. 없으면 `No path` |
| `ANCESTORS <commit_hash>` | 자기 자신을 제외한 모든 조상. 중복 없이 DFS 방문 순서 |
| `SEARCH <keyword>` | 소문자·공백 분리 토큰으로 메시지 역색인 검색 |
| `SEARCH --author=<name>` | 작성자 전체 이름으로 역색인 검색 |
| `HELP` | 명령 목록 |
| `EXIT` / `QUIT` | 프로그램 종료 |

### 문법·동률·검색 규칙

- 명령어는 대소문자를 구분하지 않습니다. `commit`, `CoMmIt`도 같습니다.
- 옵션 이름과 값은 표에 적힌 소문자를 사용합니다. 브랜치명·작성자명은 대소문자를 구분합니다.
- 공백이 있는 사용자명, 브랜치명, 메시지, 검색어는 따옴표로 감쌉니다. `SEARCH --author="Alice Kim"`도 인자 하나로 해석합니다.
- 빈 문자열이나 공백뿐인 인자는 `Invalid args`입니다. 공백 문자열을 허용하기 위해 `shlex.split()`을 사용합니다.
- 키워드는 **부분 문자열이 아니라 단어 전체**와 비교합니다. `login`은 `LOGIN`과 일치하지만 `log`나 `login,`과는 다릅니다. 구두점은 제거하지 않습니다.
- 여러 단어 검색의 결합 방식은 원문에서 정하지 않았으므로 **모든 단어가 있는 AND 검색**을 채택했습니다. `SEARCH "add login"`은 순서와 관계없이 두 토큰이 모두 들어간 메시지를 찾습니다.
- 검색 결과는 커밋 생성 순서입니다. 같은 메시지에 `login login`이 있어도 해당 커밋은 한 번만 나옵니다.
- 기본 LOG의 독립된 노드 간 순서는 생성 순서로 큐에 들어오는 순서를 따릅니다. 전체 커밋 생성 순서와 항상 같다는 뜻은 아닙니다.
- 옵션 LOG의 키가 같으면 기존 생성 순서를 보존합니다. **옵션 정렬은 부모 우선 보장을 따로 적용하지 않습니다.**
- 최단 경로가 여러 개면 `hash1->hash2->...` 문자열의 사전순이 가장 작은 경로를 고릅니다. 출력에 보이는 화살표 양쪽 공백은 가독성용입니다.
- hash는 `00000001`부터 증가하는 16진수 식별자입니다. 최소 8자리이며 8자리를 넘어도 잘라내지 않습니다. 세션 내 중복이 없고 암호학적 내용 해시는 아닙니다.

## 5. 출력 예시

아래는 위 빠른 시작 명령에 대한 **설명용 예시**입니다. timestamp는 실행 시각의 UTC(`+00:00`) 값으로 달라집니다.

```text
mini-git> COMMIT "Initial commit"
[main 00000001] Initial commit
mini-git> PATH 00000002 00000003
Path: 00000002 -> 00000001 -> 00000003
mini-git> SEARCH "login"
Found 1 commit(s)
commit 00000002 (Alice Kim, <실행 시각>)
  Add login feature
```

`LOG`에는 `hash / author / timestamp / message`가 모두 표시됩니다. 브랜치 이름은 커밋 생성 결과에 표시하며 LOG의 필수 필드는 아닙니다.

## 6. 범위와 주의사항

- `INIT` 재입력은 `Repository already initialized`로 거부하여 기존 데이터를 보존합니다. 초기화하려면 종료 후 다시 실행합니다.
- 원문의 사용자 변경 명령은 없으므로 CLI 세션에서는 INIT에 지정한 작성자를 계속 사용합니다. 작성자 정렬은 구현되어 있고 서로 다른 작성자는 모델 데이터로 별도 검증했습니다.
- 첫 커밋 전에 브랜치를 만들면 서로 독립된 루트 커밋을 생성할 수 있습니다. 이 경우 두 루트 사이 PATH는 `No path`입니다.
- 모델의 `parents`는 여러 부모를 담을 수 있고 탐색도 지원하지만 필수 COMMIT은 부모가 최대 하나입니다. 보너스 `MERGE`, `DIFF`, 정렬 성능 비교는 구현하지 않았습니다.
- 파일 내용 추적, 네트워크 통신, 데이터 파일 저장은 구현 범위에 포함하지 않습니다. 실제 Git 저장소의 파일을 수정하지 않습니다.
- 메모리나 사용자 인터페이스의 동시 접근을 제어하는 실제 서비스용 설계는 포함하지 않습니다.

## 7. 오류 해결

| 출력/문제 | 원인과 해결 |
| --- | --- |
| `Repository not initialized` | 먼저 `INIT "이름"` 실행 |
| `Invalid args` | 인자 개수, 빈 값, 따옴표 짝, 옵션 확인 |
| `Unknown branch: name` | `BRANCH name`으로 만든 브랜치만 SWITCH 가능 |
| `Branch already exists: name` | 이미 있는 이름. 다른 이름으로 생성 |
| `Unknown commit: hash` | COMMIT 결과나 LOG에 나온 전체 hash 사용 |
| `Unknown command: name` | HELP로 지원 명령 확인 |
| `No commits` | 저장소/조회 결과가 비어 있음. 오류가 아님 |
| `No path` | 두 커밋은 있지만 서로 다른 연결 요소에 속함 |
| 재실행 후 커밋이 없음 | 메모리 방식의 정상 동작 |
| `main.py`를 찾을 수 없음 | `main.py`와 다른 `.py` 파일이 같은 폴더인지 확인 |

오류를 출력한 뒤에도 다음 명령을 받을 수 있습니다. EOF 또는 Ctrl+C도 정상 종료로 처리합니다.

## 8. 검증과 재현

실제 결과는 [검증 기록](docs/verification.md)에 정리했습니다. 빠른 시작 명령으로 핵심 흐름을 재현할 수 있습니다. 추가 경계 사례는 새 실행에서 다음처럼 확인합니다.

### 연결되지 않은 두 루트

```text
INIT Bob
BRANCH other
COMMIT first
SWITCH other
COMMIT second
PATH 00000001 00000002
```

예상: `No path`. `PATH 00000001 00000001`은 자기 자신 하나를 출력합니다.

### 오류 후 계속 실행

```text
LOG
INIT Alice
COMMIT ""
COMMIT "Add LOGIN login"
SEARCH login
SEARCH log
SWITCH missing
LOG
QUIT
```

예상: 초기화 전 오류, 빈 메시지 오류, login 결과 1개, log 결과 0개, 없는 브랜치 오류. 마지막 LOG에는 성공한 커밋 하나가 남습니다.

알고리즘 입력만으로 확인한 다중 부모·순환·사전순 동률 사례와 CLI로 확인한 결과는 검증 기록에서 구분했습니다. Ctrl+C는 처리 코드를 검토했으며 실제 키 입력 검증에는 포함하지 않았습니다.

## 9. 요구사항 충족표

쪽수는 제공된 8쪽 PDF의 인쇄 페이지를 기준으로 합니다.

| 요구사항 | 구분 | 원문 위치 | 구현 위치 | 검증 방법 | 상태·증거 |
| --- | --- | --- | --- | --- | --- |
| Python 3.10 이상, main.py·README | 필수 | 2·5·6쪽 | 전체 소스, 이 문서 | 3.10 구문 분석, 3.12 실제 실행 | 충족, 검증 기록 |
| INIT·main·HEAD·작성자 | 필수 | 4쪽 | Repository.initialize | 초기 상태·반복 INIT | 충족 |
| BRANCH·SWITCH | 필수 | 4쪽 | create_branch, switch_branch | 분기 후 부모·각 브랜치 위치 | 충족 |
| COMMIT 메타데이터·유일 hash | 필수 | 3·4쪽 | Commit, Repository.commit | 2,000개 유일성·부모 확인 | 충족 |
| DAG·복수 부모 표현·hash 직접 조회 | 필수 | 3쪽 | frozen Commit, tuple parents, commits dict | 다중 부모 그래프·위상 정렬 | 충족, 새 커밋만 기존 부모를 참조 |
| 키워드·작성자 역색인, 생성 시 갱신 | 필수 | 3·4·5쪽 | InvertedIndex, Repository.search | 대소문자·반복 토큰·전체 순회 차단 | 충족 |
| 정렬 직접 구현·비교 기준 변경 | 필수 | 3·4쪽 | merge_sort, Repository.log | 무작위 100종·동률·작성자·날짜 | 충족 |
| 기본 LOG 부모 우선·필드 식별 | 필수 | 4쪽 | topological_order, print_commits | 분기·다중 부모·CLI 출력 | 충족 |
| 날짜·작성자 옵션 LOG | 필수 | 4쪽 | handle_log, Repository.log | 오름차순·동률 순서 | 충족 |
| 무방향 최단 PATH·No path | 필수 | 4쪽 | shortest_path, Repository.path | 형제·동일·분리 노드 | 충족 |
| PATH 동률의 경로 문자열 사전순 최소 | 필수 | 4쪽 | shortest_path | 무작위 100그래프×36쌍을 모든 단순 경로와 대조 | 충족 |
| 모든 조상 출력·중복 제거 | 필수 | 5쪽 | find_ancestors | 루트·공유 조상·긴 체인 | 충족 |
| 대소문자 명령·공백 문자열·옵션·오류 | 필수 | 3쪽 | execute, require_args, 각 handler | 혼합 대소문자·한글·잘못된 인자 | 충족 |
| REPL·exit/quit | 필수 | 2쪽 | main | 별도 프로세스, EOF·정상 종료 | 충족 |
| 탐색·정렬·인덱싱 분리·주요 주석 | 필수 | 6쪽 | algorithms.py, index.py | 최종 소스 검토 | 충족 |
| 표준 정렬·그래프 라이브러리 금지 | 필수 | 6쪽 | 전체 소스 | AST 검사·import 검토 | 충족 |
| diff·merge·정렬 성능 비교 | 선택 | 5쪽 | 해당 없음 | 필수 범위와 분리 | 미구현 |
| 데이터 영속 저장 | 선택 사항 | 6쪽 | 해당 없음 | 종료 후 메모리 소멸 | 미구현, 원문에서 면제 |
