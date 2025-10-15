import pytest
from src.memory_monitor import SystemMemoryMonitor
from src.config import MemoryThresholdExceededError

def test_system_memory_monitor_no_limit():
    """
    Test that check_memory_usage does nothing when max_memory_mb is None or 0.
    """
    monitor_none = SystemMemoryMonitor(max_memory_mb=None)
    monitor_none.check_memory_usage()  # Should not raise an error

    monitor_zero = SystemMemoryMonitor(max_memory_mb=0)
    monitor_zero.check_memory_usage()  # Should not raise an error

    monitor_negative = SystemMemoryMonitor(max_memory_mb=-100)
    monitor_negative.check_memory_usage() # Should not raise an error

def test_system_memory_monitor_threshold_exceeded(mocker):
    """
    Test that check_memory_usage raises MemoryThresholdExceededError when memory usage exceeds the limit.
    """
    # Mock psutil.Process().memory_info().rss
    mock_process = mocker.Mock()
    mock_process.memory_info.return_value.rss = 200 * 1024 * 1024  # 200 MB
    mocker.patch('psutil.Process', return_value=mock_process)

    monitor = SystemMemoryMonitor(max_memory_mb=100)  # Set limit to 100 MB

    with pytest.raises(MemoryThresholdExceededError) as excinfo:
        monitor.check_memory_usage()

    assert "Memory usage exceeded 100MB" in str(excinfo.value)

from src.memory_monitor import MemoryMonitor

def test_memory_monitor_abstract_pass_statement():
    """Test that the pass statement in the abstract MemoryMonitor.check_memory_usage is covered."""
    class ConcreteMemoryMonitor(MemoryMonitor):
        def check_memory_usage(self) -> None:
            pass

    monitor = ConcreteMemoryMonitor()
    monitor.check_memory_usage()
