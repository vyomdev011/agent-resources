# Architecture Audit Checklist

## Table of Contents
1. [Code Organization](#code-organization)
2. [Dependency Management](#dependency-management)
3. [Coupling & Cohesion](#coupling--cohesion)
4. [Testability](#testability)
5. [Error Handling](#error-handling)
6. [Architectural Patterns](#architectural-patterns)

---

## Code Organization

### Directory Structure
- [ ] Logical grouping of related files (by feature, layer, or domain)
- [ ] Consistent naming conventions for files and directories
- [ ] Clear separation between source code, tests, and configuration
- [ ] No deeply nested directories (>4 levels is a smell)

### File-Level Organization
- [ ] Single responsibility per file
- [ ] File sizes reasonable (<500 lines preferred, >1000 is a smell)
- [ ] Related code co-located (no scattered partial implementations)
- [ ] Clear import organization (stdlib, external, internal)

### Red Flags
- Catch-all files like `utils.py`, `helpers.js`, `common.go` with unrelated functions
- Circular directory dependencies
- Business logic mixed with infrastructure code
- UI code mixed with data access

---

## Dependency Management

### External Dependencies
- [ ] Dependencies explicitly declared (package.json, requirements.txt, go.mod)
- [ ] Version pinning strategy (exact vs range)
- [ ] No unused dependencies
- [ ] Dependencies regularly updated (check for security vulnerabilities)

### Internal Dependencies
- [ ] Clear dependency direction (higher layers depend on lower layers)
- [ ] No circular dependencies between modules
- [ ] Dependency injection used where appropriate
- [ ] Interfaces used at module boundaries

### Red Flags
- Direct instantiation of dependencies throughout codebase
- Importing implementation details across module boundaries
- God modules that everything depends on
- Dependency on concrete types rather than interfaces/protocols

---

## Coupling & Cohesion

### Coupling Assessment
- [ ] Modules communicate through well-defined interfaces
- [ ] Changes to one module rarely require changes to others
- [ ] No global mutable state shared between modules
- [ ] Event-driven or message-based communication where appropriate

### Cohesion Assessment
- [ ] Each module has a single, clear purpose
- [ ] Functions/methods within a class/module are related
- [ ] No "feature envy" (methods that use more of another class than their own)
- [ ] Data and behavior are co-located

### Coupling Types (from worst to best)
1. **Content coupling** - Module directly modifies another's internals
2. **Common coupling** - Modules share global data
3. **Control coupling** - Module controls another's flow via flags
4. **Stamp coupling** - Modules share composite data structures
5. **Data coupling** - Modules share only necessary data (GOOD)
6. **Message coupling** - Modules communicate via messages/events (GOOD)

### Red Flags
- Shotgun surgery needed for simple changes
- Feature envy (method uses many fields from another class)
- God classes/modules that know too much
- Leaky abstractions exposing implementation details

---

## Testability

### Unit Testability
- [ ] Pure functions where possible (deterministic, no side effects)
- [ ] Dependencies injectable (no hardcoded instantiation)
- [ ] Small, focused functions/methods
- [ ] State manageable and inspectable

### Integration Testability
- [ ] External services abstracted behind interfaces
- [ ] Database operations mockable/fakeable
- [ ] Clear seams between system components
- [ ] Environment configuration externalized

### Test Infrastructure
- [ ] Tests exist and run reliably
- [ ] Test coverage on critical paths
- [ ] Tests are fast enough for rapid feedback
- [ ] Clear separation between unit, integration, e2e tests

### Red Flags
- Static/global dependencies that can't be swapped
- Time-dependent logic without clock injection
- File system or network access buried in business logic
- Complex setup required to test simple functionality
- Tests that require external services to run

---

## Error Handling

### Error Design
- [ ] Errors are explicit (not hidden in return values or globals)
- [ ] Error types/codes are meaningful and actionable
- [ ] Errors contain context (what failed, why, where)
- [ ] Distinction between recoverable and fatal errors

### Error Propagation
- [ ] Errors propagated to appropriate handling layer
- [ ] No swallowed errors (catch-and-ignore)
- [ ] Stack traces preserved where useful
- [ ] Errors wrapped with context as they bubble up

### Error Recovery
- [ ] Retry logic for transient failures
- [ ] Circuit breakers for external dependencies
- [ ] Graceful degradation where possible
- [ ] Clean resource cleanup on failure

### Red Flags
- Empty catch blocks
- Generic error messages ("Something went wrong")
- Exceptions used for control flow
- Errors logged but not handled
- Missing error handling on I/O operations
- Panics/crashes on recoverable errors

---

## Architectural Patterns

### Layered Architecture
- [ ] Clear layer boundaries (presentation, business, data)
- [ ] Dependencies flow downward only
- [ ] Each layer has distinct responsibility
- [ ] Cross-cutting concerns handled consistently

### Domain-Driven Design (if applicable)
- [ ] Domain model reflects business concepts
- [ ] Ubiquitous language used consistently
- [ ] Bounded contexts clearly defined
- [ ] Domain logic isolated from infrastructure

### Clean/Hexagonal Architecture (if applicable)
- [ ] Core domain has no external dependencies
- [ ] Ports define interfaces at boundaries
- [ ] Adapters implement external integrations
- [ ] Use cases orchestrate domain operations

### Common Patterns to Look For
- Repository pattern for data access
- Service layer for business operations
- Factory pattern for complex object creation
- Strategy pattern for varying algorithms
- Observer/Event pattern for loose coupling

### Anti-Patterns to Flag
- **Big Ball of Mud** - No discernible architecture
- **Golden Hammer** - Using one pattern/technology for everything
- **Lava Flow** - Dead code preserved out of fear
- **Spaghetti Code** - Tangled control flow
- **Vendor Lock-in** - Deep coupling to specific providers

---

## Scoring Guide

For each category, assess as:
- **Strong** - Follows best practices, few issues
- **Adequate** - Generally good, some improvements possible
- **Weak** - Significant issues that should be addressed
- **Critical** - Architectural problems blocking maintainability

Prioritize findings by:
1. **Impact** - How much does this affect the codebase?
2. **Effort** - How hard is it to fix?
3. **Risk** - What's the cost of not fixing?

Focus recommendations on high-impact, reasonable-effort improvements first.
