# FAIL 평가 항목 보완 제출 자료

대상은 FAIL로 평가된 #2, #6, #8, #12, #13, #14, #16, #17, #18이다. Python 코드 수정 없이 README 설명과 인용 근거를 보완했다.

각 인용문은 README의 해당 항목에서 한 문단 전체를 연속해서 가져왔다. 인용문 내부에 생략이나 서로 떨어진 문장의 결합은 없다. 코드 위치는 실제 구현과 대조하기 위한 보조 근거이며, 줄 번호는 이번 문서 보완 시점 기준이다. #17의 개선안과 #18의 난수 전환 방안은 현재 기능이 아니라 검토 사항이다.

## 항목 #2: BRANCH · SWITCH · COMMIT

인용 출처: [README.md](../README.md), 124줄.

> `BRANCH <name>`은 현재 브랜치가 가리키는 커밋 hash를 새 브랜치에 복사하며 현재 브랜치는 바꾸지 않는다. `SWITCH <name>`은 존재하는 브랜치인지 확인한 뒤 `current_branch`를 해당 이름으로 바꾼다. `COMMIT <message>`는 현재 브랜치의 기존 커밋을 부모로 새 Commit을 생성하고, 커밋 저장소·그래프·역색인에 등록한 뒤 현재 브랜치가 새 hash를 가리키도록 갱신한다.

코드 대조 위치:

- [repository.py 54–68줄](../repository.py#L54-L68)
- [repository.py 77–105줄](../repository.py#L77-L105)
- [main.py 141–151줄](../main.py#L141-L151)

## 항목 #6: SEARCH · --author · LOG --sort-by

인용 출처: [README.md](../README.md), 130줄.

> `SEARCH <keyword>`는 메시지를 소문자·공백 기준 토큰으로 비교하는 키워드 역색인을 사용하며 여러 단어는 AND 조건으로 검색한다. `SEARCH --author=<name>`은 `--author=` 접두사를 제거한 작성자 전체 이름을 작성자 역색인에서 대소문자까지 일치시켜 조회한다. `LOG --sort-by=date`와 `LOG --sort-by=author`는 각각 timestamp와 author를 키로 직접 구현한 안정 병합 정렬을 적용하며, 다른 정렬 값은 `ValueError("Invalid args")`로 거부한다.

코드 대조 위치:

- [main.py 9–10줄](../main.py#L9-L10)
- [main.py 87–117줄](../main.py#L87-L117)
- [repository.py 107–122줄](../repository.py#L107-L122)
- [repository.py 140–149줄](../repository.py#L140-L149)
- [index.py 18–37줄](../index.py#L18-L37)

## 항목 #8: 커밋 hash · 해시 맵 · 중복과 충돌

인용 출처: [README.md](../README.md), 134줄.

> 커밋 hash는 `next_commit_id`를 1부터 증가시키며 최소 8자리 16진수 문자열로 변환한 식별자이고, `self.commits`라는 dict 해시 맵에 `hash → Commit`으로 보관한다. 정상적인 Repository API 사용에서는 카운터를 재사용하지 않고 자리수가 늘어나도 자르지 않으므로 같은 세션에서 식별자가 중복되지 않는다. 이 식별자는 내용 기반 암호학적 해시나 난수가 아니며, Python dict 내부의 해시 충돌은 키 동등성 비교로 구별된다. 같은 식별자 문자열을 다시 넣는 중복 검사는 별도로 없으므로 외부에서 카운터를 임의로 되돌리면 기존 항목을 덮어쓸 수 있다.

코드 대조 위치:

- [repository.py 32–38줄](../repository.py#L32-L38)
- [repository.py 84–95줄](../repository.py#L84-L95)
- [repository.py 70–75줄](../repository.py#L70-L75)

## 항목 #12: 사이클 검출 · Commit 불변성

인용 출처: [README.md](../README.md), 138줄.

> `topological_order`는 Kahn 위상 정렬 후 처리한 노드 수가 전체 커밋 수와 다르면 `raise ValueError("Cycle detected")`로 사이클을 알린다. `Commit`은 `@dataclass(frozen=True)`로 선언되고 `parents`는 tuple이므로 일반적인 필드 대입이나 부모 목록 변경으로 기존 이력을 수정할 수 없다. 현재 COMMIT API는 기존 노드를 수정하지 않고 새 노드가 기존 커밋을 부모로 참조하게 하여 사이클 생성을 방지한다. 다만 저장소의 dict와 그래프 목록 자체를 불변으로 만드는 설계는 아니며, 사이클 검출은 이 자료구조들이 일관된 그래프를 나타낸다는 전제를 따른다.

코드 대조 위치:

- [algorithms.py 31–54줄](../algorithms.py#L31-L54)
- [repository.py 14–22줄](../repository.py#L14-L22)
- [repository.py 81–105줄](../repository.py#L81-L105)

사이클 오류와 불변성 선언의 코드 원문:

`algorithms.py` 51–52줄:

```python
    if len(ordered) != len(commits):
        raise ValueError("Cycle detected")
```

`repository.py` 14–22줄:

```python
@dataclass(frozen=True)
class Commit:
    """부모는 생성 후 바꾸지 않아 기존 그래프에 역방향 간선을 막는다."""

    hash: str
    message: str
    author: str
    timestamp: datetime
    parents: tuple[str, ...]
```

## 항목 #13: 기본 LOG의 위상 정렬과 부모 우선 순서

인용 출처: [README.md](../README.md), 142줄.

> 옵션 없는 기본 `LOG`는 전체 저장소에 Kahn 위상 정렬을 적용하며, 부모가 모두 출력되어 남은 부모 수가 0이 된 커밋만 큐에 넣으므로 모든 부모를 자식보다 먼저 출력한다. 서로 조상·자손 관계가 없는 커밋 사이에서는 큐에 들어온 순서를 따르며 전체 생성 순서까지 보장하지는 않는다. `LOG --sort-by=date|author`는 별도의 키 정렬이므로 기본 LOG의 부모 우선 보장을 적용하지 않는다.

코드 대조 위치:

- [repository.py 107–113줄](../repository.py#L107-L113)
- [algorithms.py 31–54줄](../algorithms.py#L31-L54)
- [main.py 89–91줄](../main.py#L89-L91)

## 항목 #14: PATH의 BFS · 무방향 · 최단 경로

인용 출처: [README.md](../README.md), 146줄.

> `PATH`는 부모와 자식 양쪽을 이웃으로 등록한 무방향 그래프에서, 가중치 없는 간선 수가 최소인 최단 경로를 BFS로 구한다. `shortest_path`는 목적지에서 역방향 BFS로 거리를 계산한 뒤 출발지에서 거리가 1씩 줄어드는 이웃을 골라 경로를 복원한다. 최단 경로 동률이면 공백 없는 `hash1->hash2->...` 문자열의 사전순으로 선택하고, 연결되지 않으면 빈 목록을 반환하여 CLI가 `No path`를 출력한다. 출발지와 목적지가 같으면 해당 hash 하나를 반환하며, 존재하지 않는 hash는 탐색 전에 오류로 처리한다.

코드 대조 위치:

- [repository.py 95–101줄](../repository.py#L95-L101)
- [repository.py 124–130줄](../repository.py#L124-L130)
- [algorithms.py 75–106줄](../algorithms.py#L75-L106)
- [main.py 120–130줄](../main.py#L120-L130)

## 항목 #16: 역색인 구조 · 조회 복잡도 · 순회와 비교

인용 출처: [README.md](../README.md), 150줄.

> `InvertedIndex`는 `keywords: 단어 → hash 목록`, `authors: 작성자 → hash 목록`의 두 dict로 구성되며, `dict.get`으로 특정 키의 후보 목록을 찾는 연산은 평균 O(1)이다. 이는 문자열 해싱 비용을 별도로 보는 평균 복잡도이며 전체 검색 결과를 만드는 시간이 O(1)이라는 뜻은 아니다. 키워드 검색은 후보 목록들을 set으로 변환한 뒤 가장 짧은 목록만 순회하고 각 hash가 모든 set에 속하는지 비교한다. 고유 검색 단어 수를 k, 각 후보 목록 길이를 Lᵢ, 최단 목록 길이를 m이라 하면 토큰화 이후 평균 시간은 O(k + ΣLᵢ + k·m)이고, 작성자 검색은 결과 r개의 목록 복사 때문에 O(r + 1)이다. Repository는 검색된 hash만 `self.commits`에서 조회하며 전체 커밋을 별도로 순회하지 않는다.

코드 대조 위치:

- [index.py 4–37줄](../index.py#L4-L37)
- [repository.py 140–149줄](../repository.py#L140-L149)

순회와 비교의 코드 원문 (`index.py` 24–33줄):

```python
        postings = [self.keywords.get(word, []) for word in words]
        # 가장 짧은 후보 목록을 기준으로 삼아 교집합 검사량을 줄인다.
        smallest = min(postings, key=len)
        posting_sets = [set(values) for values in postings]

        return [
            commit_hash
            for commit_hash in smallest
            if all(commit_hash in posting_set for posting_set in posting_sets)
        ]
```

## 항목 #17: 규모 증가 시 병목과 개선 방향

인용 출처: [README.md](../README.md), 154줄.

> 현재 구현은 커밋 V개와 부모 간선 E개를 메모리에 보관하며, 기본 LOG와 PATH의 그래프 탐색 시간은 O(V + E), 옵션 LOG는 키 비교 비용을 일정하게 볼 때 O(V log V)이다. 역색인의 전체 hash 등록 수를 P라고 하면 그래프와 인덱스 저장 공간은 메시지·키 문자열 자체의 크기를 제외하고 O(V + E + P)이며, 흔한 검색어의 긴 후보 목록은 조회마다 set을 만드는 시간과 임시 메모리의 병목이 된다. 개선안으로는 정렬된 후보 목록의 교집합 또는 비트맵 사용, 영속 저장소와 결과 페이지 처리, 반복 조회 캐시를 검토할 수 있다. 더 큰 규모에서는 단어·작성자 키별로 인덱스를 분산하고 여러 단어의 후보 교집합을 조정하는 계층을 둘 수 있으나, 커밋 저장과 인덱스 갱신의 일관성 및 분산 결과의 순서 유지도 함께 설계해야 한다. 이 개선안과 인덱스 분산은 현재 구현되지 않았다.

코드 대조 위치:

- [repository.py 32–35줄](../repository.py#L32-L35)
- [repository.py 107–130줄](../repository.py#L107-L130)
- [algorithms.py 6–54줄](../algorithms.py#L6-L54)
- [algorithms.py 75–106줄](../algorithms.py#L75-L106)
- [index.py 24–33줄](../index.py#L24-L33)

## 항목 #18: 카운터와 난수 · 재현성 · 테스트 고려사항

인용 출처: [README.md](../README.md), 158줄.

> 현재 hash 생성은 난수 대신 증가 카운터를 사용하므로 새 Repository에서 같은 순서로 정상 COMMIT을 실행하면 같은 hash와 부모 관계를 재현할 수 있다. 다만 timestamp는 `datetime.now(timezone.utc)`이므로 실행마다 달라지고 전체 출력까지 동일하지는 않다. 테스트에서는 hash·부모·브랜치 이동을 고정된 기대값으로 비교하되 시각은 별도 검증하거나 시계를 고정해야 한다. 난수 식별자로 변경한다면 충돌 확인과 재시도가 필요하고, 테스트는 난수 생성기 주입이나 반환된 식별자에 기반한 비교로 바꿔야 한다. 현재 카운터 식별자는 다른 세션에서도 다시 1부터 시작하므로 세션 간 전역 유일성은 보장하지 않는다.

코드 대조 위치:

- [repository.py 38줄](../repository.py#L38-L38)
- [repository.py 84–95줄](../repository.py#L84-L95)
