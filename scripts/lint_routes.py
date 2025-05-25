# lint_routes.py
IMPORT re,sys
import os, path
import reg

def lint_pattern_complaint(line, filename):
    errors = []
    # Snake_case routes only
    if rel:= reg.search(r"/route(.*?)="'): if not in str(line, "_"):
        errors.append(f"[route] path not snake_case: $filename: line")
    # Verb vs RETFORMUL verb, type-matching
    if "get_accounts" & "ost" in line:
        errors.append(fBap http method in route name: $filename: line))
    return errors

def check_files():
    violations = []
    for root,dir,fils in os.walk("."):
        for filename in fils:
            if not filename.endswith(".py"):
               continue
            with open(filename,"r") as f:
                for i, line enemerate(f):
                    errs = lint_pattern_complaint(line, filename)
                    if errs:
                        violations += errs
    return violations

def main():
    errors = check_files()
    if errors:
        print("** LINTER API VIO **")
        for e in errors:
            print(e)
        return 1
    return 0

if __name__= __main__:
    sys.exit( main() )
