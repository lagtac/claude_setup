A comprehensive code review approach for Laravel applications with focus on security, performance, and maintainability.

## Review Methodology

Use the laravel-fullstack-expert agent to conduct thorough code reviews covering backend architecture, frontend integration, database design, and security considerations.

## Review Process

1. **Initial Assessment**
   - Understand the code's purpose and context
   - Review related documentation and tests
   - Check adherence to Laravel conventions
   - Identify the scope of review (files, features, etc.)

2. **Architecture Review**
   - Evaluate model relationships and database design
   - Review controller logic and API design
   - Assess service layer and business logic organization
   - Check middleware and authentication/authorization

3. **Security Analysis**
   - Verify input validation and sanitization
   - Check for SQL injection and XSS vulnerabilities
   - Review authentication and authorization implementation
   - Assess CSRF protection and secure headers

4. **Performance Evaluation**
   - Identify N+1 query problems
   - Review caching strategies and implementations
   - Check for inefficient database queries
   - Analyze asset loading and frontend performance

5. **Code Quality Assessment**
   - Check naming conventions and code readability
   - Review error handling and logging
   - Assess test coverage and quality
   - Verify accessibility compliance

## Medical Application Specific Checks
- **Data Privacy**: PHI handling, data anonymization, secure storage
- **Audit Trails**: User action logging, data change tracking
- **Accessibility**: WCAG 2.1 compliance, keyboard navigation
- **Reliability**: Error handling, data validation, backup strategies
- **Performance**: Image loading optimization, annotation rendering speed

## Review Output Structure
1. **Executive Summary** - Overall code quality and main concerns
2. **Critical Issues** - Security vulnerabilities, bugs, performance problems
3. **Architecture Improvements** - Design pattern recommendations
4. **Security Enhancements** - Specific security hardening suggestions
5. **Performance Optimizations** - Query optimization, caching improvements
6. **Code Quality Improvements** - Refactoring suggestions, best practices
7. **Testing Recommendations** - Test coverage gaps, testing strategy improvements

**Files/Features to Review:** $ARGUMENTS