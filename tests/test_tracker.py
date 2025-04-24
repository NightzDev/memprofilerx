from memprofilerx.tracker import track_memory

def test_result_is_returned():
    @track_memory(interval=0.1)
    def dummy(): return 123
    result = dummy()
    assert result["result"] == 123
    assert isinstance(result["memory_usage"], list)
