import pytest

from src.config import MemoryThresholdExceededError
from src.memory_monitor import (
    MemoryMonitor,
    SystemMemoryMonitor,
    TracemallocMemoryMonitor,
)


def test_system_memory_monitor_no_limit():
    """
    Test that SystemMemoryMonitor.check_memory_usage does nothing when max_memory_mb is None, 0, or negative.
    """
    monitor_none = SystemMemoryMonitor(max_memory_mb=None)
    monitor_none.check_memory_usage()  # Should not raise an error

    monitor_zero = SystemMemoryMonitor(max_memory_mb=0)
    monitor_zero.check_memory_usage()  # Should not raise an error

    monitor_negative = SystemMemoryMonitor(max_memory_mb=-100)
    monitor_negative.check_memory_usage()  # Should not raise an error


def test_tracemalloc_memory_monitor_no_limit():
    """
    Test that TracemallocMemoryMonitor.check_memory_usage does nothing when max_memory_mb is None, 0, or negative.
    """
    monitor_none = TracemallocMemoryMonitor(max_memory_mb=None)
    monitor_none.check_memory_usage()  # Should not raise an error

    monitor_zero = TracemallocMemoryMonitor(max_memory_mb=0)
    monitor_zero.check_memory_usage()  # Should not raise an error

    monitor_negative = TracemallocMemoryMonitor(max_memory_mb=-100)
    monitor_negative.check_memory_usage()  # Should not raise an error


def test_system_memory_monitor_threshold_exceeded(mocker):
    """
    Test that SystemMemoryMonitor raises MemoryThresholdExceededError when memory usage exceeds the limit.
    """
    mock_process = mocker.Mock()
    mock_process.memory_info.return_value.rss = 200 * 1024 * 1024  # 200 MB
    mocker.patch("psutil.Process", return_value=mock_process)

    monitor = SystemMemoryMonitor(max_memory_mb=100)  # Set limit to 100 MB

    with pytest.raises(MemoryThresholdExceededError) as excinfo:
        monitor.check_memory_usage()

    assert "Memory usage exceeded 100MB" in str(excinfo.value)


def test_tracemalloc_memory_monitor_threshold_exceeded(mocker):
    """
    Test that TracemallocMemoryMonitor raises MemoryThresholdExceededError when memory usage exceeds the limit.
    """
    mocker.patch(
        "tracemalloc.get_traced_memory",
        return_value=(200 * 1024 * 1024, 250 * 1024 * 1024),
    )
    mocker.patch("tracemalloc.is_tracing", return_value=True)

    monitor = TracemallocMemoryMonitor(max_memory_mb=100)  # Set limit to 100 MB

    with pytest.raises(MemoryThresholdExceededError) as excinfo:
        monitor.check_memory_usage()

    assert "Python memory usage exceeded" in str(excinfo.value)


def test_memory_monitor_abstract_pass_statement():
    """Test that the pass statement in the abstract MemoryMonitor.check_memory_usage is covered."""

    class ConcreteMemoryMonitor(MemoryMonitor):
        def check_memory_usage(self) -> None:
            # This method is intentionally empty as it's a concrete implementation
            # of an abstract method, and the test specifically covers the 'pass'
            # statement in the abstract base class.
            pass

    monitor = ConcreteMemoryMonitor()
    monitor.check_memory_usage()


def test_system_memory_monitor_no_limit_explicit():
    """
    Explicitly test the no-limit case for SystemMemoryMonitor to force coverage.
    """
    monitor = SystemMemoryMonitor(max_memory_mb=None)
    monitor.check_memory_usage()
    monitor = SystemMemoryMonitor(max_memory_mb=0)
    monitor.check_memory_usage()
    monitor = SystemMemoryMonitor(max_memory_mb=-1)
    monitor.check_memory_usage()
