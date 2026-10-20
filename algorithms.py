"""표준 정렬 API 없이 정렬하고, 커밋 그래프를 직접 탐색한다."""

from collections import deque


def merge_sort(items, key):
    """동률이면 왼쪽 항목을 먼저 선택하는 안정 병합 정렬이다."""
    if len(items) < 2:
        return list(items)

    middle = len(items) // 2
    left = merge_sort(items[:middle], key)
    right = merge_sort(items[middle:], key)

    merged = []
    left_index = right_index = 0

    while left_index < len(left) and right_index < len(right):
        if key(left[left_index]) <= key(right[right_index]):
            merged.append(left[left_index])
            left_index += 1
        else:
            merged.append(right[right_index])
            right_index += 1

    merged.extend(left[left_index:])
    merged.extend(right[right_index:])
    return merged


def topological_order(commits, children):
    """부모 수가 0이 된 노드부터 출력하는 Kahn 알고리즘이다."""
    remaining = {
        commit_hash: len(commit.parents)
        for commit_hash, commit in commits.items()
    }
    ready = deque(
        commit_hash for commit_hash in commits if remaining[commit_hash] == 0
    )
    ordered = []

    while ready:
        current = ready.popleft()
        ordered.append(current)

        for child in children[current]:
            remaining[child] -= 1
            if remaining[child] == 0:
                ready.append(child)

    if len(ordered) != len(commits):
        raise ValueError("Cycle detected")

    return ordered


def find_ancestors(commits, start):
    """재귀 한도에 걸리지 않도록 스택으로 모든 부모를 방문한다."""
    visited = set()
    stack = list(commits[start].parents)
    result = []

    while stack:
        current = stack.pop()
        if current in visited:
            continue

        visited.add(current)
        result.append(current)
        stack.extend(commits[current].parents)

    return result


def shortest_path(neighbors, start, target):
    """역방향 BFS 거리와 사전순 선택으로 최단 경로 동률을 해결한다."""
    distance = {target: 0}
    queue = deque([target])

    while queue:
        current = queue.popleft()
        for neighbor in neighbors[current]:
            if neighbor not in distance:
                distance[neighbor] = distance[current] + 1
                queue.append(neighbor)

    if start not in distance:
        return []

    path = [start]

    while path[-1] != target:
        current = path[-1]
        best = None

        for neighbor in neighbors[current]:
            if distance.get(neighbor) != distance[current] - 1:
                continue

            # 구분자까지 비교해야 한 hash가 다른 hash의 접두사여도 맞다.
            if best is None or neighbor + "->" < best + "->":
                best = neighbor

        path.append(best)

    return path
