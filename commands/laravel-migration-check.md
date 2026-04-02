---
description: Validate Laravel migrations for safety, performance, and rollback
---

A systematic approach for validating Laravel database migrations with focus on data integrity, performance, and rollback safety.

## Migration Validation Process

Use the laravel-fullstack-expert agent to thoroughly analyze database migrations to ensure they are safe, performant, and maintain data integrity.

## Validation Steps

1. **Pre-Migration Analysis**
   - Review migration files for syntax and logic errors
   - Check for potential data loss scenarios
   - Verify foreign key constraints and relationships
   - Assess impact on existing data

2. **Safety Verification**
   - Ensure migrations are reversible (proper down() methods)
   - Check for destructive operations (DROP, TRUNCATE)
   - Verify backup procedures for production data
   - Test migration rollback scenarios

3. **Performance Assessment**
   - Identify potentially slow operations on large tables
   - Review index creation and optimization
   - Check for blocking operations during migration
   - Assess downtime requirements

4. **Data Integrity Check**
   - Verify referential integrity constraints
   - Check for orphaned records after migration
   - Validate data transformation logic
   - Ensure proper handling of NULL values

5. **Testing Strategy**
   - Test migrations on copy of production data
   - Verify application functionality after migration
   - Test rollback procedures
   - Document any manual intervention required

## Migration Safety Checklist
- [ ] Migration has proper rollback (down) method
- [ ] No data loss without explicit confirmation
- [ ] Foreign key constraints are properly handled
- [ ] Indexes are created for performance-critical queries
- [ ] Migration tested on realistic dataset
- [ ] Rollback tested and verified
- [ ] Production backup plan confirmed
- [ ] Downtime window assessed and approved

## Common Migration Issues
- **Missing Indexes**: Slow queries after adding new columns
- **Constraint Violations**: Foreign key errors during migration
- **Data Loss**: Irreversible operations without backups
- **Blocking Operations**: Long-running migrations causing downtime
- **Rollback Failures**: Pending down() methods

**Migration Files to Check:** $ARGUMENTS