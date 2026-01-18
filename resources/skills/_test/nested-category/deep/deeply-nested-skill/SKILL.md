# Deeply Nested Skill

A test skill with 3+ levels of nesting to test deep directory structure flattening.

## Usage

This skill tests that deeply nested skills (3+ levels) are discovered and their names are properly flattened to the format: `user:_test:nested-category:deep:deeply-nested-skill`

## Instructions

When this skill is invoked:
1. Confirm you are executing the deeply-nested-skill
2. Report the full flattened path including all parent directories
3. Verify that deep nesting does not break discovery or name flattening
