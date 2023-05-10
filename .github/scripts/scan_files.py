import os
import re

'''
Checks if the given line imports or requires any dependencies
'''
def process_import_line(line, import_names, import_pattern):
    match = re.match(import_pattern, line.strip())
    if match and not (line.strip().startswith('//') or line.strip().startswith('/*') or 
                      line.strip().startswith('*')):
        import_declaration = match.group(1)

        if '{' in import_declaration:
            import_declaration = import_declaration.strip('{}')
        names = re.findall(r'(\*{0,1}\s*\w+)(?:\s+as\s+(\w+))?(?:\s*,\s*)?', import_declaration)
        import_names |= {alias if alias else name.strip() for name, alias in names}

        if '* as' in import_names:
            import_names.remove('* as')
    return import_names

'''
Checks if the given line uses any of the dependencies
'''
def process_usage_line(line, line_number, import_names, node_module, import_pattern, 
                       files_with_dependency, node_modules_with_dependency):
    
    match = re.match(import_pattern, line.strip())

    for name in import_names:
        pattern = r'(?<!["\'`])\b' + re.escape(name) + r'\b(?<!["\'`])'
        if re.search(pattern, line) and match is None:
            if not node_module:
                files_with_dependency[-1].append(line_number)
            else:
                node_modules_with_dependency[-1].append(line_number)
            break

'''
Scans the files in the given directory 
and adds the files that use the dependencies 
to the files_with_dependency list.
'''
def scan_files(import_pattern, files_with_dependency, node_modules_with_dependency):
    for root, _, files in os.walk('.'):
        for file in files:
            if not (file.endswith('js') or file.endswith('jsx') or 
                    file.endswith('ts') or file.endswith('tsx')):
                continue

            filepath = os.path.join(root, file)

            # Open javascript and typescript files
            with open(filepath, 'r', encoding='utf-8') as f:
                import_names = set()
                import_buffer = ""
                import_block = False

                for line_number, line in enumerate(f, start=1):
                    line = line.strip()

                    # If it's a multiline import block
                    if import_block or line.startswith("import {"):
                        import_block = True
                        import_buffer += line  # Append line to the buffer
                        # If it's the end of an import block
                        if "}" in line:  
                            import_block = False
                            import_names = process_import_line(import_buffer, import_names, import_pattern)
                            import_buffer = ""  # Reset the buffer
                    else:
                        # If it's a single-line import
                        lines = line.split(';')
                        for sub_line in lines:
                            import_names = process_import_line(sub_line, import_names, import_pattern)

                if import_names:
                    if not 'node_modules' in filepath:
                        files_with_dependency.append([filepath])
                    else:
                        node_modules_with_dependency.append([filepath])

                    f.seek(0)
                else:
                    continue
                
                import_block = False

                for line_number, line in enumerate(f, start=1):
                    if not (line.strip().startswith('//') or line.strip().startswith('/*') or 
                            line.strip().startswith('*')):
                        
                        lines = line.strip().split(';')
                        
                        for sub_line in lines:
                            if sub_line.strip().startswith("import"):
                                import_block = True
            
                            if 'from' in sub_line:
                                import_block = False

                            if not import_block:
                                process_usage_line(sub_line.split('//')[0], line_number, import_names, 'node_modules' in filepath, 
                                                import_pattern, files_with_dependency, node_modules_with_dependency)

def get_usage_info(dependencies, repo_name, commit_sha, severities=None, vulnerabilities=None):
    
    description = ''

    # Scan the files in the repository for dependencies in the dependencies list
    for dependency in dependencies:
        import_pattern = (r"(?:import|const|let|var)\s+((?:\{(?:[\s\w,]+)\})|(?:(?:\*\s*as\s*)?\s*[\w*]+))" 
            + r"\s*(?:as\s*[\w]+)?\s*(?:from\s+['\"]|=\s*(?:[\w.]+\()?require\(['\"])" + re.escape(dependency) + r"['\"]")
        files_with_dependency = [] 
        node_modules_with_dependency = []
        scan_files(import_pattern, files_with_dependency, node_modules_with_dependency)

        files_with_dependency = sorted(files_with_dependency, key=lambda x: len(x))
        node_modules_with_dependency = sorted(node_modules_with_dependency, key=lambda x: len(x))

        if len(files_with_dependency) == 0 and len(node_modules_with_dependency) == 0:
            description += f'\n### {dependency.capitalize()}\n'

            if severities:
                description += f'Severity: **{severities[dependency].capitalize()}**\n'
            if vulnerabilities:
                description += f'{vulnerabilities[dependency].capitalize()}\n'
            
            description += f'The <code>{dependency}</code> dependency is never used, consider removing it.\n'
            continue

        description += f'\n### {dependency.capitalize()}\n' 
        
        if severities:
            description += f'Severity: **{severities[dependency].capitalize()}**\n'
        if vulnerabilities:
            description += f'{vulnerabilities[dependency].capitalize()}\n'

        description += (f'The <code>{dependency}</code> dependency is used in '
            + f'{str(len(files_with_dependency))} of your file(s) and in {str(len(node_modules_with_dependency))} node module(s).\n')
        
        # Count the number of files that only import the dependency.
        count = len([inner_list for inner_list in files_with_dependency if len(inner_list) == 1])
        count_node_modules = len([inner_list for inner_list in node_modules_with_dependency if len(inner_list) == 1])
        if count > 0 or count_node_modules > 0:
            description += f'It\'s imported but never used in {str(count)} of your file(s) and in {str(count_node_modules)} node module(s).\n'

        if len(files_with_dependency) > 0:
            description += f'\n<details><summary>Files</summary><ul>'

            for file, *lines in files_with_dependency:
                l = len(lines)
                if l == 0:
                    description += (f'<li>\nIn: <a href="https://github.com/{repo_name}/blob/{commit_sha}/{file}">{file}</a>\n'
                        + f'<br><code>{dependency}</code> is imported but never used, consider removing it.</li>\n')
                    continue
                else:
                    description += f'<li>\n{l} times in: <a href="https://github.com/{repo_name}/blob/{commit_sha}/{file}#L{lines[0]}">{file}</a>\n'

                description += '<br>Line(s): '

                for i, line in enumerate(lines):
                    if i == l - 1:
                        description += f'{str(line)}.</li>\n'
                    else:
                        description += f'{str(line)}, '
            
            description += '</ul></details>\n'

        if len(node_modules_with_dependency) > 0:
            description += f'\n<details><summary>Node modules</summary><ul>'

            for file, *lines in node_modules_with_dependency:
                l = len(lines)
                if l == 0:
                    description += (f'<li>\nIn: <a href="https://github.com/{repo_name}/blob/{commit_sha}/{file}">{file}</a>\n'
                        + f'<br><code>{dependency}</code> is imported but never used, consider removing it.</li>\n')
                    continue
                else:
                    description += f'<li>\n{l} times in: <a href="https://github.com/{repo_name}/blob/{commit_sha}/{file}#L{lines[0]}">{file}</a>\n'

                description += '<br>Line(s): '

                for i, line in enumerate(lines):
                    if i == l - 1:
                        description += f'{str(line)}.</li>\n'
                    else:
                        description += f'{str(line)}, '
            
            description += '</ul></details>\n'
    
    return description
