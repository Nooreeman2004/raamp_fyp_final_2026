import re

# Read the file
with open('presentation/routers/onboarding_router.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix indentation: replace 8 spaces at start of lines with 4 spaces
# But only for function bodies (lines starting with 8 spaces)
lines = content.split('\n')
fixed_lines = []
in_function = False

for i, line in enumerate(lines):
    # Check if this is a function definition
    if line.strip().startswith('async def ') or line.strip().startswith('def '):
        in_function = True
        fixed_lines.append(line)
    # Check if line starts with exactly 8 spaces (wrong indentation)
    elif line.startswith('        ') and not line.startswith('                '):
        # Replace first 8 spaces with 4
        fixed_lines.append('    ' + line[8:])
    else:
        fixed_lines.append(line)

fixed_content = '\n'.join(fixed_lines)

# Write back
with open('presentation/routers/onboarding_router.py', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print("Indentation fixed!")
