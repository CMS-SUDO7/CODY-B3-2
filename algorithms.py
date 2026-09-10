# 그래프 탐색과 병합 정렬을 직접 구현한다.
# items는 정렬할 목록, key는 비교할 값을 꺼내는 함수이다.
def merge_sort(items, key):
    if len(items) <= 1:
        return list(items)
    middle = len(items) // 2
    left = merge_sort(items[:middle], key)
    right = merge_sort(items[middle:], key)
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if key(left[i]) <= key(right[j]):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

# 부모 수가 0이 된 커밋부터 꺼내는 Kahn 위상 정렬이다.
# 커밋 사전과 부모에서 자식으로 가는 연결 사전을 입력받는다.
def topological_order(commits, children):
    remaining = {}
    queue = []
    for commit_id, commit in commits.items():
        remaining[commit_id] = len(commit['parents'])
        if remaining[commit_id] == 0:
            queue.append(commit_id)
    result = []
    front = 0
    while front < len(queue):
        current = queue[front]
        front += 1
        result.append(current)
        for child in children[current]:
            remaining[child] -= 1
            if remaining[child] == 0:
                queue.append(child)
    if len(result) != len(commits):
        raise ValueError('Invalid graph: cycle detected')
    return result

# PATH에서만 부모 연결을 양방향으로 따라간다.
# 양방향 인접 목록과 출발·도착 식별자를 받는다.
def shortest_path(neighbors, start, target):
    queue = [start]
    previous = {start: None}
    front = 0
    while front < len(queue):
        current = queue[front]
        front += 1
        if current == target:
            path = []
            while current is not None:
                path.append(current)
                current = previous[current]
            return path[::-1]
        for neighbor in merge_sort(neighbors[current], lambda value: value):
            if neighbor not in previous:
                previous[neighbor] = current
                queue.append(neighbor)
    return None

# 스택을 이용한 반복형 깊이 우선 탐색으로 모든 조상을 찾는다.
# 전체 커밋 사전과 조상을 찾을 기준 커밋을 받는다.
def ancestor_ids(commits, start):
    stack = list(commits[start]['parents'])
    visited = set()
    result = []
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        result.append(current)
        stack.extend(commits[current]['parents'])
    return result
