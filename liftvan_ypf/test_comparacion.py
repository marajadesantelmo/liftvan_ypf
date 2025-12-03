def compare_companies(data):
    filtered_data = [d for d in data if d is not None and d != 0]
    if not filtered_data:
        return None
    return max(filtered_data)

def test_compare_companies():
    assert compare_companies([1, 2, 3]) == 3
    assert compare_companies([0, 1, 2]) == 2
    assert compare_companies([None, 0, 1]) == 1
    assert compare_companies([None, None, 0]) == None
    assert compare_companies([float('nan'), 1, 2]) == 2
    assert compare_companies([float('nan'), float('nan'), 0]) == None