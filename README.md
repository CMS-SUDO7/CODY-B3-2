# B3-2 Mini Git — 커밋 이력과 브랜치 관리  

파일이 언제, 누구에 의해, 어떤 설명으로 변경되었는지 **커밋 메타데이터**로 기록하는 학습용 CLI입니다. 파일의 실제 내용·스냅샷은 추적하지 않으며, 종료하면 기록이 사라집니다.  

## 1. 실행부터 해 보기  

- 요구 환경: **Python 3.10 이상**. 외부 패키지 설치는 필요 없습니다.  

```bash
python --version  
python main.py  
```

실행 후 `mini-git>`에 아래 명령을 **한 줄씩** 입력합니다.  

```text
INIT "Alice Smith"  
COMMIT "Initial commit"  
BRANCH feature  
SWITCH feature  
COMMIT "Add login feature"  
SWITCH main  
COMMIT "Add payment feature"  
LOG  
SEARCH login  
SEARCH "add feature"  
SEARCH --author="Alice Smith"  
LOG --sort-by=date  
LOG --sort-by=author  
PATH 0000000000000002 0000000000000003  
ANCESTORS 0000000000000003  
quit  
```

새 실행에서는 커밋 식별자가 순서대로 `0000000000000001`, `0000000000000002`, `0000000000000003`입니다. 다른 커밋을 먼저 만들었다면 출력된 식별자를 사용하세요.  

예상 핵심 결과:  

- `LOG`: 1번 → 2번 → 3번. 현재 main에서 실행해도 feature 커밋을 포함합니다.  
- `SEARCH login`: 2번 한 건. `SEARCH "add feature"`: 2번과 3번.  
- 작성자 검색: 세 건. 날짜·작성자 정렬 모두 이 예시에서는 1, 2, 3 순서입니다.  
- `PATH`: `Path: 0000000000000002->0000000000000001->0000000000000003`  
- `ANCESTORS ...3`: 1번만 출력. 다른 브랜치의 2번은 조상이 아닙니다.  
- 로그에 `hash | author | timestamp`와 다음 줄의 메시지가 표시됩니다. timestamp는 실행 시각에 따라 달라집니다.  

## 2. 파일 구성과 제출  

| 파일 | 역할 |  
| --- | --- |
| `main.py` | 실행 시작점, 따옴표 파싱, 명령 검증, REPL, 결과 출력 |  
| `repository.py` | 커밋과 브랜치 상태, HEAD, 역색인 갱신·검색 |  
| `algorithms.py` | 병합 정렬, 위상 정렬, BFS 최단 경로, DFS 조상 탐색 |  
| `README.md` | 실행법, 명령 규칙, 요구사항 대응표 |  
| `docs/basic_knowledge.md` | 기초 문법, 용어, 핵심 원리, 복잡도, 연습과 추천 도서 |  
| `docs/code_translation.md` | 전체 호출 관계, 데이터 추적, 소스 한 줄씩 해설 |  

PDF는 엔트리 포인트 1개와 README를 요구하며 알고리즘 분리를 요구합니다. 실행 시작점은 `main.py` 하나이고, 기능 모듈 두 개를 함께 제출해야 합니다. **main.py만 복사하면 실행되지 않습니다.**  

## 3. 명령 규칙과 정한 정책  

| 명령 | 동작 |  
| --- | --- |
| `INIT <user_name>` | main 브랜치와 현재 사용자 생성 |  
| `BRANCH <branch_name>` | 현재 HEAD를 가리키는 브랜치 생성. 자동 전환하지 않음 |  
| `SWITCH <branch_name>` | 현재 브랜치 전환 |  
| `COMMIT <message>` | 현재 HEAD가 부모인 커밋 생성, 브랜치 끝점 이동, 역색인 갱신 |  
| `LOG` | 저장소 전체를 부모가 먼저 나오는 위상 순서로 출력 |  
| `LOG --sort-by=date` | UTC timestamp 오름차순 |  
| `LOG --sort-by=author` | 작성자 문자열의 파이썬 사전순 오름차순 |  
| `PATH <commit1> <commit2>` | 부모 연결을 무방향으로 본 최소 간선 경로 |  
| `ANCESTORS <hash>` | 자신을 제외한 모든 조상, DFS 발견 순서, 중복 없음 |  
| `SEARCH <keyword>` | 소문자 공백 토큰의 정확 일치. 여러 토큰은 AND 검색 |  
| `SEARCH --author=<name>` | 작성자 이름 전체 정확 일치 |  
| `exit` / `quit` | 종료. 메모리 기록도 소멸 |  

- 명령어만 대소문자를 구분하지 않습니다. `iNiT`도 허용합니다. 옵션 이름·값은 PDF 표기 그대로 소문자를 사용합니다.  
- 공백 포함 문자열은 따옴표로 묶습니다. `COMMIT "Add login"`, `SEARCH --author="Alice Smith"`.  
- 사용자명·브랜치명은 대소문자와 문자열 내부 공백을 보존합니다. 빈 값이나 공백뿐인 값은 거부합니다.  
- 키워드는 부분 문자열 검색이 아닙니다. `login`은 `LOGIN`과 일치하지만 `log`나 `login,`과 일치하지 않습니다. 쉼표 등 문장부호를 제거하지 않는 PDF 최소 토큰 규칙입니다.  
- 여러 단어 검색은 모든 단어를 포함한 커밋을 찾습니다. 연속된 문장 검색은 아닙니다.  
- 색인 목록과 정렬 동률은 생성 순서를 유지합니다. 기본 위상 순서는 부모 없는 커밋과 준비된 자식의 대기열 삽입 순서로 결정합니다.  
- 기본 `LOG`만 부모 우선 규칙을 보장합니다. 명시적으로 정렬한 로그는 해당 정렬 기준이 우선입니다.  
- `PATH`는 동일 길이 경로 중 `hash1->hash2->...` 문자열이 사전순으로 가장 작은 것을 선택합니다. 16자리 고정 길이 식별자와 이웃 사전순 BFS를 사용합니다. 자기 자신으로의 경로는 한 노드, 0개 간선입니다.  
- `hash` 필드는 증가 카운터를 16자리 16진수로 표현한 식별자입니다. 실제 Git의 내용 기반 암호학적 해시와 다릅니다. 같은 세션에서 번호를 재사용하지 않으며 범위 소진 시 오류 처리합니다.  
- 재차 `INIT`하면 기존 자료를 지우지 않고 `Repository already initialized`를 출력합니다. 새 저장소는 종료 후 다시 실행하세요.  
- CLI에서 작성자는 INIT으로 한 번 설정합니다. 작성자 변경 명령은 PDF에 없으므로 추가하지 않았습니다. 여러 작성자 정렬은 내부 객체를 이용해 별도 검증했습니다.  
- 보너스인 파일 diff, MERGE 명령, 두 정렬 알고리즘 성능 비교는 포함하지 않았습니다. 내부 커밋 구조와 탐색은 다중 부모 DAG도 지원합니다.  

## 4. 요구사항 대응표  


| 요구사항 | 구현 파일·함수 | 확인 방법 | 확인 결과 |  
| --- | --- | --- | --- |
| INIT/main/HEAD/작성자 | repository.py `Repository.__init__`, main.py `execute` | 빈 HEAD, 기본 브랜치 확인 | PASS |  
| BRANCH/SWITCH/COMMIT | repository.py `branch`, `switch`, `commit` | 분기 후 각 브랜치 끝점과 부모 대조 | PASS |  
| 필수 커밋 필드, 유일 ID | repository.py `add_commit` | 필드 확인, 1,500개 생성 | PASS |  
| DAG, 0개 이상 부모 | repository.py `add_commit` | 기존 부모 검사, 독립 루트·다중 부모 생성 | PASS |  
| 부모 먼저 LOG | algorithms.py `topological_order` | 분기·다중 부모에서 부모 위치 대조 | PASS |  
| 무방향 최단 경로 | algorithms.py `shortest_path` | 형제 간 경로, 자기 경로, 단절 | PASS |  
| 최단 경로 동률 사전순 | algorithms.py `shortest_path` | 다이아몬드 및 1,024개 그래프·25,600개 경로 조건 완전탐색 대조 | PASS |  
| 모든 조상, 중복 제거 | algorithms.py `ancestor_ids` | 공통 조상과 1,500개 깊은 이력 | PASS |  
| keyword/author 역색인 | repository.py `add_commit`, `search` | 대소문자·중복 단어·정확 작성자·AND | PASS |  
| 직접 정렬, date/author | algorithms.py `merge_sort`, repository.py `log` | 빈 값·역순·동률 안정성·다른 작성자 | PASS |  
| 표준 정렬 API 금지 | 전체 Python 소스 | AST로 호출 검사 | PASS |  
| 따옴표·명령 대소문자 | main.py `main`, `validate` | 공백 포함 사용자·메시지, InIt | PASS |  
| 오류 후 계속 입력 | main.py `main` | 인자 수, 따옴표, 없는 브랜치·커밋, 옵션 오류 | PASS |  
| REPL 종료 | main.py `main` | quit, EOF, Ctrl+C 처리 확인 | quit·EOF 실행, Ctrl+C 코드 검토 |  
| 기능별 분리·한국어 주석 | 3개 Python 파일 | 소스 검토 | 확인 |  

## 5. 오류와 해결  

| 출력/증상 | 이유와 해결 |  
| --- | --- |
| `Invalid args` | 인자 개수·따옴표·옵션을 확인. 공백 포함 메시지는 따옴표 필수 |  
| `Unknown branch: ...` | BRANCH로 먼저 생성. 브랜치 이름의 대소문자도 확인 |  
| `Branch already exists: ...` | 다른 이름을 선택하거나 SWITCH 사용 |  
| `Unknown commit: ...` | LOG에 나온 16자리 식별자를 전체 복사. 축약 해시는 미지원 |  
| `Repository not initialized...` | INIT을 먼저 입력 |  
| `No path` | 두 커밋이 서로 다른 연결 성분에 있음 |  
| `No commits` | 빈 저장소, 검색 결과 없음 또는 루트 커밋의 조상 없음 |  
| `ModuleNotFoundError` | 세 Python 파일을 같은 폴더에 두고 실행 |  
| 기록이 사라짐 | 요구사항상 메모리 저장. 종료 후 복구 기능 없음 |  
