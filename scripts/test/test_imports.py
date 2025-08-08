"""
Test script for verifying aaz-dev-tools compatibility
"""
import azdev
print(f"azdev version: {azdev.__VERSION__}")
print("azdev imported successfully")

# Test core modules can be loaded
import azdev.utilities
import azdev.operations
print("Core azdev modules loaded successfully")

# Test that dependencies are compatible
import schematics
import yaml
import flask
import jinja2
import jsonschema
import packaging
print("All aaz-dev-tools dependencies imported successfully")

print("=== SUCCESS: No dependency conflicts detected ===")
