from datetime import datetime, timezone
from algorithms import ancestor_ids, merge_sort, shortest_path, topological_order

# 저장소의 상태와 역색인을 한 객체 안에서 관리한다.
class Repository:
    # Repository(user)를 만들 때 자동 실행되는 초기화 함수이다.
    def __init__(self, user):
        self.user = user
        self.commits = {}
        self.branches = {'main': None}
        self.current_branch = 'main'
        self.counter = 0
        self.children = {}
        self.neighbors = {}
        self.keyword_index = {}
        self.author_index = {}

    # 현재 브랜치의 마지막 커밋을 조회하는 함수이다.
    def head(self):
        return self.branches[self.current_branch]

    # 현재 위치에서 새 브랜치를 만드는 함수이다.
    def branch(self, name):
        if name in self.branches:
            raise ValueError('Branch already exists: ' + name)
        self.branches[name] = self.head()

    # 현재 브랜치를 변경하는 함수이다.
    def switch(self, name):
        if name not in self.branches:
            raise ValueError('Unknown branch: ' + name)
        self.current_branch = name

    # 커밋 식별자가 유효한지 공통으로 검사한다.
    def require_commit(self, commit_id):
        if commit_id not in self.commits:
            raise ValueError('Unknown commit: ' + commit_id)

    # CLI의 일반 커밋을 만드는 함수이다.
    def commit(self, message):
        parent = self.head()
        parents = []
        if parent is not None:
            parents.append(parent)
        return self.add_commit(message, parents)

    # 기존 커밋만 부모로 받으므로 새 커밋에서 순환이 생길 수 없다.
    # 0개 이상의 부모를 지원하는 내부 생성 함수이다. CLI는 commit을 사용한다.
    def add_commit(self, message, parents):
        parents = list(dict.fromkeys(parents))
        for parent in parents:
            self.require_commit(parent)
        if self.counter >= 16 ** 16 - 1:
            raise ValueError('Commit ID space exhausted')
        self.counter += 1
        commit_id = f'{self.counter:016x}'
        record = {
            'hash': commit_id,
            'message': message,
            'author': self.user,
            'timestamp': datetime.now(timezone.utc).isoformat(timespec='microseconds'),
            'parents': parents,
        }
        self.commits[commit_id] = record
        self.children[commit_id] = []
        self.neighbors[commit_id] = list(parents)
        for parent in parents:
            self.children[parent].append(commit_id)
            self.neighbors[parent].append(commit_id)
        self.author_index.setdefault(self.user, []).append(commit_id)
        for word in set(message.lower().split()):
            self.keyword_index.setdefault(word, []).append(commit_id)
        self.branches[self.current_branch] = commit_id
        return commit_id

    # 전체 저장소 로그를 기본 위상 순서 또는 지정 기준으로 반환한다.
    def log(self, sort_by=None):
        if sort_by is None:
            return topological_order(self.commits, self.children)
        field = {'date': 'timestamp', 'author': 'author'}[sort_by]
        return merge_sort(list(self.commits), lambda cid: self.commits[cid][field])

    # 두 커밋 사이 무방향 최단 경로를 구한다.
    def path(self, start, target):
        self.require_commit(start)
        self.require_commit(target)
        return shortest_path(self.neighbors, start, target)

    # 기준 커밋의 모든 조상을 조회한다.
    def ancestors(self, commit_id):
        self.require_commit(commit_id)
        return ancestor_ids(self.commits, commit_id)

    # 기본은 단어 검색이고 by_author가 참이면 작성자 검색이다.
    def search(self, query, by_author=False):
        if by_author:
            return list(self.author_index.get(query, []))
        words = list(dict.fromkeys(query.lower().split()))
        if not words:
            return []
        first = self.keyword_index.get(words[0], [])
        candidates = set(first)
        for word in words[1:]:
            candidates.intersection_update(self.keyword_index.get(word, []))
        return [cid for cid in first if cid in candidates]
