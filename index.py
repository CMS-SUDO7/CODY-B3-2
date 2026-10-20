"""메시지 단어와 작성자로 커밋 후보를 바로 찾는 역색인이다."""


class InvertedIndex:
    """생성 순서대로 hash 목록을 보관하고 같은 단어는 한 번만 등록한다."""

    def __init__(self):
        self.keywords = {}
        self.authors = {}

    def add(self, commit):
        """커밋 생성 시에만 두 인덱스를 갱신한다."""
        for word in set(commit.message.lower().split()):
            self.keywords.setdefault(word, []).append(commit.hash)

        self.authors.setdefault(commit.author, []).append(commit.hash)

    def search_keyword(self, keyword):
        """여러 단어는 모든 단어가 들어간 메시지를 찾는 AND 검색이다."""
        words = list(set(keyword.lower().split()))
        if not words:
            return []

        postings = [self.keywords.get(word, []) for word in words]
        # 가장 짧은 후보 목록을 기준으로 삼아 교집합 검사량을 줄인다.
        smallest = min(postings, key=len)
        posting_sets = [set(values) for values in postings]

        return [
            commit_hash
            for commit_hash in smallest
            if all(commit_hash in posting_set for posting_set in posting_sets)
        ]

    def search_author(self, author):
        """작성자 이름은 대소문자까지 일치시켜 찾고 복사본을 반환한다."""
        return list(self.authors.get(author, []))
