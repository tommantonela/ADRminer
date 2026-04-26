# ADRminer Agents Tests

This directory contains tests for the ADRminer Deep Agents integration.

## Test Files

### `test_middleware_loading.py`

Comprehensive tests for Deep Agents middleware and backend loading functionality.

#### Test Coverage:

1. **Graceful Degradation Tests**
   - `test_deep_agents_not_installed_graceful_degradation`: Verifies that the agent factory handles missing Deep Agents dependencies gracefully
   - `test_middleware_not_available_message`: Tests that appropriate console messages are displayed when middleware is not available

2. **Middleware Loading Tests**
   - `test_middleware_loaded_successfully`: Verifies that middleware is correctly loaded when available
   - `test_console_messages_displayed`: Tests that appropriate console messages are shown based on availability

3. **Backend Configuration Tests**
   - `test_memory_backend_configuration`: Tests that memory backend is configured correctly for both persistent and ephemeral modes
   - `test_filesystem_backend_configuration`: Verifies filesystem backend configuration with correct parameters

4. **Interrupt Rules Tests**
   - `test_interrupt_rules_configuration`: Tests that human-in-the-loop interrupt rules are set up correctly

5. **Agent Wrapper Tests**
   - `test_adrminer_agent_wrapper_initialization`: Tests that the AdrminerAgent wrapper initializes correctly

6. **Thread Safety Tests**
   - `test_thread_local_session_isolation`: Verifies that thread-local session isolation works correctly across multiple threads

## Running the Tests

### Run all agent tests:
```bash
pytest tests/test_agents/ -v
```

### Run specific test file:
```bash
pytest tests/test_agents/test_middleware_loading.py -v
```

### Run specific test:
```bash
pytest tests/test_agents/test_middleware_loading.py::TestMiddlewareLoading::test_middleware_loaded_successfully -v
```

### Run with coverage:
```bash
pytest tests/test_agents/ --cov=adrminer.agents --cov-report=html
```

## Test Requirements

- pytest
- pytest-mock (optional, for advanced mocking)

## Notes

These tests use extensive mocking to avoid requiring actual Deep Agents installation during testing. This allows the tests to run in CI/CD environments and ensures that the graceful degradation behavior is properly tested.

The tests verify:
- Correct behavior when Deep Agents is installed
- Graceful degradation when Deep Agents is not installed
- Proper configuration of middleware and backends
- Thread safety of session management
- User-facing console messages