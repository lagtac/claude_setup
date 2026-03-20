A systematic approach for debugging Laravel application issues with comprehensive diagnostics and solution strategies.

## Debugging Methodology

Use the laravel-fullstack-expert agent and  sequential-thinking to methodically isolate and resolve Laravel issues. Focus on systematic diagnosis rather than guessing, and always verify the fix works properly.

## Diagnostic Process

1. **Issue Assessment**
   - Reproduce the problem consistently
   - Check Laravel logs (`storage/logs/laravel.log`)
   - Review browser console for JavaScript errors
   - Examine database query logs if relevant

2. **System Health Check**
   - Verify database connectivity and migrations status
   - Check queue worker status if applicable
   - Review environment configuration (`.env`)
   - Confirm required services are running

3. **Code Investigation**
   - Trace through the request lifecycle
   - Check route definitions and middleware
   - Review controller logic and model relationships
   - Examine view rendering and JavaScript integration

4. **Testing & Validation**
   - Create minimal test case to isolate the issue
   - Test in different environments if available
   - Verify related functionality still works
   - Document the root cause and solution

## Common Laravel Debug Areas
- **Routes & Controllers**: Route resolution, parameter binding, middleware execution
- **Database**: Query issues, relationship problems, migration conflicts
- **Authentication**: Login failures, authorization issues, session problems
- **Views & Assets**: Blade compilation, asset loading, JavaScript integration
- **Background Jobs**: Queue failures, job processing, error handling
- **API Issues**: Response formatting, validation errors, CORS problems

## Tools & Commands
- `php artisan route:list` - Check route definitions
- `php artisan tinker` - Interactive debugging
- `php artisan queue:work --verbose` - Debug queue jobs
- `composer dump-autoload` - Fix autoloading issues
- `php artisan config:clear` - Clear configuration cache
- `php artisan view:clear` - Clear view cache

**Problem:** $ARGUMENTS