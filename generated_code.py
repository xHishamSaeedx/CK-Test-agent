def length_of_longest_substring(s: str) -> int:
    if not s:
        return 0
    char_set = set()
    left = 0
    result = 0
    for right in range(len(s)):
        while s[right] in char_set:
            char_set.remove(s[left])
            left += 1
        char_set.add(s[right])
        result = max(result, right - left + 1)
    return result