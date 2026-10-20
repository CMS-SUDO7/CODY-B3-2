"""커밋과 브랜치 상태를 관리하고 알고리즘·인덱스를 연결한다."""

from dataclasses import dataclass
from datetime import datetime, timezone

from algorithms import find_ancestors, merge_sort, shortest_path, topological_order
from index import InvertedIndex


DEFAULT_BRANCH = "main"
HASH_WIDTH = 8


@dataclass(frozen=True)
class Commit:
    """부모는 생성 후 바꾸지 않아 기존 그래프에 역방향 간선을 막는다."""

    hash: str
    message: str
    author: str
    timestamp: datetime
    parents: tuple[str, ...]


class Repository:
    """HEAD는 현재 브랜치이며 실제 커밋은 branches에서 찾는다."""

    def __init__(self):
        self.user = None
        self.current_branch = None

        self.commits = {}
        self.branches = {}
        self.children = {}
        self.neighbors = {}

        self.index = InvertedIndex()
        self.next_commit_id = 1

    def require_initialized(self):
        """초기화 전에는 상태를 변경하거나 조회하지 못하게 한다."""
        if self.user is None:
            raise ValueError("Repository not initialized")

    def initialize(self, user):
        """반복 INIT는 데이터를 지우지 않고 거부한다."""
        if self.user is not None:
            raise ValueError("Repository already initialized")

        self.user = user
        self.current_branch = DEFAULT_BRANCH
        self.branches[DEFAULT_BRANCH] = None

    def create_branch(self, name):
        """새 브랜치가 현재 브랜치의 커밋 위치를 공유하게 한다."""
        self.require_initialized()
        if name in self.branches:
            raise ValueError(f"Branch already exists: {name}")

        self.branches[name] = self.branches[self.current_branch]

    def switch_branch(self, name):
        """이동만 수행하며 커밋이나 작성자를 바꾸지 않는다."""
        self.require_initialized()
        if name not in self.branches:
            raise ValueError(f"Unknown branch: {name}")

        self.current_branch = name

    def get_commit(self, commit_hash):
        """짧은 접두사 대신 출력된 전체 hash로 정확히 조회한다."""
        if commit_hash not in self.commits:
            raise ValueError(f"Unknown commit: {commit_hash}")

        return self.commits[commit_hash]

    def commit(self, message):
        """현재 HEAD만 부모로 삼는 새 노드와 검색 인덱스를 등록한다."""
        self.require_initialized()

        parent = self.branches[self.current_branch]
        parents = () if parent is None else (parent,)

        # 증가 정수는 세션에서 재사용하지 않으며 폭을 넘어도 잘리지 않는다.
        commit_hash = f"{self.next_commit_id:0{HASH_WIDTH}x}"
        commit = Commit(
            hash=commit_hash,
            message=message,
            author=self.user,
            timestamp=datetime.now(timezone.utc),
            parents=parents,
        )
        self.next_commit_id += 1

        self.commits[commit_hash] = commit
        self.children[commit_hash] = []
        self.neighbors[commit_hash] = list(parents)

        for parent_hash in parents:
            self.children[parent_hash].append(commit_hash)
            self.neighbors[parent_hash].append(commit_hash)

        self.index.add(commit)
        self.branches[self.current_branch] = commit_hash
        return commit

    def log(self, sort_by=None):
        """기본은 전체 저장소 위상 순서, 옵션은 독립된 오름차순이다."""
        self.require_initialized()

        if sort_by is None:
            hashes = topological_order(self.commits, self.children)
            return [self.commits[commit_hash] for commit_hash in hashes]

        if sort_by not in ("date", "author"):
            raise ValueError("Invalid args")

        field = "timestamp" if sort_by == "date" else "author"
        return merge_sort(
            list(self.commits.values()),
            key=lambda commit: getattr(commit, field),
        )

    def path(self, start, target):
        """없는 hash와 연결되지 않은 커밋을 구분한다."""
        self.require_initialized()
        self.get_commit(start)
        self.get_commit(target)

        return shortest_path(self.neighbors, start, target)

    def ancestors(self, commit_hash):
        """자기 자신을 제외한 조상을 DFS 방문 순서로 반환한다."""
        self.require_initialized()
        self.get_commit(commit_hash)

        hashes = find_ancestors(self.commits, commit_hash)
        return [self.commits[ancestor_hash] for ancestor_hash in hashes]

    def search(self, value, by_author=False):
        """전체 커밋을 훑지 않고 인덱스에서 받은 hash만 조회한다."""
        self.require_initialized()

        if by_author:
            hashes = self.index.search_author(value)
        else:
            hashes = self.index.search_keyword(value)

        return [self.commits[commit_hash] for commit_hash in hashes]
